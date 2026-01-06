"""Create HAGES organization and users

Revision ID: 008
Revises: 007
Create Date: 2026-01-06

This migration creates:
1. HAGES organization (buyer type)
2. Three HAGES users: Helge Bischoff (owner), Mats Morten Jarsetz (admin), Eike Pannen (admin)
3. Organization memberships for all users
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import uuid

revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for reproducibility
HAGES_ORG_ID = uuid.UUID('00000000-0000-0000-0000-000000000002')
VIBOTAJ_ORG_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')

# HAGES users with pre-generated bcrypt password hashes
# Passwords: Hages2026Helge!, Hages2026Mats!, Hages2026Eike!
# Users should reset on first login
# Note: role must use enum name (BUYER), not value (buyer)
HAGES_USERS = [
    {
        "id": uuid.UUID('00000000-0000-0000-0002-000000000001'),
        "email": "helge.bischoff@hages.de",
        "full_name": "Helge Bischoff",
        "role": "BUYER",
        "org_role": "owner",
        "hashed_password": "$2b$12$oDVLgHGn1H7FfILzA69Pde1dlTALTqJ3FKsUidzNv/mnVBnwV.Bui"
    },
    {
        "id": uuid.UUID('00000000-0000-0000-0002-000000000002'),
        "email": "mats.jarsetz@hages.de",
        "full_name": "Mats Morten Jarsetz",
        "role": "BUYER",
        "org_role": "admin",
        "hashed_password": "$2b$12$BgH7pEU0EifVhsWOKtVO8.wGbDe64QpIvaCIo8lA9.8kYawvFo986"
    },
    {
        "id": uuid.UUID('00000000-0000-0000-0002-000000000003'),
        "email": "eike.pannen@hages.de",
        "full_name": "Eike Pannen",
        "role": "BUYER",
        "org_role": "admin",
        "hashed_password": "$2b$12$EbHTkwYAStX8c/KmELXEW.tJzgu3ccjAu4pyqKTPwb24fIVXRG6t2"
    },
]


def upgrade() -> None:
    """Create HAGES organization and users."""

    connection = op.get_bind()

    # =================================================================
    # STEP 1: Create HAGES organization
    # =================================================================
    print("Step 1/3: Creating HAGES organization...")

    connection.execute(sa.text("""
        INSERT INTO organizations (
            id, name, slug, type, email, country,
            is_active, subscription_tier, subscription_status,
            settings, features, created_at, updated_at
        ) VALUES (
            :org_id,
            'HAGES Futtermittel GmbH & Co. KG',
            'hages',
            'buyer',
            'info@hages.de',
            'DE',
            true,
            'professional',
            'active',
            '{
                "default_currency": "EUR",
                "timezone": "Europe/Berlin",
                "language": "de"
            }'::jsonb,
            '{
                "eudr_compliance": true,
                "container_tracking": true,
                "ai_document_classification": true,
                "multi_user": true
            }'::jsonb,
            now(),
            now()
        )
        ON CONFLICT (id) DO NOTHING
    """), {"org_id": str(HAGES_ORG_ID)})

    print(f"HAGES organization (ID: {HAGES_ORG_ID})")

    # =================================================================
    # STEP 2: Create HAGES users
    # =================================================================
    print("Step 2/3: Creating HAGES users...")

    for user_data in HAGES_USERS:
        connection.execute(sa.text("""
            INSERT INTO users (
                id, email, full_name, hashed_password, role,
                organization_id, is_active, created_at, updated_at
            ) VALUES (
                :user_id,
                :email,
                :full_name,
                :hashed_password,
                :role,
                :org_id,
                true,
                now(),
                now()
            )
            ON CONFLICT (email) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                organization_id = EXCLUDED.organization_id,
                updated_at = now()
        """), {
            "user_id": str(user_data["id"]),
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "hashed_password": user_data["hashed_password"],
            "role": user_data["role"],
            "org_id": str(HAGES_ORG_ID)
        })

        print(f"  - {user_data['full_name']} ({user_data['email']})")

    # =================================================================
    # STEP 3: Create organization memberships
    # =================================================================
    print("Step 3/3: Creating organization memberships...")

    for user_data in HAGES_USERS:
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
            ON CONFLICT (organization_id, user_id) DO UPDATE SET
                role = EXCLUDED.role,
                updated_at = now()
        """), {
            "org_id": str(HAGES_ORG_ID),
            "user_id": str(user_data["id"]),
            "org_role": user_data["org_role"]
        })

    # =================================================================
    # SUMMARY
    # =================================================================
    print("\n" + "="*60)
    print("HAGES ORGANIZATION SETUP COMPLETE")
    print("="*60)
    print(f"Organization:  HAGES Futtermittel GmbH & Co. KG")
    print(f"Slug:          hages")
    print(f"Type:          buyer")
    print(f"Users:         {len(HAGES_USERS)} created")
    print("-"*60)
    print("Users created:")
    for user in HAGES_USERS:
        print(f"  {user['full_name']} ({user['org_role']})")
        print(f"    Email: {user['email']}")
    print("="*60 + "\n")


def downgrade() -> None:
    """Remove HAGES organization and users."""

    connection = op.get_bind()

    # Delete memberships first
    connection.execute(sa.text("""
        DELETE FROM org_memberships
        WHERE organization_id = :org_id
    """), {"org_id": str(HAGES_ORG_ID)})

    # Delete users
    for user_data in HAGES_USERS:
        connection.execute(sa.text("""
            DELETE FROM users WHERE id = :user_id
        """), {"user_id": str(user_data["id"])})

    # Delete organization
    connection.execute(sa.text("""
        DELETE FROM organizations WHERE id = :org_id
    """), {"org_id": str(HAGES_ORG_ID)})

    print("HAGES organization and users removed.")
