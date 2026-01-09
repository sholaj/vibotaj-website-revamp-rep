"""Add missing shipment and container_events columns

Revision ID: 009
Revises: 008
Create Date: 2026-01-06

Comprehensive fix for schema mismatch between models and production database.
Adds all missing columns to shipments and container_events tables.
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
    """Add missing columns to shipments and container_events tables."""

    # ============================================
    # SHIPMENTS TABLE - Add all missing columns
    # ============================================

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
                ALTER TABLE shipments ADD COLUMN carrier_code VARCHAR(10);
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

    # Add exporter_name if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'shipments' AND column_name = 'exporter_name'
            ) THEN
                ALTER TABLE shipments ADD COLUMN exporter_name VARCHAR(255);
            END IF;
        END $$;
    """)

    # Add importer_name if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'shipments' AND column_name = 'importer_name'
            ) THEN
                ALTER TABLE shipments ADD COLUMN importer_name VARCHAR(255);
            END IF;
        END $$;
    """)

    # Add eudr_compliant if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'shipments' AND column_name = 'eudr_compliant'
            ) THEN
                ALTER TABLE shipments ADD COLUMN eudr_compliant BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
    """)

    # Add eudr_statement_id if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'shipments' AND column_name = 'eudr_statement_id'
            ) THEN
                ALTER TABLE shipments ADD COLUMN eudr_statement_id VARCHAR(100);
            END IF;
        END $$;
    """)

    # ============================================
    # CONTAINER_EVENTS TABLE - Add missing columns
    # ============================================

    # Create the eventstatus enum type if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'eventstatus') THEN
                CREATE TYPE eventstatus AS ENUM (
                    'BOOKED', 'GATE_IN', 'LOADED', 'DEPARTED', 'IN_TRANSIT',
                    'TRANSSHIPMENT', 'ARRIVED', 'DISCHARGED', 'GATE_OUT',
                    'DELIVERED', 'OTHER'
                );
            END IF;
        END $$;
    """)

    # Add event_status column if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'container_events' AND column_name = 'event_status'
            ) THEN
                ALTER TABLE container_events ADD COLUMN event_status eventstatus NOT NULL DEFAULT 'OTHER';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove added columns (optional - for rollback)."""
    # We don't drop these columns on downgrade as they may contain data
    pass
