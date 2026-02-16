"""Add notification_preferences and email_log tables (PRD-020).

Revision ID: 20260216_0004
Revises: 20260216_0003
Create Date: 2026-02-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260216_0004"
down_revision = "20260216_0003"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :col"
        ),
        {"table": table_name, "col": column_name},
    )
    return result.fetchone() is not None


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :table"
        ),
        {"table": table_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not table_exists("notification_preferences"):
        op.create_table(
            "notification_preferences",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "organization_id",
                UUID(as_uuid=True),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("event_type", sa.String(50), nullable=False),
            sa.Column(
                "email_enabled", sa.Boolean, nullable=False, server_default="true"
            ),
            sa.Column(
                "in_app_enabled", sa.Boolean, nullable=False, server_default="true"
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "user_id",
                "organization_id",
                "event_type",
                name="uq_notification_pref_user_org_event",
            ),
        )
        op.create_index(
            "ix_notification_preferences_user_id",
            "notification_preferences",
            ["user_id"],
        )

    if not table_exists("email_log"):
        op.create_table(
            "email_log",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
            sa.Column("recipient_email", sa.String(320), nullable=False),
            sa.Column("event_type", sa.String(50), nullable=False),
            sa.Column("subject", sa.String(500), nullable=False),
            sa.Column(
                "status",
                sa.String(20),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("provider_message_id", sa.String(255), nullable=True),
            sa.Column("error_message", sa.Text, nullable=True),
            sa.Column(
                "attempts", sa.Integer, nullable=False, server_default="0"
            ),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_email_log_organization_id",
            "email_log",
            ["organization_id"],
        )


def downgrade() -> None:
    op.drop_table("email_log")
    op.drop_table("notification_preferences")
