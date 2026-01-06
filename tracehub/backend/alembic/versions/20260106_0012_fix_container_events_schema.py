"""Fix container_events schema to match model

Revision ID: 012
Revises: 011
Create Date: 2026-01-06

Production database has different column names than the model expects:
- event_type -> event_status
- event_timestamp -> event_time
- raw_payload -> raw_data
- Missing: description column
- Extra: delay_hours, external_id, location_lat, location_lng (keep these)

This migration handles both cases:
1. Fresh databases with correct schema (no-op)
2. Production databases with old schema (renames + adds columns)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = :table AND column_name = :column
    """), {"table": table_name, "column": column_name})
    return result.fetchone() is not None


def enum_exists(enum_name: str) -> bool:
    """Check if an enum type exists."""
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT typname FROM pg_type WHERE typname = :name
    """), {"name": enum_name})
    return result.fetchone() is not None


def upgrade() -> None:
    """Fix container_events schema to match model."""

    # Create eventstatus enum if it doesn't exist (for fresh DBs it should exist)
    if not enum_exists('eventstatus'):
        op.execute("""
            CREATE TYPE eventstatus AS ENUM (
                'BOOKED', 'GATE_IN', 'LOADED', 'DEPARTED', 'IN_TRANSIT',
                'TRANSSHIPMENT', 'ARRIVED', 'DISCHARGED', 'GATE_OUT', 'DELIVERED', 'OTHER'
            )
        """)
        print("✓ Created eventstatus enum")

    # Handle event_type -> event_status rename (if old schema exists)
    if column_exists('container_events', 'event_type') and not column_exists('container_events', 'event_status'):
        # Check if eventtype enum exists and convert
        if enum_exists('eventtype'):
            # Rename column and convert enum
            op.execute("""
                ALTER TABLE container_events
                ALTER COLUMN event_type TYPE eventstatus
                USING event_type::text::eventstatus
            """)
        op.alter_column('container_events', 'event_type', new_column_name='event_status')
        print("✓ Renamed event_type to event_status")

    # Handle event_timestamp -> event_time rename
    if column_exists('container_events', 'event_timestamp') and not column_exists('container_events', 'event_time'):
        op.alter_column('container_events', 'event_timestamp', new_column_name='event_time')
        print("✓ Renamed event_timestamp to event_time")

    # Handle raw_payload -> raw_data rename
    if column_exists('container_events', 'raw_payload') and not column_exists('container_events', 'raw_data'):
        op.alter_column('container_events', 'raw_payload', new_column_name='raw_data')
        print("✓ Renamed raw_payload to raw_data")

    # Add description column if missing
    if not column_exists('container_events', 'description'):
        op.add_column('container_events', sa.Column('description', sa.Text(), nullable=True))
        print("✓ Added description column")

    # Add index on event_time if not exists (for query performance)
    try:
        op.create_index('ix_container_events_event_time', 'container_events', ['event_time'])
    except Exception:
        pass  # Index may already exist

    print("✓ container_events schema fix complete")


def downgrade() -> None:
    """Revert container_events schema changes (optional)."""
    # Note: Downgrade is complex due to enum changes
    # In practice, we don't usually downgrade schema fixes
    pass
