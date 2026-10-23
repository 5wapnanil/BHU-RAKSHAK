"""Pydantic schemas for FieldReport operations.

Strict validation for coordinate ranges, coordinate pair integrity,
review-status transitions, and client-supplied metadata rejection.
"""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


VALID_AI_HAZARD_LEVELS = ("low", "moderate", "high", "critical", "indeterminate")
VALID_REVIEW_STATUSES = ("pending", "verified", "rejected", "needs_inspection")


class FieldReportBase(BaseModel):
    """Base fields submitted by a citizen or field responder."""

    notes: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Observer qualitative field notes",
    )
    location_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Descriptive location name, village, or highway marker",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="WGS-84 latitude in [-90.0, 90.0]",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="WGS-84 longitude in [-180.0, 180.0]",
    )
    reporter_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional reporter display name",
    )
    reporter_phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional contact telephone number",
    )
    photo_url: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Relative web path or public URL of an uploaded photo",
    )

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude must be between -90.0 and 90.0, got {v}")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude must be between -180.0 and 180.0, got {v}")
        return v

    @model_validator(mode="after")
    def validate_coordinate_pair(self) -> "FieldReportBase":
        has_lat = self.latitude is not None
        has_lon = self.longitude is not None
        if has_lat != has_lon:
            raise ValueError(
                "Both latitude and longitude must be provided together, or both omitted."
            )
        return self


class FieldReportCreate(FieldReportBase):
    """Payload for creating a new field report via JSON.

    Forbids client-supplied AI metadata to prevent untrusted analysis injection.
    """

    model_config = ConfigDict(extra="forbid")


class FieldReportReviewRequest(BaseModel):
    """Administrative review status transition request.

    reviewed_by is populated strictly by server-side authentication context,
    never accepted from request body.
    """

    model_config = ConfigDict(extra="forbid")

    review_status: Literal["pending", "verified", "rejected", "needs_inspection"] = Field(
        ...,
        description="Target administrative review lifecycle state",
    )
    admin_notes: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Optional administrative review commentary",
    )


class FieldReportResponse(BaseModel):
    """Full representation of a persistent field report."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    submitted_at: datetime

    # AI screening metadata
    ai_hazard_level: str
    ai_detected_hazards: List[str] = Field(default_factory=list)
    ai_confidence: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_analyzed_at: Optional[datetime] = None

    @computed_field
    def ai_status(self) -> str:
        if self.ai_analyzed_at is not None:
            return "completed"
        if self.ai_summary:
            if self.ai_summary.startswith("[FAILED]"):
                return "failed"
            if self.ai_summary.startswith("[UNAVAILABLE]") or self.ai_summary.startswith("[NOT_CONFIGURED]"):
                return "unavailable"
            if self.ai_summary.startswith("[PROCESSING]"):
                return "processing"
        return "pending"

    # Review workflow
    review_status: str
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    admin_notes: Optional[str] = None


class FieldReportListResponse(BaseModel):
    """Paginated list of field reports."""

    items: List[FieldReportResponse]
    total: int
    limit: int
    offset: int


class PhotoUploadResponse(BaseModel):
    """Metadata response for a successfully staged field photograph."""

    photo_url: str
    filename: str
    content_type: str
    size_bytes: int
