"""Add container extraction fields to documents table.

Revision ID: 20260115_0002
Revises: 20260115_0001
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa

revision = '20260115_0002'
down_revision = '20260115_0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('documents', sa.Column('extracted_container_number', sa.String(20), nullable=True))
    op.add_column('documents', sa.Column('extraction_confidence', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('documents', 'extraction_confidence')
    op.drop_column('documents', 'extracted_container_number')
