"""SQLAlchemy models for the LRM SG central database.

10 entities designed in STEP 7G, implemented in STEP 7H.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


# ────────────────────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────────────────────

def utcnow():
    return datetime.now(timezone.utc)


def generate_uuid():
    return uuid.uuid4()


# ────────────────────────────────────────────────────────────
# ENTITY 1: users
# ────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(Text, nullable=False)
    phone = Column(Text)
    email = Column(Text)
    role = Column(Text, nullable=False, default="citizen")
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    volunteer_profile = relationship("VolunteerProfile", back_populates="user", uselist=False)
    requests = relationship("EmergencyRequest", back_populates="requester")
    resources = relationship("ReliefResource", back_populates="provider")
    shelters_operated = relationship("Shelter", back_populates="operator")
    audit_entries = relationship("AuditHistory", back_populates="actor")

    __table_args__ = (
        CheckConstraint(
            "role IN ('citizen', 'volunteer', 'responder', 'authority', 'admin')",
            name="ck_users_role",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 2: volunteer_profiles
# ────────────────────────────────────────────────────────────

class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # CRITICAL: one profile per user
    )
    # PostGIS GEOGRAPHY column — requires PostGIS extension
    location = Column(Text)  # Placeholder; actual type set by migration with PostGIS
    skills = Column(JSONB, default=list)  # Stored as JSONB array
    has_transport = Column(Boolean)
    capacity = Column(Integer)
    availability = Column(Text)
    status = Column(Text, nullable=False, default="pending")
    is_active = Column(Boolean, default=True)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="volunteer_profile")
    assignments = relationship("Assignment", back_populates="volunteer")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'verified', 'active', 'unavailable', 'inactive')",
            name="ck_volunteer_profiles_status",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 3: incidents
# ────────────────────────────────────────────────────────────

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    title = Column(Text, nullable=False)
    description = Column(Text)
    incident_type = Column(Text, nullable=False)
    severity = Column(Text)
    location = Column(Text)  # PostGIS GEOGRAPHY — set by migration
    district = Column(Text)
    state = Column(Text)
    status = Column(Text, nullable=False, default="reported")
    source = Column(Text)
    started_at = Column(DateTime(timezone=True))
    reported_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    requests = relationship("EmergencyRequest", back_populates="incident")
    alerts = relationship("Alert", back_populates="incident")

    __table_args__ = (
        CheckConstraint(
            "status IN ('reported', 'active', 'contained', 'resolved', 'closed')",
            name="ck_incidents_status",
        ),
        CheckConstraint(
            "incident_type IN ('landslide', 'flood', 'earthquake', 'fire', 'cyclone', 'other')",
            name="ck_incidents_type",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 4: emergency_requests
# ────────────────────────────────────────────────────────────

class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    client_op_id = Column(Text, nullable=False, unique=True)  # Mobile request.id — idempotency key
    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
    )
    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    request_type = Column(Text, nullable=False)
    location = Column(Text)  # PostGIS GEOGRAPHY — set by migration
    location_text = Column(Text)
    severity = Column(Text)
    people_affected = Column(Integer)
    contact_name = Column(Text)
    contact_phone = Column(Text)
    payload = Column(JSONB, nullable=False, default=dict)
    status = Column(Text, nullable=False, default="pending")
    server_status = Column(Text, nullable=False, default="received")
    synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="requests")
    requester = relationship("User", back_populates="requests")
    assignments = relationship("Assignment", back_populates="request")

    __table_args__ = (
        CheckConstraint(
            "request_type IN ('evacuation', 'help', 'relief', 'evacuation_volunteer', 'relief_volunteer')",
            name="ck_emergency_requests_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'resolved', 'cancelled')",
            name="ck_emergency_requests_status",
        ),
        CheckConstraint(
            "server_status IN ('received', 'processing', 'synced', 'failed')",
            name="ck_emergency_requests_server_status",
        ),
        CheckConstraint(
            "people_affected IS NULL OR people_affected >= 0",
            name="ck_emergency_requests_people_affected",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 5: relief_resources
# ────────────────────────────────────────────────────────────

class ReliefResource(Base):
    __tablename__ = "relief_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    resource_type = Column(Text, nullable=False)
    description = Column(Text)
    quantity = Column(Numeric)
    unit = Column(Text)
    available_quantity = Column(Numeric)
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    location = Column(Text)  # PostGIS GEOGRAPHY — set by migration
    status = Column(Text, nullable=False, default="available")
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    provider = relationship("User", back_populates="resources")
    assignments = relationship("Assignment", back_populates="resource")

    __table_args__ = (
        CheckConstraint(
            "status IN ('available', 'allocated', 'depleted', 'expired')",
            name="ck_relief_resources_status",
        ),
        CheckConstraint(
            "quantity IS NULL OR quantity >= 0",
            name="ck_relief_resources_quantity",
        ),
        CheckConstraint(
            "available_quantity IS NULL OR available_quantity >= 0",
            name="ck_relief_resources_available_quantity",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 6: assignments
# ────────────────────────────────────────────────────────────

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("emergency_requests.id", ondelete="CASCADE"),
        nullable=True,
    )
    volunteer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("volunteer_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("relief_resources.id", ondelete="SET NULL"),
        nullable=True,
    )
    assignment_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="created")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    request = relationship("EmergencyRequest", back_populates="assignments")
    volunteer = relationship("VolunteerProfile", back_populates="assignments")
    resource = relationship("ReliefResource", back_populates="assignments")

    __table_args__ = (
        CheckConstraint(
            "assignment_type IN ('volunteer', 'resource', 'combined')",
            name="ck_assignments_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'created', 'accepted', 'rejected', 'started', 'in_progress', 'completed', 'cancelled')",
            name="ck_assignments_status",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 7: shelters
# ────────────────────────────────────────────────────────────

class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(Text, nullable=False)
    location = Column(Text)  # PostGIS GEOGRAPHY — set by migration
    address = Column(Text)
    capacity = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, nullable=False, default=0)
    facilities = Column(JSONB, default=dict)
    contact_phone = Column(Text)
    status = Column(Text, nullable=False, default="open")
    operated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    operator = relationship("User", back_populates="shelters_operated")

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'full', 'closed')",
            name="ck_shelters_status",
        ),
        CheckConstraint(
            "capacity >= 0",
            name="ck_shelters_capacity",
        ),
        CheckConstraint(
            "current_occupancy >= 0",
            name="ck_shelters_occupancy",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 8: alerts
# ────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    title = Column(Text, nullable=True)
    location_id = Column(Text)
    location_name = Column(Text)
    district = Column(Text)
    state = Column(Text)
    location = Column(Text)  # PostGIS GEOGRAPHY — set by migration
    severity = Column(Text, nullable=False)
    risk_probability = Column(Numeric)
    trigger = Column(Text)
    contributing_factors = Column(Text)
    rainfall = Column(Numeric)
    soil_condition = Column(Numeric)
    slope_condition = Column(Numeric)
    road_status = Column(Text)
    response_priority = Column(Text)
    status = Column(Text, nullable=False, default="ACTIVE")
    notifications = Column(JSONB, default=dict)
    incident_id = Column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    triggered_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="alerts")

    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')",
            name="ck_alerts_severity",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'ACKNOWLEDGED', 'UNDER_RESPONSE', 'RESOLVED')",
            name="ck_alerts_status",
        ),
        CheckConstraint(
            "risk_probability IS NULL OR (risk_probability >= 0 AND risk_probability <= 100)",
            name="ck_alerts_risk_probability",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 9: risk_observations
# ────────────────────────────────────────────────────────────

class RiskObservation(Base):
    __tablename__ = "risk_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    location = Column(Text)  # PostGIS GEOGRAPHY — set by migration
    location_name = Column(Text)
    district = Column(Text)
    state = Column(Text)
    xgboost_probability = Column(Numeric)
    ahc_cluster = Column(Integer)
    ahc_susceptibility = Column(Numeric)
    ahc_category = Column(Text)
    final_probability = Column(Numeric)
    final_prediction = Column(Integer)
    risk_level = Column(Text)
    rainfall_mm = Column(Numeric)
    soil_moisture = Column(Numeric)
    slope_deg = Column(Numeric)
    elevation_m = Column(Numeric)
    soil_type = Column(Text)
    model_version = Column(Text)
    features = Column(JSONB)
    predicted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    valid_until = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "risk_level IS NULL OR risk_level IN ('CRITICAL', 'HIGH', 'MODERATE', 'LOW')",
            name="ck_risk_observations_level",
        ),
        CheckConstraint(
            "final_prediction IS NULL OR final_prediction IN (0, 1)",
            name="ck_risk_observations_prediction",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 10: audit_history
# ────────────────────────────────────────────────────────────

class AuditHistory(Base):
    __tablename__ = "audit_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(Text, nullable=False)
    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    actor = relationship("User", back_populates="audit_entries")

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('request', 'volunteer', 'assignment', 'alert', 'resource', 'shelter', 'incident')",
            name="ck_audit_history_entity_type",
        ),
    )


# ────────────────────────────────────────────────────────────
# ENTITY 11: field_reports
# ────────────────────────────────────────────────────────────

class FieldReport(Base):
    """Field intelligence observation report submitted via mobile or web.

    Authoritative persistent store for citizen and responder ground observations,
    AI multimodal screening metadata (preliminary hazard level, detected features),
    and administrative review workflow.

    Coordinate & Spatial Representation:
    - latitude: WGS-84 float coordinate in [-90.0, 90.0]
    - longitude: WGS-84 float coordinate in [-180.0, 180.0]
    - location: PostGIS geometry(Point, 4326) representing
      ST_SetSRID(ST_MakePoint(longitude, latitude), 4326).
    The eventual API layer validates that when lat/long are provided, location is
    populated consistently with matching EPSG:4326 spatial points.
    """
    __tablename__ = "field_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    photo_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    location_name = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Text)  # PostGIS geometry(Point, 4326) — set by migration
    reporter_name = Column(Text, nullable=True)
    reporter_phone = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utcnow, server_default=func.now(), nullable=False)

    # AI analysis metadata (preliminary screening only — not certified geotechnical assessments)
    ai_hazard_level = Column(Text, nullable=False, default="indeterminate", server_default="indeterminate")
    ai_detected_hazards = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    ai_confidence = Column(Float, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Human review
    review_status = Column(Text, nullable=False, default="pending", server_default="pending")
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    admin_notes = Column(Text, nullable=True)

    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        CheckConstraint(
            "ai_hazard_level IN ('low', 'moderate', 'high', 'critical', 'indeterminate')",
            name="ck_field_reports_ai_hazard_level",
        ),
        CheckConstraint(
            "review_status IN ('pending', 'verified', 'rejected', 'needs_inspection')",
            name="ck_field_reports_review_status",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)",
            name="ck_field_reports_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)",
            name="ck_field_reports_longitude",
        ),
        CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0.0 AND ai_confidence <= 1.0)",
            name="ck_field_reports_ai_confidence",
        ),
        Index("idx_field_reports_review_status", "review_status"),
        Index("idx_field_reports_submitted_at", "submitted_at"),
        Index("idx_field_reports_reviewed_by", "reviewed_by"),
    )
