"""Add user deletion fields.

Revision ID: 20260119_0001
Revises: 20260118_0001
Create Date: 2026-01-19

This migration adds fields for user deletion support:
- deleted_at: Timestamp when user was deleted (soft delete)
- deleted_by: UUID of admin who deleted the user
- deletion_reason: Required reason for deletion (audit trail)

All operations are idempotent - safe to run multiple times.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260119_0001'
down_revision = '20260118_0001'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in the table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(index_name: str) -> bool:
    """Check if an index exists."""
    bind = op.get_bind()
    result = bind.execute(sa.text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :index_name"
    ), {"index_name": index_name})
    return result.fetchone() is not None


def upgrade() -> None:
    """Add user deletion fields to users table."""

    # =========================================================================
    # Add deleted_at timestamp column
    # =========================================================================
    if not column_exists('users', 'deleted_at'):
        op.add_column(
            'users',
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True,
                      comment='Timestamp when user was deleted (NULL = not deleted)')
        )

    # =========================================================================
    # Add deleted_by foreign key column
    # =========================================================================
    if not column_exists('users', 'deleted_by'):
        op.add_column(
            'users',
            sa.Column('deleted_by', UUID(as_uuid=True), nullable=True,
                      comment='UUID of admin who deleted this user')
        )
        # Add foreign key constraint (self-referencing)
        op.create_foreign_key(
            'fk_users_deleted_by',
            'users', 'users',
            ['deleted_by'], ['id'],
            ondelete='SET NULL'
        )

    # =========================================================================
    # Add deletion_reason column
    # =========================================================================
    if not column_exists('users', 'deletion_reason'):
        op.add_column(
            'users',
            sa.Column('deletion_reason', sa.String(500), nullable=True,
                      comment='Required reason for deletion (audit trail)')
        )

    # =========================================================================
    # Add index for finding deleted users
    # =========================================================================
    if not index_exists('ix_users_deleted_at'):
        op.create_index(
            'ix_users_deleted_at',
            'users',
            ['deleted_at'],
            postgresql_where=sa.text('deleted_at IS NOT NULL')
        )

    # =========================================================================
    # Add index for finding active (non-deleted) users
    # =========================================================================
    if not index_exists('ix_users_active'):
        op.create_index(
            'ix_users_active',
            'users',
            ['organization_id', 'is_active'],
            postgresql_where=sa.text('deleted_at IS NULL')
        )


def downgrade() -> None:
    """Remove user deletion fields from users table."""

    # Drop indexes first
    op.drop_index('ix_users_active', table_name='users', if_exists=True)
    op.drop_index('ix_users_deleted_at', table_name='users', if_exists=True)

    # Drop foreign key constraint
    op.drop_constraint('fk_users_deleted_by', 'users', type_='foreignkey')

    # Drop columns
    columns_to_drop = ['deletion_reason', 'deleted_by', 'deleted_at']
    for col in columns_to_drop:
        if column_exists('users', col):
            op.drop_column('users', col)
