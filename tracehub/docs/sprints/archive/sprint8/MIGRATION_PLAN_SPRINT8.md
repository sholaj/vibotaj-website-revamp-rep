# TraceHub Sprint 8: Multi-Tenancy Database Migration & DevOps Strategy

**Version:** 1.0
**Date:** 2026-01-05
**Status:** READY FOR REVIEW
**Author:** DevOps Architect

---

## Executive Summary

This document outlines the complete database migration strategy to transform TraceHub from a single-tenant system (VIBOTAJ internal) to a multi-tenant SaaS platform. The migration will be executed with **zero downtime** and includes comprehensive rollback procedures.

**Key Metrics:**
- Estimated downtime: 0 minutes (blue-green deployment)
- Migration execution time: 15-20 minutes
- Rollback time: < 5 minutes
- Tables affected: 14 tables
- New tables: 3 (organizations, org_memberships, invitations)

---

## 1. Migration Sequence & Dependencies

### 1.1 Migration Steps (Numbered with Dependencies)

```
Migration 001: Initial Schema (ALREADY APPLIED)
    |
    ├─> Migration 002: Add document_types (ALREADY APPLIED)
    |
    └─> Migration 003: Create Multi-Tenancy Infrastructure ⬅ NEW
            |
            ├─> Step 3.1: Create organizations table
            ├─> Step 3.2: Create org_memberships table
            ├─> Step 3.3: Create invitations table
            |
            └─> Migration 004: Add organization_id Columns (NULLABLE) ⬅ NEW
                    |
                    ├─> Step 4.1: Add organization_id to users
                    ├─> Step 4.2: Add organization_id to shipments
                    ├─> Step 4.3: Add organization_id to documents
                    ├─> Step 4.4: Add organization_id to products
                    ├─> Step 4.5: Add organization_id to parties
                    ├─> Step 4.6: Add organization_id to origins
                    ├─> Step 4.7: Add organization_id to container_events
                    ├─> Step 4.8: Add organization_id to notifications
                    └─> Step 4.9: Add organization_id to audit_logs
                    |
                    └─> Migration 005: Data Migration to VIBOTAJ Org ⬅ NEW
                            |
                            ├─> Step 5.1: Create VIBOTAJ organization
                            ├─> Step 5.2: Migrate users → VIBOTAJ
                            ├─> Step 5.3: Create org_memberships for users
                            ├─> Step 5.4: Migrate shipments → VIBOTAJ
                            ├─> Step 5.5: Migrate documents → VIBOTAJ
                            ├─> Step 5.6: Migrate products → VIBOTAJ
                            ├─> Step 5.7: Migrate parties → VIBOTAJ
                            ├─> Step 5.8: Migrate origins → VIBOTAJ
                            ├─> Step 5.9: Migrate container_events → VIBOTAJ
                            ├─> Step 5.10: Migrate notifications → VIBOTAJ
                            └─> Step 5.11: Migrate audit_logs → VIBOTAJ
                            |
                            └─> Migration 006: Add Constraints & Indexes ⬅ NEW
                                    |
                                    ├─> Step 6.1: Validate NO NULL organization_id
                                    ├─> Step 6.2: Add NOT NULL constraints
                                    ├─> Step 6.3: Add foreign key constraints
                                    ├─> Step 6.4: Add composite indexes
                                    └─> Step 6.5: Add unique constraints where needed
```

**Critical Path:** Each migration MUST be fully applied and validated before proceeding to the next.

---

## 2. Alembic Migration Files

### 2.1 Migration 003: Create Multi-Tenancy Infrastructure

**File:** `/backend/alembic/versions/20260106_0003_create_multitenancy_tables.py`

