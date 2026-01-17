"""Add validation override fields to shipments

Revision ID: 20260117_0002
Revises: 20260117_0001
Create Date: 2026-01-17

Adds fields for admin validation override:
- validation_override_reason: Reason for the override
- validation_override_by: Email of admin who performed override
- validation_override_at: Timestamp of override

IDEMPOTENT: Safe to run multiple times - checks if columns exist first.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260117_0002'
down_revision = '20260117_0001'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Add validation override fields to shipments table (idempotent)
    if not column_exists('shipments', 'validation_override_reason'):
        op.add_column(
            'shipments',
            sa.Column('validation_override_reason', sa.String(500), nullable=True)
        )

    if not column_exists('shipments', 'validation_override_by'):
        op.add_column(
            'shipments',
            sa.Column('validation_override_by', sa.String(255), nullable=True)
        )

    if not column_exists('shipments', 'validation_override_at'):
        op.add_column(
            'shipments',
            sa.Column('validation_override_at', sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    # Remove validation override fields (idempotent)
    if column_exists('shipments', 'validation_override_at'):
        op.drop_column('shipments', 'validation_override_at')

    if column_exists('shipments', 'validation_override_by'):
        op.drop_column('shipments', 'validation_override_by')

    if column_exists('shipments', 'validation_override_reason'):
        op.drop_column('shipments', 'validation_override_reason')
