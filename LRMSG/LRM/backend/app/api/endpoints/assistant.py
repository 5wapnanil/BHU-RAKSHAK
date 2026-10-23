"""FastAPI route endpoints for PahaarPulse Backboard AI Knowledge Assistant.

Endpoints:
- POST /api/assistant/threads — Initialize an isolated conversation thread session.
- POST /api/assistant/query   — Submit a query within a verified thread session.

TRANSPORT MODES:
1. Web Browsers (transport='cookie'):
   - Token set in HttpOnly, SameSite=Lax, Secure-in-production cookie ('pp_assistant_session').
   - JSON response omits session_token.
   - CSRF/Origin verification enforced on cookie-authenticated queries.
2. Native Mobile / Non-Browser (transport='bearer'):
   - Token returned in JSON response body.
   - Client presents token via standard 'Authorization: Bearer <token>' header.
   - Does not set or require cookies.

SECURITY NOTICE:
These endpoints implement anonymous thread session isolation.
They prevent cross-conversation snooping and client-controlled thread substitution.
They do not establish verified human user identity or account-level ownership.
"""

import logging
from typing import Literal, Optional
import urllib.parse

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)

from backend.app.api.deps import (
    InMemoryRateLimiter,
    get_assistant_rate_limiter,
    get_backboard_service,
    get_client_ip,
    is_trusted_origin,
)
from backend.app.api.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    AssistantThreadCreateResponse,
    SourceCitationSchema,
)
from backend.app.services.backboard.exceptions import (
    BackboardAuthenticationError,
    BackboardQueryValidationError,
    BackboardRateLimitError,
    BackboardTemporaryUnavailableError,
    BackboardTimeoutError,
    InvalidSessionError,
    SessionExpiredError,
)
from backend.app.services.backboard.models import AssistantThreadSession
from backend.app.services.backboard_service import BackboardService

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limit policies approved in Phase 1
THREAD_CREATION_RATE_LIMIT_REQUESTS: int = 5
THREAD_CREATION_RATE_LIMIT_WINDOW_SECONDS: int = 3600  # 1 hour

QUERY_RATE_LIMIT_REQUESTS: int = 10
QUERY_RATE_LIMIT_WINDOW_SECONDS: int = 60  # 1 minute

COOKIE_NAME: str = "pp_assistant_session"
COOKIE_PATH: str = "/api/assistant"


