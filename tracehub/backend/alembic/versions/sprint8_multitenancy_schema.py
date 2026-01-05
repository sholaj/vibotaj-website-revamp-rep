"""Sprint 8: Multi-tenancy schema

Revision ID: sprint8_001
Revises: [PREVIOUS_REVISION]
Create Date: 2026-01-05

This migration creates the multi-tenancy infrastructure:
- organizations table
- organization_memberships table
- invitations table
- Updates to users table for system_role
- Foreign keys on shipments for organization_id
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'sprint8_001'
down_revision = None  # TODO: Set to actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============ Create organization type enum ============
    org_type_enum = postgresql.ENUM(
        'vibotaj', 'buyer', 'supplier', 'logistics_agent',
        name='organizationtype',
        create_type=False
    )
    org_type_enum.create(op.get_bind(), checkfirst=True)

    # ============ Create organization status enum ============
    org_status_enum = postgresql.ENUM(
        'active', 'suspended', 'pending_setup',
        name='organizationstatus',
        create_type=False
    )
    org_status_enum.create(op.get_bind(), checkfirst=True)

    # ============ Create org role enum ============
    org_role_enum = postgresql.ENUM(
        'admin', 'manager', 'member', 'viewer',
        name='orgrole',
        create_type=False
    )
    org_role_enum.create(op.get_bind(), checkfirst=True)

    # ============ Create membership status enum ============
    membership_status_enum = postgresql.ENUM(
        'active', 'suspended', 'pending',
        name='membershipstatus',
        create_type=False
    )
    membership_status_enum.create(op.get_bind(), checkfirst=True)

    # ============ Create invitation status enum ============
    invitation_status_enum = postgresql.ENUM(
        'pending', 'accepted', 'expired', 'revoked',
        name='invitationstatus',
        create_type=False
    )
    invitation_status_enum.create(op.get_bind(), checkfirst=True)

    # ============ Create organizations table ============
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(50), unique=True, nullable=False),
        sa.Column('type', sa.Enum('vibotaj', 'buyer', 'supplier', 'logistics_agent', name='organizationtype'), nullable=False),
        sa.Column('status', sa.Enum('active', 'suspended', 'pending_setup', name='organizationstatus'), nullable=False, server_default='active'),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('address', postgresql.JSONB, server_default='{}'),
        sa.Column('tax_id', sa.String(100), nullable=True),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # Organization indexes
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])
    op.create_index('ix_organizations_type_status', 'organizations', ['type', 'status'])
    op.create_index('ix_organizations_name', 'organizations', ['name'])

    # ============ Create organization_memberships table ============
    op.create_table(
        'organization_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('org_role', sa.Enum('admin', 'manager', 'member', 'viewer', name='orgrole'), nullable=False, server_default='member'),
        sa.Column('status', sa.Enum('active', 'suspended', 'pending', name='membershipstatus'), nullable=False, server_default='active'),
        sa.Column('is_primary', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('joined_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime, nullable=True),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK added after invitations table
    )

    # Membership indexes
    op.create_index('ix_membership_user_org', 'organization_memberships', ['user_id', 'organization_id'], unique=True)
    op.create_index('ix_membership_org_role', 'organization_memberships', ['organization_id', 'org_role'])
    op.create_index('ix_membership_user_primary', 'organization_memberships', ['user_id', 'is_primary'])

    # ============ Create invitations table ============
    op.create_table(
        'invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('org_role', sa.Enum('admin', 'manager', 'member', 'viewer', name='orgrole'), nullable=False, server_default='member'),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'expired', 'revoked', name='invitationstatus'), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('accepted_at', sa.DateTime, nullable=True),
        sa.Column('accepted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
    )

    # Invitation indexes
    op.create_index('ix_invitation_email', 'invitations', ['email'])
    op.create_index('ix_invitation_token_hash', 'invitations', ['token_hash'], unique=True)
    op.create_index('ix_invitation_org_email', 'invitations', ['organization_id', 'email'])
    op.create_index('ix_invitation_status', 'invitations', ['status'])
    op.create_index('ix_invitation_expires', 'invitations', ['expires_at'])

    # Add FK for invitation_id in memberships now that invitations table exists
    op.create_foreign_key(
        'fk_membership_invitation',
        'organization_memberships',
        'invitations',
        ['invitation_id'],
        ['id']
    )

    # ============ Update users table ============
    # Add system_role column for distinguishing platform-level admins
    op.add_column(
        'users',
        sa.Column(
            'system_role',
            sa.String(20),
            nullable=False,
            server_default='user'
        )
    )
    op.create_index('ix_users_system_role', 'users', ['system_role'])

    # ============ Update shipments table ============
    # Add organization_id foreign key
    op.add_column(
        'shipments',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id'),
            nullable=True  # Nullable initially for migration
        )
    )

    # Add buyer_org_id and supplier_org_id for organization-level relationships
    op.add_column(
        'shipments',
        sa.Column(
            'buyer_org_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id'),
            nullable=True
        )
    )
    op.add_column(
        'shipments',
        sa.Column(
            'supplier_org_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id'),
            nullable=True
        )
    )

    op.create_index('ix_shipments_organization_id', 'shipments', ['organization_id'])
    op.create_index('ix_shipments_buyer_org_id', 'shipments', ['buyer_org_id'])
    op.create_index('ix_shipments_supplier_org_id', 'shipments', ['supplier_org_id'])

    # ============ Update documents table ============
    # Documents inherit organization from shipment, but we add direct reference for querying
    op.add_column(
        'documents',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id'),
            nullable=True  # Nullable initially for migration
        )
    )
    op.create_index('ix_documents_organization_id', 'documents', ['organization_id'])


def downgrade() -> None:
    # ============ Revert documents changes ============
    op.drop_index('ix_documents_organization_id', 'documents')
    op.drop_column('documents', 'organization_id')

    # ============ Revert shipments changes ============
    op.drop_index('ix_shipments_supplier_org_id', 'shipments')
    op.drop_index('ix_shipments_buyer_org_id', 'shipments')
    op.drop_index('ix_shipments_organization_id', 'shipments')
    op.drop_column('shipments', 'supplier_org_id')
    op.drop_column('shipments', 'buyer_org_id')
    op.drop_column('shipments', 'organization_id')

    # ============ Revert users changes ============
    op.drop_index('ix_users_system_role', 'users')
    op.drop_column('users', 'system_role')

    # ============ Drop invitations table ============
    op.drop_constraint('fk_membership_invitation', 'organization_memberships', type_='foreignkey')
    op.drop_index('ix_invitation_expires', 'invitations')
    op.drop_index('ix_invitation_status', 'invitations')
    op.drop_index('ix_invitation_org_email', 'invitations')
    op.drop_index('ix_invitation_token_hash', 'invitations')
    op.drop_index('ix_invitation_email', 'invitations')
    op.drop_table('invitations')

    # ============ Drop organization_memberships table ============
    op.drop_index('ix_membership_user_primary', 'organization_memberships')
    op.drop_index('ix_membership_org_role', 'organization_memberships')
    op.drop_index('ix_membership_user_org', 'organization_memberships')
    op.drop_table('organization_memberships')

    # ============ Drop organizations table ============
    op.drop_index('ix_organizations_name', 'organizations')
    op.drop_index('ix_organizations_type_status', 'organizations')
    op.drop_index('ix_organizations_slug', 'organizations')
    op.drop_table('organizations')

    # ============ Drop enums ============
    sa.Enum(name='invitationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='membershipstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='orgrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='organizationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='organizationtype').drop(op.get_bind(), checkfirst=True)
