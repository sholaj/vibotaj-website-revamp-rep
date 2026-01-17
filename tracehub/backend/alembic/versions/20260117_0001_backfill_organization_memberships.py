"""Backfill organization memberships for existing users.

ARCH-004: Ensure all users have OrganizationMembership records.

Revision ID: 20260117_0001
Revises: 20260116_0001
Create Date: 2026-01-17

IDEMPOTENT: Safe to run multiple times - uses ON CONFLICT DO NOTHING.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20260117_0001'
down_revision = '20260116_0001'
branch_labels = None
depends_on = None


# Role mapping: UserRole -> OrgRole (UPPERCASE to match PostgreSQL enum)
USER_ROLE_TO_ORG_ROLE = {
    'admin': 'ADMIN',
    'compliance': 'MANAGER',
    'logistics_agent': 'MEMBER',
    'buyer': 'VIEWER',
    'supplier': 'MEMBER',
    'viewer': 'VIEWER',
}


def upgrade():
    """Create missing OrganizationMembership records for users."""
    conn = op.get_bind()

    # Find users without memberships
    users_without_memberships = conn.execute(sa.text("""
        SELECT u.id, u.organization_id, u.role, u.created_at
        FROM users u
        LEFT JOIN organization_memberships om ON u.id = om.user_id AND u.organization_id = om.organization_id
        WHERE om.id IS NULL
    """)).fetchall()

    print(f"Found {len(users_without_memberships)} users without memberships")

    for user in users_without_memberships:
        user_id = user[0]
        org_id = user[1]
        user_role = user[2]
        created_at = user[3] or datetime.utcnow()

        # Map user role to org role (UPPERCASE to match PostgreSQL enum)
        org_role = USER_ROLE_TO_ORG_ROLE.get(user_role, 'MEMBER')

        print(f"Creating membership for user {user_id} in org {org_id} with role {org_role}")

        conn.execute(sa.text("""
            INSERT INTO organization_memberships (id, user_id, organization_id, org_role, status, is_primary, joined_at, last_active_at)
            VALUES (gen_random_uuid(), :user_id, :org_id, :org_role, 'ACTIVE', true, :joined_at, :joined_at)
            ON CONFLICT (user_id, organization_id) DO NOTHING
        """), {
            'user_id': user_id,
            'org_id': org_id,
            'org_role': org_role,
            'joined_at': created_at,
        })

    print(f"Created {len(users_without_memberships)} membership records")


def downgrade():
    """Remove auto-created memberships - not recommended in production."""
    # We don't actually want to delete memberships on downgrade
    # This would break user access
    pass
