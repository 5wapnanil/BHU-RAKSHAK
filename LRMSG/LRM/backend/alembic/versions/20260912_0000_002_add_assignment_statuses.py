"""Add pending and rejected to assignment status CHECK constraint.

STEP 7K: Extends the assignment lifecycle to support explicit pending/rejected states
while preserving backward compatibility with existing created/started values.

Revision ID: 002
Revises: 001_initial
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa

revision = "002_add_assignment_statuses"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old CHECK constraint and recreate with expanded status values.
    # New values: pending, created, accepted, rejected, started, in_progress, completed, cancelled
    op.execute(
        "ALTER TABLE assignments DROP CONSTRAINT IF EXISTS ck_assignments_status"
    )
    op.execute(
        "ALTER TABLE assignments ADD CONSTRAINT ck_assignments_status "
        "CHECK (status IN ('pending', 'created', 'accepted', 'rejected', 'started', 'in_progress', 'completed', 'cancelled'))"
    )


def downgrade() -> None:
    # Revert to original status values
    op.execute(
        "ALTER TABLE assignments DROP CONSTRAINT IF EXISTS ck_assignments_status"
    )
    op.execute(
        "ALTER TABLE assignments ADD CONSTRAINT ck_assignments_status "
        "CHECK (status IN ('created', 'accepted', 'started', 'completed', 'cancelled'))"
    )
