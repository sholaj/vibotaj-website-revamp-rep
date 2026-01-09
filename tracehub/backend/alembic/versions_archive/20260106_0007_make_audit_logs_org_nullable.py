"""Make audit_logs.organization_id nullable

Revision ID: 007
Revises: 006
Create Date: 2026-01-06

Audit logs may not always have an organization context:
- System-level actions
- Login failures for unknown users
- Actions during authentication before user is loaded
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make audit_logs.organization_id nullable."""
    # Remove NOT NULL constraint on audit_logs.organization_id
    op.alter_column(
        'audit_logs',
        'organization_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True
    )
    print("✓ Made audit_logs.organization_id nullable")


def downgrade() -> None:
    """Make audit_logs.organization_id NOT NULL again."""
    # Re-add NOT NULL constraint
    op.alter_column(
        'audit_logs',
        'organization_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False
    )
