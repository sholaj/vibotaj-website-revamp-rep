"""Add document validation enhancement fields.

Revision ID: 20260118_0001
Revises: 20260117_0002_add_validation_override_fields
Create Date: 2026-01-18

This migration adds fields for:
- Canonical document data (JSONB)
- Document versioning (version, is_primary, supersedes_id)
- Classification confidence
- Document issues table for tracking validation issues

All operations are idempotent - safe to run multiple times.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260118_0001'
down_revision = '20260117_0002_add_validation_override_fields'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in the table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def index_exists(index_name: str) -> bool:
    """Check if an index exists."""
    bind = op.get_bind()
    result = bind.execute(sa.text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :index_name"
    ), {"index_name": index_name})
    return result.fetchone() is not None


def upgrade() -> None:
    """Add document validation fields and document_issues table."""

    # =========================================================================
    # Add canonical_data JSONB column to documents table
    # =========================================================================
    if not column_exists('documents', 'canonical_data'):
        op.add_column(
            'documents',
            sa.Column('canonical_data', JSONB, nullable=True,
                      comment='Canonical extracted data in standardized format')
        )

    # =========================================================================
    # Add versioning fields to documents table
    # =========================================================================
    if not column_exists('documents', 'version'):
        op.add_column(
            'documents',
            sa.Column('version', sa.Integer, nullable=False, server_default='1',
                      comment='Document version number (increments for duplicates)')
        )

    if not column_exists('documents', 'is_primary'):
        op.add_column(
            'documents',
            sa.Column('is_primary', sa.Boolean, nullable=False, server_default='true',
                      comment='Whether this is the primary version for validation')
        )

    if not column_exists('documents', 'supersedes_id'):
        op.add_column(
            'documents',
            sa.Column('supersedes_id', UUID(as_uuid=True), nullable=True,
                      comment='ID of the document this version supersedes')
        )
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_documents_supersedes_id',
            'documents', 'documents',
            ['supersedes_id'], ['id'],
            ondelete='SET NULL'
        )

    # =========================================================================
    # Add classification confidence field
    # =========================================================================
    if not column_exists('documents', 'classification_confidence'):
        op.add_column(
            'documents',
            sa.Column('classification_confidence', sa.Float, nullable=True,
                      comment='AI classification confidence score (0.0-1.0)')
        )

    # =========================================================================
    # Add parser metadata fields
    # =========================================================================
    if not column_exists('documents', 'parsed_at'):
        op.add_column(
            'documents',
            sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True,
                      comment='Timestamp when document was parsed')
        )

    if not column_exists('documents', 'parser_version'):
        op.add_column(
            'documents',
            sa.Column('parser_version', sa.String(20), nullable=True,
                      comment='Version of parser used for extraction')
        )

    # =========================================================================
    # Create document_issues table for tracking validation issues
    # =========================================================================
    if not table_exists('document_issues'):
        op.create_table(
            'document_issues',
            sa.Column('id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('document_id', UUID(as_uuid=True),
                      sa.ForeignKey('documents.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('shipment_id', UUID(as_uuid=True),
                      sa.ForeignKey('shipments.id', ondelete='CASCADE'),
                      nullable=True, index=True),
            sa.Column('rule_id', sa.String(50), nullable=False,
                      comment='Rule identifier (e.g., DOC-001, XD-002)'),
            sa.Column('rule_name', sa.String(255), nullable=False,
                      comment='Human-readable rule name'),
            sa.Column('severity', sa.String(20), nullable=False,
                      comment='ERROR, WARNING, or INFO'),
            sa.Column('message', sa.Text, nullable=False,
                      comment='Validation failure message'),
            sa.Column('field', sa.String(100), nullable=True,
                      comment='Field path that failed validation'),
            sa.Column('expected_value', sa.Text, nullable=True,
                      comment='Expected value (for comparison rules)'),
            sa.Column('actual_value', sa.Text, nullable=True,
                      comment='Actual value found'),
            sa.Column('source_document_type', sa.String(50), nullable=True,
                      comment='Source document type (for cross-doc rules)'),
            sa.Column('target_document_type', sa.String(50), nullable=True,
                      comment='Target document type (for cross-doc rules)'),
            # Override tracking
            sa.Column('is_overridden', sa.Boolean, nullable=False, server_default='false',
                      comment='Whether this issue has been overridden'),
            sa.Column('overridden_by', UUID(as_uuid=True),
                      sa.ForeignKey('users.id'), nullable=True),
            sa.Column('overridden_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('override_reason', sa.Text, nullable=True,
                      comment='Reason for override'),
            # Timestamps
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True),
                      server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            # Organization for multi-tenancy
            sa.Column('organization_id', UUID(as_uuid=True),
                      sa.ForeignKey('organizations.id'), nullable=True, index=True),
        )

        # Create indexes for common queries
        if not index_exists('ix_document_issues_rule_id'):
            op.create_index('ix_document_issues_rule_id', 'document_issues', ['rule_id'])

        if not index_exists('ix_document_issues_severity'):
            op.create_index('ix_document_issues_severity', 'document_issues', ['severity'])

        if not index_exists('ix_document_issues_not_overridden'):
            op.create_index(
                'ix_document_issues_not_overridden',
                'document_issues',
                ['document_id'],
                postgresql_where=sa.text('is_overridden = false')
            )

    # =========================================================================
    # Add index for finding primary documents
    # =========================================================================
    if not index_exists('ix_documents_primary_by_type'):
        op.create_index(
            'ix_documents_primary_by_type',
            'documents',
            ['shipment_id', 'document_type'],
            postgresql_where=sa.text('is_primary = true')
        )

    # =========================================================================
    # Add revalidation tracking fields
    # =========================================================================
    if not column_exists('documents', 'last_validated_at'):
        op.add_column(
            'documents',
            sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True,
                      comment='Last time document was validated')
        )

    if not column_exists('documents', 'validation_version'):
        op.add_column(
            'documents',
            sa.Column('validation_version', sa.Integer, nullable=True,
                      comment='Version of validation rules used')
        )


def downgrade() -> None:
    """Remove document validation fields and document_issues table."""

    # Drop indexes first
    op.drop_index('ix_documents_primary_by_type', table_name='documents', if_exists=True)
    op.drop_index('ix_document_issues_not_overridden', table_name='document_issues', if_exists=True)
    op.drop_index('ix_document_issues_severity', table_name='document_issues', if_exists=True)
    op.drop_index('ix_document_issues_rule_id', table_name='document_issues', if_exists=True)

    # Drop document_issues table
    op.drop_table('document_issues', if_exists=True)

    # Drop foreign key constraint
    op.drop_constraint('fk_documents_supersedes_id', 'documents', type_='foreignkey')

    # Drop columns from documents table
    columns_to_drop = [
        'validation_version',
        'last_validated_at',
        'parser_version',
        'parsed_at',
        'classification_confidence',
        'supersedes_id',
        'is_primary',
        'version',
        'canonical_data',
    ]

    for col in columns_to_drop:
        if column_exists('documents', col):
            op.drop_column('documents', col)
