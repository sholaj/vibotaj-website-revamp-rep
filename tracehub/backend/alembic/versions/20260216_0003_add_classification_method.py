"""Add classification_method to documents table.

Revision ID: 20260216_0003
Revises: 20260216_0002
Create Date: 2026-02-16

PRD-019: AI Document Classification v2
"""

from alembic import op
import sqlalchemy as sa

revision = "20260216_0003"
down_revision = "20260216_0002"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists (idempotent migration)."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :col"
        ),
        {"table": table_name, "col": column_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not column_exists("documents", "classification_method"):
        op.add_column(
            "documents",
            sa.Column(
                "classification_method",
                sa.String(20),
                nullable=True,
                comment="Classification method: ai, keyword, manual",
            ),
        )


def downgrade() -> None:
    if column_exists("documents", "classification_method"):
        op.drop_column("documents", "classification_method")
