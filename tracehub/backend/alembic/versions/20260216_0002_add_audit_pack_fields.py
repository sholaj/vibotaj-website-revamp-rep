"""Add audit pack caching fields to shipments.

PRD-017: Audit Pack v2 — store generation timestamp and storage path
for caching and signed URL generation.

Revision ID: 20260216_0002
Revises: 20260216_0001
Create Date: 2026-02-16
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision = "20260216_0002"
down_revision = "20260216_0001"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists (idempotent migrations)."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :col"
        ),
        {"table": table_name, "col": column_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not column_exists("shipments", "audit_pack_generated_at"):
        op.add_column(
            "shipments",
            sa.Column("audit_pack_generated_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not column_exists("shipments", "audit_pack_storage_path"):
        op.add_column(
            "shipments",
            sa.Column("audit_pack_storage_path", sa.String(500), nullable=True),
        )


def downgrade() -> None:
    if column_exists("shipments", "audit_pack_storage_path"):
        op.drop_column("shipments", "audit_pack_storage_path")
    if column_exists("shipments", "audit_pack_generated_at"):
        op.drop_column("shipments", "audit_pack_generated_at")
