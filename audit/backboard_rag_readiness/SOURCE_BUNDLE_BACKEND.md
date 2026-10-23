# PahaarPulse — Sanitized Backend Source Bundle for Backboard RAG Integration

This document contains key backend architectural files illustrating application entry, routing, database session handling, security guards, service orchestration, and third-party AI integration patterns.

---

## 1. Dependency Manifest: `backend/requirements.txt`

```text
requests>=2.32,<3
earthengine-api>=1.6,<2
fastapi
uvicorn
pydantic
pandas
numpy
scikit-learn
xgboost
pytest

# ── Database (STEP 7H) ──
sqlalchemy>=2.0,<3
psycopg2-binary>=2.9,<3
alembic>=1.14,<2
```

---

## 2. Environment Configuration Template: `backend/.env.example`

```bash
# ── SMS Configuration ──
TWOFACTOR_API_KEY=your_2factor_api_key_here
TWOFACTOR_SENDER_ID=
SMS_ENABLED=false
SMS_PROVIDER=2factor

# ── PostgreSQL Database ──
# For Docker Compose: use service name "db" as host
# For local PostgreSQL: use "localhost"
DATABASE_URL=postgresql://lrm:lrm_password@localhost:5432/lrm_db
DATABASE_URL_SYNC=postgresql://lrm:lrm_password@localhost:5432/lrm_db
DB_ECHO=false

# ── Docker Compose (used by docker-compose.yml) ──
DB_PORT=5432
DB_NAME=lrm_db
DB_USER=lrm
DB_PASSWORD=lrm_password
```

---

## 3. Database Infrastructure: `docker-compose.yml`

```yaml
# LRM SG — PostgreSQL + PostGIS for local development
# STEP 7H: Database infrastructure

services:
  db:
    image: postgis/postgis:16-3.4
    container_name: lrm_postgres
    restart: unless-stopped
    ports:
      - "${DB_PORT:-5432}:5432"
    environment:
      POSTGRES_DB: ${DB_NAME:-lrm_db}
      POSTGRES_USER: ${DB_USER:-lrm}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-lrm_password}
    volumes:
      - lrm_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-lrm} -d ${DB_NAME:-lrm_db}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  lrm_pgdata:
```

---

## 4. Application Entry Point: `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.endpoints.health import router as health_router
from backend.app.api.endpoints.prediction import router as prediction_router
from backend.app.api.endpoints.environment import router as environment_router
from backend.app.api.analytics import router as analytics_router

app = FastAPI(
    title="Landslide Risk Management API",
    description="Backend API for the layered landslide risk prediction system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.102:3000",
        "http://192.168.47.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.0\.2\.2)(:\d+)?$",
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
```

---

## 5. Security & Authorization Guard: `backend/app/api/deps.py`

```python
"""Centralized API dependencies and security authorization guards.

Provides:
- verify_coordinator_authorization: Enforces fail-closed authentication for all
  administrative, coordination, shelter, alert, and review mutation endpoints.
"""

import logging
import os
import secrets
from typing import Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


def verify_coordinator_authorization(request: Request) -> Optional[str]:
    """Verify administrative authorization for coordinator actions.

    SECURITY / FAIL-CLOSED POLICY:
    - In production deployments, if COORDINATOR_API_KEY is not configured, the endpoint
      FAILS CLOSED by rejecting all requests with HTTP 503.
    - If COORDINATOR_API_KEY is configured, the client must provide a matching
      'X-Coordinator-Key' header or 'Authorization: Bearer <token>'.
    - Constant-time comparison (secrets.compare_digest) is enforced.
    - In development/testing environments without COORDINATOR_API_KEY, access is permitted.
    """
    env_name = (
        os.environ.get("ENVIRONMENT")
        or os.environ.get("APP_ENV")
        or os.environ.get("FASTAPI_ENV")
        or os.environ.get("NODE_ENV")
        or os.environ.get("ENV")
        or ""
    ).lower().strip()
    is_production = env_name in ("production", "prod", "live")

    expected = os.environ.get("COORDINATOR_API_KEY", "").strip()

    if is_production and not expected:
        logger.error(
            "Security alert: Coordinator endpoint invoked in production, but COORDINATOR_API_KEY is not configured. Failing closed."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrative access unavailable: Coordinator authentication is not configured for production deployment.",
        )

    if not expected:
        return None

    provided = request.headers.get("X-Coordinator-Key")
    if not provided:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided = auth_header[7:].strip()

    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Valid coordinator credentials required.",
        )
    return provided
```

---

## 6. Database Session Configuration: `backend/app/database/base.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 7. Database Config Loader: `backend/app/database/config.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend/ directory
_backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_backend_dir / ".env")


class Settings:
    """Database configuration from environment variables.

    All secrets are read from environment variables.
    Never hardcode credentials — use backend/.env for local development.
    """

    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    DATABASE_URL_SYNC: str = os.environ.get("DATABASE_URL_SYNC", "")
    DB_ECHO: bool = os.environ.get("DB_ECHO", "false").lower() == "true"

    def __init__(self):
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL must be set in environment or backend/.env. "
                "See backend/.env.example for configuration."
            )


settings = Settings()
```

---

## 8. AI Provider Protocol & Exception Hierarchy: `backend/app/services/gemma_providers.py` (Excerpts)

```python
"""Provider-independent AI inference boundary.
Demonstrates existing exception hierarchy and abstract protocol.
"""
from typing import Optional, Protocol, Tuple

class GemmaProviderError(Exception):
    """Base exception for AI provider inference failures."""
    pass

class GemmaProviderUnavailableError(GemmaProviderError):
    """Raised when configured provider runtime or credentials are not available."""
    pass

class GemmaTimeoutError(GemmaProviderError):
    """Raised when model inference times out."""
    pass

class GemmaRateLimitError(GemmaProviderError):
    """Raised when inference request is rate limited (HTTP 429)."""
    pass

class GemmaTemporaryUnavailableError(GemmaProviderError):
    """Raised when provider is temporarily unavailable or overloaded (HTTP 503)."""
    pass

class GemmaMalformedOutputError(GemmaProviderError):
    """Raised when model response cannot be parsed into the expected schema."""
    pass

class AnalysisProvider(Protocol):
    """Abstract protocol for AI hazard analysis."""
    @property
    def provider_name(self) -> str:
        ...

    async def analyze(
        self,
        image_bytes: bytes,
        mime_type: str,
        notes: Optional[str] = None,
        location_name: Optional[str] = None,
    ) -> "GemmaHazardOutput":
        ...
```
