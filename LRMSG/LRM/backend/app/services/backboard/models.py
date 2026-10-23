"""Data models and typed structures for Backboard AI RAG integration.

Defines standardized data classes for documents retrieved via RAG,
structured message outputs returned by Backboard provider implementations,
HMAC session payloads, and assistant query responses.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_ASSISTANT_DISCLAIMER: str = (
    "PahaarPulse Assistant provides general educational and safety guidance based on "
    "documented landslide science. It does not replace real-time emergency orders from "
    "district authorities or on-site geotechnical engineering inspections."
)


@dataclass
class RetrievedDocument:
    """Represents a source document retrieved by Backboard during RAG inference."""

    document_id: str
    filename: str
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert document metadata to a serializable dictionary."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "score": self.score,
            "metadata": dict(self.metadata),
        }


@dataclass
class BackboardMessageOutput:
    """Structured response from a Backboard provider message invocation."""

    content: str
    thread_id: str
    assistant_id: str
    message_id: Optional[str] = None
    status: str = "COMPLETED"
    retrieved_files: List[str] = field(default_factory=list)
    retrieved_files_count: int = 0
    documents: List[RetrievedDocument] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure retrieved_files_count reflects retrieved_files if omitted."""
        if not self.retrieved_files_count and self.retrieved_files:
            self.retrieved_files_count = len(self.retrieved_files)
        elif self.retrieved_files_count and not self.retrieved_files and self.documents:
            self.retrieved_files = [doc.filename for doc in self.documents]

    def to_dict(self) -> Dict[str, Any]:
        """Convert complete message output to a serializable dictionary."""
        return {
            "content": self.content,
            "thread_id": self.thread_id,
            "assistant_id": self.assistant_id,
            "message_id": self.message_id,
            "status": self.status,
            "retrieved_files": list(self.retrieved_files),
            "retrieved_files_count": self.retrieved_files_count,
            "documents": [doc.to_dict() for doc in self.documents],
            "raw_response": dict(self.raw_response),
        }

    def __getitem__(self, item: str) -> Any:
        """Allow dictionary-style access for backwards compatibility."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    @property
    def is_billing_restricted(self) -> bool:
        """True if the response text indicates an account credit or billing restriction."""
        if not self.content:
            return False
        content_lower = self.content.lower()
        patterns = (
            "free credit is reserved for memory & rag",
            "can't cover llm chat",
            "cannot cover llm chat",
            "billing page to continue",
            "add credits or start a subscription",
            "turn on auto-reload",
            "insufficient credit",
        )
        return any(p in content_lower for p in patterns)

    @property
    def is_successful(self) -> bool:
        """True if upstream status is COMPLETED and no billing restriction was returned."""
        return (self.status or "").upper() == "COMPLETED" and not self.is_billing_restricted

    def get(self, item: str, default: Any = None) -> Any:
        """Dictionary-style get for backwards compatibility."""
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        """Dictionary-style membership check for backwards compatibility."""
        return hasattr(self, item)


@dataclass
class SourceCitation:
    """Structured citation referencing a verified or retrieved knowledge source."""

    title: str
    document_id: str
    url_or_slug: Optional[str] = None
    category: Optional[str] = None
    is_curated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "document_id": self.document_id,
            "url_or_slug": self.url_or_slug,
            "category": self.category,
            "is_curated": self.is_curated,
        }


@dataclass
class AssistantSessionPayload:
    """Unpacked, cryptographically verified contents of an assistant session token."""

    version: int
    session_id: str
    thread_id: str
    issued_at: int
    expires_at: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "v": self.version,
            "sid": self.session_id,
            "tid": self.thread_id,
            "iat": self.issued_at,
            "exp": self.expires_at,
        }


@dataclass
class AssistantThreadSession:
    """Public session handle returned when initializing a conversation thread."""

    session_token: str
    expires_at: str
    session_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_token": self.session_token,
            "expires_at": self.expires_at,
            "session_id": self.session_id,
        }


@dataclass
class AssistantQueryResponse:
    """Final, grounded assistant response returned to the caller."""

    reply: str
    sources: List[SourceCitation] = field(default_factory=list)
    disclaimer: str = DEFAULT_ASSISTANT_DISCLAIMER
    fallback_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reply": self.reply,
            "sources": [s.to_dict() for s in self.sources],
            "disclaimer": self.disclaimer,
            "fallback_mode": self.fallback_mode,
        }

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)
