"""Orchestration and security service for PahaarPulse Backboard AI RAG Assistant.

Implements:
1. Server-managed thread lifecycle bound to cryptographically signed HMAC-SHA256 session tokens.
2. Constant-time token signature validation, expiration checking, and payload versioning.
3. Strict session-to-thread binding (client never provides or controls raw Backboard thread IDs).
4. Curated source citation enrichment against a trusted domain knowledge manifest.
5. Fail-closed configuration safeguards for production environments.
6. Resilient fallback handling for transient upstream provider outages.

SECURITY NOTICE & AUTHENTICATION LIMITATIONS:
This service provides an interim, stateless, anonymous-session authorization mechanism.
It guarantees thread isolation (preventing cross-session snooping without possession of a
cryptographically valid token) and prevents client-side thread substitution.
However:
- It is NOT full user authentication.
- It does not verify user identity.
- A stolen token can be presented until expiration (token revocation requires server-side state).
- Future milestones will introduce authenticated user identity and database-backed ownership.
"""

import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any, Dict, List, Optional

from backend.app.services.backboard.config import BackboardSettings, settings
from backend.app.services.backboard.exceptions import (
    BackboardAuthenticationError,
    BackboardConfigurationError,
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
    MockBackboardProvider,
    get_backboard_provider,
)

logger = logging.getLogger(__name__)

# Current session token schema version
SESSION_TOKEN_VERSION: int = 1

# Minimum required signing key length for production deployments
MIN_PRODUCTION_KEY_LENGTH: int = 32

# Curated Tier 1 knowledge base manifest for verified citation enrichment
TRUSTED_KNOWLEDGE_MANIFEST: Dict[str, Dict[str, Any]] = {
    "01_why_do_landslides_happen.md": {
        "doc_id": "DOC-001",
        "title": "Why Do Landslides Happen? Understanding Signals Before Failure",
        "category": "landslide_science",
        "slug": "why-do-landslides-happen",
        "source": "PahaarPulse Research Team",
    },
    "02_how_gis_turns_terrain_data_into_risk_maps.md": {
        "doc_id": "DOC-002",
        "title": "How GIS Turns Terrain Data into Landslide Risk Maps",
        "category": "geospatial_mapping",
        "slug": "how-gis-turns-terrain-data-into-risk-maps",
        "source": "PahaarPulse Research Team",
    },
    "03_how_machine_learning_predicts_landslide_risk.md": {
        "doc_id": "DOC-003",
        "title": "How Machine Learning Can Predict Landslide Risk",
        "category": "predictive_modeling",
        "slug": "how-machine-learning-predicts-landslide-risk",
        "source": "PahaarPulse Research Team",
    },
    "04_why_rainfall_and_soil_moisture_matter.md": {
        "doc_id": "DOC-004",
        "title": "Why Rainfall and Soil Moisture Matter for Landslide Risk",
        "category": "hydrology_and_triggers",
        "slug": "why-rainfall-and-soil-moisture-matter",
        "source": "PahaarPulse Research Team",
    },
    "05_watching_landscape_from_space.md": {
        "doc_id": "DOC-005",
        "title": "Watching the Landscape from Space: Satellites & Monitoring",
        "category": "remote_sensing",
        "slug": "watching-landscape-from-space",
        "source": "PahaarPulse Research Team",
    },
    "06_from_risk_maps_to_early_warning.md": {
        "doc_id": "DOC-006",
        "title": "From Risk Maps to Early Warning: What Happens After Prediction?",
        "category": "early_warning_systems",
        "slug": "from-risk-maps-to-early-warning",
        "source": "PahaarPulse Research Team",
    },
    "07_ndma_community_landslide_safety_guidelines.md": {
        "doc_id": "DOC-007",
        "title": "Community Landslide Safety & Evacuation Protocols",
        "category": "emergency_guidelines",
        "slug": "ndma-community-landslide-safety-guidelines",
        "source": "National Disaster Management Authority (NDMA)",
    },
    # Simulated provider fixtures mapped to authoritative safety topics
    "02_warning_signs_before_failure.md": {
        "doc_id": "DOC-SIM-02",
        "title": "Early Warning Signs of Slope Destabilization",
        "category": "hazard_identification",
        "slug": "warning-signs-before-failure",
        "source": "PahaarPulse Geotechnical Team",
    },
    "03_evacuation_and_shelter_protocols.md": {
        "doc_id": "DOC-SIM-03",
        "title": "Community Evacuation and Relief Shelter Protocols",
        "category": "emergency_response",
        "slug": "evacuation-and-shelter-protocols",
        "source": "PahaarPulse Disaster Management",
    },
    "05_emergency_contacts_and_protocols.md": {
        "doc_id": "DOC-SIM-05",
        "title": "Emergency Contacts, Hotlines and Response Coordination",
        "category": "emergency_contacts",
        "slug": "emergency-contacts-and-protocols",
        "source": "District Disaster Management Authority",
    },
}


