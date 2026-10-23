"""Pydantic schemas for volunteer coordination endpoints.

STEP 7L: Input validation hardening — coordinate ranges, string limits, enum constraints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# ── Coordinate validation helper ──

def _validate_latitude(v: float) -> float:
    if not (-90.0 <= v <= 90.0):
        raise ValueError(f"Latitude must be between -90 and 90, got {v}")
    return v


def _validate_longitude(v: float) -> float:
    if not (-180.0 <= v <= 180.0):
        raise ValueError(f"Longitude must be between -180 and 180, got {v}")
    return v


# ── Volunteer Profile ──

class VolunteerProfileCreate(BaseModel):
    user_id: UUID
    skills: List[str] = Field(default_factory=list, max_length=20)
    has_transport: Optional[bool] = None
    capacity: Optional[int] = Field(default=None, ge=0, le=1000)
    availability: Optional[str] = Field(default=None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def check_latitude(cls, v):
        if v is not None:
            return _validate_latitude(v)
        return v

    @field_validator("longitude")
    @classmethod
    def check_longitude(cls, v):
        if v is not None:
            return _validate_longitude(v)
        return v

    @field_validator("skills")
    @classmethod
    def check_skills(cls, v):
        if v and len(v) > 20:
            raise ValueError("Maximum 20 skills allowed")
        for s in v:
            if len(s) > 100:
                raise ValueError(f"Skill name too long (max 100 chars): {s[:30]}...")
        return v


class VolunteerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    skills: List[str]
    has_transport: Optional[bool]
    capacity: Optional[int]
    availability: Optional[str]
    status: str
    is_active: bool
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VolunteerStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|verified|active|unavailable|inactive)$")


# ── Candidate Matching ──

class CandidateVolunteerResponse(BaseModel):
    volunteer_id: UUID
    user_id: UUID
    skills: List[str]
    has_transport: bool
    capacity: Optional[int]
    availability: Optional[str]
    distance_km: float
    active_assignments: int
    rank_score: float


class MatchingRequest(BaseModel):
    radius_km: float = Field(default=25.0, gt=0, le=500)
    limit: int = Field(default=10, ge=1, le=50)


# ── Assignment ──

class AssignmentCreate(BaseModel):
    request_id: UUID
    volunteer_id: UUID
    notes: Optional[str] = Field(default=None, max_length=2000)


class AssignmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(accepted|rejected|in_progress|completed|cancelled)$")
    notes: Optional[str] = Field(default=None, max_length=2000)


class AssignmentResponse(BaseModel):
    id: UUID
    request_id: Optional[UUID]
    volunteer_id: Optional[UUID]
    resource_id: Optional[UUID]
    assignment_type: str
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Relief Resource ──

class ReliefResourceCreate(BaseModel):
    resource_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    quantity: Optional[float] = Field(default=None, gt=0, le=1000000)
    unit: Optional[str] = Field(default=None, max_length=50)
    provider_id: Optional[UUID] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def check_latitude(cls, v):
        if v is not None:
            return _validate_latitude(v)
        return v

    @field_validator("longitude")
    @classmethod
    def check_longitude(cls, v):
        if v is not None:
            return _validate_longitude(v)
        return v


class ReliefResourceResponse(BaseModel):
    id: UUID
    resource_type: str
    description: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    available_quantity: Optional[float]
    provider_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceAllocationRequest(BaseModel):
    request_id: UUID
    quantity: float = Field(..., gt=0, le=1000000)
    notes: Optional[str] = Field(default=None, max_length=2000)


# ── Shelter ──

class ShelterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    capacity: int = Field(default=0, ge=0, le=100000)
    current_occupancy: int = Field(default=0, ge=0, le=100000)
    facilities: Optional[Dict[str, Any]] = None
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    operated_by: Optional[UUID] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def check_latitude(cls, v):
        if v is not None:
            return _validate_latitude(v)
        return v

    @field_validator("longitude")
    @classmethod
    def check_longitude(cls, v):
        if v is not None:
            return _validate_longitude(v)
        return v


class ShelterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    capacity: Optional[int] = Field(default=None, ge=0, le=100000)
    current_occupancy: Optional[int] = Field(default=None, ge=0, le=100000)
    facilities: Optional[Dict[str, Any]] = None
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, pattern="^(open|full|closed)$")
    operated_by: Optional[UUID] = None


class ShelterResponse(BaseModel):
    id: UUID
    name: str
    location: Optional[str]
    address: Optional[str]
    capacity: int
    current_occupancy: int
    facilities: Optional[Dict[str, Any]]
    contact_phone: Optional[str]
    status: str
    operated_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Alert ──

class AlertResponse(BaseModel):
    id: UUID
    title: Optional[str] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    severity: str
    risk_probability: Optional[float] = None
    trigger: Optional[str] = None
    contributing_factors: Optional[str] = None
    rainfall: Optional[float] = None
    soil_condition: Optional[float] = None
    slope_condition: Optional[float] = None
    road_status: Optional[str] = None
    response_priority: Optional[str] = None
    status: str
    notifications: Optional[Dict[str, Any]] = None
    incident_id: Optional[UUID] = None
    created_at: datetime
    triggered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Audit History ──

class AuditResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    actor_id: Optional[UUID] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
