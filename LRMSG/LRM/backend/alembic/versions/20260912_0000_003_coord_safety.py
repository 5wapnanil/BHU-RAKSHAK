"""STEP 7L: Add performance indexes for coordinator query patterns.

Revision ID: 003_coord_safety
Revises: 002_add_assignment_statuses
Create Date: 2026-09-12
"""

from alembic import op

revision = "003_coord_safety"
down_revision = "002_add_assignment_statuses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments (status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_volunteer_profiles_status ON volunteer_profiles (status, is_active);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_relief_resources_status ON relief_resources (status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_emergency_requests_status ON emergency_requests (status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_history_entity ON audit_history (entity_type, entity_id);")


def downgrade() -> None:
    op.drop_index("idx_assignments_status", "assignments")
    op.drop_index("idx_volunteer_profiles_status", "volunteer_profiles")
    op.drop_index("idx_relief_resources_status", "relief_resources")
    op.drop_index("idx_emergency_requests_status", "emergency_requests")
    op.drop_index("idx_audit_history_entity", "audit_history")
