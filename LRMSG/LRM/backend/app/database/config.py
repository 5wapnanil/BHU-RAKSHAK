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

    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "",
    )

    # Alembic uses this for migration scripts
    DATABASE_URL_SYNC: str = os.environ.get(
        "DATABASE_URL_SYNC",
        "",
    )

    DB_ECHO: bool = os.environ.get("DB_ECHO", "false").lower() == "true"

    def __init__(self):
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL must be set in environment or backend/.env. "
                "See backend/.env.example for configuration."
            )


settings = Settings()
