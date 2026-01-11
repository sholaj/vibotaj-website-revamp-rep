"""Drop unused parties table.

Sprint 10 - ARCH-003: Remove unused Party table.
Shipments now use exporter_name/importer_name strings instead of party FKs.

Revision ID: 20260111_0001
Revises: 20260109_0003
Create Date: 2026-01-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260111_0001'
down_revision = '20260109_0003'
branch_labels = None
depends_on = None


def upgrade():
    """Drop the parties table - no longer used."""
    # Check if table exists before dropping (safety check)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'parties' in inspector.get_table_names():
        op.drop_table('parties')


def downgrade():
    """Recreate the parties table if needed for rollback."""
    op.create_table(
        'parties',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('address', sa.String(500)),
        sa.Column('city', sa.String(100)),
        sa.Column('country', sa.String(2)),
        sa.Column('registration_number', sa.String(100)),
        sa.Column('tax_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
