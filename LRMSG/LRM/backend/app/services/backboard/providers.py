"""Provider implementations and abstractions for Backboard AI RAG integration.

Provides:
- BackboardProvider: Protocol defining the abstract interface for Backboard RAG operations.
- MockBackboardProvider: Deterministic offline mock implementation for testing and development.
- LiveBackboardProvider: Stub for live provider (full HTTP integration scheduled for Milestone 2).
- get_backboard_provider: Factory function selecting the appropriate provider.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Protocol

from backend.app.services.backboard.config import BackboardSettings, settings
from backend.app.services.backboard.exceptions import (
    BackboardAuthenticationError,
    BackboardConfigurationError,
    BackboardConnectionError,
    BackboardError,
    BackboardMalformedOutputError,
    BackboardNotFoundError,
    BackboardRateLimitError,
    BackboardTemporaryUnavailableError,
    BackboardTimeoutError,
)
from backend.app.services.backboard.models import BackboardMessageOutput, RetrievedDocument
import httpx

logger = logging.getLogger(__name__)


class BackboardProvider(Protocol):
    """Abstract protocol for Backboard RAG interactions."""

    @property
    def provider_name(self) -> str:
        """Return the unique identifier of this provider implementation."""
        ...

    def is_available(self) -> bool:
        """Check whether provider configuration and runtime are available."""
        ...

    async def create_thread(self, assistant_id: Optional[str] = None) -> str:
        """Initialize an isolated conversation thread and return the thread ID."""
        ...

    async def send_message(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        content: str = "",
        *,
        stream: bool = False,
        memory: str = "off",
    ) -> BackboardMessageOutput:
        """Send a user query to Backboard and return the structured response."""
        ...


class MockBackboardProvider:
    """Deterministic, offline mock provider for testing and safe local development."""

    def __init__(
        self,
        mode: str = "success",
        *,
        custom_output: Optional[BackboardMessageOutput] = None,
        default_assistant_id: str = "mock-asst-landslide-safety-001",
        default_thread_id: str = "mock-thread-uuid-1234",
    ):
        self.mode = mode.lower().strip()
        self.custom_output = custom_output
        self.default_assistant_id = default_assistant_id
        self.default_thread_id = default_thread_id

        # Observability tracking for unit and integration tests
        self.created_threads: List[str] = []
        self.dispatched_messages: List[Dict[str, Any]] = []
        self.last_thread_id: Optional[str] = None
        self.last_assistant_id: Optional[str] = None
        self.last_content: Optional[str] = None
        self.last_stream: Optional[bool] = None
        self.last_memory: Optional[str] = None
        self.call_count: int = 0

    @property
    def provider_name(self) -> str:
        return "mock_backboard"

    def is_available(self) -> bool:
        return True

    async def create_thread(self, assistant_id: Optional[str] = None) -> str:
        """Simulate creating an isolated conversation thread."""
        if self.mode == "timeout":
            raise BackboardTimeoutError("Upstream Backboard timeout during thread creation (30s)")
        if self.mode == "rate_limit":
            raise BackboardRateLimitError("Rate limit exceeded during thread creation (HTTP 429)")
        if self.mode == "unavailable":
            raise BackboardTemporaryUnavailableError("Service temporarily unavailable (HTTP 503)")
        if self.mode == "auth_error":
            raise BackboardAuthenticationError(
                "Authentication failed: invalid or missing Backboard API key (HTTP 401)"
            )

        thread_index = len(self.created_threads) + 1
        generated_thread = f"{self.default_thread_id}-{thread_index}" if thread_index > 1 else self.default_thread_id
        self.created_threads.append(generated_thread)
        return generated_thread

    async def send_message(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        content: str = "",
        *,
        stream: bool = False,
        memory: str = "off",
    ) -> BackboardMessageOutput:
        """Simulate sending a query to Backboard and returning grounded answers."""
        # Normalize arguments: if 2 positional args were given (thread_id, query_content)
        if not content and assistant_id:
            if " " in assistant_id or len(assistant_id) > 50 or not assistant_id.startswith(("asst_", "mock-asst")):
                content = assistant_id
                assistant_id = self.default_assistant_id

        effective_assistant_id = assistant_id or self.default_assistant_id
        self.call_count += 1
        self.last_thread_id = thread_id
        self.last_assistant_id = effective_assistant_id
        self.last_content = content
        self.last_stream = stream
        self.last_memory = memory

        self.dispatched_messages.append(
            {
                "thread_id": thread_id,
                "assistant_id": effective_assistant_id,
                "content": content,
                "stream": stream,
                "memory": memory,
            }
        )

        # Mode-based failure simulation
        if self.mode == "timeout":
            raise BackboardTimeoutError("Upstream Backboard timeout (30s)")
        if self.mode == "rate_limit":
            raise BackboardRateLimitError("Rate limit exceeded (HTTP 429)")
        if self.mode == "unavailable":
            raise BackboardTemporaryUnavailableError("Service temporarily unavailable (HTTP 503)")
        if self.mode == "auth_error":
            raise BackboardAuthenticationError(
                "Authentication failed: invalid or missing Backboard API key (HTTP 401)"
            )
        if self.mode == "not_found":
            raise BackboardNotFoundError(f"Thread '{thread_id}' or assistant '{effective_assistant_id}' not found (HTTP 404)")
        if self.mode == "malformed":
            raise BackboardMalformedOutputError("Backboard returned unparseable or schema-invalid output")
        if self.custom_output:
            return self.custom_output

        # Simulated empty knowledge retrieval (off-topic or unindexed queries)
        if self.mode in ("empty", "empty_retrieval"):
            return BackboardMessageOutput(
                content=(
                    "I do not have sufficient information in the knowledge base to answer this question. "
                    "Please refer to local disaster management authorities or official emergency services for specific advice."
                ),
                thread_id=thread_id,
                assistant_id=effective_assistant_id,
                message_id=f"mock-msg-{uuid.uuid4().hex[:8]}",
                status="COMPLETED",
                retrieved_files=[],
                retrieved_files_count=0,
                documents=[],
                raw_response={
                    "status": "COMPLETED",
                    "retrieved_files": [],
                    "retrieved_files_count": 0,
                    "simulated": True,
                },
            )

        # Realistic domain-specific responses based on query content
        query_lower = (content or "").lower()

        if any(w in query_lower for w in ("warning", "sign", "crack", "tension", "scarp", "bulge")):
            reply_text = (
                "Key early warning signs of slope failure include:\n"
                "1. Tension cracks opening in the soil, asphalt roads, or retaining walls.\n"
                "2. Bulging of the slope toe or ground buckling at the base.\n"
                "3. Tilting utility poles, fences, or trees leaning downhill ('drunken trees').\n"
                "4. Sudden appearance of water seeping from new locations or previously clear springs turning muddy.\n"
                "If these indicators are observed, evacuate immediately along uphill or perpendicular paths and alert authorities."
            )
            retrieved_files = [
                "02_warning_signs_before_failure.md",
                "01_why_do_landslides_happen.md",
            ]
            documents = [
                RetrievedDocument(
                    document_id="doc-warn-02",
                    filename="02_warning_signs_before_failure.md",
                    score=0.95,
                    metadata={"category": "hazard_identification", "tier": 1},
                ),
                RetrievedDocument(
                    document_id="doc-why-01",
                    filename="01_why_do_landslides_happen.md",
                    score=0.88,
                    metadata={"category": "landslide_science", "tier": 1},
                ),
            ]
        elif any(w in query_lower for w in ("rain", "monsoon", "water", "moisture", "drain")):
            reply_text = (
                "Rainfall and soil moisture are primary triggering factors for landslides in mountainous regions:\n"
                "1. Infiltration increases pore water pressure, drastically reducing the effective friction holding soil together.\n"
                "2. Added water mass significantly increases the downslope driving force (gravitational load).\n"
                "3. Intense short-duration storms often trigger rapid debris flows, while prolonged monsoon precipitation induces deep-seated rotational slides.\n"
                "Maintain clear slope drainage paths and avoid directing roof runoff onto steep embankments."
            )
            retrieved_files = [
                "04_why_rainfall_and_soil_moisture_matter.md",
                "01_why_do_landslides_happen.md",
            ]
            documents = [
                RetrievedDocument(
                    document_id="doc-rain-04",
                    filename="04_why_rainfall_and_soil_moisture_matter.md",
                    score=0.94,
                    metadata={"category": "hydrology_and_triggers", "tier": 1},
                ),
                RetrievedDocument(
                    document_id="doc-why-01",
                    filename="01_why_do_landslides_happen.md",
                    score=0.87,
                    metadata={"category": "landslide_science", "tier": 1},
                ),
            ]
        elif any(w in query_lower for w in ("evacuat", "shelter", "safe", "route", "emergency", "contact")):
            reply_text = (
                "Evacuation and emergency response guidelines for landslide-prone zones:\n"
                "1. Move immediately along designated evacuation routes towards ridgelines or high, stable ground.\n"
                "2. Never flee down a ravine, stream valley, or natural drainage gully.\n"
                "3. Report to verified district relief shelters.\n"
                "4. Dial emergency disaster helplines (112, 1070/1077 in India) to report trapped individuals or blocked roads."
            )
            retrieved_files = [
                "03_evacuation_and_shelter_protocols.md",
                "05_emergency_contacts_and_protocols.md",
            ]
            documents = [
                RetrievedDocument(
                    document_id="doc-evac-03",
                    filename="03_evacuation_and_shelter_protocols.md",
                    score=0.96,
                    metadata={"category": "emergency_response", "tier": 1},
                ),
                RetrievedDocument(
                    document_id="doc-cont-05",
                    filename="05_emergency_contacts_and_protocols.md",
                    score=0.91,
                    metadata={"category": "emergency_contacts", "tier": 1},
                ),
            ]
        else:
            reply_text = (
                "Landslides occur when the downward gravitational shear stress along a slope exceeds "
                "the resisting shear strength of the rock, soil, or debris. Key contributing factors include "
                "steep slope angle, geological weathering, groundwater saturation, and unengineered slope cutting. "
                "Always monitor slopes for ground displacement and heed district warning advisories."
            )
            retrieved_files = [
                "01_why_do_landslides_happen.md",
                "04_why_rainfall_and_soil_moisture_matter.md",
            ]
            documents = [
                RetrievedDocument(
                    document_id="doc-why-01",
                    filename="01_why_do_landslides_happen.md",
                    score=0.92,
                    metadata={"category": "landslide_science", "tier": 1},
                ),
                RetrievedDocument(
                    document_id="doc-rain-04",
                    filename="04_why_rainfall_and_soil_moisture_matter.md",
                    score=0.85,
                    metadata={"category": "hydrology_and_triggers", "tier": 1},
                ),
            ]

        return BackboardMessageOutput(
            content=reply_text,
            thread_id=thread_id,
            assistant_id=effective_assistant_id,
            message_id=f"mock-msg-{uuid.uuid4().hex[:8]}",
            status="COMPLETED",
            retrieved_files=retrieved_files,
            retrieved_files_count=len(retrieved_files),
            documents=documents,
            raw_response={
                "status": "COMPLETED",
                "retrieved_files": retrieved_files,
                "retrieved_files_count": len(retrieved_files),
                "simulated": True,
            },
        )


class LiveBackboardProvider:
    """Live Backboard API provider using asynchronous HTTP requests via httpx.

    Features:
    - Direct REST communication with Backboard.io (https://app.backboard.io/api).
    - Strict enforcement of memory="off" to protect multi-user data privacy.
    - Comprehensive mapping of upstream HTTP status codes to typed Backboard exceptions.
    - Zero credential leakage in exceptions and routine logs.
    - Support for injected httpx.AsyncClient / MockTransport for offline unit tests.
    """

    def __init__(
        self,
        config: Optional[BackboardSettings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.config = config or settings
        if not self.config.is_configured:
            raise BackboardConfigurationError(
                "Cannot initialize LiveBackboardProvider: BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID must be set."
            )
        self._client = http_client
        self.base_url = self.config.base_url.rstrip("/")
        self.timeout = float(self.config.timeout_seconds)

    @property
    def provider_name(self) -> str:
        return "live_backboard"

    def is_available(self) -> bool:
        return self.config.is_configured

    def _get_headers(self) -> Dict[str, str]:
        """Construct secure authorization headers without exposing keys in logs."""
        return {
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json",
            "User-Agent": "PahaarPulse-RAG-Assistant/1.0",
        }

    async def create_thread(self, assistant_id: Optional[str] = None) -> str:
        """Create a new conversation thread on Backboard associated with the assistant."""
        effective_assistant_id = (assistant_id or self.config.assistant_id).strip()
        if not effective_assistant_id:
            raise BackboardConfigurationError("assistant_id is required for thread creation.")

        url = f"{self.base_url}/assistants/{effective_assistant_id}/threads"
        body = {}
        headers = self._get_headers()

        timeout_obj = httpx.Timeout(timeout=self.timeout, connect=10.0, read=self.timeout)

        try:
            if self._client:
                res = await self._client.post(url, headers=headers, json=body, timeout=timeout_obj)
            else:
                async with httpx.AsyncClient(timeout=timeout_obj) as client:
                    res = await client.post(url, headers=headers, json=body)
        except httpx.ConnectTimeout as e:
            raise BackboardTimeoutError(
                f"Backboard thread creation connection timed out after 10.0s."
            ) from e
        except httpx.ReadTimeout as e:
            raise BackboardTimeoutError(
                f"Backboard thread creation timed out waiting for upstream response after {self.timeout}s."
            ) from e
        except httpx.TimeoutException as e:
            raise BackboardTimeoutError(
                f"Backboard thread creation timed out after {self.timeout}s."
            ) from e
        except (httpx.ConnectError, httpx.NetworkError) as e:
            raise BackboardConnectionError(
                f"Cannot connect to Backboard service at {self.base_url}: {e}"
            ) from e
        except httpx.RequestError as e:
            raise BackboardConnectionError(f"Backboard network communication error: {e}") from e

        # Handle upstream status codes
        if res.status_code == 401:
            raise BackboardAuthenticationError(
                "Backboard API key authentication failed (HTTP 401). Check BACKBOARD_API_KEY."
            )
        if res.status_code == 404:
            raise BackboardNotFoundError(
                f"Backboard assistant '{effective_assistant_id}' not found (HTTP 404)."
            )
        if res.status_code == 429:
            retry_after = res.headers.get("Retry-After")
            raise BackboardRateLimitError(
                f"Backboard rate limit exceeded (HTTP 429). Retry-After: {retry_after or 'unspecified'}."
            )
        if res.status_code in (500, 502, 503, 504):
            raise BackboardTemporaryUnavailableError(
                f"Backboard service temporarily unavailable (HTTP {res.status_code})."
            )
        if res.status_code not in (200, 201):
            raise BackboardError(
                f"Backboard thread creation returned HTTP {res.status_code}: {res.text[:200]}"
            )

        # Parse JSON response
        try:
            data = res.json()
        except Exception as e:
            raise BackboardMalformedOutputError(
                f"Failed to parse Backboard thread creation response as JSON: {e}"
            ) from e

        if not isinstance(data, dict):
            raise BackboardMalformedOutputError(
                "Backboard thread creation returned non-dict JSON output."
            )

        thread_id = data.get("thread_id") or data.get("id")
        if not thread_id or not isinstance(thread_id, str):
            raise BackboardMalformedOutputError(
                "Backboard thread creation response missing valid 'thread_id' or 'id' field."
            )

        return thread_id

    async def send_message(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        content: str = "",
        *,
        stream: bool = False,
        memory: str = "off",
    ) -> BackboardMessageOutput:
        """Send a message to an existing thread and parse grounded retrieval answer."""
        if not content and assistant_id:
            if " " in assistant_id or len(assistant_id) > 50 or not assistant_id.startswith(("asst_", "mock-asst")):
                content = assistant_id
                assistant_id = None

        effective_assistant_id = (assistant_id or self.config.assistant_id).strip()
        if not effective_assistant_id:
            raise BackboardConfigurationError("assistant_id is required to send messages.")

        clean_thread_id = (thread_id or "").strip()
        if not clean_thread_id:
            raise ValueError("thread_id must be a non-empty string.")

        url = f"{self.base_url}/threads/messages"
        headers = self._get_headers()

        # Decision 3: memory MUST remain strictly 'off' to protect multi-user privacy
        body = {
            "thread_id": clean_thread_id,
            "assistant_id": effective_assistant_id,
            "content": content,
            "stream": stream,
            "memory": "off",
        }

        timeout_obj = httpx.Timeout(timeout=self.timeout, connect=10.0, read=self.timeout)

        try:
            if self._client:
                res = await self._client.post(url, headers=headers, json=body, timeout=timeout_obj)
            else:
                async with httpx.AsyncClient(timeout=timeout_obj) as client:
                    res = await client.post(url, headers=headers, json=body)
        except httpx.ConnectTimeout as e:
            raise BackboardTimeoutError(
                f"Backboard connection timed out after 10.0s."
            ) from e
        except httpx.ReadTimeout as e:
            raise BackboardTimeoutError(
                f"Backboard message query timed out waiting for upstream response after {self.timeout}s."
            ) from e
        except httpx.TimeoutException as e:
            raise BackboardTimeoutError(
                f"Backboard message query timed out after {self.timeout}s."
            ) from e
        except (httpx.ConnectError, httpx.NetworkError) as e:
            raise BackboardConnectionError(
                f"Cannot connect to Backboard service at {self.base_url}: {e}"
            ) from e
        except httpx.RequestError as e:
            raise BackboardConnectionError(f"Backboard network communication error: {e}") from e

        # Handle upstream status codes
        if res.status_code == 401:
            raise BackboardAuthenticationError(
                "Backboard API key authentication failed (HTTP 401). Check BACKBOARD_API_KEY."
            )
        if res.status_code == 404:
            raise BackboardNotFoundError(
                f"Resource not found on Backboard (HTTP 404): thread or assistant not found."
            )
        if res.status_code == 429:
            retry_after = res.headers.get("Retry-After")
            raise BackboardRateLimitError(
                f"Backboard rate limit exceeded (HTTP 429). Retry-After: {retry_after or 'unspecified'}."
            )
        if res.status_code in (500, 502, 503, 504):
            raise BackboardTemporaryUnavailableError(
                f"Backboard service temporarily unavailable (HTTP {res.status_code})."
            )
        if res.status_code not in (200, 201):
            raise BackboardError(
                f"Backboard message query returned HTTP {res.status_code}: {res.text[:200]}"
            )

        # Parse JSON response
        try:
            data = res.json()
        except Exception as e:
            raise BackboardMalformedOutputError(
                f"Failed to parse Backboard response as JSON: {e}"
            ) from e

        if not isinstance(data, dict):
            raise BackboardMalformedOutputError("Backboard response is not a valid JSON object.")

        content_str = data.get("content")
        if content_str is None or not isinstance(content_str, str):
            raise BackboardMalformedOutputError(
                "Backboard response missing required 'content' string field."
            )

        # Parse retrieved files and structured documents
        raw_retrieved = (
            data.get("retrieved_files")
            or data.get("sources")
            or data.get("documents")
            or []
        )
        retrieved_files: List[str] = []
        documents: List[RetrievedDocument] = []

        if isinstance(raw_retrieved, list):
            for idx, item in enumerate(raw_retrieved):
                if isinstance(item, str) and item.strip():
                    fname = item.strip()
                    retrieved_files.append(fname)
                    documents.append(
                        RetrievedDocument(
                            document_id=f"doc-{idx+1}",
                            filename=fname,
                            score=None,
                            metadata={},
                        )
                    )
                elif isinstance(item, dict):
                    fname = item.get("filename") or item.get("name") or f"document_{idx+1}"
                    doc_id = str(item.get("document_id") or item.get("id") or f"doc-{idx+1}")
                    score = item.get("score")
                    meta = item.get("metadata") or {}
                    retrieved_files.append(fname)
                    documents.append(
                        RetrievedDocument(
                            document_id=doc_id,
                            filename=fname,
                            score=float(score) if score is not None else None,
                            metadata=meta if isinstance(meta, dict) else {},
                        )
                    )

        resp_thread_id = data.get("thread_id") or clean_thread_id
        resp_asst_id = data.get("assistant_id") or effective_assistant_id
        msg_id = data.get("message_id") or data.get("id")
        status_str = data.get("status", "COMPLETED")

        return BackboardMessageOutput(
            content=content_str,
            thread_id=resp_thread_id,
            assistant_id=resp_asst_id,
            message_id=msg_id,
            status=status_str,
            retrieved_files=retrieved_files,
            retrieved_files_count=len(retrieved_files),
            documents=documents,
            raw_response=data,
        )


def get_backboard_provider(
    config: Optional[BackboardSettings] = None,
    force_mock: bool = False,
) -> BackboardProvider:
    """Factory selecting the Backboard provider based on configuration.

    Defaults safely to MockBackboardProvider when credentials are absent or provider is 'mock'.
    """
    cfg = config or settings

    if force_mock:
        return MockBackboardProvider()

    if cfg.provider == "mock" or not cfg.is_configured:
        return MockBackboardProvider()

    if cfg.provider in ("live", "backboard"):
        return LiveBackboardProvider(config=cfg)

    # Default fallback
    return MockBackboardProvider()