```python
"""Create multi-tenancy infrastructure tables

Revision ID: 003
Revises: 002
Create Date: 2026-01-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUID for VIBOTAJ organization (for consistency across environments)
VIBOTAJ_ORG_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


def upgrade() -> None:
    """Create organizations, org_memberships, and invitations tables."""

    # Create organization_type enum
    op.execute("""
        CREATE TYPE organization_type AS ENUM (
            'internal',      -- VIBOTAJ's internal operations
            'customer',      -- External exporters using TraceHub as SaaS
            'supplier',      -- Supplier organizations
            'buyer',         -- Buyer organizations
            'partner'        -- Strategic partners
        )
    """)

    # Create org_role enum
    op.execute("""
        CREATE TYPE org_role AS ENUM (
            'owner',         -- Full administrative access
            'admin',         -- Admin access (cannot delete org)
            'manager',       -- Manage shipments and users
            'member',        -- Regular access
            'viewer'         -- Read-only access
        )
    """)

    # Create membership_status enum
    op.execute("""
        CREATE TYPE membership_status AS ENUM (
            'active',
            'inactive',
            'suspended',
            'pending'
        )
    """)

    # Create invitation_status enum
    op.execute("""
        CREATE TYPE invitation_status AS ENUM (
            'pending',
            'accepted',
            'expired',
            'revoked'
        )
    """)

    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('type', postgresql.ENUM(
            'internal', 'customer', 'supplier', 'buyer', 'partner',
            name='organization_type', create_type=False
        ), nullable=False),

        # Contact information
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('address', sa.Text()),
        sa.Column('country', sa.String(2)),  # ISO country code
        sa.Column('registration_number', sa.String(100)),
        sa.Column('tax_id', sa.String(100)),

        # Settings
        sa.Column('settings', postgresql.JSONB, default={}),
        sa.Column('features', postgresql.JSONB, default={}),  # Feature flags

        # Subscription & billing (for future SaaS)
        sa.Column('subscription_tier', sa.String(50), default='free'),
        sa.Column('subscription_status', sa.String(50), default='active'),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True)),

        # Status
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)
    op.create_index('ix_organizations_type', 'organizations', ['type'])
    op.create_index('ix_organizations_is_active', 'organizations', ['is_active'])

    # 2. Create org_memberships table (user-organization many-to-many)
    op.create_table(
        'org_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', postgresql.ENUM(
            'owner', 'admin', 'manager', 'member', 'viewer',
            name='org_role', create_type=False
        ), nullable=False, server_default='member'),
        sa.Column('status', postgresql.ENUM(
            'active', 'inactive', 'suspended', 'pending',
            name='membership_status', create_type=False
        ), nullable=False, server_default='active'),

        # Timestamps
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        sa.PrimaryKeyConstraint('id'),
        # Ensure user can only have one membership per org
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_user')
    )
    op.create_index('ix_org_memberships_organization_id', 'org_memberships', ['organization_id'])
    op.create_index('ix_org_memberships_user_id', 'org_memberships', ['user_id'])
    op.create_index('ix_org_memberships_status', 'org_memberships', ['status'])

    # 3. Create invitations table
    op.create_table(
        'invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM(
            'owner', 'admin', 'manager', 'member', 'viewer',
            name='org_role', create_type=False
        ), nullable=False, server_default='member'),

        # Token security
        sa.Column('token_hash', sa.String(64), unique=True, nullable=False),  # SHA-256 hash

        # Status
        sa.Column('status', postgresql.ENUM(
            'pending', 'accepted', 'expired', 'revoked',
            name='invitation_status', create_type=False
        ), nullable=False, server_default='pending'),

        # Metadata
        sa.Column('invited_by', postgresql.UUID(as_uuid=True)),
        sa.Column('accepted_by', postgresql.UUID(as_uuid=True)),

        # Timestamps
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True)),

        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['accepted_by'], ['users.id'], ondelete='SET NULL'),

        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invitations_token_hash', 'invitations', ['token_hash'], unique=True)
    op.create_index('ix_invitations_organization_id', 'invitations', ['organization_id'])
    op.create_index('ix_invitations_email', 'invitations', ['email'])
    op.create_index('ix_invitations_status', 'invitations', ['status'])
    op.create_index('ix_invitations_expires_at', 'invitations', ['expires_at'])


def downgrade() -> None:
    """Drop multi-tenancy tables."""
    op.drop_table('invitations')
    op.drop_table('org_memberships')
    op.drop_table('organizations')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS invitation_status")
    op.execute("DROP TYPE IF EXISTS membership_status")
    op.execute("DROP TYPE IF EXISTS org_role")
    op.execute("DROP TYPE IF EXISTS organization_type")
```

---

### 2.2 Migration 004: Add organization_id Columns (NULLABLE)

**File:** `/backend/alembic/versions/20260106_0004_add_organization_id_columns.py`

```python
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
```

---

### 2.3 Migration 005: Data Migration to VIBOTAJ Organization

**File:** `/backend/alembic/versions/20260106_0005_migrate_data_to_vibotaj_org.py`

```python
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
```

---

### 2.4 Migration 006: Add Constraints & Indexes

**File:** `/backend/alembic/versions/20260106_0006_add_multitenancy_constraints.py`

```python
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
        ('origins', ['organization_id', 'shipment_id']),
        ('container_events', ['organization_id', 'shipment_id']),
        ('container_events', ['organization_id', 'event_time']),
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
    print(f"NOT NULL constraints:  {len(tenant_tables)} tables")
    print(f"Foreign key constraints: {len(tenant_tables)} tables")
    print(f"Composite indexes:     {len(composite_indexes)} indexes")
    print(f"Unique constraints:    1 constraint")
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
        ('origins', ['organization_id', 'shipment_id']),
        ('container_events', ['organization_id', 'shipment_id']),
        ('container_events', ['organization_id', 'event_time']),
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
```

---

## 3. Rollback Strategy

### 3.1 Rollback Procedures

**Level 1: Rollback individual migration**
```bash
# Rollback Migration 006 only (remove constraints)
alembic downgrade 005

# Rollback Migration 005 only (clear organization data)
alembic downgrade 004

# Rollback Migration 004 only (remove organization_id columns)
alembic downgrade 003

# Rollback Migration 003 only (drop multi-tenancy tables)
alembic downgrade 002
```

**Level 2: Full rollback to pre-migration state**
```bash
# Rollback all multi-tenancy migrations
alembic downgrade 002

# Verify rollback
psql -U tracehub -d tracehub -c "SELECT * FROM alembic_version;"
# Should show: 002
```

