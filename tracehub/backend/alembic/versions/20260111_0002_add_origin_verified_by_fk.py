"""Add FK constraint to origins.verified_by.

Sprint 11 - SCHEMA-003: Add missing FK constraint for verified_by to users table.

Revision ID: 20260111_0002
Revises: 20260111_0001
Create Date: 2026-01-11
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260111_0002'
down_revision = '20260111_0001'
branch_labels = None
depends_on = None


def upgrade():
    """Add FK constraint to origins.verified_by referencing users.id."""
    # Check if the constraint already exists (safety check)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing foreign keys on origins table
    existing_fks = inspector.get_foreign_keys('origins')
    fk_names = [fk['name'] for fk in existing_fks]

    if 'fk_origin_verified_by_user' not in fk_names:
        # Add FK constraint (SET NULL on delete - if user deleted, keep origin but clear verifier)
        op.create_foreign_key(
            'fk_origin_verified_by_user',
            'origins',
            'users',
            ['verified_by'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade():
    """Remove FK constraint from origins.verified_by."""
    op.drop_constraint('fk_origin_verified_by_user', 'origins', type_='foreignkey')
