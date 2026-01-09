"""Add organization_id columns to tenant tables (nullable initially)

Revision ID: 004
Revises: 003
Create Date: 2026-01-06

IMPORTANT: These columns are added as NULLABLE to allow data migration.
Migration 006 will add NOT NULL constraints after data migration.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add organization_id column to all tenant-specific tables."""

    # List of tables that need organization_id
    tenant_tables = [
        'users',
        'shipments',
        'documents',
        'products',
        'parties',
        'origins',
        'container_events',
        'notifications',
        'audit_logs'
    ]

    # Add organization_id column to each table (NULLABLE for now)
    for table in tenant_tables:
        op.add_column(
            table,
            sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True)
        )
        # Add index for query performance (will be composite with other columns later)
        op.create_index(
            f'ix_{table}_organization_id',
            table,
            ['organization_id']
        )

    print(f"✓ Added organization_id columns to {len(tenant_tables)} tables")


def downgrade() -> None:
    """Remove organization_id columns."""

    tenant_tables = [
        'users',
        'shipments',
        'documents',
        'products',
        'parties',
        'origins',
        'container_events',
        'notifications',
        'audit_logs'
    ]

    for table in tenant_tables:
        op.drop_index(f'ix_{table}_organization_id', table_name=table)
        op.drop_column(table, 'organization_id')
