from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import os
import uuid
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.database.base import get_db
from backend.app.services.emergency_request_service import EmergencyRequestService

logger = logging.getLogger(__name__)

router = APIRouter()

# ── JSON fallback (dual-write mode) ────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "incidents_db.json"

# Try to import DB settings; if DB is unreachable, fall back to JSON-only mode
_db_available = True
try:
    from backend.app.database.config import settings as db_settings
    from sqlalchemy import create_engine, text
    _test_engine = create_engine(db_settings.DATABASE_URL, pool_pre_ping=True)
    with _test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    _test_engine.dispose()
    logger.info("PostgreSQL connection verified — dual-write mode active")
except Exception as e:
    _db_available = False
    logger.warning(f"PostgreSQL not available ({e}) — falling back to JSON-only mode")


class OperationPayload(BaseModel):
    id: str
    operation: str
    entity: str
    payload: Dict[str, Any]
    createdAt: str


class SyncBatch(BaseModel):
    operations: List[OperationPayload]


# ── JSON fallback helpers ───────────────────────────────────

def load_incidents() -> List[Dict[str, Any]]:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_incidents(incidents: List[Dict[str, Any]]):
    with open(DB_FILE, "w") as f:
        json.dump(incidents, f, indent=2)


# ── Endpoints ───────────────────────────────────────────────

@router.post("/upload")
async def sync_upload(
    batch: SyncBatch,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Sync endpoint: writes emergency requests and field reports to PostgreSQL (primary) and JSON (fallback).

    Idempotency: operations with the same `id` are detected across DB and persistent sync store.
    """
    success_ids: List[str] = []
    failed_ids: List[str] = []
    db_results: List[Dict[str, Any]] = []

    # Preload existing persistent operations for cross-store idempotency
    incidents = load_incidents()
    prior_synced_ops = {inc.get("_op_id") for inc in incidents if inc.get("_op_id")}

    # ── PostgreSQL path (primary) ────────────────────────────
    if _db_available:
        svc = EmergencyRequestService(db)
        try:
            for op in batch.operations:
                if op.operation != "CREATE":
                    failed_ids.append(op.id)
                    continue

                if op.entity == "incident_report":
                    result = svc.process_operation(op_id=op.id, payload=op.payload)
                    db_results.append({"op_id": op.id, **result})

                    if result["status"] in ("synced", "idempotent"):
                        success_ids.append(op.id)
                    else:
                        failed_ids.append(op.id)
                elif op.entity == "field_report":
                    # Check idempotency: skip if already processed in prior sync
                    if op.id in prior_synced_ops:
                        db_results.append({"op_id": op.id, "status": "idempotent"})
                        if op.id not in success_ids:
                            success_ids.append(op.id)
                        continue

                    try:
                        from backend.app.services.field_report_service import FieldReportService
                        from backend.app.services.photo_storage_service import photo_storage_service
                        import base64
                        import io

                        p = op.payload or {}
                        photo_url = p.get("photo_url")
                        photo_data = p.get("photo_data") or p.get("photo_data_url")
                        if not photo_url and photo_data:
                            try:
                                if "," in photo_data:
                                    header_part, b64_str = photo_data.split(",", 1)
                                    mime = header_part.split(":")[1].split(";")[0] if ":" in header_part else "image/jpeg"
                                else:
                                    b64_str = photo_data
                                    mime = p.get("photo_mime") or "image/jpeg"
                                b64_str = b64_str.strip()
                                missing_pad = len(b64_str) % 4
                                if missing_pad:
                                    b64_str += "=" * (4 - missing_pad)
                                raw_bytes = base64.b64decode(b64_str)
                                saved_url, _, _ = photo_storage_service.save_photo(
                                    io.BytesIO(raw_bytes),
                                    content_type=mime,
                                    size_hint=len(raw_bytes),
                                )
                                photo_url = saved_url
                            except Exception as photo_err:
                                logger.warning(f"Failed to decode queued photo for {op.id}: {photo_err}")

                        fr_svc = FieldReportService(db)
                        created_report = fr_svc.create_report(
                            notes=p.get("notes") or p.get("description"),
                            location_name=p.get("location_name") or p.get("location"),
                            latitude=p.get("latitude"),
                            longitude=p.get("longitude"),
                            reporter_name=p.get("reporter_name") or p.get("contactName"),
                            reporter_phone=p.get("reporter_phone") or p.get("contactPhone"),
                            photo_url=photo_url,
                        )
                        db_results.append({"op_id": op.id, "report_id": str(created_report.id), "status": "synced"})
                        success_ids.append(op.id)

                        # Enqueue background AI screening if available
                        try:
                            from backend.app.api.endpoints.field_reports import _run_background_ai_analysis
                            background_tasks.add_task(_run_background_ai_analysis, created_report.id)
                        except Exception as bg_err:
                            logger.warning(f"Could not enqueue AI background analysis for {created_report.id}: {bg_err}")

                    except Exception as fr_err:
                        logger.error(f"Failed to process queued field_report {op.id}: {fr_err}")
                        failed_ids.append(op.id)
                else:
                    failed_ids.append(op.id)

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"DB sync batch failed: {e}")
            # Mark all remaining as failed
            for op in batch.operations:
                if op.id not in success_ids and op.id not in failed_ids:
                    failed_ids.append(op.id)

    # ── JSON fallback / dual-write ───────────────────────────
    for op in batch.operations:
        if op.entity not in ("incident_report", "field_report") or op.operation != "CREATE":
            continue

        # Skip operations already failed by the DB path
        if op.id in failed_ids:
            continue

        if op.id in prior_synced_ops:
            if op.id not in success_ids:
                success_ids.append(op.id)
            continue

        try:
            new_incident = op.payload.copy()
            new_incident["_op_id"] = op.id
            new_incident["id"] = str(uuid.uuid4())
            new_incident["sync_time"] = op.createdAt
            new_incident["_db_synced"] = op.id in success_ids
            incidents.append(new_incident)
            prior_synced_ops.add(op.id)
            if op.id not in success_ids:
                success_ids.append(op.id)
        except Exception as e:
            logger.error(f"JSON sync failed for {op.id}: {e}")
            if op.id not in failed_ids:
                failed_ids.append(op.id)

    save_incidents(incidents)

    return {
        "success": True,
        "success_ids": success_ids,
        "failed_ids": failed_ids,
        "db_results": db_results if _db_available else None,
        "mode": "dual-write" if _db_available else "json-only",
    }


@router.get("/health")
async def sync_health(db: Session = Depends(get_db)):
    """Quick health check for the sync subsystem."""
    db_ok = False
    if _db_available:
        try:
            svc = EmergencyRequestService(db)
            svc.get_all_requests(limit=1)
            db_ok = True
        except Exception:
            db_ok = False

    return {
        "status": "healthy",
        "db_connected": db_ok,
        "mode": "dual-write" if db_ok else "json-only",
    }
