# Clerk Integration Guide for TraceHub

> Detailed guide for replacing custom JWT authentication with Clerk

**Status:** Planning
**Created:** 2026-01-20

---

## Overview

This guide details how to integrate Clerk authentication into TraceHub, replacing the current custom JWT implementation while preserving the existing multi-tenant data model.

### Current State vs Target State

| Feature | Current (Custom JWT) | Target (Clerk) |
|---------|---------------------|----------------|
| User Storage | PostgreSQL users table | Clerk + synced users table |
| Session Management | JWT in localStorage | Clerk session cookies |
| Password Hashing | bcrypt (self-managed) | Clerk (managed) |
| MFA | Not implemented | Built-in |
| SSO | Not implemented | Google, Microsoft, SAML |
| Organization Management | Custom code | Clerk Organizations |
| Role Assignment | Manual in database | Clerk + webhook sync |
| Invitation Flow | Custom tokens | Clerk Invitations |

---

## 1. Clerk Concepts → TraceHub Mapping

### Organizations

```
Clerk Organization ──────────────── TraceHub Organization
│                                   │
├── org.id (clerk-generated)        ├── organization.id (UUID)
├── org.name                        ├── organization.name
├── org.slug                        ├── organization.slug
├── org.metadata.type  ──────────── ├── organization.type (vibotaj|buyer|supplier|logistics_agent)
├── org.metadata.tax_id             ├── organization.tax_id
└── org.metadata.eu_traces_number   └── organization.settings (JSON)
```

### Users & Memberships

```
Clerk User ─────────────────────── TraceHub User
│                                  │
├── user.id (clerk-generated)      ├── user.id (UUID, keep existing)
├── user.email_addresses[0]        ├── user.email
├── user.first_name + last_name    ├── user.full_name
├── user.metadata.tracehub_id ──── ├── user.id (link back)
└── user.created_at                └── user.created_at

Clerk Membership ──────────────────TraceHub OrganizationMembership
│                                  │
├── membership.organization.id     ├── organization_membership.organization_id
├── membership.public_user_data    ├── organization_membership.user_id
├── membership.role  ─────────────├── organization_membership.org_role
│   (admin, member)               │   (admin, manager, member, viewer)
└── membership.created_at          └── organization_membership.joined_at
```

### Role Mapping

**Clerk → TraceHub Organization Roles:**

| Clerk Role | TraceHub org_role | Permissions |
|------------|-------------------|-------------|
| admin | admin | Full org management, invite members |
| basic_member | member | View/edit shipments, upload documents |
| - (custom) | manager | Manage shipments, no user management |
| - (custom) | viewer | Read-only access |

**System Roles (stored in user.metadata):**

| System Role | Description |
|-------------|-------------|
| admin | Platform super admin (VIBOTAJ staff only) |
| compliance | Compliance officer |
| logistics_agent | External logistics partner |
| buyer | Buyer organization member |
| supplier | Supplier organization member |
| viewer | Read-only system access |

---

## 2. Database Schema Changes

### Add Clerk Integration Fields

```sql
-- Migration: add_clerk_integration_fields.sql

-- Add Clerk ID to users table
ALTER TABLE users
ADD COLUMN clerk_id VARCHAR(255) UNIQUE,
ADD COLUMN clerk_metadata JSONB DEFAULT '{}';

-- Add Clerk ID to organizations table
ALTER TABLE organizations
ADD COLUMN clerk_org_id VARCHAR(255) UNIQUE;

-- Create index for fast lookups
CREATE INDEX idx_users_clerk_id ON users(clerk_id) WHERE clerk_id IS NOT NULL;
CREATE INDEX idx_organizations_clerk_org_id ON organizations(clerk_org_id) WHERE clerk_org_id IS NOT NULL;

-- Migration note: clerk_id will be populated during user migration
-- Legacy users without clerk_id can still exist (for service accounts, etc.)
```

### Alembic Migration

