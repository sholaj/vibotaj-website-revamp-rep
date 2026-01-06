"""Add missing shipment columns

Revision ID: 009
Revises: 008
Create Date: 2026-01-06

Fixes schema mismatch where booking_ref column was defined in model
but not present in production database.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to shipments table."""
    # Add booking_ref if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'shipments' AND column_name = 'booking_ref'
            ) THEN
                ALTER TABLE shipments ADD COLUMN booking_ref VARCHAR(50);
            END IF;
        END $$;
    """)

    # Add carrier_code if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'shipments' AND column_name = 'carrier_code'
            ) THEN
                ALTER TABLE shipments ADD COLUMN carrier_code VARCHAR(20);
            END IF;
        END $$;
    """)

    # Add carrier_name if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'shipments' AND column_name = 'carrier_name'
            ) THEN
                ALTER TABLE shipments ADD COLUMN carrier_name VARCHAR(100);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove added columns (optional - for rollback)."""
    # We don't drop these columns on downgrade as they may contain data
    pass
