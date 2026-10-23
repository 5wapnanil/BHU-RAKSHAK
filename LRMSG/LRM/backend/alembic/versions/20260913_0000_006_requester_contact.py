"""Add contact_name and contact_phone columns to emergency_requests.

Mobile app collects contactName/contactPhone but they were only stored inside
the JSONB payload. This migration adds first-class columns and backfills from
the existing payload data.

Revision ID: 006_requester_contact
Revises: 005_audit_index
Create Date: 2026-09-13
"""

from alembic import op

revision = "006_requester_contact"
down_revision = "005_audit_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE emergency_requests
        ADD COLUMN IF NOT EXISTS contact_name TEXT,
        ADD COLUMN IF NOT EXISTS contact_phone TEXT
    """)

    # Backfill from existing JSONB payload
    op.execute("""
        UPDATE emergency_requests
        SET
            contact_name = COALESCE(contact_name, payload->>'contactName'),
            contact_phone = COALESCE(contact_phone, payload->>'contactPhone')
        WHERE
            contact_name IS NULL OR contact_phone IS NULL
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE emergency_requests
        DROP COLUMN IF EXISTS contact_name,
        DROP COLUMN IF EXISTS contact_phone
    """)
