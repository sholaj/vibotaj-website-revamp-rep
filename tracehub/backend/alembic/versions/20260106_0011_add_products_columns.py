"""Add missing product and container_events columns

Revision ID: 011
Revises: 010
Create Date: 2026-01-06

Adds missing columns to products and container_events tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to products and container_events tables."""

    # ============================================
    # PRODUCTS TABLE - Add all columns that might be missing
    # ============================================

    # Add name column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'name'
            ) THEN
                ALTER TABLE products ADD COLUMN name VARCHAR(255);
            END IF;
        END $$;
    """)

    # Add description column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'description'
            ) THEN
                ALTER TABLE products ADD COLUMN description TEXT;
            END IF;
        END $$;
    """)

    # Add hs_code column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'hs_code'
            ) THEN
                ALTER TABLE products ADD COLUMN hs_code VARCHAR(20);
            END IF;
        END $$;
    """)

    # Add quantity_net_kg column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'quantity_net_kg'
            ) THEN
                ALTER TABLE products ADD COLUMN quantity_net_kg FLOAT;
            END IF;
        END $$;
    """)

    # Add quantity_gross_kg column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'quantity_gross_kg'
            ) THEN
                ALTER TABLE products ADD COLUMN quantity_gross_kg FLOAT;
            END IF;
        END $$;
    """)

    # Add quantity_units column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'quantity_units'
            ) THEN
                ALTER TABLE products ADD COLUMN quantity_units INTEGER;
            END IF;
        END $$;
    """)

    # Add packaging column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'packaging'
            ) THEN
                ALTER TABLE products ADD COLUMN packaging VARCHAR(100);
            END IF;
        END $$;
    """)

    # Add batch_number column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'batch_number'
            ) THEN
                ALTER TABLE products ADD COLUMN batch_number VARCHAR(100);
            END IF;
        END $$;
    """)

    # Add lot_number column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'lot_number'
            ) THEN
                ALTER TABLE products ADD COLUMN lot_number VARCHAR(100);
            END IF;
        END $$;
    """)

    # Add moisture_content column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'moisture_content'
            ) THEN
                ALTER TABLE products ADD COLUMN moisture_content FLOAT;
            END IF;
        END $$;
    """)

    # Add quality_grade column
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'quality_grade'
            ) THEN
                ALTER TABLE products ADD COLUMN quality_grade VARCHAR(50);
            END IF;
        END $$;
    """)

    # Add organization_id column (for multi-tenancy)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'organization_id'
            ) THEN
                ALTER TABLE products ADD COLUMN organization_id UUID;
            END IF;
        END $$;
    """)

    # ============================================
    # CONTAINER_EVENTS TABLE - Add all missing columns
    # ============================================

    # Add event_time column (if missing)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'container_events' AND column_name = 'event_time'
            ) THEN
                ALTER TABLE container_events ADD COLUMN event_time TIMESTAMPTZ;
            END IF;
        END $$;
    """)

    # Add organization_id to container_events
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'container_events' AND column_name = 'organization_id'
            ) THEN
                ALTER TABLE container_events ADD COLUMN organization_id UUID;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove added columns (optional - for rollback)."""
    pass
