"""Pydantic schemas for Gemma AI FieldReport analysis.

Strict validation for AI screening outputs, hazard categories,
confidence bounds, and provider-agnostic serialization.
"""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


AIHazardLevel = Literal["low", "moderate", "high", "critical", "indeterminate"]
AIAnalysisStatus = Literal["pending", "processing", "completed", "failed", "unavailable"]


class GemmaHazardOutput(BaseModel):
    """Structured output expected from Gemma model inference."""

    model_config = ConfigDict(extra="ignore")

    hazard_level: AIHazardLevel = Field(
        default="indeterminate",
        description="Assessed preliminary hazard level based on visible evidence.",
    )
    detected_hazards: List[str] = Field(
        default_factory=list,
        description="Structured observable indicators (e.g. tension_cracks, slope_displacement, rockfall_debris).",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model confidence score or evidence strength measure (0.0 to 1.0).",
    )
    summary: str = Field(
        default="",
        description="Concise description of visible geotechnical features and analytical limitations.",
    )
    limitations: Optional[str] = Field(
        default=None,
        description="Explicit uncertainties or observational limitations.",
    )

    @field_validator("hazard_level", mode="before")
    @classmethod
    def normalize_hazard_level(cls, v: Optional[str]) -> str:
        if not v or not isinstance(v, str):
            return "indeterminate"
        clean = v.strip().lower()
        if clean in ("low", "moderate", "high", "critical", "indeterminate"):
            return clean
        if clean in ("medium", "mod"):
            return "moderate"
        if clean in ("severe", "extreme"):
            return "critical"
        return "indeterminate"

    @field_validator("detected_hazards", mode="before")
    @classmethod
    def clean_detected_hazards(cls, v: Optional[List[str]]) -> List[str]:
        if not v or not isinstance(v, list):
            return []
        cleaned = []
        for item in v:
            if isinstance(item, str) and item.strip():
                clean_item = item.strip().lower().replace(" ", "_").replace("-", "_")
                if clean_item not in cleaned:
                    cleaned.append(clean_item)
        return cleaned


class FieldReportAIAnalysisResponse(BaseModel):
    """API response model for report AI screening metadata."""

    model_config = ConfigDict(from_attributes=True)

    report_id: UUID
    ai_status: AIAnalysisStatus
    ai_hazard_level: str
    ai_detected_hazards: List[str] = Field(default_factory=list)
    ai_confidence: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_analyzed_at: Optional[datetime] = None
    provider_name: str
    has_photo: bool
    disclaimer: str = (
        "Preliminary AI hazard screening is intended strictly as an observational triage aid. "
        "It does not replace on-site geotechnical engineering inspection or validate clearance "
        "for human occupancy."
    )
