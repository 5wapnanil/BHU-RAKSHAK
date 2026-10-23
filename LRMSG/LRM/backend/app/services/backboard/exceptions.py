"""Provider exception hierarchy for Backboard AI RAG integration.

Defines standardized, typed exceptions for Backboard provider interactions,
mirroring the pattern in backend/app/services/gemma_providers.py.
"""


class BackboardError(Exception):
    """Base exception for all Backboard integration errors."""
    pass


class BackboardConfigurationError(BackboardError):
    """Raised when configuration or credentials are missing or invalid."""
    pass


class BackboardConnectionError(BackboardError):
    """Raised when network connection to Backboard fails."""
    pass


class BackboardTimeoutError(BackboardError):
    """Raised when a request to Backboard times out."""
    pass


class BackboardRateLimitError(BackboardError):
    """Raised when Backboard rate limits a request (HTTP 429)."""
    pass


class BackboardTemporaryUnavailableError(BackboardError):
    """Raised when Backboard or its upstream model is unavailable (HTTP 503)."""
    pass


class BackboardAuthenticationError(BackboardError):
    """Raised when authentication fails (HTTP 401)."""
    pass


class BackboardNotFoundError(BackboardError):
    """Raised when a requested resource (assistant, thread, document) is not found (HTTP 404)."""
    pass


class BackboardMalformedOutputError(BackboardError):
    """Raised when Backboard returns unparseable or schema-invalid output."""
    pass


class BackboardSessionError(BackboardError):
    """Base exception for assistant session and token validation failures."""
    pass


class InvalidSessionError(BackboardSessionError):
    """Raised when an assistant session token is missing, malformed, or tampered."""
    pass


class SessionExpiredError(BackboardSessionError):
    """Raised when an assistant session token has exceeded its configured lifetime."""
    pass


class BackboardQueryValidationError(BackboardError):
    """Raised when an assistant query is empty, whitespace, or exceeds character limits."""
    pass


# Backward-compatible aliases
BackboardInvalidSessionError = InvalidSessionError
BackboardSessionExpiredError = SessionExpiredError

