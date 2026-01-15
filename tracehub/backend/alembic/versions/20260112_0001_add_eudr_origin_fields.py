"""Add EUDR compliance fields to origins table

Sprint 14: Compliance Feature Hardening

Adds missing EUDR-specific fields to the origins table:
- deforestation_free_statement: Boolean flag for explicit statement
- due_diligence_statement_ref: Reference number for DDS
- geolocation_polygon: GeoJSON for plot boundaries
- supplier_attestation_date: When supplier attested compliance

Revision ID: 20260112_0001
Revises: 20260111_0005
Create Date: 2026-01-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic
revision = '20260112_0001'
down_revision = '20260111_0005'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """Add EUDR compliance fields to origins table (idempotent)."""
    # Add new columns for EUDR compliance only if they don't exist
    if not column_exists('origins', 'deforestation_free_statement'):
        op.add_column('origins', sa.Column('deforestation_free_statement', sa.Boolean(), nullable=True))
    if not column_exists('origins', 'due_diligence_statement_ref'):
        op.add_column('origins', sa.Column('due_diligence_statement_ref', sa.String(255), nullable=True))
    if not column_exists('origins', 'geolocation_polygon'):
        op.add_column('origins', sa.Column('geolocation_polygon', sa.Text(), nullable=True))
    if not column_exists('origins', 'supplier_attestation_date'):
        op.add_column('origins', sa.Column('supplier_attestation_date', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    """Remove EUDR compliance fields from origins table (idempotent)."""
    if column_exists('origins', 'supplier_attestation_date'):
        op.drop_column('origins', 'supplier_attestation_date')
    if column_exists('origins', 'geolocation_polygon'):
        op.drop_column('origins', 'geolocation_polygon')
    if column_exists('origins', 'due_diligence_statement_ref'):
        op.drop_column('origins', 'due_diligence_statement_ref')
    if column_exists('origins', 'deforestation_free_statement'):
        op.drop_column('origins', 'deforestation_free_statement')
