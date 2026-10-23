"""Add field_reports table with PostGIS geometry, AI metadata, and review tracking.

Revision ID: 007_field_reports
Revises: 006_requester_contact
Create Date: 2026-10-22

Creates the dedicated field_reports table for PahaarPulse Field Intelligence:
- UUID primary key
- Geographic point geometry (PostGIS SRID 4326) with GIST spatial index
- Explicit latitude and longitude bounds check constraints
- Preliminary AI screening metadata (hazard level, JSONB hazards, confidence)
- Human review lifecycle (status check constraint, reviewer foreign key, admin notes)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "007_field_reports"
down_revision: Union[str, None] = "006_requester_contact"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("location_name", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),  # Placeholder — altered to PostGIS below
        sa.Column("reporter_name", sa.Text(), nullable=True),
        sa.Column("reporter_phone", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ai_hazard_level", sa.Text(), nullable=False, server_default="indeterminate"),
        sa.Column("ai_detected_hazards", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "ai_hazard_level IN ('low', 'moderate', 'high', 'critical', 'indeterminate')",
            name="ck_field_reports_ai_hazard_level",
        ),
        sa.CheckConstraint(
            "review_status IN ('pending', 'verified', 'rejected', 'needs_inspection')",
            name="ck_field_reports_review_status",
        ),
        sa.CheckConstraint(
            "latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)",
            name="ck_field_reports_latitude",
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)",
            name="ck_field_reports_longitude",
        ),
        sa.CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0.0 AND ai_confidence <= 1.0)",
            name="ck_field_reports_ai_confidence",
        ),
    )

    # PostGIS geometry(Point, 4326) column conversion
    op.execute("""
        ALTER TABLE field_reports
        ALTER COLUMN location TYPE geometry(Point, 4326)
        USING NULL
    """)

    # Performance and spatial indexes
    op.create_index("idx_field_reports_review_status", "field_reports", ["review_status"])
    op.create_index("idx_field_reports_submitted_at", "field_reports", ["submitted_at"])
    op.create_index("idx_field_reports_reviewed_by", "field_reports", ["reviewed_by"])
    op.create_index("idx_field_reports_location_gist", "field_reports", ["location"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_table("field_reports")