```python
# alembic/versions/xxxx_add_clerk_integration.py
"""Add Clerk integration fields

Revision ID: xxxx_add_clerk_integration
Revises: previous_revision
Create Date: 2026-01-20
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add clerk_id to users
    op.add_column('users', sa.Column('clerk_id', sa.String(255), unique=True, nullable=True))
    op.add_column('users', sa.Column('clerk_metadata', sa.JSON(), server_default='{}'))

    # Add clerk_org_id to organizations
    op.add_column('organizations', sa.Column('clerk_org_id', sa.String(255), unique=True, nullable=True))

    # Create indexes
    op.create_index('idx_users_clerk_id', 'users', ['clerk_id'], postgresql_where=sa.text('clerk_id IS NOT NULL'))
    op.create_index('idx_organizations_clerk_org_id', 'organizations', ['clerk_org_id'], postgresql_where=sa.text('clerk_org_id IS NOT NULL'))

def downgrade():
    op.drop_index('idx_organizations_clerk_org_id')
    op.drop_index('idx_users_clerk_id')
    op.drop_column('organizations', 'clerk_org_id')
    op.drop_column('users', 'clerk_metadata')
    op.drop_column('users', 'clerk_id')
```

---

## 3. Backend Integration (FastAPI)

### Install Dependencies

```bash
pip install svix  # For webhook signature verification
pip install pyjwt[crypto]  # For Clerk JWT verification
pip install httpx  # For Clerk API calls
```

### Clerk Configuration

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...

    # Clerk Configuration
    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    clerk_webhook_secret: str = ""
    clerk_api_url: str = "https://api.clerk.com/v1"

    # JWT verification
    clerk_jwt_issuer: str = ""  # e.g., https://your-app.clerk.accounts.dev
    clerk_jwks_url: str = ""    # e.g., https://your-app.clerk.accounts.dev/.well-known/jwks.json

    class Config:
        env_file = ".env"
```

### Clerk JWT Verification

```python
# backend/app/services/clerk_auth.py
import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError
from functools import lru_cache
from typing import Optional
from ..config import settings

class ClerkAuthService:
    """Service for verifying Clerk JWT tokens."""

    def __init__(self):
        self._jwks_cache: dict = {}

    async def get_jwks(self) -> dict:
        """Fetch JWKS from Clerk with caching."""
        if not self._jwks_cache:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.clerk_jwks_url)
                self._jwks_cache = response.json()
        return self._jwks_cache

    async def verify_token(self, token: str) -> dict:
        """Verify Clerk JWT and return claims."""
        try:
            jwks = await self.get_jwks()

            # Get the key id from token header
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            # Find matching key in JWKS
            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break

            if not rsa_key:
                raise ValueError("Unable to find matching key")

            # Verify and decode token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                issuer=settings.clerk_jwt_issuer,
                options={"verify_aud": False}  # Clerk doesn't always set aud
            )

            return payload

        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def extract_user_info(self, payload: dict) -> dict:
        """Extract user information from Clerk JWT claims."""
        return {
            "clerk_id": payload.get("sub"),
            "email": payload.get("email"),
            "org_id": payload.get("org_id"),
            "org_role": payload.get("org_role"),
            "org_permissions": payload.get("org_permissions", []),
            "metadata": payload.get("metadata", {})
        }


clerk_auth_service = ClerkAuthService()
```

### Updated Auth Dependency

```python
# backend/app/routers/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.clerk_auth import clerk_auth_service
from ..schemas.auth import CurrentUser
from ..models import User, Organization, OrganizationMembership

security = HTTPBearer()


