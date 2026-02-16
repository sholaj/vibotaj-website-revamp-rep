"""Add document_transitions table and extend compliance_results.

Revision ID: 20260216_0001
Revises: 20260120_0002
Create Date: 2026-02-16

PRD-016: Enhanced Compliance Engine
- Creates document_transitions table for state machine audit trail
- Adds shipment_id and document_type columns to compliance_results

All operations are idempotent - safe to run multiple times.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260216_0001'
down_revision = '20260120_0002'
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
    """Add document_transitions table and extend compliance_results."""

    # =========================================================================
    # Create document_transitions table
    # =========================================================================
    if not table_exists('document_transitions'):
        op.create_table(
            'document_transitions',
            sa.Column('id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('document_id', UUID(as_uuid=True),
                      sa.ForeignKey('documents.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('from_state', sa.String(50), nullable=False),
            sa.Column('to_state', sa.String(50), nullable=False),
            sa.Column('actor_id', UUID(as_uuid=True),
                      sa.ForeignKey('users.id'), nullable=True),
            sa.Column('reason', sa.Text, nullable=True),
            sa.Column('metadata', JSONB, server_default='{}'),
            sa.Column('organization_id', UUID(as_uuid=True),
                      sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                      nullable=False, index=True),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.text('CURRENT_TIMESTAMP'),
                      nullable=False),
        )

        # Indexes for common queries
        if not index_exists('ix_document_transitions_doc_created'):
            op.create_index(
                'ix_document_transitions_doc_created',
                'document_transitions',
                ['document_id', 'created_at'],
            )

    # =========================================================================
    # Extend compliance_results with shipment_id and document_type
    # =========================================================================
    if not column_exists('compliance_results', 'shipment_id'):
        op.add_column(
            'compliance_results',
            sa.Column('shipment_id', UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            'fk_compliance_results_shipment_id',
            'compliance_results', 'shipments',
            ['shipment_id'], ['id'],
            ondelete='CASCADE',
        )
        if not index_exists('ix_compliance_results_shipment_id'):
            op.create_index(
                'ix_compliance_results_shipment_id',
                'compliance_results',
                ['shipment_id'],
            )

    if not column_exists('compliance_results', 'document_type'):
        op.add_column(
            'compliance_results',
            sa.Column('document_type', sa.String(50), nullable=True),
        )


def downgrade() -> None:
    """Remove document_transitions table and compliance_results extensions."""

    # Drop indexes and columns from compliance_results
    if column_exists('compliance_results', 'document_type'):
        op.drop_column('compliance_results', 'document_type')

    if column_exists('compliance_results', 'shipment_id'):
        op.drop_constraint(
            'fk_compliance_results_shipment_id',
            'compliance_results',
            type_='foreignkey',
        )
        op.drop_index(
            'ix_compliance_results_shipment_id',
            table_name='compliance_results',
        )
        op.drop_column('compliance_results', 'shipment_id')

    # Drop document_transitions table
    if table_exists('document_transitions'):
        op.drop_index(
            'ix_document_transitions_doc_created',
            table_name='document_transitions',
        )
        op.drop_table('document_transitions')
