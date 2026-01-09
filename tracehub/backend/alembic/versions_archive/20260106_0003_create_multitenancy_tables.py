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