def _is_production_environment() -> bool:
    """Detect whether current runtime environment is flagged as production."""
    env_name = (
        os.environ.get("ENVIRONMENT")
        or os.environ.get("APP_ENV")
        or os.environ.get("FASTAPI_ENV")
        or os.environ.get("NODE_ENV")
        or os.environ.get("ENV")
        or ""
    ).lower().strip()
    return env_name in ("production", "prod", "live")


class BackboardService:
    """Core orchestration service for Backboard RAG Knowledge Assistant.

    Provides cryptographically verified anonymous session handling, query dispatching,
    curated citation enrichment, and resilient fallback execution.
    """

    def __init__(
        self,
        provider: Optional[BackboardProvider] = None,
        config: Optional[BackboardSettings] = None,
        signing_key: Optional[str] = None,
        session_expiry_seconds: Optional[int] = None,
        is_production: Optional[bool] = None,
        assistant_id: Optional[str] = None,
        fail_on_missing_key: bool = False,
    ):
        self.config = config or settings
        self.provider = provider or get_backboard_provider(self.config)
        self.is_production = (
            is_production if is_production is not None else _is_production_environment()
        )

        # Assistant ID resolution
        self.assistant_id = (
            assistant_id
            or self.config.assistant_id
            or "mock-asst-landslide-safety-001"
        )

        # Expiry duration in seconds (defaults to settings or 24 hours)
        if session_expiry_seconds is not None:
            self.session_expiry_seconds = int(session_expiry_seconds)
        else:
            self.session_expiry_seconds = int(self.config.session_expiry_hours * 3600)

        # Resolve and validate dedicated session signing key
        self.signing_key = self._resolve_signing_key(
            explicit_key=signing_key,
            fail_on_missing_key=fail_on_missing_key,
        )

    def _resolve_signing_key(
        self,
        explicit_key: Optional[str],
        fail_on_missing_key: bool,
    ) -> str:
        """Resolve and enforce security requirements on the session signing secret."""
        resolved = (
            explicit_key
            if explicit_key is not None
            else self.config.session_signing_key
        ).strip()

        # Reject key reuse: signing key must not duplicate Backboard API key
        if resolved and self.config.api_key and resolved == self.config.api_key:
            raise BackboardConfigurationError(
                "Security violation: SESSION_SIGNING_KEY must not reuse BACKBOARD_API_KEY."
            )

        if self.is_production:
            if not resolved:
                logger.error(
                    "Security violation: SESSION_SIGNING_KEY is not configured for production deployment. Failing closed."
                )
                raise BackboardConfigurationError(
                    "SESSION_SIGNING_KEY is required for production deployments. Failing closed."
                )
            if len(resolved) < MIN_PRODUCTION_KEY_LENGTH:
                logger.error(
                    "Security violation: SESSION_SIGNING_KEY length is insufficient for production."
                )
                raise BackboardConfigurationError(
                    f"SESSION_SIGNING_KEY must be at least {MIN_PRODUCTION_KEY_LENGTH} characters long in production (got {len(resolved)})."
                )
            return resolved

        # Development / test environment behavior
        if not resolved:
            if fail_on_missing_key:
                raise BackboardConfigurationError(
                    "SESSION_SIGNING_KEY is required when fail_on_missing_key=True."
                )
            # Use deterministic dev signing key to avoid silent invalidation on restart
            logger.warning(
                "SESSION_SIGNING_KEY is not configured; using deterministic local dev signing key. Do NOT use in production."
            )
            return "dev-insecure-pahaarpulse-session-signing-key-32chars-min"

        return resolved

    def create_session_token(self, thread_id: str) -> str:
        """Construct and sign an HMAC-SHA256 session token bound to a specific thread ID."""
        if not thread_id or not isinstance(thread_id, str):
            raise ValueError("thread_id must be a non-empty string.")

        session_id = secrets.token_hex(16)
        issued_at = int(time.time())
        expires_at = issued_at + self.session_expiry_seconds

        payload_dict = {
            "v": SESSION_TOKEN_VERSION,
            "sid": session_id,
            "tid": thread_id,
            "iat": issued_at,
            "exp": expires_at,
        }

        # Canonical JSON serialization
        payload_bytes = json.dumps(
            payload_dict, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        payload_b64 = (
            base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
        )

        # Compute HMAC-SHA256 signature over base64url payload
        signature = hmac.new(
            self.signing_key.encode("utf-8"),
            payload_b64.encode("ascii"),
            hashlib.sha256,
        ).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

        return f"{payload_b64}.{sig_b64}"

    def verify_session_token(self, token: str) -> AssistantSessionPayload:
        """Validate HMAC signature, expiration, and payload integrity.

        Raises:
            InvalidSessionError: If the token is malformed, has invalid signature, or wrong version.
            SessionExpiredError: If the token lifetime has elapsed.
        """
        if not token or not isinstance(token, str):
            raise InvalidSessionError("Missing or invalid session token.")

        cleaned = token.strip()
        parts = cleaned.split(".")
        if len(parts) != 2:
            raise InvalidSessionError("Malformed session token: invalid token structure.")

        payload_b64, sig_b64 = parts[0], parts[1]

        # Decode signature
        sig_padding = 4 - (len(sig_b64) % 4)
        sig_padded = sig_b64 + ("=" * sig_padding) if sig_padding != 4 else sig_b64
        try:
            actual_sig = base64.urlsafe_b64decode(sig_padded.encode("ascii"))
        except Exception as e:
            raise InvalidSessionError("Malformed session token: invalid signature encoding.") from e

        # Decode payload
        payload_padding = 4 - (len(payload_b64) % 4)
        payload_padded = (
            payload_b64 + ("=" * payload_padding) if payload_padding != 4 else payload_b64
        )
        try:
            payload_bytes = base64.urlsafe_b64decode(payload_padded.encode("ascii"))
        except Exception as e:
            raise InvalidSessionError("Malformed session token: invalid payload encoding.") from e

        # Compute expected signature and perform constant-time comparison
        expected_sig = hmac.new(
            self.signing_key.encode("utf-8"),
            payload_b64.encode("ascii"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(actual_sig, expected_sig):
            raise InvalidSessionError(
                "Invalid session signature: token has been tampered with or signed with an untrusted key."
            )

        # Parse and validate JSON structure
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            raise InvalidSessionError("Malformed session token: invalid JSON payload.") from e

        # Version check
        if payload.get("v") != SESSION_TOKEN_VERSION:
            raise InvalidSessionError(
                f"Unsupported session token version: {payload.get('v')}."
            )

        # Check required claims
        required_claims = ("sid", "tid", "iat", "exp")
        for claim in required_claims:
            if claim not in payload:
                raise InvalidSessionError(
                    f"Malformed session token: missing claim '{claim}'."
                )

        # Type checks
        if not isinstance(payload["sid"], str) or not payload["sid"]:
            raise InvalidSessionError("Malformed session token: invalid session ID.")
        if not isinstance(payload["tid"], str) or not payload["tid"]:
            raise InvalidSessionError("Malformed session token: invalid thread ID.")
        if not isinstance(payload["iat"], (int, float)):
            raise InvalidSessionError("Malformed session token: invalid issued_at timestamp.")
        if not isinstance(payload["exp"], (int, float)):
            raise InvalidSessionError("Malformed session token: invalid expires_at timestamp.")

        # Check expiration
        now = time.time()
        if now > payload["exp"]:
            raise SessionExpiredError(
                "Assistant session token has expired. Please initialize a new thread session."
            )

        return AssistantSessionPayload(
            version=int(payload["v"]),
            session_id=str(payload["sid"]),
            thread_id=str(payload["tid"]),
            issued_at=int(payload["iat"]),
            expires_at=int(payload["exp"]),
        )

    async def create_thread_session(self) -> AssistantThreadSession:
        """Initialize a new conversation thread on Backboard and return a signed session token.

        Does not expose raw thread ID to caller.
        """
        thread_id = await self.provider.create_thread(self.assistant_id)
        token = self.create_session_token(thread_id)
        session_payload = self.verify_session_token(token)

        expiry_iso = datetime.fromtimestamp(
            session_payload.expires_at, tz=timezone.utc
        ).isoformat()

        return AssistantThreadSession(
            session_token=token,
            expires_at=expiry_iso,
            session_id=session_payload.session_id,
        )

    async def query(
        self,
        session_token: str,
        query: str,
        *,
        enable_fallback: bool = True,
    ) -> AssistantQueryResponse:
        """Validate session token, dispatch user query to Backboard, and format response.

        Guarantees:
        - If session_token is invalid or expired, the provider is NEVER called.
        - Client cannot substitute another thread ID.
        - Citations are grounded strictly against verified sources or tagged as uncurated.
        - Geotechnical disclaimer is always appended.
        """
        # Validate query length and content
        if not query or not isinstance(query, str):
            raise BackboardQueryValidationError("Query text cannot be empty.")

        clean_query = query.strip()
        if len(clean_query) < 2:
            raise BackboardQueryValidationError("Query text must be at least 2 characters long.")
        if len(clean_query) > 1000:
            raise BackboardQueryValidationError("Query text cannot exceed 1000 characters.")

        # Cryptographically verify session and extract server-bound thread ID
        session_payload = self.verify_session_token(session_token)
        thread_id = session_payload.thread_id

        # Dispatch query to provider
        try:
            output: BackboardMessageOutput = await self.provider.send_message(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                content=clean_query,
                stream=False,
                memory="off",
            )
        except (
            BackboardTimeoutError,
            BackboardRateLimitError,
            BackboardTemporaryUnavailableError,
        ) as transient_err:
            if not enable_fallback:
                raise
            logger.warning(
                f"Backboard provider {self.provider.provider_name} encountered {transient_err.__class__.__name__}. "
                "Returning safety fallback guidance."
            )
            return self._build_fallback_response()

        # Enrich citations against trusted domain manifest
        sources = self._enrich_citations(output)

        return AssistantQueryResponse(
            reply=output.content,
            sources=sources,
            disclaimer=DEFAULT_ASSISTANT_DISCLAIMER,
            fallback_mode=False,
        )

    def _enrich_citations(self, output: BackboardMessageOutput) -> List[SourceCitation]:
        """Map retrieved documents to trusted manifest entries without inventing citations."""
        sources: List[SourceCitation] = []
        seen_filenames: set[str] = set()

        # Prioritize explicit RetrievedDocument objects if present
        candidate_filenames: List[str] = []
        doc_map: Dict[str, RetrievedDocument] = {}

        if output.documents:
            for doc in output.documents:
                candidate_filenames.append(doc.filename)
                doc_map[doc.filename] = doc
        elif output.retrieved_files:
            candidate_filenames = list(output.retrieved_files)

        for fname in candidate_filenames:
            if fname in seen_filenames:
                continue
            seen_filenames.add(fname)

            clean_name = os.path.basename(fname).strip()
            if clean_name in TRUSTED_KNOWLEDGE_MANIFEST:
                manifest_entry = TRUSTED_KNOWLEDGE_MANIFEST[clean_name]
                sources.append(
                    SourceCitation(
                        title=manifest_entry["title"],
                        document_id=manifest_entry["doc_id"],
                        url_or_slug=manifest_entry.get("slug"),
                        category=manifest_entry.get("category"),
                        is_curated=True,
                    )
                )
            else:
                # Unverified or non-manifest source: preserve metadata without inventing details
                doc_obj = doc_map.get(fname)
                doc_id = doc_obj.document_id if doc_obj else f"raw-{clean_name}"
                sources.append(
                    SourceCitation(
                        title=clean_name,
                        document_id=doc_id,
                        url_or_slug=None,
                        category="unverified",
                        is_curated=False,
                    )
                )

        return sources

    def _build_fallback_response(self) -> AssistantQueryResponse:
        """Generate safe, conservative guidance when provider is unreachable."""
        fallback_text = (
            "The knowledge assistant is temporarily operating in offline fallback mode. "
            "General Mountain Safety Notice: In the event of heavy rainfall, visible ground cracking, "
            "or active slope movement, evacuate immediately along uphill or perpendicular paths towards "
            "high, stable ground. Never follow natural stream channels or drainage ravines. "
            "Contact district emergency operations centers (112 / 1070) for real-time instructions."
        )
        fallback_source = SourceCitation(
            title="Community Landslide Safety & Evacuation Protocols",
            document_id="DOC-007",
            url_or_slug="ndma-community-landslide-safety-guidelines",
            category="emergency_guidelines",
            is_curated=True,
        )
        return AssistantQueryResponse(
            reply=fallback_text,
            sources=[fallback_source],
            disclaimer=DEFAULT_ASSISTANT_DISCLAIMER,
            fallback_mode=True,
        )
