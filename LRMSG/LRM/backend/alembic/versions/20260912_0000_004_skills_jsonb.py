"""STEP 7L: Convert volunteer_profiles.skills from TEXT to JSONB.

Revision ID: 004_skills_jsonb
Revises: 003_coord_safety
Create Date: 2026-09-12
"""

from alembic import op

revision = "004_skills_jsonb"
down_revision = "003_coord_safety"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE volunteer_profiles
        ALTER COLUMN skills TYPE jsonb
        USING CASE
            WHEN skills IS NULL THEN '[]'::jsonb
            WHEN skills = '' THEN '[]'::jsonb
            WHEN skills ~ '^\\[' THEN skills::jsonb
            WHEN skills = '{}' THEN '[]'::jsonb
            ELSE ('["' || skills || '"]')::jsonb
        END
    """)
    op.execute("""
        ALTER TABLE volunteer_profiles
        ALTER COLUMN skills SET DEFAULT '[]'::jsonb
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE volunteer_profiles
        ALTER COLUMN skills TYPE text
        USING skills::text
    """)
    op.execute("""
        ALTER TABLE volunteer_profiles
        ALTER COLUMN skills SET DEFAULT NULL
    """)