**Level 3: Emergency restore from backup**
```bash
# Stop application
docker-compose down

# Restore from backup
docker-compose up -d db
docker exec -i tracehub-db pg_restore -U tracehub -d tracehub < /backup/tracehub_pre_migration.dump

# Verify data
docker exec -it tracehub-db psql -U tracehub -d tracehub -c "SELECT COUNT(*) FROM shipments;"

# Restart application
docker-compose up -d
```

### 3.2 Rollback Decision Matrix

| Issue | Severity | Action | Rollback Level |
|-------|----------|--------|----------------|
| Migration 003 fails | CRITICAL | Stop immediately | No rollback needed |
| Migration 004 fails | CRITICAL | Rollback to 003 | Level 1 |
| Migration 005 fails (data migration) | CRITICAL | Rollback to 004 | Level 1-2 |
| Migration 006 fails (constraints) | HIGH | Rollback to 005 | Level 1 |
| Data validation errors | HIGH | Rollback to 004 | Level 2 |
| Performance degradation | MEDIUM | Analyze indexes | No rollback |
| Application bugs | MEDIUM | Fix application | No rollback |
| Database corruption | CRITICAL | Restore from backup | Level 3 |

---

## 4. Zero-Downtime Deployment Plan

### 4.1 Blue-Green Deployment Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCTION ENVIRONMENT                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │   BLUE (v1.2)   │              │  GREEN (v1.3)   │      │
│  │  No Multi-Tenancy│              │ Multi-Tenancy  │      │
│  │                  │              │                 │      │
│  │  - Frontend v1.2 │              │ - Frontend v1.3 │      │
│  │  - Backend v1.2  │              │ - Backend v1.3  │      │
│  │  - DB (current)  │─────────────▶│ - DB (migrated)│      │
│  └─────────────────┘              └─────────────────┘      │
│           │                                 │               │
│           │        ┌─────────────┐         │               │
│           └───────▶│  Load       │◀────────┘               │
│                    │  Balancer   │                         │
│                    └─────────────┘                         │
│                           │                                 │
│                           ▼                                 │
│                    ┌─────────────┐                         │
│                    │   Users     │                         │
│                    └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Deployment Steps

**Phase 1: Preparation (1 hour before)**
```bash
# 1. Create database backup
docker exec tracehub-db pg_dump -U tracehub -Fc tracehub > \
  /backup/tracehub_pre_sprint8_$(date +%Y%m%d_%H%M%S).dump

# 2. Verify backup
ls -lh /backup/*.dump

# 3. Tag current production version
git tag -a v1.2.0 -m "Pre-Sprint8 Multi-Tenancy"
git push origin v1.2.0

# 4. Create maintenance page (optional)
# Note: With blue-green, this is not needed
```

**Phase 2: Database Migration (15-20 minutes)**
```bash
# 1. Run migrations on production database
cd /opt/tracehub/backend

# Migration 003: Create tables
alembic upgrade 003
# Expected time: 1-2 seconds
# Verify: SELECT COUNT(*) FROM organizations;

# Migration 004: Add columns
alembic upgrade 004
# Expected time: 5-10 seconds (depends on data volume)
# Verify: SELECT column_name FROM information_schema.columns WHERE table_name='users';

# Migration 005: Data migration
alembic upgrade 005
# Expected time: 10-15 minutes (depends on data volume)
# Verify: SELECT organization_id, COUNT(*) FROM users GROUP BY organization_id;

# Migration 006: Add constraints
alembic upgrade 006
# Expected time: 5-10 seconds
# Verify: SELECT * FROM pg_constraint WHERE conrelid='users'::regclass;
```

**Phase 3: Deploy Green Environment (10 minutes)**
```bash
# 1. Build new images
docker-compose -f docker-compose.green.yml build

# 2. Start green environment (port 8001, no traffic yet)
docker-compose -f docker-compose.green.yml up -d

# 3. Health check green environment
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/organizations

# 4. Run smoke tests
pytest tests/integration/test_multitenancy.py --env=green
```

**Phase 4: Traffic Switch (2 minutes)**
```bash
# 1. Update nginx/load balancer to route to green
# Option A: Gradual canary (10% -> 50% -> 100%)
# Option B: Instant switch

# Instant switch:
sudo cp /etc/nginx/sites-available/tracehub-green.conf \
        /etc/nginx/sites-enabled/tracehub.conf
sudo nginx -t
sudo systemctl reload nginx

# 2. Monitor error rates
tail -f /var/log/nginx/access.log
docker logs -f tracehub-backend

# 3. Verify users can access
curl https://tracehub.vibotaj.com/api/v1/shipments
```

**Phase 5: Validation & Cleanup (5 minutes)**
```bash
# 1. Validate multi-tenancy
psql -U tracehub -d tracehub -c "
  SELECT o.name, COUNT(s.id) AS shipment_count
  FROM organizations o
  LEFT JOIN shipments s ON s.organization_id = o.id
  GROUP BY o.name;
"

# 2. Monitor for 30 minutes

# 3. Stop blue environment (keep for 24h rollback)
# docker-compose -f docker-compose.blue.yml down

# 4. Create post-migration backup
docker exec tracehub-db pg_dump -U tracehub -Fc tracehub > \
  /backup/tracehub_post_sprint8_$(date +%Y%m%d_%H%M%S).dump
```

---

## 5. Data Validation Queries

### 5.1 Pre-Migration Validation

