"""STEP 8H: Add composite index for audit_history query patterns.

Revision ID: 005_audit_index
Revises: 004_skills_jsonb
Create Date: 2026-09-12
"""

from alembic import op

revision = "005_audit_index"
down_revision = "004_skills_jsonb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_history_type_action_created
        ON audit_history (entity_type, action, created_at)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_audit_history_type_action_created")
