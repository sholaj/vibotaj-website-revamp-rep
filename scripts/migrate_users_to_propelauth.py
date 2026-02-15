#!/usr/bin/env python3
"""Migrate v1 TraceHub users to PropelAuth.

Reads users from the v1 PostgreSQL database and creates them in PropelAuth
via the Management API. Since v1 bcrypt hashes cannot be imported, all
migrated users will be forced to reset their passwords.

Usage:
    # Dry run (default) — shows what would happen
    python scripts/migrate_users_to_propelauth.py

    # Execute migration
    python scripts/migrate_users_to_propelauth.py --execute

    # Execute with specific database URL
    python scripts/migrate_users_to_propelauth.py --execute --database-url postgresql://...

Environment variables:
    PROPELAUTH_AUTH_URL   — PropelAuth auth URL
    PROPELAUTH_API_KEY    — PropelAuth Management API key
    DATABASE_URL          — v1 database connection string (or use --database-url)
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from uuid import UUID

import httpx
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class V1User:
    """User record from v1 database."""

    id: str
    email: str
    full_name: str
    role: str  # system role (admin, compliance, etc.)
    is_active: bool
    organization_id: str
    org_role: str | None  # from organization_memberships
    org_type: str | None  # from organizations
    org_name: str | None


def fetch_v1_users(database_url: str) -> list[V1User]:
    """Fetch all active users from v1 database with org info."""
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                u.id,
                u.email,
                u.full_name,
                u.role,
                u.is_active,
                u.organization_id,
                m.org_role,
                o.type AS org_type,
                o.name AS org_name
            FROM users u
            LEFT JOIN organization_memberships m
                ON m.user_id = u.id
                AND m.organization_id = u.organization_id
                AND m.is_primary = true
            LEFT JOIN organizations o
                ON o.id = u.organization_id
            WHERE u.deleted_at IS NULL
            ORDER BY u.created_at
        """))

        users = []
        for row in result.mappings():
            users.append(V1User(
                id=str(row["id"]),
                email=row["email"],
                full_name=row["full_name"],
                role=row["role"],
                is_active=row["is_active"],
                organization_id=str(row["organization_id"]) if row["organization_id"] else "",
                org_role=row["org_role"],
                org_type=row["org_type"],
                org_name=row["org_name"],
            ))
        return users


