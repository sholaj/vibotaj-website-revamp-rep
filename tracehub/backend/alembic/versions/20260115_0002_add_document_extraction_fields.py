"""Add container extraction fields to documents table.

Revision ID: 20260115_0002
Revises: 20260115_0001
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '20260115_0002'
down_revision = '20260115_0001'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """Add container extraction fields (idempotent)."""
    if not column_exists('documents', 'extracted_container_number'):
        op.add_column('documents', sa.Column('extracted_container_number', sa.String(20), nullable=True))
    if not column_exists('documents', 'extraction_confidence'):
        op.add_column('documents', sa.Column('extraction_confidence', sa.Float(), nullable=True))


def downgrade():
    """Remove container extraction fields (idempotent)."""
    if column_exists('documents', 'extraction_confidence'):
        op.drop_column('documents', 'extraction_confidence')
    if column_exists('documents', 'extracted_container_number'):
        op.drop_column('documents', 'extracted_container_number')
