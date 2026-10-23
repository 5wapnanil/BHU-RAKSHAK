"""Backboard AI RAG integration package for PahaarPulse.

Exports settings, exceptions, models, and provider factories for the
PahaarPulse Landslide Knowledge Assistant.
"""

from backend.app.services.backboard.config import BackboardSettings, settings
from backend.app.services.backboard.exceptions import (
    BackboardAuthenticationError,
    BackboardConfigurationError,
    BackboardConnectionError,
    BackboardError,
    BackboardInvalidSessionError,
    BackboardMalformedOutputError,
    BackboardNotFoundError,
    BackboardQueryValidationError,
    BackboardRateLimitError,
    BackboardSessionError,
    BackboardSessionExpiredError,
    BackboardTemporaryUnavailableError,
    BackboardTimeoutError,
    InvalidSessionError,
    SessionExpiredError,
)
from backend.app.services.backboard.models import (
    DEFAULT_ASSISTANT_DISCLAIMER,
    AssistantQueryResponse,
    AssistantSessionPayload,
    AssistantThreadSession,
    BackboardMessageOutput,
    RetrievedDocument,
    SourceCitation,
)
from backend.app.services.backboard.providers import (
    BackboardProvider,
    LiveBackboardProvider,
    MockBackboardProvider,
    get_backboard_provider,
)

__all__ = [
    "BackboardSettings",
    "settings",
    "BackboardError",
    "BackboardConfigurationError",
    "BackboardConnectionError",
    "BackboardTimeoutError",
    "BackboardRateLimitError",
    "BackboardTemporaryUnavailableError",
    "BackboardAuthenticationError",
    "BackboardNotFoundError",
    "BackboardMalformedOutputError",
    "BackboardSessionError",
    "InvalidSessionError",
    "SessionExpiredError",
    "BackboardQueryValidationError",
    "BackboardInvalidSessionError",
    "BackboardSessionExpiredError",
    "RetrievedDocument",
    "BackboardMessageOutput",
    "SourceCitation",
    "AssistantSessionPayload",
    "AssistantThreadSession",
    "AssistantQueryResponse",
    "DEFAULT_ASSISTANT_DISCLAIMER",
    "BackboardProvider",
    "MockBackboardProvider",
    "LiveBackboardProvider",
    "get_backboard_provider",
]
