"""Add validation override fields to shipments

Revision ID: 20260117_0002
Revises: 20260117_0001
Create Date: 2026-01-17

Adds fields for admin validation override:
- validation_override_reason: Reason for the override
- validation_override_by: Email of admin who performed override
- validation_override_at: Timestamp of override
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260117_0002'
down_revision = '20260117_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add validation override fields to shipments table
    op.add_column(
        'shipments',
        sa.Column('validation_override_reason', sa.String(500), nullable=True)
    )
    op.add_column(
        'shipments',
        sa.Column('validation_override_by', sa.String(255), nullable=True)
    )
    op.add_column(
        'shipments',
        sa.Column('validation_override_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    # Remove validation override fields
    op.drop_column('shipments', 'validation_override_at')
    op.drop_column('shipments', 'validation_override_by')
    op.drop_column('shipments', 'validation_override_reason')