```sql
-- Count existing records (baseline)
SELECT
  (SELECT COUNT(*) FROM users) AS users_count,
  (SELECT COUNT(*) FROM shipments) AS shipments_count,
  (SELECT COUNT(*) FROM documents) AS documents_count,
  (SELECT COUNT(*) FROM products) AS products_count,
  (SELECT COUNT(*) FROM parties) AS parties_count,
  (SELECT COUNT(*) FROM origins) AS origins_count,
  (SELECT COUNT(*) FROM container_events) AS events_count,
  (SELECT COUNT(*) FROM notifications) AS notifications_count,
  (SELECT COUNT(*) FROM audit_logs) AS audit_logs_count;

-- Check for orphaned records
SELECT 'documents' AS table_name, COUNT(*) AS orphaned_count
FROM documents d
WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.id = d.shipment_id)
UNION ALL
SELECT 'products', COUNT(*)
FROM products p
WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.id = p.shipment_id)
UNION ALL
SELECT 'origins', COUNT(*)
FROM origins o
WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.id = o.shipment_id);
```

### 5.2 Post-Migration Validation

```sql
-- Verify VIBOTAJ organization created
SELECT id, name, slug, type, is_active
FROM organizations
WHERE slug = 'vibotaj';
-- Expected: 1 row with id '00000000-0000-0000-0000-000000000001'

-- Verify all users migrated
SELECT
  COUNT(*) AS total_users,
  COUNT(organization_id) AS users_with_org,
  COUNT(*) - COUNT(organization_id) AS users_without_org
FROM users;
-- Expected: users_without_org = 0

-- Verify all shipments migrated
SELECT
  COUNT(*) AS total_shipments,
  COUNT(organization_id) AS shipments_with_org,
  COUNT(*) - COUNT(organization_id) AS shipments_without_org
FROM shipments;
-- Expected: shipments_without_org = 0

-- Verify org_memberships created
SELECT
  o.name AS organization,
  COUNT(om.id) AS member_count,
  COUNT(CASE WHEN om.role = 'owner' THEN 1 END) AS owners,
  COUNT(CASE WHEN om.role = 'admin' THEN 1 END) AS admins,
  COUNT(CASE WHEN om.role = 'manager' THEN 1 END) AS managers,
  COUNT(CASE WHEN om.role = 'member' THEN 1 END) AS members,
  COUNT(CASE WHEN om.role = 'viewer' THEN 1 END) AS viewers
FROM organizations o
LEFT JOIN org_memberships om ON om.organization_id = o.id
GROUP BY o.name;

-- Verify data integrity (no orphaned records)
SELECT
  'users' AS table_name,
  COUNT(*) AS records_without_valid_org
FROM users u
WHERE NOT EXISTS (SELECT 1 FROM organizations o WHERE o.id = u.organization_id)
UNION ALL
SELECT 'shipments', COUNT(*)
FROM shipments s
WHERE NOT EXISTS (SELECT 1 FROM organizations o WHERE o.id = s.organization_id)
UNION ALL
SELECT 'documents', COUNT(*)
FROM documents d
WHERE NOT EXISTS (SELECT 1 FROM organizations o WHERE o.id = d.organization_id);
-- Expected: All counts = 0

-- Verify foreign key constraints
SELECT
  tc.constraint_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND kcu.column_name = 'organization_id'
ORDER BY tc.table_name;
-- Expected: 9 rows (users, shipments, documents, products, parties, origins, container_events, notifications, audit_logs)

-- Verify indexes created
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE indexname LIKE '%organization_id%'
ORDER BY tablename, indexname;
-- Expected: Single + composite indexes on all tenant tables

-- Record count comparison (pre vs post)
SELECT
  'VIBOTAJ' AS organization,
  (SELECT COUNT(*) FROM users WHERE organization_id = '00000000-0000-0000-0000-000000000001') AS users,
  (SELECT COUNT(*) FROM shipments WHERE organization_id = '00000000-0000-0000-0000-000000000001') AS shipments,
  (SELECT COUNT(*) FROM documents WHERE organization_id = '00000000-0000-0000-0000-000000000001') AS documents;
-- Expected: Counts match pre-migration baseline
```

---

## 6. Performance Impact Analysis

### 6.1 Index Strategy

**Single-Column Indexes (Already Added in Migration 004):**
- `ix_users_organization_id`
- `ix_shipments_organization_id`
- `ix_documents_organization_id`
- `ix_products_organization_id`
- `ix_parties_organization_id`
- `ix_origins_organization_id`
- `ix_container_events_organization_id`
- `ix_notifications_organization_id`
- `ix_audit_logs_organization_id`

**Composite Indexes (Added in Migration 006):**
```sql
-- High-frequency query patterns
CREATE INDEX ix_users_organization_id_email ON users(organization_id, email);
CREATE INDEX ix_users_organization_id_is_active ON users(organization_id, is_active);
CREATE INDEX ix_shipments_organization_id_status ON shipments(organization_id, status);
CREATE INDEX ix_shipments_organization_id_reference ON shipments(organization_id, reference);
CREATE INDEX ix_shipments_organization_id_created_at ON shipments(organization_id, created_at);
CREATE INDEX ix_documents_organization_id_shipment_id ON documents(organization_id, shipment_id);
CREATE INDEX ix_container_events_organization_id_event_time ON container_events(organization_id, event_time);
```

