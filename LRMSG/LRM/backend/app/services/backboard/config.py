"""Configuration loader for Backboard RAG Knowledge Assistant.

Reads configuration from environment or .env, providing safe offline defaults
and validation helpers without making any remote network calls.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Ensure backend/.env is loaded following project conventions
_backend_dir = Path(__file__).resolve().parents[3]
load_dotenv(_backend_dir / ".env")


class BackboardSettings:
    """Configuration settings for Backboard AI RAG integration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        assistant_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        provider: Optional[str] = None,
        session_signing_key: Optional[str] = None,
        session_expiry_hours: Optional[int] = None,
    ):
        self.api_key: str = (
            api_key if api_key is not None else os.environ.get("BACKBOARD_API_KEY", "")
        ).strip()

        raw_base_url = (
            base_url
            if base_url is not None
            else os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
        ).strip()
        self.base_url: str = raw_base_url.rstrip("/") if raw_base_url else "https://app.backboard.io/api"

        self.assistant_id: str = (
            assistant_id
            if assistant_id is not None
            else os.environ.get("BACKBOARD_ASSISTANT_ID", "")
        ).strip()

        raw_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else os.environ.get("BACKBOARD_TIMEOUT_SECONDS", "60.0")
        )
        try:
            self.timeout_seconds: float = float(raw_timeout)
        except (ValueError, TypeError):
            self.timeout_seconds = 60.0

        self.provider: str = (
            provider
            if provider is not None
            else os.environ.get("BACKBOARD_PROVIDER", "mock")
        ).strip().lower()

        self.session_signing_key: str = (
            session_signing_key
            if session_signing_key is not None
            else os.environ.get("SESSION_SIGNING_KEY", "")
        ).strip()

        raw_expiry = (
            session_expiry_hours
            if session_expiry_hours is not None
            else os.environ.get("SESSION_EXPIRY_HOURS", "24")
        )
        try:
            self.session_expiry_hours: int = int(raw_expiry)
        except (ValueError, TypeError):
            self.session_expiry_hours = 24

    @property
    def is_configured(self) -> bool:
        """Return True if live Backboard API credentials and assistant ID are provided."""
        return bool(self.api_key and self.assistant_id)

    # Uppercase aliases for compatibility with spec
    @property
    def API_KEY(self) -> str:
        return self.api_key

    @property
    def BASE_URL(self) -> str:
        return self.base_url

    @property
    def ASSISTANT_ID(self) -> str:
        return self.assistant_id

    @property
    def TIMEOUT_SECONDS(self) -> float:
        return self.timeout_seconds

    @property
    def PROVIDER(self) -> str:
        return self.provider

    @property
    def SESSION_SIGNING_KEY(self) -> str:
        return self.session_signing_key

    @property
    def SESSION_EXPIRY_HOURS(self) -> int:
        return self.session_expiry_hours


# Default singleton instance
settings = BackboardSettings()
