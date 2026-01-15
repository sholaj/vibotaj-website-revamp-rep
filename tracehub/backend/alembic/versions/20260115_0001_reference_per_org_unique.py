"""Make shipment reference unique per organization instead of globally.

IMPL-001: Fix shipment reference uniqueness constraint.

Previously, the `reference` column had a global unique constraint which prevented
different organizations from using the same reference numbers. This migration
changes it to a composite unique constraint on (organization_id, reference),
allowing each organization to have their own reference numbering scheme.

Revision ID: 20260115_0001
Revises: 20260112_0001
Create Date: 2026-01-15
"""
from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic
revision = '20260115_0001'
down_revision = '20260112_0001'
branch_labels = None
depends_on = None


def constraint_exists(table_name: str, constraint_name: str) -> bool:
    """Check if a constraint exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = inspector.get_unique_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def upgrade():
    """Change from global unique to per-organization unique constraint (idempotent)."""
    # Drop the global unique constraint on reference if it exists
    if constraint_exists('shipments', 'shipments_reference_key'):
        op.drop_constraint('shipments_reference_key', 'shipments', type_='unique')

    # Create per-organization unique constraint if it doesn't exist
    if not constraint_exists('shipments', 'uq_shipment_org_reference'):
        op.create_unique_constraint(
            'uq_shipment_org_reference',
            'shipments',
            ['organization_id', 'reference']
        )


def downgrade():
    """Restore global unique constraint (idempotent, may fail if duplicates exist)."""
    # Drop per-org constraint if it exists
    if constraint_exists('shipments', 'uq_shipment_org_reference'):
        op.drop_constraint('uq_shipment_org_reference', 'shipments', type_='unique')

    # Restore global unique constraint if it doesn't exist
    # WARNING: This will fail if there are duplicate references across organizations
    if not constraint_exists('shipments', 'shipments_reference_key'):
        op.create_unique_constraint('shipments_reference_key', 'shipments', ['reference'])
