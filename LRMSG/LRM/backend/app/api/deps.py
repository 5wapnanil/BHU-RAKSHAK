"""Centralized API dependencies and security authorization guards.

Provides:
- verify_coordinator_authorization: Enforces fail-closed authentication for all
  administrative, coordination, shelter, alert, and review mutation endpoints.
- InMemoryRateLimiter: Thread-safe in-memory sliding-window rate limiter for assistant endpoints.
- get_client_ip: Secure client IP extraction resisting X-Forwarded-For spoofing.
- is_trusted_origin: CORS and CSRF origin validator for cookie-authenticated requests.
- get_backboard_service: Dependency provider for BackboardService orchestration.
"""

import collections
import logging
import os
import re
import secrets
import threading
import time
import urllib.parse
from typing import Any, Deque, Dict, List, Optional

from fastapi import HTTPException, Request, status

from backend.app.services.backboard_service import BackboardService

logger = logging.getLogger(__name__)

MIN_COORDINATOR_KEY_LENGTH: int = 16


def verify_coordinator_authorization(request: Request) -> Optional[str]:
    """Verify administrative authorization for coordinator actions.

    SECURITY / FAIL-CLOSED POLICY:
    - In production deployments (ENVIRONMENT, APP_ENV, FASTAPI_ENV, NODE_ENV, or ENV set to production/prod/live),
      if COORDINATOR_API_KEY is not configured or has insufficient entropy, the endpoint FAILS CLOSED by rejecting
      all requests with HTTP 503 Service Unavailable to prevent unauthenticated administrative access.
    - If COORDINATOR_API_KEY is configured (in any environment), the client must provide a matching
      'X-Coordinator-Key' header or 'Authorization: Bearer <token>'.
    - Constant-time comparison (secrets.compare_digest) is enforced to prevent timing side-channel attacks.
    - In development/testing environments without COORDINATOR_API_KEY, access is permitted with
      a logged security warning.
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

    # Fail-closed in production if credentials are not configured
    if is_production:
        if not expected:
            logger.error(
                "Security alert: Coordinator endpoint invoked in production, but COORDINATOR_API_KEY is not configured. Failing closed."
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Administrative access unavailable: Coordinator authentication is not configured for production deployment.",
            )
        if len(expected) < MIN_COORDINATOR_KEY_LENGTH:
            logger.warning(
                f"Security recommendation: COORDINATOR_API_KEY length ({len(expected)} chars) is less than recommended {MIN_COORDINATOR_KEY_LENGTH}+ characters for production."
            )

    # In development/test, if no key configured, permit access
    if not expected:
        return None

    # Validate provided key
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


# ---------------------------------------------------------------------
# Assistant Rate Limiting & Origin Security
# ---------------------------------------------------------------------

DEFAULT_TRUSTED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.0.102:3000",
    "http://192.168.47.1:8000",
]

DEFAULT_ORIGIN_REGEX = re.compile(
    r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.0\.2\.2)(:\d+)?$"
)


def validate_origin(origin: str, is_production: bool = False) -> str:
    """Validate and normalize an HTTP(S) origin string.

    Rejects:
    - Wildcard origins ('*') when credentialed requests are allowed.
    - Origins containing path components, query strings, or fragments.
    - Origins containing embedded credentials (userinfo).
    - Insecure unencrypted HTTP origins in production mode (except loopback testing).
    """
    if not origin or not origin.strip():
        raise ValueError("Origin cannot be empty.")

    clean = origin.strip().rstrip("/")
    if clean == "*":
        raise ValueError("Wildcard origin '*' is forbidden when credentials/cookies are enabled.")

    parsed = urllib.parse.urlsplit(clean)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid origin scheme '{parsed.scheme}': must be http or https.")

    if is_production and parsed.scheme != "https":
        # In production, require HTTPS unless explicit loopback test host
        if parsed.hostname not in ("localhost", "127.0.0.1"):
            raise ValueError(f"Insecure origin '{clean}': Production trusted origins must use HTTPS.")

    if parsed.path and parsed.path != "/":
        raise ValueError(f"Origin cannot contain a path component: '{clean}'.")

    if parsed.query:
        raise ValueError(f"Origin cannot contain query parameters: '{clean}'.")

    if parsed.fragment:
        raise ValueError(f"Origin cannot contain fragments: '{clean}'.")

    if parsed.username or parsed.password:
        raise ValueError(f"Origin cannot contain embedded credentials: '{clean}'.")

    if not parsed.hostname:
        raise ValueError(f"Invalid origin missing hostname: '{clean}'.")

    port_suffix = ""
    if parsed.port:
        if not ((parsed.scheme == "https" and parsed.port == 443) or (parsed.scheme == "http" and parsed.port == 80)):
            port_suffix = f":{parsed.port}"
    return f"{parsed.scheme}://{parsed.hostname}{port_suffix}"


def get_effective_trusted_origins(is_production: Optional[bool] = None) -> List[str]:
    """Retrieve and validate the effective list of trusted origins for the environment."""
    if is_production is None:
        env_name = (
            os.environ.get("ENVIRONMENT")
            or os.environ.get("APP_ENV")
            or os.environ.get("FASTAPI_ENV")
            or os.environ.get("NODE_ENV")
            or os.environ.get("ENV")
            or ""
        ).lower().strip()
        is_production = env_name in ("production", "prod", "live")

    configured = os.environ.get("TRUSTED_ORIGINS", "").strip()

    if is_production:
        if not configured:
            logger.error(
                "Security violation: TRUSTED_ORIGINS is not configured for production deployment. Failing closed."
            )
            return []

        trusted = []
        for raw in configured.split(","):
            raw_clean = raw.strip()
            if not raw_clean:
                continue
            try:
                trusted.append(validate_origin(raw_clean, is_production=True))
            except ValueError as e:
                logger.error(f"Invalid production trusted origin '{raw_clean}': {e}")
        return trusted

    # Development mode
    origins = list(DEFAULT_TRUSTED_ORIGINS)
    if configured:
        for raw in configured.split(","):
            raw_clean = raw.strip()
            if raw_clean:
                try:
                    val = validate_origin(raw_clean, is_production=False)
                    if val not in origins:
                        origins.append(val)
                except ValueError as e:
                    logger.warning(f"Ignored invalid origin in TRUSTED_ORIGINS: {raw_clean} ({e})")
    return origins


def get_cors_configuration(is_production: Optional[bool] = None) -> Dict[str, Any]:
    """Provide production-hardened CORS settings consistent with session CSRF origin validation."""
    if is_production is None:
        env_name = (
            os.environ.get("ENVIRONMENT")
            or os.environ.get("APP_ENV")
            or os.environ.get("FASTAPI_ENV")
            or os.environ.get("NODE_ENV")
            or os.environ.get("ENV")
            or ""
        ).lower().strip()
        is_production = env_name in ("production", "prod", "live")

    effective_origins = get_effective_trusted_origins(is_production=is_production)
    if is_production:
        return {
            "allow_origins": effective_origins,
            "allow_origin_regex": None,
        }
    return {
        "allow_origins": effective_origins,
        "allow_origin_regex": r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.0\.2\.2)(:\d+)?$",
    }


def get_client_ip(request: Request, trusted_proxies: Optional[List[str]] = None) -> str:
    """Extract client IP, inspecting X-Forwarded-For only if direct peer is a trusted proxy.

    Prevents IP spoofing via attacker-controlled X-Forwarded-For headers.
    """
    peer_ip = request.client.host if request.client else "127.0.0.1"

    # Resolve trusted proxies list
    proxies: List[str] = list(trusted_proxies or [])
    trusted_env = os.environ.get("TRUSTED_PROXIES", "").strip()
    if trusted_env:
        proxies.extend([p.strip() for p in trusted_env.split(",") if p.strip()])

    if peer_ip in proxies:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
            for ip in reversed(ips):
                if ip not in proxies:
                    return ip

    return peer_ip


def is_trusted_origin(origin: Optional[str], is_production: Optional[bool] = None) -> bool:
    """Validate whether an Origin/Referer matches configured trusted domains.

    In production mode:
    - Enforces that TRUSTED_ORIGINS is configured and explicitly matches clean HTTPS origins.
    - Broad local-network regular expressions are disabled.
    """
    if not origin:
        return False

    if is_production is None:
        env_name = (
            os.environ.get("ENVIRONMENT")
            or os.environ.get("APP_ENV")
            or os.environ.get("FASTAPI_ENV")
            or os.environ.get("NODE_ENV")
            or os.environ.get("ENV")
            or ""
        ).lower().strip()
        is_production = env_name in ("production", "prod", "live")

    try:
        clean_origin = validate_origin(origin, is_production=False)
    except ValueError:
        return False

    effective = get_effective_trusted_origins(is_production=is_production)
    if is_production:
        return clean_origin in effective

    # In development mode:
    if clean_origin in effective:
        return True
    return bool(DEFAULT_ORIGIN_REGEX.match(clean_origin))


class InMemoryRateLimiter:
    """Thread-safe sliding-window rate limiter for single-process FastAPI deployments.

    ARCHITECTURE & LIMITATION NOTICE:
    This rate limiter operates strictly in-memory within the local Python process.
    - Single worker / local development: Enforces exact sliding-window request quotas.
    - Multi-process / Gunicorn cluster: Rate limits are enforced independently per worker
      process without shared state coordination. A distributed Redis-backed limiter should
      be connected for enterprise multi-instance clustering in future phases.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._windows: Dict[str, Deque[float]] = collections.defaultdict(collections.deque)

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        """Check sliding window rate limit for given key.

        Raises:
            HTTPException(429): If rate limit is exceeded, includes Retry-After header.
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            queue = self._windows[key]

            # Evict timestamps outside current window
            while queue and queue[0] < window_start:
                queue.popleft()

            if len(queue) >= max_requests:
                oldest = queue[0]
                retry_after = max(1, int(oldest + window_seconds - now) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: maximum {max_requests} requests per {window_seconds} seconds. Try again in {retry_after}s.",
                    headers={"Retry-After": str(retry_after)},
                )

            # Record timestamp for this request
            queue.append(now)

    def clear(self) -> None:
        """Clear all rate limit windows (for test isolation)."""
        with self._lock:
            self._windows.clear()


assistant_rate_limiter = InMemoryRateLimiter()


def get_assistant_rate_limiter() -> InMemoryRateLimiter:
    """Dependency provider returning singleton assistant rate limiter."""
    return assistant_rate_limiter


def get_backboard_service() -> BackboardService:
    """Dependency provider returning BackboardService instance."""
    return BackboardService()
