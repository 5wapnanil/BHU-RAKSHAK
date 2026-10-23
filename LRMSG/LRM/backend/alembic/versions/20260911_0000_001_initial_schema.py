"""initial schema — 10 central entities with PostGIS

Revision ID: 001_initial
Revises: None
Create Date: 2026-09-11

STEP 7H: Initial database schema for LRM SG.
Creates all 10 central data entities with:
- UUID primary keys
- Foreign key relationships
- CHECK constraints
- PostGIS GEOGRAPHY columns
- GIST spatial indexes
- Standard B-tree indexes
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TEXT as PG_TEXT

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enable PostGIS extension ──
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ────────────────────────────────────────────────
    # TABLE: users
    # ────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("role", sa.Text(), nullable=False, server_default="citizen"),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "role IN ('citizen', 'volunteer', 'responder', 'authority', 'admin')",
            name="ck_users_role",
        ),
    )
    op.create_index("idx_users_phone", "users", ["phone"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # ────────────────────────────────────────────────
    # TABLE: volunteer_profiles
    # ────────────────────────────────────────────────
    op.create_table(
        "volunteer_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("location", sa.Text()),  # Placeholder — ALTERed to PostGIS below
        sa.Column("skills", PG_TEXT, server_default="{}"),
        sa.Column("has_transport", sa.Boolean()),
        sa.Column("capacity", sa.Integer()),
        sa.Column("availability", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'verified', 'active', 'unavailable', 'inactive')",
            name="ck_volunteer_profiles_status",
        ),
    )
    op.create_index("idx_volunteer_profiles_user_id", "volunteer_profiles", ["user_id"])
    op.create_index("idx_volunteer_profiles_status", "volunteer_profiles", ["status"])

    # ────────────────────────────────────────────────
    # TABLE: incidents
    # ────────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("incident_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text()),
        sa.Column("location", sa.Text()),  # Placeholder — ALTERed to PostGIS below
        sa.Column("district", sa.Text()),
        sa.Column("state", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="reported"),
        sa.Column("source", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('reported', 'active', 'contained', 'resolved', 'closed')",
            name="ck_incidents_status",
        ),
        sa.CheckConstraint(
            "incident_type IN ('landslide', 'flood', 'earthquake', 'fire', 'cyclone', 'other')",
            name="ck_incidents_type",
        ),
    )
    op.create_index("idx_incidents_status", "incidents", ["status"])
    op.create_index("idx_incidents_type", "incidents", ["incident_type"])
    op.create_index("idx_incidents_created_at", "incidents", ["created_at"])

    # ────────────────────────────────────────────────
    # TABLE: emergency_requests
    # ────────────────────────────────────────────────
    op.create_table(
        "emergency_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("client_op_id", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "incident_id",
            UUID(as_uuid=True),
            sa.ForeignKey("incidents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "requester_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("request_type", sa.Text(), nullable=False),
        sa.Column("location", sa.Text()),  # Placeholder — ALTERed to PostGIS below
        sa.Column("location_text", sa.Text()),
        sa.Column("severity", sa.Text()),
        sa.Column("people_affected", sa.Integer()),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("server_status", sa.Text(), nullable=False, server_default="received"),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "request_type IN ('evacuation', 'help', 'evacuation_volunteer', 'relief_volunteer')",
            name="ck_emergency_requests_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'resolved', 'cancelled')",
            name="ck_emergency_requests_status",
        ),
        sa.CheckConstraint(
            "server_status IN ('received', 'processing', 'synced', 'failed')",
            name="ck_emergency_requests_server_status",
        ),
        sa.CheckConstraint(
            "people_affected IS NULL OR people_affected >= 0",
            name="ck_emergency_requests_people_affected",
        ),
    )
    op.create_index("idx_emergency_requests_client_op_id", "emergency_requests", ["client_op_id"])
    op.create_index("idx_emergency_requests_status", "emergency_requests", ["status"])
    op.create_index("idx_emergency_requests_type", "emergency_requests", ["request_type"])
    op.create_index("idx_emergency_requests_created_at", "emergency_requests", ["created_at"])
    op.create_index("idx_emergency_requests_incident_id", "emergency_requests", ["incident_id"])
    op.create_index("idx_emergency_requests_requester_id", "emergency_requests", ["requester_id"])

    # ────────────────────────────────────────────────
    # TABLE: relief_resources
    # ────────────────────────────────────────────────
    op.create_table(
        "relief_resources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("quantity", sa.Numeric()),
        sa.Column("unit", sa.Text()),
        sa.Column("available_quantity", sa.Numeric()),
        sa.Column(
            "provider_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("location", sa.Text()),  # Placeholder — ALTERed to PostGIS below
        sa.Column("status", sa.Text(), nullable=False, server_default="available"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('available', 'allocated', 'depleted', 'expired')",
            name="ck_relief_resources_status",
        ),
        sa.CheckConstraint(
            "quantity IS NULL OR quantity >= 0",
            name="ck_relief_resources_quantity",
        ),
        sa.CheckConstraint(
            "available_quantity IS NULL OR available_quantity >= 0",
            name="ck_relief_resources_available_quantity",
        ),
    )
    op.create_index("idx_relief_resources_provider_id", "relief_resources", ["provider_id"])
    op.create_index("idx_relief_resources_status", "relief_resources", ["status"])

    # ────────────────────────────────────────────────
    # TABLE: assignments
    # ────────────────────────────────────────────────
    op.create_table(
        "assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("emergency_requests.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "volunteer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("volunteer_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "resource_id",
            UUID(as_uuid=True),
            sa.ForeignKey("relief_resources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assignment_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="created"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "assignment_type IN ('volunteer', 'resource', 'combined')",
            name="ck_assignments_type",
        ),
        sa.CheckConstraint(
            "status IN ('created', 'accepted', 'started', 'completed', 'cancelled')",
            name="ck_assignments_status",
        ),
    )
    op.create_index("idx_assignments_request_id", "assignments", ["request_id"])
    op.create_index("idx_assignments_volunteer_id", "assignments", ["volunteer_id"])
    op.create_index("idx_assignments_resource_id", "assignments", ["resource_id"])

    # ────────────────────────────────────────────────
    # TABLE: shelters
    # ────────────────────────────────────────────────
    op.create_table(
        "shelters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("location", sa.Text()),  # Placeholder — ALTERed to PostGIS below
        sa.Column("address", sa.Text()),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("current_occupancy", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("facilities", JSONB, server_default="{}"),
        sa.Column("contact_phone", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column(
            "operated_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('open', 'full', 'closed')",
            name="ck_shelters_status",
        ),
        sa.CheckConstraint("capacity >= 0", name="ck_shelters_capacity"),
        sa.CheckConstraint("current_occupancy >= 0", name="ck_shelters_occupancy"),
    )
    op.create_index("idx_shelters_operated_by", "shelters", ["operated_by"])
    op.create_index("idx_shelters_status", "shelters", ["status"])

    # ────────────────────────────────────────────────
    # TABLE: alerts
    # ────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("location_id", sa.Text()),
        sa.Column("location_name", sa.Text()),
        sa.Column("district", sa.Text()),
        sa.Column("state", sa.Text()),
        sa.Column("location", sa.Text()),  # Placeholder — ALTERed to PostGIS below
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("risk_probability", sa.Numeric()),
        sa.Column("trigger", sa.Text()),
        sa.Column("contributing_factors", sa.Text()),
        sa.Column("rainfall", sa.Numeric()),
        sa.Column("soil_condition", sa.Numeric()),
        sa.Column("slope_condition", sa.Numeric()),
        sa.Column("road_status", sa.Text()),
        sa.Column("response_priority", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("notifications", JSONB, server_default="{}"),
        sa.Column(
            "incident_id",
            UUID(as_uuid=True),
            sa.ForeignKey("incidents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("triggered_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')",
            name="ck_alerts_severity",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'ACKNOWLEDGED', 'UNDER_RESPONSE', 'RESOLVED')",
            name="ck_alerts_status",
        ),
        sa.CheckConstraint(
            "risk_probability IS NULL OR (risk_probability >= 0 AND risk_probability <= 100)",
            name="ck_alerts_risk_probability",
        ),
    )
    op.create_index("idx_alerts_status", "alerts", ["status"])
    op.create_index("idx_alerts_severity", "alerts", ["severity"])
    op.create_index("idx_alerts_created_at", "alerts", ["created_at"])
    op.create_index("idx_alerts_incident_id", "alerts", ["incident_id"])

    # ────────────────────────────────────────────────
    # TABLE: risk_observations
    # ────────────────────────────────────────────────
    op.create_table(
        "risk_observations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("location", sa.Text()),  # Placeholder — ALTERed to PostGIS below
        sa.Column("location_name", sa.Text()),
        sa.Column("district", sa.Text()),
        sa.Column("state", sa.Text()),
        sa.Column("xgboost_probability", sa.Numeric()),
        sa.Column("ahc_cluster", sa.Integer()),
        sa.Column("ahc_susceptibility", sa.Numeric()),
        sa.Column("ahc_category", sa.Text()),
        sa.Column("final_probability", sa.Numeric()),
        sa.Column("final_prediction", sa.Integer()),
        sa.Column("risk_level", sa.Text()),
        sa.Column("rainfall_mm", sa.Numeric()),
        sa.Column("soil_moisture", sa.Numeric()),
        sa.Column("slope_deg", sa.Numeric()),
        sa.Column("elevation_m", sa.Numeric()),
        sa.Column("soil_type", sa.Text()),
        sa.Column("model_version", sa.Text()),
        sa.Column("features", JSONB),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "risk_level IS NULL OR risk_level IN ('CRITICAL', 'HIGH', 'MODERATE', 'LOW')",
            name="ck_risk_observations_level",
        ),
        sa.CheckConstraint(
            "final_prediction IS NULL OR final_prediction IN (0, 1)",
            name="ck_risk_observations_prediction",
        ),
    )
    op.create_index("idx_risk_observations_predicted_at", "risk_observations", ["predicted_at"])
    op.create_index("idx_risk_observations_valid_until", "risk_observations", ["valid_until"])
    op.create_index("idx_risk_observations_risk_level", "risk_observations", ["risk_level"])

    # ────────────────────────────────────────────────
    # TABLE: audit_history
    # ────────────────────────────────────────────────
    op.create_table(
        "audit_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column(
            "actor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("old_value", JSONB),
        sa.Column("new_value", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "entity_type IN ('request', 'volunteer', 'assignment', 'alert', 'resource', 'shelter', 'incident')",
            name="ck_audit_history_entity_type",
        ),
    )
    op.create_index("idx_audit_history_entity_type", "audit_history", ["entity_type"])
    op.create_index("idx_audit_history_entity_id", "audit_history", ["entity_id"])
    op.create_index("idx_audit_history_actor_id", "audit_history", ["actor_id"])
    op.create_index("idx_audit_history_created_at", "audit_history", ["created_at"])

    # ────────────────────────────────────────────────
    # PostGIS GEOGRAPHY columns (ALTER TABLE)
    # ────────────────────────────────────────────────
    # We create tables with TEXT placeholders first, then ALTER to GEOGRAPHY.
    # This avoids SQLAlchemy type-mapping issues with PostGIS during autogenerate.
    geography_columns = [
        ("volunteer_profiles", "location"),
        ("incidents", "location"),
        ("emergency_requests", "location"),
        ("relief_resources", "location"),
        ("shelters", "location"),
        ("alerts", "location"),
        ("risk_observations", "location"),
    ]

    for table, column in geography_columns:
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN {column} TYPE geometry(Point, 4326)
            USING ST_SetSRID(ST_GeomFromText('POINT(0 0)'), 4326)
        """)
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN {column} DROP DEFAULT
        """)
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN {column} DROP NOT NULL
        """)
        # Create GIST index for spatial queries
        op.create_index(f"idx_{table}_{column}_gist", table, [column], postgresql_using="gist")


def downgrade() -> None:
    # Drop tables in reverse dependency order
    tables = [
        "audit_history",
        "risk_observations",
        "alerts",
        "assignments",
        "shelters",
        "relief_resources",
        "emergency_requests",
        "incidents",
        "volunteer_profiles",
        "users",
    ]

    for table in tables:
        op.drop_table(table)

    # PostGIS extension can be kept (other tools may need it)
    # op.execute("DROP EXTENSION IF EXISTS postgis")
