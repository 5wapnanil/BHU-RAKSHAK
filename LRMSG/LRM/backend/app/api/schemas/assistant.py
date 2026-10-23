"""Pydantic schemas for Backboard AI Assistant endpoints.

Defines request/response contracts for thread initialization, session transport,
queries, citation metadata, and safety guidance.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.backboard.models import DEFAULT_ASSISTANT_DISCLAIMER


class AssistantThreadCreateResponse(BaseModel):
    """Response returned upon conversation thread initialization."""

    model_config = ConfigDict(extra="forbid")

    transport: Literal["cookie", "bearer"] = Field(
        ...,
        description="Transport mode used: 'cookie' (token set in HttpOnly cookie) or 'bearer' (token in payload).",
    )
    expires_at: str = Field(
        ...,
        description="ISO-8601 UTC timestamp indicating when the session token expires.",
    )
    session_token: Optional[str] = Field(
        default=None,
        description="Cryptographically signed session token. Populated ONLY for native mobile / bearer transport.",
    )


class AssistantQueryRequest(BaseModel):
    """Incoming user question submitted to the assistant."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="User question regarding landslide science, safety, or preparedness.",
        examples=["What are early warning signs before a slope failure?"],
    )


class SourceCitationSchema(BaseModel):
    """Citation referencing a verified or retrieved knowledge source."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., description="Document or section title.")
    document_id: str = Field(..., description="Internal or external document identifier.")
    url_or_slug: Optional[str] = Field(default=None, description="Slug or web link if curated.")
    category: Optional[str] = Field(default=None, description="Domain category of the source.")
    is_curated: bool = Field(default=True, description="True if source is verified against trusted manifest.")


class AssistantQueryResponse(BaseModel):
    """Structured assistant reply with citations and safety disclaimer."""

    model_config = ConfigDict(extra="ignore")

    reply: str = Field(..., description="Grounded answer to user question.")
    sources: List[SourceCitationSchema] = Field(
        default_factory=list,
        description="Curated knowledge citations retrieved for this response.",
    )
    disclaimer: str = Field(
        default=DEFAULT_ASSISTANT_DISCLAIMER,
        description="Standard geotechnical educational and emergency disclaimer.",
    )
    fallback_mode: bool = Field(
        default=False,
        description="True if upstream provider was unavailable and conservative safety fallback guidance was served.",
    )
