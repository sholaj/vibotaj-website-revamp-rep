"""Add integration_credentials and integration_logs tables (PRD-021).

Revision ID: 20260216_0005
Revises: 20260216_0004
Create Date: 2026-02-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260216_0005"
down_revision = "20260216_0004"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
        ),
        {"t": table_name},
    )
    return result.scalar()


def upgrade() -> None:
    if not table_exists("integration_credentials"):
        op.create_table(
            "integration_credentials",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("integration_type", sa.String(50), nullable=False),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_test_success", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("organization_id", "integration_type", name="uq_integration_credentials_org_type"),
        )
        op.create_index("ix_integration_credentials_org", "integration_credentials", ["organization_id"])

    if not table_exists("integration_logs"):
        op.create_table(
            "integration_logs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("integration_type", sa.String(50), nullable=False),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("method", sa.String(100), nullable=False),
            sa.Column("request_summary", sa.String(500), nullable=True),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("response_time_ms", sa.Integer(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("shipment_id", UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("idx_integration_logs_org_type", "integration_logs", ["organization_id", "integration_type"])
        op.create_index("idx_integration_logs_created", "integration_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("integration_logs")
    op.drop_table("integration_credentials")
