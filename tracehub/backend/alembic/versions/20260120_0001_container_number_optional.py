"""Make container_number optional for draft shipments.

Issue #41: Allow creating shipment drafts without a container number.

This migration changes the container_number column from NOT NULL to NULL,
allowing shipments to be created without an assigned container. The container
can be added later when known.

Revision ID: 20260120_0001
Revises: 20260119_0001_add_user_deletion_fields
Create Date: 2026-01-20
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260120_0001"
down_revision = "20260119_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make container_number nullable to support draft shipments."""
    # ALTER COLUMN to allow NULL values
    op.alter_column(
        'shipments',
        'container_number',
        existing_type=sa.String(20),
        nullable=True,
        comment='ISO 6346 container number (optional for drafts)'
    )


def downgrade() -> None:
    """Revert container_number to required field.

    Note: This may fail if there are existing rows with NULL container_number.
    Consider providing a default value or cleaning up data before downgrade.
    """
    # For safety, update any NULL values to a placeholder before making NOT NULL
    op.execute(
        "UPDATE shipments SET container_number = 'TBD' WHERE container_number IS NULL"
    )

    # ALTER COLUMN back to NOT NULL
    op.alter_column(
        'shipments',
        'container_number',
        existing_type=sa.String(20),
        nullable=False,
        comment=None
    )
