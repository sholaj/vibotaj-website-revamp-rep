"""Add new document types to enum

Revision ID: 002
Revises: 001
Create Date: 2026-01-05

Adds new document types required for Sprint 7:
- SANITARY_CERTIFICATE
- EUDR_DUE_DILIGENCE
- QUALITY_CERTIFICATE
- EU_TRACES_CERTIFICATE
- VETERINARY_HEALTH_CERTIFICATE
- EXPORT_DECLARATION
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new document types to the documenttype enum."""
    # PostgreSQL requires ALTER TYPE to add enum values
    # Note: ADD VALUE cannot run inside a transaction block, so we commit after each

    # Add new document types
    new_types = [
        'SANITARY_CERTIFICATE',
        'EUDR_DUE_DILIGENCE',
        'QUALITY_CERTIFICATE',
        'EU_TRACES_CERTIFICATE',
        'VETERINARY_HEALTH_CERTIFICATE',
        'EXPORT_DECLARATION',
    ]

    for doc_type in new_types:
        # Check if value already exists before adding
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum
                    WHERE enumlabel = '{doc_type}'
                    AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'documenttype')
                ) THEN
                    ALTER TYPE documenttype ADD VALUE '{doc_type}';
                END IF;
            END
            $$;
        """)


def downgrade() -> None:
    """Remove new document types from enum.

    Note: PostgreSQL doesn't support removing enum values directly.
    To properly downgrade, we would need to:
    1. Create a new enum without the values
    2. Update all columns to use the new enum
    3. Drop the old enum
    4. Rename the new enum

    For safety, we'll just log a warning that manual intervention is needed.
    """
    # PostgreSQL doesn't easily support removing enum values
    # This would require recreating the type, which is complex
    # For production, consider keeping the enum values or doing a manual migration
    pass