async def get_current_user_from_clerk(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """
    Authenticate user via Clerk JWT and return CurrentUser schema.

    This replaces the legacy get_current_user dependency.
    """
    try:
        # Verify Clerk token
        payload = await clerk_auth_service.verify_token(credentials.credentials)
        user_info = clerk_auth_service.extract_user_info(payload)

        # Find user in our database by clerk_id
        user = await db.execute(
            select(User)
            .where(User.clerk_id == user_info["clerk_id"])
            .where(User.is_active == True)
        )
        user = user.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in TraceHub"
            )

        # Get organization from Clerk token
        org_id = user_info.get("org_id")
        if org_id:
            # Find organization by clerk_org_id
            org = await db.execute(
                select(Organization)
                .where(Organization.clerk_org_id == org_id)
            )
            org = org.scalar_one_or_none()

            if org:
                # Get membership for role
                membership = await db.execute(
                    select(OrganizationMembership)
                    .where(OrganizationMembership.user_id == user.id)
                    .where(OrganizationMembership.organization_id == org.id)
                )
                membership = membership.scalar_one_or_none()
        else:
            # Use user's primary organization
            org = await db.execute(
                select(Organization)
                .where(Organization.id == user.organization_id)
            )
            org = org.scalar_one_or_none()
            membership = None

        if not org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization context"
            )

        # Build CurrentUser response (matches existing schema)
        return CurrentUser(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            organization_id=str(org.id),
            organization_name=org.name,
            organization_type=org.type,
            org_role=membership.org_role if membership else "member",
            permissions=user_info.get("org_permissions", [])
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# Alias for backward compatibility
get_current_active_user = get_current_user_from_clerk
```

### Clerk Webhook Handler

```python
# backend/app/routers/webhooks.py
from fastapi import APIRouter, Request, HTTPException, Depends
from svix.webhooks import Webhook, WebhookVerificationError
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..config import settings
from ..models import User, Organization, OrganizationMembership
import logging

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


async def verify_clerk_webhook(request: Request) -> dict:
    """Verify Clerk webhook signature and return payload."""
    payload = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id"),
        "svix-timestamp": request.headers.get("svix-timestamp"),
        "svix-signature": request.headers.get("svix-signature"),
    }

    try:
        wh = Webhook(settings.clerk_webhook_secret)
        return wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


