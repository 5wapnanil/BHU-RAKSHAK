from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from backend.app.database.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check including PostgreSQL connectivity.

    NOTE: Error details are logged server-side only; clients receive safe generic messages.
    """
    result = {"status": "healthy", "database": {}}

    # PostgreSQL check
    try:
        db.execute(text("SELECT 1"))
        db.execute(text("SELECT COUNT(*) FROM emergency_requests"))
        result["database"]["postgresql"] = "connected"
    except Exception as e:
        logger.error(f"Health check PostgreSQL error: {e}")
        result["database"]["postgresql"] = "error"
        result["status"] = "degraded"

    # PostGIS check
    try:
        db.execute(text("SELECT PostGIS_Version()"))
        result["database"]["postgis"] = "available"
    except Exception as e:
        logger.error(f"Health check PostGIS error: {e}")
        result["database"]["postgis"] = "error"
        result["status"] = "degraded"

    # Table count check
    try:
        tables = db.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )).fetchall()
        result["database"]["table_count"] = len(tables)
    except Exception:
        result["database"]["table_count"] = "unknown"

    return result