### 6.2 Performance Benchmarks

**Expected Query Performance:**

| Query | Before | After | Impact |
|-------|--------|-------|--------|
| `SELECT * FROM shipments WHERE reference = 'X'` | 5ms | 3ms | +40% faster (composite index) |
| `SELECT * FROM shipments WHERE status = 'IN_TRANSIT'` | 20ms | 15ms | +25% faster |
| `SELECT * FROM users WHERE email = 'X'` | 3ms | 2ms | +33% faster |
| `SELECT * FROM documents WHERE shipment_id = 'X'` | 10ms | 8ms | +20% faster |
| Full table scan (worst case) | 100ms | 120ms | -20% slower (additional column) |

**Storage Impact:**
- Additional storage per row: 16 bytes (UUID)
- Total storage increase: ~1% of current database size
- Index storage: ~5% increase

### 6.3 Performance Monitoring

```sql
-- Monitor index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan AS index_scans,
  idx_tup_read AS tuples_read,
  idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE indexname LIKE '%organization_id%'
ORDER BY idx_scan DESC;

-- Monitor slow queries
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time,
  rows
FROM pg_stat_statements
WHERE query LIKE '%organization_id%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Monitor table bloat
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 7. Backup and Recovery Procedures

### 7.1 Backup Strategy

**Pre-Migration Backup:**
```bash
#!/bin/bash
# File: /opt/tracehub/scripts/backup_pre_migration.sh

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/tracehub"
BACKUP_FILE="${BACKUP_DIR}/tracehub_pre_sprint8_${TIMESTAMP}.dump"

echo "Creating pre-migration backup..."

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Dump database
docker exec tracehub-db pg_dump -U tracehub -Fc tracehub > ${BACKUP_FILE}

# Verify backup
if [ -f ${BACKUP_FILE} ]; then
  SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
  echo "✓ Backup created: ${BACKUP_FILE} (${SIZE})"

  # Test restore to temporary database
  docker exec tracehub-db psql -U tracehub -c "CREATE DATABASE tracehub_verify;"
  docker exec -i tracehub-db pg_restore -U tracehub -d tracehub_verify < ${BACKUP_FILE}
  docker exec tracehub-db psql -U tracehub -c "DROP DATABASE tracehub_verify;"

  echo "✓ Backup verified successfully"
else
  echo "✗ Backup failed!"
  exit 1
fi

# Backup application config
cp /opt/tracehub/.env ${BACKUP_DIR}/.env.${TIMESTAMP}
cp /opt/tracehub/docker-compose.yml ${BACKUP_DIR}/docker-compose.yml.${TIMESTAMP}

# Create backup manifest
cat > ${BACKUP_DIR}/manifest_${TIMESTAMP}.txt <<EOF
Backup Date: $(date)
Database Version: $(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "SELECT version();")
Alembic Version: $(docker exec tracehub-backend alembic current)
Git Commit: $(git rev-parse HEAD)
Git Tag: $(git describe --tags --always)

Table Counts:
$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT
    'users: ' || COUNT(*) FROM users
  UNION ALL
  SELECT 'shipments: ' || COUNT(*) FROM shipments
  UNION ALL
  SELECT 'documents: ' || COUNT(*) FROM documents;
")
EOF

echo "✓ Backup manifest created"
echo "Backup location: ${BACKUP_FILE}"
```

**Continuous Backup Strategy:**
```bash
# Schedule daily backups with cron
# /etc/cron.d/tracehub-backup
0 2 * * * root /opt/tracehub/scripts/backup_pre_migration.sh >> /var/log/tracehub-backup.log 2>&1

# Backup retention policy
find /backup/tracehub -name "*.dump" -mtime +30 -delete  # Keep 30 days
```

### 7.2 Recovery Procedures

**Scenario 1: Rollback from Migration 006**
```bash
# Quick rollback (constraints only)
alembic downgrade 005
# Time: < 1 minute
```

**Scenario 2: Full Database Restore**
```bash
#!/bin/bash
# File: /opt/tracehub/scripts/restore_from_backup.sh

set -euo pipefail

BACKUP_FILE=$1

if [ -z "${BACKUP_FILE}" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

echo "Restoring from backup: ${BACKUP_FILE}"

# 1. Stop application
docker-compose down

# 2. Backup current database (just in case)
docker-compose up -d db
sleep 5
docker exec tracehub-db pg_dump -U tracehub -Fc tracehub > \
  /backup/tracehub_before_restore_$(date +%Y%m%d_%H%M%S).dump

# 3. Drop and recreate database
docker exec tracehub-db psql -U tracehub -c "DROP DATABASE IF EXISTS tracehub;"
docker exec tracehub-db psql -U tracehub -c "CREATE DATABASE tracehub;"

# 4. Restore from backup
docker exec -i tracehub-db pg_restore -U tracehub -d tracehub < ${BACKUP_FILE}

# 5. Verify restore
SHIPMENT_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "SELECT COUNT(*) FROM shipments;")
echo "✓ Restored ${SHIPMENT_COUNT} shipments"

