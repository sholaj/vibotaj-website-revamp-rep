"""Add NOT NULL constraints, foreign keys, and composite indexes for multi-tenancy

Revision ID: 006
Revises: 005
Create Date: 2026-01-06

This migration finalizes the multi-tenancy setup by:
1. Validating that NO NULL organization_id values exist
2. Adding NOT NULL constraints
3. Adding foreign key constraints to organizations table
4. Adding composite indexes for tenant-scoped queries

IMPORTANT: This migration will FAIL if any organization_id is NULL.
Run Migration 005 first to populate all organization_id columns.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add constraints and indexes for multi-tenancy."""

    connection = op.get_bind()

    tenant_tables = [
        'users', 'shipments', 'documents', 'products',
        'parties', 'origins', 'container_events',
        'notifications', 'audit_logs'
    ]

    # =================================================================
    # STEP 1: Validate NO NULL organization_id
    # =================================================================
    print("Step 1/4: Validating data integrity...")

    for table in tenant_tables:
        result = connection.execute(sa.text(f"""
            SELECT COUNT(*) FROM {table} WHERE organization_id IS NULL
        """)).scalar()

        if result > 0:
            raise Exception(
                f"MIGRATION FAILED: {result} rows in {table} have NULL organization_id. "
                f"Run Migration 005 first to migrate data."
            )
        print(f"✓ {table}: All rows have valid organization_id")

    # =================================================================
    # STEP 2: Add NOT NULL constraints
    # =================================================================
    print("\nStep 2/4: Adding NOT NULL constraints...")

    for table in tenant_tables:
        op.alter_column(
            table,
            'organization_id',
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=False
        )
        print(f"✓ {table}.organization_id is now NOT NULL")

    # =================================================================
    # STEP 3: Add foreign key constraints
    # =================================================================
    print("\nStep 3/4: Adding foreign key constraints...")

    for table in tenant_tables:
        op.create_foreign_key(
            f'fk_{table}_organization_id',
            table,
            'organizations',
            ['organization_id'],
            ['id'],
            ondelete='RESTRICT'  # Prevent organization deletion if data exists
        )
        print(f"✓ Added FK constraint on {table}.organization_id")

    # =================================================================
    # STEP 4: Add composite indexes for tenant-scoped queries
    # =================================================================
    print("\nStep 4/4: Adding composite indexes for performance...")

    # Composite indexes for common query patterns
    composite_indexes = [
        ('users', ['organization_id', 'email']),
        ('users', ['organization_id', 'is_active']),
        ('shipments', ['organization_id', 'status']),
        ('shipments', ['organization_id', 'reference']),
        ('shipments', ['organization_id', 'created_at']),
        ('documents', ['organization_id', 'shipment_id']),
        ('documents', ['organization_id', 'document_type']),
        ('products', ['organization_id', 'shipment_id']),
        ('parties', ['organization_id', 'type']),
        ('origins', ['organization_id', 'product_id']),
        ('container_events', ['organization_id', 'shipment_id']),
        ('container_events', ['organization_id', 'event_timestamp']),
        ('notifications', ['organization_id', 'user_id']),
        ('notifications', ['organization_id', 'read']),
        ('audit_logs', ['organization_id', 'user_id']),
        ('audit_logs', ['organization_id', 'resource_type']),
    ]

    for table, columns in composite_indexes:
        index_name = f"ix_{table}_{'_'.join(columns)}"
        op.create_index(index_name, table, columns)
        print(f"✓ Created composite index: {index_name}")

    # Unique constraint for shipment reference within organization
    op.create_unique_constraint(
        'uq_shipments_organization_reference',
        'shipments',
        ['organization_id', 'reference']
    )
    print("✓ Added unique constraint: organization_id + reference on shipments")

    # =================================================================
    # SUMMARY
    # =================================================================
    print("\n" + "="*60)
    print("CONSTRAINT & INDEX SUMMARY")
    print("="*60)
    print(f"NOT NULL constraints:    {len(tenant_tables)} tables")
    print(f"Foreign key constraints: {len(tenant_tables)} tables")
    print(f"Composite indexes:       {len(composite_indexes)} indexes")
    print(f"Unique constraints:      1 constraint")
    print("="*60)
    print("✓ Multi-tenancy constraints applied successfully!")
    print("="*60 + "\n")


def downgrade() -> None:
    """Remove constraints and indexes."""

    tenant_tables = [
        'users', 'shipments', 'documents', 'products',
        'parties', 'origins', 'container_events',
        'notifications', 'audit_logs'
    ]

    # Drop unique constraint
    op.drop_constraint('uq_shipments_organization_reference', 'shipments', type_='unique')

    # Drop composite indexes
    composite_indexes = [
        ('users', ['organization_id', 'email']),
        ('users', ['organization_id', 'is_active']),
        ('shipments', ['organization_id', 'status']),
        ('shipments', ['organization_id', 'reference']),
        ('shipments', ['organization_id', 'created_at']),
        ('documents', ['organization_id', 'shipment_id']),
        ('documents', ['organization_id', 'document_type']),
        ('products', ['organization_id', 'shipment_id']),
        ('parties', ['organization_id', 'type']),
        ('origins', ['organization_id', 'product_id']),
        ('container_events', ['organization_id', 'shipment_id']),
        ('container_events', ['organization_id', 'event_timestamp']),
        ('notifications', ['organization_id', 'user_id']),
        ('notifications', ['organization_id', 'read']),
        ('audit_logs', ['organization_id', 'user_id']),
        ('audit_logs', ['organization_id', 'resource_type']),
    ]

    for table, columns in composite_indexes:
        index_name = f"ix_{table}_{'_'.join(columns)}"
        op.drop_index(index_name, table_name=table)

    # Drop foreign key constraints
    for table in tenant_tables:
        op.drop_constraint(f'fk_{table}_organization_id', table, type_='foreignkey')

    # Make organization_id nullable again
    for table in tenant_tables:
        op.alter_column(
            table,
            'organization_id',
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=True
        )
