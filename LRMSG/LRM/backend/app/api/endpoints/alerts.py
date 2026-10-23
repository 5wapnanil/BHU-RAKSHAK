from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
import asyncio
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.app.services.alert_engine import alert_engine
from backend.app.api.schemas.coordination import AlertResponse
from backend.app.api.deps import verify_coordinator_authorization
from backend.app.database.base import get_db
from backend.app.database.repositories.alert_repository import AlertRepository

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    queue = asyncio.Queue()
    alert_engine.add_listener(queue)
    
    try:
        # Send initial state (sort descending by created_at or updated_at, we'll just send all)
        active_alerts = [a for a in alert_engine.alerts.values() if a['status'] != 'RESOLVED']
        await websocket.send_json({"type": "INITIAL_STATE", "alerts": active_alerts})
        
        while True:
            # Wait for messages from the engine
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        alert_engine.remove_listener(queue)

@router.get("/")
def get_all_alerts():
    return [a for a in alert_engine.alerts.values()]

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    alert = await alert_engine.update_status(alert_id, "ACKNOWLEDGED")
    if alert is None:
        # Try DB lookup for alerts created via DB-first path
        repo = AlertRepository(db)
        from uuid import UUID as _UUID
        try:
            db_alert = repo.update_alert_status(_UUID(alert_id), "ACKNOWLEDGED")
            if db_alert:
                db.commit()
                return {"status": "success", "alert": AlertResponse.model_validate(db_alert).model_dump()}
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "alert": alert}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    alert = await alert_engine.update_status(alert_id, "RESOLVED")
    if alert is None:
        repo = AlertRepository(db)
        from uuid import UUID as _UUID
        try:
            db_alert = repo.update_alert_status(_UUID(alert_id), "RESOLVED")
            if db_alert:
                db.commit()
                return {"status": "success", "alert": AlertResponse.model_validate(db_alert).model_dump()}
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "alert": alert}


@router.post("/{alert_id}/responding")
async def responding_alert(
    alert_id: str,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
    db: Session = Depends(get_db),
):
    alert = await alert_engine.update_status(alert_id, "UNDER_RESPONSE")
    if alert is None:
        repo = AlertRepository(db)
        from uuid import UUID as _UUID
        try:
            db_alert = repo.update_alert_status(_UUID(alert_id), "UNDER_RESPONSE")
            if db_alert:
                db.commit()
                return {"status": "success", "alert": AlertResponse.model_validate(db_alert).model_dump()}
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "alert": alert}

# Demo Mode endpoint
@router.post("/demo/trigger")
async def trigger_demo_alert(
    payload: dict,
    _auth: Optional[str] = Depends(verify_coordinator_authorization),
):
    # payload: {lat, lng, prob, rainfall, slope, soil, location_name, district, state, title}
    await alert_engine.evaluate_prediction(
        location_id=f"demo_{payload.get('district', 'unknown')}",
        location_name=payload.get('location_name', 'Demo Location'),
        district=payload.get('district', 'Demo District'),
        state=payload.get('state', 'Demo State'),
        lat=payload.get('lat', 27.0),
        lng=payload.get('lng', 93.0),
        probability=payload.get('prob', 0.9),
        rainfall=payload.get('rainfall', 120.0),
        soil=payload.get('soil', 0.8),
        slope=payload.get('slope', 35.0),
        demo_mode=True,
        title=payload.get('title'),
    )
    return {"status": "demo alert triggered"}


# ── DB-First Endpoints (PostgreSQL) ──

VALID_SEVERITIES = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
VALID_STATUSES = {"ACTIVE", "ACKNOWLEDGED", "UNDER_RESPONSE", "RESOLVED"}


@router.get("/list", response_model=List[AlertResponse], tags=["alerts"])
def list_alerts_db(
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List alerts from PostgreSQL. Used by the coordinator dashboard."""
    from backend.app.database.models import Alert
    q = db.query(Alert)

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
        q = q.filter(Alert.status == status)

    if severity:
        if severity not in VALID_SEVERITIES:
            raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {VALID_SEVERITIES}")
        q = q.filter(Alert.severity == severity)

    q = q.order_by(Alert.created_at.desc())
    alerts = q.offset(skip).limit(limit).all()
    return alerts


@router.get("/list/{alert_id}", response_model=AlertResponse, tags=["alerts"])
def get_alert_db(
    alert_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single alert from PostgreSQL. Used by the coordinator dashboard."""
    repo = AlertRepository(db)
    alert = repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