# 6. Check Alembic version
ALEMBIC_VERSION=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "SELECT version_num FROM alembic_version;")
echo "✓ Database at Alembic version: ${ALEMBIC_VERSION}"

# 7. Restart application
docker-compose up -d

echo "✓ Restore completed successfully"
```

**Scenario 3: Point-in-Time Recovery (PITR)**
```bash
# Requires PostgreSQL WAL archiving (set up in production)
# /etc/postgresql/15/main/postgresql.conf
# archive_mode = on
# archive_command = 'cp %p /backup/wal/%f'

# Restore to specific point in time
pg_restore -U tracehub -d tracehub --target-time='2026-01-06 15:30:00' /backup/tracehub_base.dump
```

---

## 8. CI/CD Integration

### 8.1 Updated GitHub Actions Workflow

**File:** `/.github/workflows/deploy-production.yml` (updated)

```yaml
name: Deploy to Production (Multi-Tenancy)

on:
  push:
    branches:
      - main
    paths:
      - 'backend/**'
      - 'frontend/**'
      - '.github/workflows/deploy-production.yml'

env:
  SSH_HOST: ${{ secrets.SSH_HOST }}
  SSH_USER: ${{ secrets.SSH_USER }}
  SSH_KEY: ${{ secrets.SSH_PRIVATE_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: tracehub
          POSTGRES_PASSWORD: tracehub
          POSTGRES_DB: tracehub_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run database migrations
        env:
          DATABASE_URL: postgresql://tracehub:tracehub@localhost:5432/tracehub_test
        run: |
          cd backend
          alembic upgrade head

      - name: Run tests
        env:
          DATABASE_URL: postgresql://tracehub:tracehub@localhost:5432/tracehub_test
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.SSH_HOST }} >> ~/.ssh/known_hosts

      - name: Create backup before deployment
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} \
            '/opt/tracehub/scripts/backup_pre_migration.sh'

      - name: Deploy code
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
            cd /opt/tracehub
            git fetch origin main
            git checkout main
            git pull origin main
          EOF

      - name: Run database migrations
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
            cd /opt/tracehub/backend
            docker-compose exec -T backend alembic upgrade head
          EOF

      - name: Build and restart containers
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
            cd /opt/tracehub
            docker-compose build
            docker-compose up -d
          EOF

      - name: Wait for health check
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
            for i in {1..30}; do
              if curl -f http://localhost:8000/health; then
                echo "✓ Backend is healthy"
                exit 0
              fi
              echo "Waiting for backend... ($i/30)"
              sleep 2
            done
            echo "✗ Backend health check failed"
            exit 1
          EOF

      - name: Verify multi-tenancy migration
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
            docker exec tracehub-db psql -U tracehub -d tracehub -c "
              SELECT
                o.name AS organization,
                COUNT(s.id) AS shipment_count,
                COUNT(u.id) AS user_count
              FROM organizations o
              LEFT JOIN shipments s ON s.organization_id = o.id
              LEFT JOIN users u ON u.organization_id = o.id
              GROUP BY o.name;
            "
          EOF

      - name: Run smoke tests
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
            cd /opt/tracehub/backend
            pytest tests/integration/test_multitenancy_smoke.py -v
          EOF

      - name: Notify success
        if: success()
        run: |
          echo "✓ Deployment completed successfully"
          # Add Slack/Discord notification here

      - name: Rollback on failure
        if: failure()
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
            cd /opt/tracehub/backend
            alembic downgrade 002
            docker-compose restart backend
          EOF
```

---

## 9. Testing Strategy

### 9.1 Migration Tests

**File:** `/backend/tests/migrations/test_sprint8_migration.py`

```python
"""Tests for Sprint 8 multi-tenancy migration."""

import pytest
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
import uuid

VIBOTAJ_ORG_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


def test_migration_003_creates_tables(alembic_config, db_engine):
    """Test Migration 003: Create multi-tenancy tables."""

    # Run migration
    command.upgrade(alembic_config, "003")

    # Verify tables exist
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('organizations', 'org_memberships', 'invitations')
        """))
        tables = {row[0] for row in result}

    assert tables == {'organizations', 'org_memberships', 'invitations'}


def test_migration_004_adds_columns(alembic_config, db_engine):
    """Test Migration 004: Add organization_id columns."""

    # Run migration
    command.upgrade(alembic_config, "004")

    # Verify columns exist
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name, column_name, is_nullable
            FROM information_schema.columns
            WHERE column_name = 'organization_id'
              AND table_schema = 'public'
        """))
        columns = {(row[0], row[2]) for row in result}

    # All columns should be nullable at this stage
    assert all(nullable == 'YES' for _, nullable in columns)


def test_migration_005_migrates_data(alembic_config, db_engine, seed_data):
    """Test Migration 005: Data migration to VIBOTAJ."""

    # Run migration
    command.upgrade(alembic_config, "005")

    with db_engine.connect() as conn:
        # Verify VIBOTAJ organization created
        org = conn.execute(text("""
            SELECT id, name, slug FROM organizations WHERE slug = 'vibotaj'
        """)).fetchone()
        assert org is not None
        assert org[1] == 'VIBOTAJ GmbH'

        # Verify all users migrated
        users_without_org = conn.execute(text("""
            SELECT COUNT(*) FROM users WHERE organization_id IS NULL
        """)).scalar()
        assert users_without_org == 0

        # Verify all shipments migrated
        shipments_without_org = conn.execute(text("""
            SELECT COUNT(*) FROM shipments WHERE organization_id IS NULL
        """)).scalar()
        assert shipments_without_org == 0


