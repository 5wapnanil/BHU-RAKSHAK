from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.deps import get_cors_configuration
from backend.app.api.endpoints.health import router as health_router
from backend.app.api.endpoints.prediction import router as prediction_router
from backend.app.api.endpoints.environment import router as environment_router
from backend.app.api.analytics import router as analytics_router

app = FastAPI(
    title="Landslide Risk Management API",
    description="Backend API for the layered landslide risk prediction system",
    version="1.0.0",
)

cors_config = get_cors_configuration()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_origin_regex=cors_config["allow_origin_regex"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# API Routers
# ---------------------------------------------------------------------

from backend.app.api.endpoints.gis import router as gis_router
from backend.app.api.endpoints.alerts import router as alerts_router
from backend.app.api.endpoints.risk_zones import router as risk_zones_router
from backend.app.api.endpoints.sync import router as sync_router
from backend.app.api.endpoints.coordination import router as coordination_router
from backend.app.api.endpoints.field_reports import router as field_reports_router
from backend.app.api.endpoints.assistant import router as assistant_router
from starlette.staticfiles import StaticFiles
from backend.app.services.photo_storage_service import photo_storage_service

app.include_router(health_router)
app.include_router(prediction_router)
app.include_router(environment_router)
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(gis_router, prefix="/api/gis", tags=["gis"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
app.include_router(risk_zones_router)
app.include_router(sync_router, prefix="/api/sync", tags=["sync"])
app.include_router(coordination_router, prefix="/api", tags=["coordination"])
app.include_router(field_reports_router, prefix="/api/field-reports", tags=["field-reports"])
app.include_router(assistant_router, prefix="/api/assistant", tags=["assistant"])


# Mount static uploads directory for field photographs
uploads_base_dir = photo_storage_service.upload_dir.parent
uploads_base_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_base_dir)), name="uploads")


# ---------------------------------------------------------------------
# Startup: attach DB session to alert_engine for dual-write
# ---------------------------------------------------------------------

@app.on_event("startup")
def attach_db_to_alert_engine():
    """Attach the SQLAlchemy session factory to alert_engine for PostgreSQL dual-write."""
    try:
        from backend.app.database.base import SessionLocal
        from backend.app.services.alert_engine import alert_engine
        alert_engine.attach_db_session(SessionLocal)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not attach DB to alert_engine: {e}")
