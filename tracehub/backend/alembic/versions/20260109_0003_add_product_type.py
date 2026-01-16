"""Add product_type to shipments table.

This migration adds the product_type field to track the type of goods
being shipped, enabling upfront document requirement display based on
the compliance matrix.

All existing shipments are backfilled as 'horn_hoof' since VIBOTAJ's
historical shipments are horn and hoof products.

Revision ID: 20260109_0003
Revises: 20260109_0002
Create Date: 2026-01-09
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260109_0003"
down_revision = "20260109_0002"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in the table."""
    bind = op.get_bind()
    result = bind.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :table AND column_name = :column"
    ), {"table": table_name, "column": column_name})
    return result.fetchone() is not None


def upgrade() -> None:
    # Skip if column already exists (baseline migration created it)
    if column_exists("shipments", "product_type"):
        return

    # Create the producttype enum
    product_type_enum = sa.Enum(
        'horn_hoof', 'sweet_potato', 'hibiscus', 'ginger', 'cocoa', 'other',
        name='producttype'
    )
    product_type_enum.create(op.get_bind(), checkfirst=True)

    # Add product_type column to shipments table (nullable initially for backfill)
    op.add_column(
        "shipments",
        sa.Column(
            "product_type",
            sa.Enum(
                'horn_hoof', 'sweet_potato', 'hibiscus', 'ginger', 'cocoa', 'other',
                name='producttype'
            ),
            nullable=True
        )
    )

    # Backfill all existing shipments as horn_hoof (cast to enum type)
    # Note: PostgreSQL enum values are case-sensitive, must match enum definition
    op.execute("UPDATE shipments SET product_type = 'horn_hoof'::producttype WHERE product_type IS NULL")

    # Add index for filtering shipments by product type
    op.create_index(
        "ix_shipments_product_type",
        "shipments",
        ["product_type"]
    )


def downgrade() -> None:
    # Remove index
    op.drop_index("ix_shipments_product_type", table_name="shipments")

    # Remove column
    op.drop_column("shipments", "product_type")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS producttype")