def test_migration_006_adds_constraints(alembic_config, db_engine):
    """Test Migration 006: Add constraints and indexes."""

    # Run migration
    command.upgrade(alembic_config, "006")

    with db_engine.connect() as conn:
        # Verify NOT NULL constraints
        result = conn.execute(text("""
            SELECT table_name, column_name, is_nullable
            FROM information_schema.columns
            WHERE column_name = 'organization_id'
              AND table_schema = 'public'
        """))
        columns = list(result)

        # All columns should be NOT NULL
        assert all(nullable == 'NO' for _, _, nullable in columns)

        # Verify foreign key constraints
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE constraint_type = 'FOREIGN KEY'
              AND constraint_name LIKE 'fk_%_organization_id'
        """))
        fk_count = result.scalar()
        assert fk_count == 9  # 9 tenant tables


def test_rollback_to_002(alembic_config, db_engine):
    """Test rollback from head to 002 (pre-multi-tenancy)."""

    # Upgrade to head
    command.upgrade(alembic_config, "head")

    # Rollback to 002
    command.downgrade(alembic_config, "002")

    with db_engine.connect() as conn:
        # Verify multi-tenancy tables dropped
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('organizations', 'org_memberships', 'invitations')
        """))
        tables = list(result)
        assert len(tables) == 0

        # Verify organization_id columns removed
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE column_name = 'organization_id'
              AND table_schema = 'public'
        """))
        count = result.scalar()
        assert count == 0
```

---

## 10. Risk Assessment & Mitigation

### 10.1 Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| Data migration fails | LOW | CRITICAL | HIGH | Pre-migration validation queries, rollback script |
| NULL constraint violation | LOW | HIGH | MEDIUM | Validation step in Migration 006 |
| Performance degradation | MEDIUM | MEDIUM | MEDIUM | Comprehensive indexing strategy |
| Foreign key conflicts | LOW | HIGH | MEDIUM | Data integrity checks before constraints |
| Downtime exceeds window | LOW | HIGH | MEDIUM | Blue-green deployment (zero downtime) |
| Backup restoration fails | LOW | CRITICAL | HIGH | Backup verification procedure |
| Application bugs post-deployment | MEDIUM | MEDIUM | MEDIUM | Comprehensive testing, gradual rollout |

### 10.2 Mitigation Strategies

**Risk: Data migration fails midway**
- **Prevention:** Transaction-based migrations (all-or-nothing)
- **Detection:** Row count validation after each step
- **Response:** Automatic rollback to Migration 004
- **Recovery Time:** < 5 minutes

**Risk: Performance degradation**
- **Prevention:** Composite indexes on high-frequency queries
- **Detection:** APM monitoring (response time > baseline + 20%)
- **Response:** Analyze slow queries, add indexes
- **Recovery Time:** 10-30 minutes

**Risk: Application crashes due to missing organization context**
- **Prevention:** Comprehensive unit and integration tests
- **Detection:** Error rate monitoring (threshold: > 1%)
- **Response:** Rollback to v1.2 (blue environment)
- **Recovery Time:** 2 minutes (traffic switch)

---

## 11. Communication Plan

### 11.1 Stakeholder Communication

**Pre-Deployment (24 hours before):**
```
Subject: TraceHub Sprint 8 Deployment - Multi-Tenancy Upgrade

Dear VIBOTAJ Team,

We will deploy Sprint 8 (Multi-Tenancy Platform) on January 7, 2026 at 02:00 CET.

Expected Impact:
- ZERO downtime (blue-green deployment)
- No user action required
- All existing data will be migrated automatically

Timeline:
- 02:00 - 02:20 CET: Database migration (background)
- 02:20 - 02:30 CET: Deploy new version
- 02:30 - 03:00 CET: Monitoring and validation

If you experience any issues, please contact: devops@vibotaj.com

Best regards,
DevOps Team
```

**During Deployment:**
- Slack channel updates every 5 minutes
- Status page: https://status.vibotaj.com

**Post-Deployment (Success):**
```
Subject: ✓ TraceHub Sprint 8 Deployed Successfully

The multi-tenancy upgrade has been completed successfully.

Summary:
- Migration completed in 18 minutes
- All data migrated to VIBOTAJ organization
- Zero downtime achieved
- 45 users, 23 shipments, 89 documents migrated

New Features:
- Organization management
- User invitations
- Multi-tenant data isolation

No action required from users.
```

---

## 12. Post-Deployment Monitoring

### 12.1 Monitoring Checklist

**First 1 Hour:**
- [ ] Check error rates (threshold: < 0.1%)
- [ ] Verify all users can log in
- [ ] Test shipment creation/viewing
- [ ] Check database query performance
- [ ] Monitor CPU/memory usage
- [ ] Verify organization_id in all new records

**First 24 Hours:**
- [ ] Analyze slow query log
- [ ] Check database connection pool
- [ ] Monitor disk space (indexes increase storage)
- [ ] Verify backup jobs running
- [ ] Check audit logs for anomalies

**First Week:**
- [ ] Review user feedback
- [ ] Analyze API response times
- [ ] Check for N+1 query issues
- [ ] Monitor index usage statistics
- [ ] Plan optimization if needed

### 12.2 Monitoring Queries

```sql
-- Hourly health check
SELECT
  o.name AS organization,
  COUNT(DISTINCT u.id) AS active_users,
  COUNT(DISTINCT s.id) AS total_shipments,
  COUNT(CASE WHEN s.status = 'IN_TRANSIT' THEN 1 END) AS active_shipments,
  MAX(s.created_at) AS last_shipment_created
FROM organizations o
LEFT JOIN users u ON u.organization_id = o.id AND u.is_active = true
LEFT JOIN shipments s ON s.organization_id = o.id
GROUP BY o.name;

-- Performance monitoring
SELECT
  query,
  calls,
  mean_exec_time::numeric(10,2) AS avg_ms,
  max_exec_time::numeric(10,2) AS max_ms,
  stddev_exec_time::numeric(10,2) AS stddev_ms
FROM pg_stat_statements
WHERE query LIKE '%organization_id%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 13. Success Criteria

### 13.1 Migration Success Definition

The Sprint 8 multi-tenancy migration is considered successful when:

1. **Data Integrity** ✓
   - [ ] 100% of users have valid organization_id
   - [ ] 100% of shipments have valid organization_id
   - [ ] 0 orphaned records
   - [ ] VIBOTAJ organization exists with correct metadata

2. **Performance** ✓
   - [ ] Average query response time < baseline + 10%
   - [ ] P95 response time < baseline + 20%
   - [ ] Database CPU usage < 70%
   - [ ] No slow queries (> 1000ms)

3. **Functionality** ✓
   - [ ] Users can log in and view their shipments
   - [ ] New shipments are created with organization_id
   - [ ] Documents upload and display correctly
   - [ ] Container tracking works as before
   - [ ] EUDR compliance checks work as before

4. **Operational** ✓
   - [ ] Zero unplanned downtime
   - [ ] Backup created and verified
   - [ ] Rollback procedure tested
   - [ ] Monitoring dashboards updated
   - [ ] Documentation updated

### 13.2 Acceptance Tests

```bash
# File: /opt/tracehub/scripts/acceptance_tests.sh

#!/bin/bash
set -euo pipefail

echo "Running Sprint 8 Acceptance Tests..."

# Test 1: VIBOTAJ organization exists
echo "Test 1: Verify VIBOTAJ organization..."
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT id, name FROM organizations WHERE slug = 'vibotaj';
" | grep -q "VIBOTAJ GmbH" && echo "✓ PASS" || echo "✗ FAIL"

# Test 2: All users have organization
echo "Test 2: Verify all users have organization..."
NULL_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*) FROM users WHERE organization_id IS NULL;
")
[ "$NULL_COUNT" -eq 0 ] && echo "✓ PASS" || echo "✗ FAIL"

# Test 3: API returns organization data
echo "Test 3: Verify API returns organization data..."
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  https://tracehub.vibotaj.com/api/v1/organizations)
echo "$RESPONSE" | grep -q "VIBOTAJ" && echo "✓ PASS" || echo "✗ FAIL"

# Test 4: User can create shipment
echo "Test 4: Test shipment creation..."
RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reference":"TEST-2026-999","container_number":"TEST1234567"}' \
  https://tracehub.vibotaj.com/api/v1/shipments)
echo "$RESPONSE" | grep -q "organization_id" && echo "✓ PASS" || echo "✗ FAIL"

echo "Acceptance tests completed."
```

---

## 14. Appendices

### 14.1 Glossary

- **Blue-Green Deployment:** Deployment strategy with two identical environments (blue=old, green=new)
- **Multi-Tenancy:** Architecture where single application serves multiple organizations (tenants)
- **RLS:** Row-Level Security (PostgreSQL feature for tenant isolation)
- **Composite Index:** Database index on multiple columns for optimized queries
- **PITR:** Point-in-Time Recovery (restore database to specific timestamp)
- **WAL:** Write-Ahead Log (PostgreSQL transaction log for recovery)

### 14.2 References

- PostgreSQL Multi-Tenancy Best Practices: https://www.postgresql.org/docs/15/ddl-rowsecurity.html
- Alembic Documentation: https://alembic.sqlalchemy.org/
- Django Multi-Tenancy Patterns: https://django-tenants.readthedocs.io/
- Blue-Green Deployment: https://martinfowler.com/bliki/BlueGreenDeployment.html

### 14.3 Contact Information

- **DevOps Lead:** devops@vibotaj.com
- **Database Administrator:** dba@vibotaj.com
- **On-Call Engineer:** +49 XXX XXXXXXX
- **Emergency Rollback:** Slack #tracehub-alerts

---

## 15. Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| DevOps Architect | [Your Name] | __________ | 2026-01-05 |
| Technical Lead | [Name] | __________ | ________ |
| Product Owner | [Name] | __________ | ________ |
| QA Lead | [Name] | __________ | ________ |

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
**Next Review:** 2026-01-12 (post-deployment)
