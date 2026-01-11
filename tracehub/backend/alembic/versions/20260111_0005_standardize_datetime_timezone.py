"""Standardize DateTime columns to include timezone.

Sprint 12 - SCHEMA-004: Standardize DateTime timezone handling.

All DateTime columns should use timezone=True for consistent UTC handling.

Revision ID: 20260111_0005
Revises: 20260111_0004
Create Date: 2026-01-11
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260111_0005'
down_revision = '20260111_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add timezone to all DateTime columns."""

    # shipments table - 6 columns
    op.alter_column('shipments', 'etd',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="etd AT TIME ZONE 'UTC'")
    op.alter_column('shipments', 'eta',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="eta AT TIME ZONE 'UTC'")
    op.alter_column('shipments', 'atd',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="atd AT TIME ZONE 'UTC'")
    op.alter_column('shipments', 'ata',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="ata AT TIME ZONE 'UTC'")
    op.alter_column('shipments', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('shipments', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="updated_at AT TIME ZONE 'UTC'")

    # users table - 3 columns
    op.alter_column('users', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('users', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="updated_at AT TIME ZONE 'UTC'")
    op.alter_column('users', 'last_login',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="last_login AT TIME ZONE 'UTC'")

    # audit_logs table - 1 column
    op.alter_column('audit_logs', 'timestamp',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="timestamp AT TIME ZONE 'UTC'")

    # organizations table - 2 columns
    op.alter_column('organizations', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('organizations', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="updated_at AT TIME ZONE 'UTC'")

    # organization_memberships table - 2 columns
    op.alter_column('organization_memberships', 'joined_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="joined_at AT TIME ZONE 'UTC'")
    op.alter_column('organization_memberships', 'last_active_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="last_active_at AT TIME ZONE 'UTC'")

    # invitations table - 4 columns
    op.alter_column('invitations', 'expires_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="expires_at AT TIME ZONE 'UTC'")
    op.alter_column('invitations', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('invitations', 'accepted_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="accepted_at AT TIME ZONE 'UTC'")

    # reference_registry table - 1 column
    op.alter_column('reference_registry', 'first_seen_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using="first_seen_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    """Remove timezone from DateTime columns (revert to naive datetime)."""

    # shipments table
    op.alter_column('shipments', 'etd', type_=sa.DateTime())
    op.alter_column('shipments', 'eta', type_=sa.DateTime())
    op.alter_column('shipments', 'atd', type_=sa.DateTime())
    op.alter_column('shipments', 'ata', type_=sa.DateTime())
    op.alter_column('shipments', 'created_at', type_=sa.DateTime())
    op.alter_column('shipments', 'updated_at', type_=sa.DateTime())

    # users table
    op.alter_column('users', 'created_at', type_=sa.DateTime())
    op.alter_column('users', 'updated_at', type_=sa.DateTime())
    op.alter_column('users', 'last_login', type_=sa.DateTime())

    # audit_logs table
    op.alter_column('audit_logs', 'timestamp', type_=sa.DateTime())

    # organizations table
    op.alter_column('organizations', 'created_at', type_=sa.DateTime())
    op.alter_column('organizations', 'updated_at', type_=sa.DateTime())

    # organization_memberships table
    op.alter_column('organization_memberships', 'joined_at', type_=sa.DateTime())
    op.alter_column('organization_memberships', 'last_active_at', type_=sa.DateTime())

    # invitations table
    op.alter_column('invitations', 'expires_at', type_=sa.DateTime())
    op.alter_column('invitations', 'created_at', type_=sa.DateTime())
    op.alter_column('invitations', 'accepted_at', type_=sa.DateTime())

    # reference_registry table
    op.alter_column('reference_registry', 'first_seen_at', type_=sa.DateTime())
