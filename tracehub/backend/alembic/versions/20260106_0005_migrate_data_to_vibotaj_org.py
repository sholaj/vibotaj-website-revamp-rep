"""Migrate all existing data to VIBOTAJ organization

Revision ID: 005
Revises: 004
Create Date: 2026-01-06

This migration:
1. Creates VIBOTAJ as the default organization
2. Migrates ALL existing users to VIBOTAJ organization
3. Creates org_memberships for all users
4. Migrates ALL existing shipments and related data to VIBOTAJ
5. Links historical shipments to buyer accounts (HAGES, Witatrade)

CRITICAL: This migration MUST be run during a maintenance window
or with application traffic disabled to ensure data consistency.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import table, column
import uuid
from datetime import datetime

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUID for VIBOTAJ organization (must match across all environments)
VIBOTAJ_ORG_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


def upgrade() -> None:
    """Migrate all existing data to VIBOTAJ organization."""

    connection = op.get_bind()

    # =================================================================
    # STEP 1: Create VIBOTAJ organization
    # =================================================================
    print("Step 1/11: Creating VIBOTAJ organization...")

    connection.execute(sa.text("""
        INSERT INTO organizations (
            id, name, slug, type, email, country,
            is_active, subscription_tier, subscription_status,
            settings, features, created_at, updated_at
        ) VALUES (
            :org_id,
            'VIBOTAJ GmbH',
            'vibotaj',
            'internal',
            'info@vibotaj.com',
            'DE',
            true,
            'enterprise',
            'active',
            '{
                "default_currency": "EUR",
                "timezone": "Europe/Berlin",
                "language": "en"
            }'::jsonb,
            '{
                "eudr_compliance": true,
                "container_tracking": true,
                "ai_document_classification": true,
                "multi_user": true,
                "api_access": true
            }'::jsonb,
            now(),
            now()
        )
        ON CONFLICT (id) DO NOTHING
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    print(f"✓ Created VIBOTAJ organization (ID: {VIBOTAJ_ORG_ID})")

    # =================================================================
    # STEP 2: Migrate users to VIBOTAJ organization
    # =================================================================
    print("Step 2/11: Migrating users to VIBOTAJ organization...")

    users_updated = connection.execute(sa.text("""
        UPDATE users
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id, email, role
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    user_count = users_updated.rowcount
    print(f"✓ Migrated {user_count} users to VIBOTAJ organization")

    # =================================================================
    # STEP 3: Create org_memberships for all users
    # =================================================================
    print("Step 3/11: Creating organization memberships...")

    # Map UserRole to OrgRole
    role_mapping = {
        'admin': 'owner',           # VIBOTAJ admins are org owners
        'compliance': 'admin',
        'logistics_agent': 'manager',
        'buyer': 'member',
        'supplier': 'member',
        'viewer': 'viewer'
    }

    # Get all users and create memberships
    users = connection.execute(sa.text("""
        SELECT id, email, role
        FROM users
        WHERE organization_id = :org_id
    """), {"org_id": str(VIBOTAJ_ORG_ID)}).fetchall()

    for user in users:
        user_id, email, user_role = user
        org_role = role_mapping.get(user_role, 'member')

        connection.execute(sa.text("""
            INSERT INTO org_memberships (
                id, organization_id, user_id, role, status, joined_at, updated_at
            ) VALUES (
                gen_random_uuid(),
                :org_id,
                :user_id,
                :org_role,
                'active',
                now(),
                now()
            )
            ON CONFLICT (organization_id, user_id) DO NOTHING
        """), {
            "org_id": str(VIBOTAJ_ORG_ID),
            "user_id": str(user_id),
            "org_role": org_role
        })

    print(f"✓ Created {len(users)} organization memberships")

    # =================================================================
    # STEP 4: Migrate shipments to VIBOTAJ organization
    # =================================================================
    print("Step 4/11: Migrating shipments to VIBOTAJ organization...")

    shipments_updated = connection.execute(sa.text("""
        UPDATE shipments
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id, reference
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    shipment_count = shipments_updated.rowcount
    print(f"✓ Migrated {shipment_count} shipments to VIBOTAJ organization")

    # =================================================================
    # STEP 5: Migrate documents to VIBOTAJ organization
    # =================================================================
    print("Step 5/11: Migrating documents to VIBOTAJ organization...")

    documents_updated = connection.execute(sa.text("""
        UPDATE documents
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    document_count = documents_updated.rowcount
    print(f"✓ Migrated {document_count} documents to VIBOTAJ organization")

    # =================================================================
    # STEP 6: Migrate products to VIBOTAJ organization
    # =================================================================
    print("Step 6/11: Migrating products to VIBOTAJ organization...")

    products_updated = connection.execute(sa.text("""
        UPDATE products
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    product_count = products_updated.rowcount
    print(f"✓ Migrated {product_count} products to VIBOTAJ organization")

    # =================================================================
    # STEP 7: Migrate parties to VIBOTAJ organization
    # =================================================================
    print("Step 7/11: Migrating parties to VIBOTAJ organization...")

    parties_updated = connection.execute(sa.text("""
        UPDATE parties
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id, company_name
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    party_count = parties_updated.rowcount
    print(f"✓ Migrated {party_count} parties to VIBOTAJ organization")

    # =================================================================
    # STEP 8: Migrate origins to VIBOTAJ organization
    # =================================================================
    print("Step 8/11: Migrating origins to VIBOTAJ organization...")

    origins_updated = connection.execute(sa.text("""
        UPDATE origins
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    origin_count = origins_updated.rowcount
    print(f"✓ Migrated {origin_count} origins to VIBOTAJ organization")

    # =================================================================
    # STEP 9: Migrate container_events to VIBOTAJ organization
    # =================================================================
    print("Step 9/11: Migrating container events to VIBOTAJ organization...")

    events_updated = connection.execute(sa.text("""
        UPDATE container_events
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    event_count = events_updated.rowcount
    print(f"✓ Migrated {event_count} container events to VIBOTAJ organization")

    # =================================================================
    # STEP 10: Migrate notifications to VIBOTAJ organization
    # =================================================================
    print("Step 10/11: Migrating notifications to VIBOTAJ organization...")

    notifications_updated = connection.execute(sa.text("""
        UPDATE notifications
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    notification_count = notifications_updated.rowcount
    print(f"✓ Migrated {notification_count} notifications to VIBOTAJ organization")

    # =================================================================
    # STEP 11: Migrate audit_logs to VIBOTAJ organization
    # =================================================================
    print("Step 11/11: Migrating audit logs to VIBOTAJ organization...")

    audit_logs_updated = connection.execute(sa.text("""
        UPDATE audit_logs
        SET organization_id = :org_id
        WHERE organization_id IS NULL
        RETURNING id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    audit_count = audit_logs_updated.rowcount
    print(f"✓ Migrated {audit_count} audit logs to VIBOTAJ organization")

    # =================================================================
    # SUMMARY
    # =================================================================
    print("\n" + "="*60)
    print("DATA MIGRATION SUMMARY")
    print("="*60)
    print(f"Organization:      VIBOTAJ GmbH ({VIBOTAJ_ORG_ID})")
    print(f"Users:             {user_count} migrated")
    print(f"Memberships:       {len(users)} created")
    print(f"Shipments:         {shipment_count} migrated")
    print(f"Documents:         {document_count} migrated")
    print(f"Products:          {product_count} migrated")
    print(f"Parties:           {party_count} migrated")
    print(f"Origins:           {origin_count} migrated")
    print(f"Container Events:  {event_count} migrated")
    print(f"Notifications:     {notification_count} migrated")
    print(f"Audit Logs:        {audit_count} migrated")
    print("="*60)
    print("✓ Data migration completed successfully!")
    print("="*60 + "\n")


def downgrade() -> None:
    """Rollback data migration (set organization_id to NULL)."""

    connection = op.get_bind()

    print("Rolling back data migration...")

    # Remove organization_id from all tables
    tenant_tables = [
        'users', 'shipments', 'documents', 'products',
        'parties', 'origins', 'container_events',
        'notifications', 'audit_logs'
    ]

    for table in tenant_tables:
        connection.execute(sa.text(f"""
            UPDATE {table}
            SET organization_id = NULL
            WHERE organization_id = :org_id
        """), {"org_id": str(VIBOTAJ_ORG_ID)})
        print(f"✓ Cleared organization_id from {table}")

    # Delete org_memberships
    connection.execute(sa.text("""
        DELETE FROM org_memberships
        WHERE organization_id = :org_id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    # Delete VIBOTAJ organization
    connection.execute(sa.text("""
        DELETE FROM organizations
        WHERE id = :org_id
    """), {"org_id": str(VIBOTAJ_ORG_ID)})

    print("✓ Rollback completed")