@router.post("/clerk")
async def handle_clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Clerk webhook events.

    Events handled:
    - user.created: Create new user in TraceHub
    - user.updated: Update user details
    - user.deleted: Soft delete user
    - organization.created: Create new organization
    - organization.updated: Update organization
    - organizationMembership.created: Add user to organization
    - organizationMembership.deleted: Remove user from organization
    """
    payload = await verify_clerk_webhook(request)
    event_type = payload.get("type")
    data = payload.get("data", {})

    logger.info(f"Received Clerk webhook: {event_type}")

    try:
        if event_type == "user.created":
            await handle_user_created(db, data)
        elif event_type == "user.updated":
            await handle_user_updated(db, data)
        elif event_type == "user.deleted":
            await handle_user_deleted(db, data)
        elif event_type == "organization.created":
            await handle_org_created(db, data)
        elif event_type == "organization.updated":
            await handle_org_updated(db, data)
        elif event_type == "organizationMembership.created":
            await handle_membership_created(db, data)
        elif event_type == "organizationMembership.deleted":
            await handle_membership_deleted(db, data)
        else:
            logger.info(f"Unhandled Clerk event: {event_type}")

        await db.commit()
        return {"status": "processed", "event": event_type}

    except Exception as e:
        logger.error(f"Error processing Clerk webhook: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def handle_user_created(db: AsyncSession, data: dict):
    """Create new user from Clerk user.created event."""
    clerk_id = data.get("id")
    email = data.get("email_addresses", [{}])[0].get("email_address")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")

    # Check if user already exists (by email)
    existing = await db.execute(
        select(User).where(User.email == email)
    )
    existing = existing.scalar_one_or_none()

    if existing:
        # Link existing user to Clerk
        existing.clerk_id = clerk_id
        existing.clerk_metadata = data.get("public_metadata", {})
        logger.info(f"Linked existing user {email} to Clerk ID {clerk_id}")
    else:
        # Create new user
        # Note: Organization assignment happens via membership webhook
        new_user = User(
            email=email,
            full_name=f"{first_name} {last_name}".strip() or email.split("@")[0],
            clerk_id=clerk_id,
            clerk_metadata=data.get("public_metadata", {}),
            role="viewer",  # Default role, updated by admin
            is_active=True,
            # organization_id will be set when they join an org
        )
        db.add(new_user)
        logger.info(f"Created new user {email} with Clerk ID {clerk_id}")


async def handle_user_updated(db: AsyncSession, data: dict):
    """Update user from Clerk user.updated event."""
    clerk_id = data.get("id")
    user = await db.execute(
        select(User).where(User.clerk_id == clerk_id)
    )
    user = user.scalar_one_or_none()

    if user:
        email = data.get("email_addresses", [{}])[0].get("email_address")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        user.email = email
        user.full_name = f"{first_name} {last_name}".strip() or user.full_name
        user.clerk_metadata = data.get("public_metadata", {})
        logger.info(f"Updated user {email}")


async def handle_user_deleted(db: AsyncSession, data: dict):
    """Soft delete user from Clerk user.deleted event."""
    clerk_id = data.get("id")
    user = await db.execute(
        select(User).where(User.clerk_id == clerk_id)
    )
    user = user.scalar_one_or_none()

    if user:
        from datetime import datetime, timezone
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        user.deletion_reason = "Deleted via Clerk"
        logger.info(f"Soft deleted user {user.email}")


async def handle_org_created(db: AsyncSession, data: dict):
    """Create organization from Clerk organization.created event."""
    clerk_org_id = data.get("id")
    name = data.get("name")
    slug = data.get("slug")
    metadata = data.get("public_metadata", {})

    # Check if org already exists (by slug)
    existing = await db.execute(
        select(Organization).where(Organization.slug == slug)
    )
    existing = existing.scalar_one_or_none()

    if existing:
        existing.clerk_org_id = clerk_org_id
        logger.info(f"Linked existing org {name} to Clerk org ID {clerk_org_id}")
    else:
        org_type = metadata.get("type", "buyer")  # Default to buyer
        new_org = Organization(
            name=name,
            slug=slug,
            type=org_type,
            clerk_org_id=clerk_org_id,
            status="active",
            settings=metadata
        )
        db.add(new_org)
        logger.info(f"Created new organization {name} with Clerk org ID {clerk_org_id}")


async def handle_org_updated(db: AsyncSession, data: dict):
    """Update organization from Clerk organization.updated event."""
    clerk_org_id = data.get("id")
    org = await db.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    org = org.scalar_one_or_none()

    if org:
        org.name = data.get("name", org.name)
        org.slug = data.get("slug", org.slug)
        org.settings = {**org.settings, **data.get("public_metadata", {})}
        logger.info(f"Updated organization {org.name}")


async def handle_membership_created(db: AsyncSession, data: dict):
    """Create organization membership from Clerk event."""
    clerk_org_id = data.get("organization", {}).get("id")
    clerk_user_id = data.get("public_user_data", {}).get("user_id")
    clerk_role = data.get("role")  # 'admin' or 'basic_member'

    # Map Clerk role to TraceHub org_role
    role_mapping = {
        "admin": "admin",
        "basic_member": "member"
    }
    org_role = role_mapping.get(clerk_role, "member")

    # Find user and org
    user = await db.execute(
        select(User).where(User.clerk_id == clerk_user_id)
    )
    user = user.scalar_one_or_none()

    org = await db.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    org = org.scalar_one_or_none()

    if user and org:
        # Check if membership exists
        existing = await db.execute(
            select(OrganizationMembership)
            .where(OrganizationMembership.user_id == user.id)
            .where(OrganizationMembership.organization_id == org.id)
        )
        existing = existing.scalar_one_or_none()

        if not existing:
            membership = OrganizationMembership(
                user_id=user.id,
                organization_id=org.id,
                org_role=org_role,
                is_primary=True  # First org is primary
            )
            db.add(membership)

            # Update user's primary organization if not set
            if not user.organization_id:
                user.organization_id = org.id

            logger.info(f"Added user {user.email} to org {org.name} as {org_role}")


async def handle_membership_deleted(db: AsyncSession, data: dict):
    """Remove organization membership from Clerk event."""
    clerk_org_id = data.get("organization", {}).get("id")
    clerk_user_id = data.get("public_user_data", {}).get("user_id")

    user = await db.execute(
        select(User).where(User.clerk_id == clerk_user_id)
    )
    user = user.scalar_one_or_none()

    org = await db.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    org = org.scalar_one_or_none()

    if user and org:
        membership = await db.execute(
            select(OrganizationMembership)
            .where(OrganizationMembership.user_id == user.id)
            .where(OrganizationMembership.organization_id == org.id)
        )
        membership = membership.scalar_one_or_none()

        if membership:
            await db.delete(membership)
            logger.info(f"Removed user {user.email} from org {org.name}")
```

---

## 4. Frontend Integration (Next.js)

### Install Clerk SDK

```bash
npm install @clerk/nextjs
```

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Sign-in/sign-up URLs
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding
```

### Clerk Provider Setup

```typescript
// app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: undefined,
        variables: {
          colorPrimary: '#0066cc', // TraceHub blue
          colorBackground: '#ffffff',
          colorText: '#1a1a1a',
        },
        elements: {
          formButtonPrimary: 'bg-blue-600 hover:bg-blue-700',
          card: 'shadow-lg',
        }
      }}
    >
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

### Middleware Configuration

```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks/clerk',  // Clerk webhooks must be public
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};
```

### Sign-In Page

```typescript
// app/sign-in/[[...sign-in]]/page.tsx
import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">TraceHub</h1>
          <p className="text-gray-600 mt-2">Container Tracking & Compliance</p>
        </div>
        <SignIn
          routing="path"
          path="/sign-in"
          signUpUrl="/sign-up"
          afterSignInUrl="/dashboard"
        />
      </div>
    </div>
  );
}
```

### Organization Switcher

```typescript
// components/OrganizationSwitcher.tsx
'use client';

import { OrganizationSwitcher as ClerkOrgSwitcher } from '@clerk/nextjs';

export function OrganizationSwitcher() {
  return (
    <ClerkOrgSwitcher
      hidePersonal={true}  // Only show organizations, not personal workspace
      afterSelectOrganizationUrl="/dashboard"
      afterCreateOrganizationUrl="/onboarding/organization"
      appearance={{
        elements: {
          rootBox: 'w-full',
          organizationSwitcherTrigger:
            'w-full flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50',
        }
      }}
    />
  );
}
```

### Protected API Calls

```typescript
// lib/api.ts
import { auth } from '@clerk/nextjs/server';

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const { getToken } = await auth();
  const token = await getToken();

  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
}

// Usage in Server Component
async function getShipments() {
  const response = await fetchWithAuth(
    `${process.env.API_URL}/api/shipments`
  );
  return response.json();
}
```

### Client-Side Hook

```typescript
// hooks/useApi.ts
'use client';

import { useAuth } from '@clerk/nextjs';
import { useCallback } from 'react';

export function useApi() {
  const { getToken } = useAuth();

  const fetchWithAuth = useCallback(async (url: string, options: RequestInit = {}) => {
    const token = await getToken();

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }, [getToken]);

  return { fetchWithAuth };
}

// Usage in Client Component
function ShipmentList() {
  const { fetchWithAuth } = useApi();
  const [shipments, setShipments] = useState([]);

  useEffect(() => {
    fetchWithAuth('/api/shipments')
      .then(data => setShipments(data))
      .catch(console.error);
  }, [fetchWithAuth]);

  // ...
}
```

### Permission Guard Component

```typescript
// components/PermissionGuard.tsx
'use client';

import { useOrganization } from '@clerk/nextjs';
import { ReactNode } from 'react';

type Permission =
  | 'shipment:create'
  | 'shipment:edit'
  | 'shipment:delete'
  | 'document:upload'
  | 'document:validate'
  | 'user:manage'
  | 'org:manage';

interface PermissionGuardProps {
  permission: Permission;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGuard({
  permission,
  children,
  fallback = null
}: PermissionGuardProps) {
  const { organization, membership } = useOrganization();

  // Define permission mappings
  const rolePermissions: Record<string, Permission[]> = {
    admin: [
      'shipment:create', 'shipment:edit', 'shipment:delete',
      'document:upload', 'document:validate',
      'user:manage', 'org:manage'
    ],
    manager: [
      'shipment:create', 'shipment:edit',
      'document:upload', 'document:validate'
    ],
    member: [
      'shipment:create', 'shipment:edit',
      'document:upload'
    ],
    viewer: []  // Read-only
  };

  const userRole = membership?.role || 'viewer';
  const hasPermission = rolePermissions[userRole]?.includes(permission) ?? false;

  if (!hasPermission) {
    return fallback;
  }

  return <>{children}</>;
}

// Usage
<PermissionGuard permission="document:upload">
  <UploadButton />
</PermissionGuard>
```

---

## 5. User Migration Script

### Migrate Existing Users to Clerk

```python
# scripts/migrate_users_to_clerk.py
"""
Migrate existing TraceHub users to Clerk.

