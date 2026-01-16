"""Add BoL compliance fields and compliance_results table.

Revision ID: 20260116_0001
Revises: 20260115_0002_add_document_extraction_fields
Create Date: 2026-01-16

This migration adds:
1. bol_parsed_data JSONB column to documents table for storing parsed BoL data
2. compliance_results table for storing compliance check results
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '20260116_0001'
down_revision = '20260115_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Add BoL compliance fields."""
    # Add bol_parsed_data column to documents table (idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('documents')]

    if 'bol_parsed_data' not in columns:
        op.add_column(
            'documents',
            sa.Column('bol_parsed_data', JSONB, nullable=True,
                      comment='Parsed Bill of Lading data in canonical format')
        )

    if 'compliance_status' not in columns:
        op.add_column(
            'documents',
            sa.Column('compliance_status', sa.String(20), nullable=True,
                      comment='Compliance decision: APPROVE, HOLD, or REJECT')
        )

    if 'compliance_checked_at' not in columns:
        op.add_column(
            'documents',
            sa.Column('compliance_checked_at', sa.DateTime(timezone=True), nullable=True,
                      comment='When compliance was last checked')
        )

    # Create compliance_results table (idempotent)
    tables = inspector.get_table_names()
    if 'compliance_results' not in tables:
        op.create_table(
            'compliance_results',
            sa.Column('id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('document_id', UUID(as_uuid=True),
                      sa.ForeignKey('documents.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('rule_id', sa.String(20), nullable=False,
                      comment='Rule identifier (e.g., BOL-001)'),
            sa.Column('rule_name', sa.String(100), nullable=False,
                      comment='Human-readable rule name'),
            sa.Column('passed', sa.Boolean, nullable=False,
                      comment='Whether the rule passed'),
            sa.Column('message', sa.Text, nullable=True,
                      comment='Result message or error description'),
            sa.Column('severity', sa.String(20), nullable=False,
                      comment='Rule severity: ERROR, WARNING, INFO'),
            sa.Column('field_path', sa.String(100), nullable=True,
                      comment='Field that was evaluated'),
            sa.Column('checked_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
            sa.Column('organization_id', UUID(as_uuid=True),
                      sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=False),
        )

        # Create index for efficient queries
        op.create_index(
            'ix_compliance_results_document_rule',
            'compliance_results',
            ['document_id', 'rule_id']
        )


def downgrade():
    """Remove BoL compliance fields."""
    # Drop compliance_results table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'compliance_results' in tables:
        op.drop_index('ix_compliance_results_document_rule', table_name='compliance_results')
        op.drop_table('compliance_results')

    # Remove columns from documents table
    columns = [col['name'] for col in inspector.get_columns('documents')]

    if 'compliance_checked_at' in columns:
        op.drop_column('documents', 'compliance_checked_at')

    if 'compliance_status' in columns:
        op.drop_column('documents', 'compliance_status')

    if 'bol_parsed_data' in columns:
        op.drop_column('documents', 'bol_parsed_data')
