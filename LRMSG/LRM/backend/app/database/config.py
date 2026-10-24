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

    _raw_db_url: str = os.environ.get("DATABASE_URL", "")
    DATABASE_URL: str = (
        "postgresql+psycopg2://" + _raw_db_url[len("postgresql://"):]
        if _raw_db_url.startswith("postgresql://")
        else _raw_db_url
    )

    # Alembic uses this for migration scripts
    _raw_sync_url: str = os.environ.get("DATABASE_URL_SYNC", "")
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://" + _raw_sync_url[len("postgresql://"):]
        if _raw_sync_url.startswith("postgresql://")
        else _raw_sync_url
    )

    DB_ECHO: bool = os.environ.get("DB_ECHO", "false").lower() == "true"

    def __init__(self):
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL must be set in environment or backend/.env. "
                "See backend/.env.example for configuration."
            )


settings = Settings()