class PropelAuthMigrator:
    """Handles PropelAuth Management API calls for user migration."""

    def __init__(self, auth_url: str, api_key: str):
        self.auth_url = auth_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=f"{self.auth_url}/api/backend/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        # Cache org_id mappings (v1 org_id → PropelAuth org_id)
        self._org_cache: dict[str, str] = {}

    def create_user(self, user: V1User) -> dict:
        """Create a user in PropelAuth with metadata."""
        payload = {
            "email": user.email,
            "email_confirmed": True,
            "send_email_to_confirm_email_address": False,
            "ask_user_to_update_password_on_login": True,  # Force password reset
            "first_name": user.full_name.split(" ")[0] if user.full_name else "",
            "last_name": " ".join(user.full_name.split(" ")[1:]) if user.full_name else "",
            "properties": {
                "system_role": user.role,
                "full_name": user.full_name,
                "v1_user_id": user.id,
            },
        }
        resp = self.client.post("/create_user", json=payload)
        resp.raise_for_status()
        return resp.json()

    def create_org(self, org_id: str, org_name: str, org_type: str) -> str:
        """Create an org in PropelAuth and return its PropelAuth org_id."""
        if org_id in self._org_cache:
            return self._org_cache[org_id]

        payload = {
            "name": org_name,
            "metadata": {
                "org_type": org_type,
                "v1_org_id": org_id,
            },
        }
        resp = self.client.post("/create_org", json=payload)
        resp.raise_for_status()
        propel_org_id = resp.json()["org_id"]
        self._org_cache[org_id] = propel_org_id
        return propel_org_id

    def add_user_to_org(self, propel_user_id: str, propel_org_id: str, org_role: str) -> None:
        """Add a user to an org with a specific role."""
        payload = {
            "user_id": propel_user_id,
            "org_id": propel_org_id,
            "role": org_role or "Member",
        }
        resp = self.client.post("/add_user_to_org", json=payload)
        resp.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Migrate v1 users to PropelAuth")
    parser.add_argument("--execute", action="store_true", help="Actually execute (default is dry run)")
    parser.add_argument("--database-url", help="v1 database URL (default: DATABASE_URL env var)")
    args = parser.parse_args()

    # Config
    auth_url = os.environ.get("PROPELAUTH_AUTH_URL", "")
    api_key = os.environ.get("PROPELAUTH_API_KEY", "")
    database_url = args.database_url or os.environ.get("DATABASE_URL", "")

    if not database_url:
        logger.error("DATABASE_URL not set. Use --database-url or set the env var.")
        sys.exit(1)

    if args.execute and (not auth_url or not api_key):
        logger.error("PROPELAUTH_AUTH_URL and PROPELAUTH_API_KEY must be set for --execute mode.")
        sys.exit(1)

    # Fetch v1 users
    logger.info(f"Fetching users from v1 database...")
    users = fetch_v1_users(database_url)
    logger.info(f"Found {len(users)} users")

    if not users:
        logger.info("No users to migrate.")
        return

    # Print summary
    print("\n--- Migration Summary ---")
    print(f"{'Email':<35} {'Role':<18} {'Org Role':<10} {'Org Type':<18} {'Active'}")
    print("-" * 110)
    for u in users:
        print(f"{u.email:<35} {u.role:<18} {(u.org_role or '-'):<10} {(u.org_type or '-'):<18} {u.is_active}")

    # Collect unique orgs
    orgs: dict[str, tuple[str, str]] = {}  # org_id → (org_name, org_type)
    for u in users:
        if u.organization_id and u.org_name:
            orgs[u.organization_id] = (u.org_name, u.org_type or "buyer")

    print(f"\nOrganizations to create: {len(orgs)}")
    for oid, (name, otype) in orgs.items():
        print(f"  {name} ({otype}) — v1 id: {oid}")

    if not args.execute:
        print("\n[DRY RUN] No changes made. Use --execute to run the migration.")
        return

    # Execute migration
    migrator = PropelAuthMigrator(auth_url, api_key)

    # Step 1: Create orgs
    print("\n--- Creating organizations ---")
    for org_id, (org_name, org_type) in orgs.items():
        try:
            propel_org_id = migrator.create_org(org_id, org_name, org_type)
            logger.info(f"Created org: {org_name} → {propel_org_id}")
        except Exception as e:
            logger.error(f"Failed to create org {org_name}: {e}")

    # Step 2: Create users and assign to orgs
    print("\n--- Creating users ---")
    success = 0
    failed = 0
    for user in users:
        try:
            result = migrator.create_user(user)
            propel_user_id = result["user_id"]
            logger.info(f"Created user: {user.email} → {propel_user_id}")

            # Add to org
            if user.organization_id and user.organization_id in migrator._org_cache:
                propel_org_id = migrator._org_cache[user.organization_id]
                # Map v1 org_role to PropelAuth role name
                role_map = {"admin": "Admin", "manager": "Manager", "member": "Member", "viewer": "Viewer"}
                propel_role = role_map.get(user.org_role or "member", "Member")
                migrator.add_user_to_org(propel_user_id, propel_org_id, propel_role)
                logger.info(f"  Added to org as {propel_role}")

            success += 1
        except Exception as e:
            logger.error(f"Failed to migrate {user.email}: {e}")
            failed += 1

    print(f"\n--- Migration Complete ---")
    print(f"Success: {success}, Failed: {failed}, Total: {len(users)}")
    print("All migrated users will be prompted to reset their passwords on first login.")


if __name__ == "__main__":
    main()
