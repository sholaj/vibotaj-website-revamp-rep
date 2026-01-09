"""Add buyer_organization_id to shipments table.

This migration adds the buyer_organization_id field to support linking
shipments to buyer organizations (e.g., HAGES, Witatrade) separately
from the owning organization (VIBOTAJ).

Revision ID: 20260109_0002
Revises: 20260109_0001
Create Date: 2026-01-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260109_0002"
down_revision = "20260109_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add buyer_organization_id column to shipments table
    op.add_column(
        "shipments",
        sa.Column(
            "buyer_organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True  # Backward compatible with existing shipments
        )
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_shipments_buyer_organization_id",
        "shipments",
        "organizations",
        ["buyer_organization_id"],
        ["id"]
    )

    # Add index for efficient buyer queries
    op.create_index(
        "ix_shipments_buyer_organization_id",
        "shipments",
        ["buyer_organization_id"]
    )


def downgrade() -> None:
    # Remove index
    op.drop_index("ix_shipments_buyer_organization_id", table_name="shipments")

    # Remove foreign key constraint
    op.drop_constraint(
        "fk_shipments_buyer_organization_id",
        "shipments",
        type_="foreignkey"
    )

    # Remove column
    op.drop_column("shipments", "buyer_organization_id")