@router.post(
    "/threads",
    response_model=AssistantThreadCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize conversation thread session",
    description=(
        "Initializes a server-side Backboard conversation thread and returns a signed "
        "HMAC-SHA256 session token. Supports 'cookie' transport for web browsers and "
        "'bearer' transport for native mobile clients."
    ),
)
async def create_assistant_thread(
    request: Request,
    response: Response,
    transport: Literal["cookie", "bearer"] = Query(
        "cookie",
        description="Session transport mechanism: 'cookie' for web browsers, 'bearer' for mobile apps.",
    ),
    service: BackboardService = Depends(get_backboard_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_assistant_rate_limiter),
) -> AssistantThreadCreateResponse:
    """Initialize an isolated assistant conversation session."""
    # Enforce thread creation rate limit per client IP
    client_ip = get_client_ip(request)
    rate_limiter.check_rate_limit(
        key=f"threads:ip:{client_ip}",
        max_requests=THREAD_CREATION_RATE_LIMIT_REQUESTS,
        window_seconds=THREAD_CREATION_RATE_LIMIT_WINDOW_SECONDS,
    )

    # For web cookie transport, validate Origin if provided
    if transport == "cookie":
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if origin:
            # Normalize Referer to Origin
            parsed = urllib.parse.urlparse(origin)
            check_origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else origin
            if not is_trusted_origin(check_origin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Untrusted request origin for web session initialization.",
                )

    # Initialize server thread and issue cryptographically signed session token
    try:
        session: AssistantThreadSession = await service.create_thread_session()
    except BackboardTimeoutError:
        logger.warning("Upstream Backboard timeout during thread creation.")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream AI knowledge service timed out during thread creation.",
        )
    except BackboardRateLimitError:
        logger.warning("Upstream Backboard rate limit during thread creation.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Upstream AI knowledge service rate limit exceeded. Please try again later.",
        )
    except BackboardTemporaryUnavailableError:
        logger.warning("Upstream Backboard temporarily unavailable during thread creation.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upstream AI knowledge service is temporarily unavailable. Please try again later.",
        )
    except BackboardAuthenticationError:
        logger.error("Upstream Backboard authentication error during thread creation.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI knowledge service authentication failure.",
        )


    if transport == "cookie":
        # Web browser transport: Set HttpOnly, scoped cookie; omit token from JSON body
        response.set_cookie(
            key=COOKIE_NAME,
            value=session.session_token,
            httponly=True,
            secure=service.is_production,
            samesite="lax",
            path=COOKIE_PATH,
            max_age=service.session_expiry_seconds,
        )
        return AssistantThreadCreateResponse(
            transport="cookie",
            expires_at=session.expires_at,
            session_token=None,
        )

    # Native mobile / bearer transport: Return session token in response body; no cookie
    return AssistantThreadCreateResponse(
        transport="bearer",
        expires_at=session.expires_at,
        session_token=session.session_token,
    )


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit query to knowledge assistant",
    description=(
        "Submits a user query within a verified conversation thread. "
        "Accepts session token via 'Authorization: Bearer <token>' header or "
        "'pp_assistant_session' HttpOnly cookie. Returns grounded answer with citations."
    ),
)
async def query_assistant(
    request: Request,
    payload: AssistantQueryRequest,
    service: BackboardService = Depends(get_backboard_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_assistant_rate_limiter),
) -> AssistantQueryResponse:
    """Submit a question within a verified thread session."""
    # 1. Extract session token from Authorization header or HttpOnly cookie
    token: Optional[str] = None
    is_cookie_auth: bool = False

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        is_cookie_auth = False
    elif COOKIE_NAME in request.cookies:
        token = request.cookies.get(COOKIE_NAME, "").strip()
        is_cookie_auth = True

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No assistant session token or cookie provided.",
        )

    # 2. For cookie-authenticated requests, enforce CSRF/Origin validation
    if is_cookie_auth:
        origin = request.headers.get("Origin")
        if not origin:
            referer = request.headers.get("Referer", "")
            if referer:
                parsed = urllib.parse.urlparse(referer)
                origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""

        if not origin or not is_trusted_origin(origin):
            logger.warning(
                f"Rejected cookie-authenticated assistant query with untrusted or missing origin: {origin or 'None'}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Untrusted or missing request origin for cookie-authenticated request.",
            )

    # 3. Cryptographically verify session token to extract session_id for rate limiting
    try:
        session_payload = service.verify_session_token(token)
    except SessionExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assistant session token has expired. Please initialize a new thread session.",
        )
    except InvalidSessionError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or tampered assistant session token.",
        )

    # 4. Enforce query rate limit per verified session ID
    rate_limiter.check_rate_limit(
        key=f"queries:session:{session_payload.session_id}",
        max_requests=QUERY_RATE_LIMIT_REQUESTS,
        window_seconds=QUERY_RATE_LIMIT_WINDOW_SECONDS,
    )

    # 5. Dispatch query through orchestration service
    try:
        result = await service.query(
            session_token=token,
            query=payload.query,
            enable_fallback=True,
        )

        sources_schema = [
            SourceCitationSchema(
                title=s.title,
                document_id=s.document_id,
                url_or_slug=s.url_or_slug,
                category=s.category,
                is_curated=s.is_curated,
            )
            for s in result.sources
        ]

        return AssistantQueryResponse(
            reply=result.reply,
            sources=sources_schema,
            disclaimer=result.disclaimer,
            fallback_mode=result.fallback_mode,
        )

    except BackboardQueryValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except (SessionExpiredError, InvalidSessionError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except BackboardAuthenticationError:
        logger.error("Upstream Backboard authentication error during assistant query.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream AI knowledge service authentication failure.",
        )
    except Exception as e:
        logger.error(f"Unexpected error during assistant query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal assistant service error.",
        )