This script:
1. Reads all active users from the database
2. Creates corresponding Clerk users
3. Creates Clerk organizations
4. Links users to organizations
5. Updates database with clerk_id references

Run with: python scripts/migrate_users_to_clerk.py --dry-run
"""
import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import argparse
import logging

from app.config import settings
from app.models import User, Organization, OrganizationMembership

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClerkMigrator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.clerk_api = "https://api.clerk.com/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.clerk_secret_key}",
            "Content-Type": "application/json"
        }

    async def migrate_all(self):
        """Run full migration."""
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            # 1. Migrate organizations first
            await self.migrate_organizations(db)

            # 2. Migrate users
            await self.migrate_users(db)

            # 3. Create memberships
            await self.migrate_memberships(db)

            if not self.dry_run:
                await db.commit()
                logger.info("Migration committed successfully")
            else:
                logger.info("DRY RUN - no changes committed")

    async def migrate_organizations(self, db: AsyncSession):
        """Create Clerk organizations for each TraceHub organization."""
        result = await db.execute(
            select(Organization)
            .where(Organization.clerk_org_id.is_(None))
            .where(Organization.status == "active")
        )
        orgs = result.scalars().all()

        logger.info(f"Migrating {len(orgs)} organizations to Clerk")

        async with httpx.AsyncClient() as client:
            for org in orgs:
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would create Clerk org: {org.name}")
                    continue

                payload = {
                    "name": org.name,
                    "slug": org.slug,
                    "public_metadata": {
                        "tracehub_id": str(org.id),
                        "type": org.type,
                        "tax_id": org.tax_id
                    }
                }

                response = await client.post(
                    f"{self.clerk_api}/organizations",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 200:
                    clerk_org = response.json()
                    org.clerk_org_id = clerk_org["id"]
                    logger.info(f"Created Clerk org {org.name}: {clerk_org['id']}")
                else:
                    logger.error(f"Failed to create org {org.name}: {response.text}")

    async def migrate_users(self, db: AsyncSession):
        """Create Clerk users for each TraceHub user."""
        result = await db.execute(
            select(User)
            .where(User.clerk_id.is_(None))
            .where(User.is_active == True)
        )
        users = result.scalars().all()

        logger.info(f"Migrating {len(users)} users to Clerk")

        async with httpx.AsyncClient() as client:
            for user in users:
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would create Clerk user: {user.email}")
                    continue

                # Split full_name into first/last
                name_parts = (user.full_name or "").split(" ", 1)
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                payload = {
                    "email_address": [user.email],
                    "first_name": first_name,
                    "last_name": last_name,
                    "public_metadata": {
                        "tracehub_id": str(user.id),
                        "system_role": user.role
                    },
                    "skip_password_requirement": True  # Users will set password via Clerk
                }

                response = await client.post(
                    f"{self.clerk_api}/users",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 200:
                    clerk_user = response.json()
                    user.clerk_id = clerk_user["id"]
                    logger.info(f"Created Clerk user {user.email}: {clerk_user['id']}")
                elif "email_address already exists" in response.text:
                    # User already exists in Clerk, find and link
                    search_response = await client.get(
                        f"{self.clerk_api}/users",
                        headers=self.headers,
                        params={"email_address": user.email}
                    )
                    if search_response.status_code == 200:
                        clerk_users = search_response.json()
                        if clerk_users:
                            user.clerk_id = clerk_users[0]["id"]
                            logger.info(f"Linked existing Clerk user {user.email}")
                else:
                    logger.error(f"Failed to create user {user.email}: {response.text}")

    async def migrate_memberships(self, db: AsyncSession):
        """Create Clerk organization memberships."""
        result = await db.execute(
            select(OrganizationMembership)
            .join(User, OrganizationMembership.user_id == User.id)
            .join(Organization, OrganizationMembership.organization_id == Organization.id)
            .where(User.clerk_id.isnot(None))
            .where(Organization.clerk_org_id.isnot(None))
        )
        memberships = result.scalars().all()

        logger.info(f"Migrating {len(memberships)} memberships to Clerk")

        # Map TraceHub roles to Clerk roles
        role_mapping = {
            "admin": "admin",
            "manager": "admin",  # Clerk only has admin/basic_member
            "member": "basic_member",
            "viewer": "basic_member"
        }

        async with httpx.AsyncClient() as client:
            for membership in memberships:
                # Get user and org
                user = await db.get(User, membership.user_id)
                org = await db.get(Organization, membership.organization_id)

                if not user.clerk_id or not org.clerk_org_id:
                    continue

                if self.dry_run:
                    logger.info(f"[DRY RUN] Would add {user.email} to {org.name}")
                    continue

                clerk_role = role_mapping.get(membership.org_role, "basic_member")

                payload = {
                    "user_id": user.clerk_id,
                    "role": clerk_role
                }

                response = await client.post(
                    f"{self.clerk_api}/organizations/{org.clerk_org_id}/memberships",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 200:
                    logger.info(f"Added {user.email} to {org.name} as {clerk_role}")
                elif "already a member" in response.text.lower():
                    logger.info(f"User {user.email} already member of {org.name}")
                else:
                    logger.error(f"Failed to add membership: {response.text}")


async def main():
    parser = argparse.ArgumentParser(description="Migrate users to Clerk")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    migrator = ClerkMigrator(dry_run=args.dry_run)
    await migrator.migrate_all()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Testing Checklist

### Authentication Flow

- [ ] User can sign up with email/password
- [ ] User can sign in with email/password
- [ ] Session persists across page refreshes
- [ ] Logout clears session
- [ ] Password reset flow works
- [ ] MFA enrollment works (optional)

### Organization Flow

- [ ] New organization can be created in Clerk
- [ ] Organization syncs to TraceHub database
- [ ] User can be invited to organization
- [ ] Invitation acceptance works
- [ ] User can switch between organizations
- [ ] Organization deletion cascades properly

### API Authorization

- [ ] API calls include valid Clerk JWT
- [ ] Invalid tokens return 401
- [ ] Expired tokens return 401
- [ ] Organization context is respected in queries
- [ ] Role-based permissions work correctly

### Webhook Integration

- [ ] user.created webhook creates TraceHub user
- [ ] user.updated webhook updates TraceHub user
- [ ] organization.created webhook creates TraceHub org
- [ ] organizationMembership.created adds membership
- [ ] Webhook signature verification works

### Migration

- [ ] All existing users have clerk_id after migration
- [ ] All existing orgs have clerk_org_id after migration
- [ ] Users can sign in with existing credentials
- [ ] Existing sessions are invalidated (expected)

---

## 7. Rollback Plan

If Clerk integration fails, rollback steps:

1. **Revert middleware:** Restore legacy JWT authentication
2. **Revert auth dependency:** Use original `get_current_user`
3. **Keep clerk_id columns:** No need to remove, just ignore
4. **Disable webhooks:** Remove webhook route from Clerk dashboard
5. **Communicate to users:** Send password reset links for legacy auth

---

## Appendix: Clerk Dashboard Setup

### 1. Create Application

1. Go to https://dashboard.clerk.com
2. Create new application "TraceHub"
3. Select authentication methods:
   - Email + Password
   - Google OAuth (optional)
   - Microsoft OAuth (for enterprise SSO)

### 2. Configure Organizations

1. Enable Organizations feature
2. Set organization creation permissions:
   - Allow users to create organizations: **No** (admin only)
3. Configure organization roles:
   - Keep default: admin, basic_member

### 3. Set Up Webhooks

1. Go to Webhooks section
2. Create endpoint: `https://tracehub.vibotaj.com/api/webhooks/clerk`
3. Select events:
   - user.created
   - user.updated
   - user.deleted
   - organization.created
   - organization.updated
   - organizationMembership.created
   - organizationMembership.deleted
4. Copy signing secret to `CLERK_WEBHOOK_SECRET`

### 4. Configure JWT Template

1. Go to JWT Templates
2. Create new template for API access:
```json
{
  "org_id": "{{org.id}}",
  "org_role": "{{org.role}}",
  "org_permissions": [],
  "metadata": {
    "tracehub_id": "{{user.public_metadata.tracehub_id}}",
    "system_role": "{{user.public_metadata.system_role}}"
  }
}
```

### 5. Production Checklist

- [ ] Switch to production instance
- [ ] Configure custom domain (auth.tracehub.vibotaj.com)
- [ ] Set up HTTPS redirect
- [ ] Configure rate limiting
- [ ] Enable attack protection
- [ ] Review session settings (24-hour expiry)

---

*Document maintained by TraceHub Engineering Team*
