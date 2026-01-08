"""Extend documentstatus enum with compliance/linking states

Revision ID: 003
Revises: 002
Create Date: 2026-01-08

Adds additional statuses used by application code to the documentstatus enum:
- DRAFT
- COMPLIANCE_OK
- COMPLIANCE_FAILED
- LINKED
- ARCHIVED
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new document statuses to the documentstatus enum.

    Uses ALTER TYPE ADD VALUE guarded by existence checks.
    """
    new_statuses = [
        'DRAFT',
        'COMPLIANCE_OK',
        'COMPLIANCE_FAILED',
        'LINKED',
        'ARCHIVED',
    ]

    for status in new_statuses:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum
                    WHERE enumlabel = '{status}'
                    AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'documentstatus')
                ) THEN
                    ALTER TYPE documentstatus ADD VALUE '{status}';
                END IF;
            END
            $$;
        """)


def downgrade() -> None:
    """Downgrade not supported for enum value removals.

    Removing enum values in PostgreSQL requires recreating the type and remapping
    columns, which is out of scope for automated downgrades.
    """
    pass
