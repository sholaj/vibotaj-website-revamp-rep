# PRD-003: PropelAuth Integration

**Status:** Done
**Complexity:** High
**Target:** Week 3
**Dependencies:** PRD-001 (Next.js frontend), PRD-002 (Supabase schema — user/org tables)
**Branch:** `feature/prd-003-propelauth`

---

## Problem

v1 uses custom JWT authentication (python-jose, HS256) with 463 lines of auth logic including two user resolution paths (`get_current_user` deprecated, `get_current_active_user` preferred), a demo user fallback, manual password hashing (bcrypt), and no SSO/SAML support. The RBAC system spans 3 files: system roles (6 roles, 22 permissions), org roles (4 roles, 23 org permissions), and org-type bonuses (3 permission sets). No MFA, no session management, no audit trail for auth events.

## Acceptance Criteria

1. PropelAuth project configured with dev environment
2. 6 system roles mapped with correct permission sets:
   - `admin` (22 permissions — full access + `system:admin`)
   - `compliance` (9 permissions — validate/approve docs, audit pack)
   - `logistics_agent` (10 permissions — create/manage shipments, tracking)
   - `buyer` (5 permissions — read-only shipments/docs, tracking)
   - `supplier` (6 permissions — read shipments, upload/create docs)
   - `viewer` (4 permissions — read-only everything)
3. 4 org roles mapped: `admin` (23 perms), `manager` (15), `member` (10), `viewer` (7)
4. Org types stored as PropelAuth org metadata: `vibotaj`, `buyer`, `supplier`, `logistics_agent`
5. Org-type bonus permissions applied at runtime (VIBOTAJ: approve/validate/compliance, BUYER: approve/validate, LOGISTICS_AGENT: tracking:refresh)
6. FastAPI backend: `propelauth-fastapi` SDK replaces custom JWT auth
7. `get_current_user_v2()` dependency returns existing `CurrentUser` schema shape (backward compatible)
8. Next.js frontend: `@propelauth/nextjs` with middleware protecting all routes except `/login`
9. User migration script for v1 users → PropelAuth (force password reset)
10. v1 JWT auth on Hostinger is completely untouched
11. Role hierarchy preserved: admin > compliance > logistics_agent > buyer = supplier > viewer

## Technical Approach

### 1. PropelAuth Project Setup

- Create PropelAuth project at propelauth.com
- Configure:
  - Login methods: email + password (SSO/SAML deferred to Phase 4)
  - Frontend integration: Next.js
  - Backend integration: FastAPI
  - Org settings: enabled, with metadata schema for `org_type`

### 2. Role Mapping Strategy

PropelAuth uses **org-level roles** natively. TraceHub has both system roles and org roles. Strategy:

**System roles** → PropelAuth user metadata (`system_role` field):
```json
{ "system_role": "admin", "permissions": ["users:create", "users:read", ...] }
```

**Org roles** → PropelAuth org roles (native feature):
- Map TraceHub `OrgRole` enum values directly to PropelAuth org roles
- PropelAuth handles role assignment per org membership

**Org-type bonuses** → Computed at runtime in the role adapter:
```python
def compute_effective_permissions(system_role, org_role, org_type, is_system_admin):
    base = ROLE_PERMISSIONS[system_role]
    org = ORG_ROLE_PERMISSIONS[org_role]
    bonus = ORG_TYPE_PERMISSIONS.get(org_type, set())
    if is_system_admin:
        return ALL_PERMISSIONS
    return base | org | bonus
```

### 3. FastAPI Backend Integration

```python
# v2/backend/app/auth/propelauth.py
from propelauth_fastapi import init_auth, User as PropelAuthUser

auth = init_auth(
    auth_url=settings.PROPELAUTH_AUTH_URL,
    api_key=settings.PROPELAUTH_API_KEY,
)

async def get_current_user_v2(
    propel_user: PropelAuthUser = Depends(auth.require_user),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Bridge PropelAuth user to TraceHub CurrentUser schema."""
    # 1. Get system_role from PropelAuth user metadata
    # 2. Get org membership + org_role from PropelAuth
    # 3. Get org_type from PropelAuth org metadata
    # 4. Compute effective permissions via role_adapter
    # 5. Return CurrentUser (same schema shape as v1)
```

### 4. Role Adapter (v1 RBAC Compatibility Layer)

```python
# v2/backend/app/auth/role_adapter.py

# Preserve exact permission sets from v1:
# - ROLE_PERMISSIONS from services/permissions.py
# - ORG_ROLE_PERMISSIONS from services/org_permissions.py
# - ORG_TYPE_PERMISSIONS from services/org_permissions.py
# - ROLE_HIERARCHY from services/permissions.py
# - ORG_ROLE_HIERARCHY from models/organization.py

def adapt_propelauth_to_current_user(
    propel_user, org_membership, org_metadata
) -> CurrentUser:
    """Map PropelAuth primitives to v1 CurrentUser contract."""
```

### 5. Next.js Frontend Auth

```typescript
// v2/frontend/src/middleware.ts
import { authMiddleware } from "@propelauth/nextjs/server";

export const middleware = authMiddleware({
  publicRoutes: ["/login", "/signup", "/forgot-password"],
});
```

Protected pages use `withRequiredUser()` server-side or `useUser()` client-side.

### 6. User Migration Script

```python
# scripts/migrate_users_to_propelauth.py
# 1. Read all users from v1 database
# 2. Create in PropelAuth via Management API
# 3. Set system_role in user metadata
# 4. Create org memberships with org_role
# 5. Force password reset for all migrated users
# 6. Log migration results
```

**Decision: Force password reset** — cleanest for security. v1 uses bcrypt hashes which cannot be imported into PropelAuth. Users receive a password reset email on first login.

## CurrentUser Schema Contract (Must Preserve)

```python
class CurrentUser(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole          # System role (admin, compliance, etc.)
    is_active: bool
    organization_id: UUID   # Current org context
    permissions: list[str]  # System permissions (e.g., "users:create")
    org_role: OrgRole | None        # Org-level role
    org_type: OrganizationType | None  # Org type (vibotaj, buyer, etc.)
    org_permissions: list[str]      # Org-scoped permissions
```

All existing endpoints depend on this shape. The role adapter must produce identical output regardless of whether auth comes from v1 JWT or v2 PropelAuth.

## Files to Create

```
v2/backend/app/auth/
  __init__.py
  propelauth.py           # PropelAuth SDK init + get_current_user_v2()
  role_adapter.py          # RBAC mapping: PropelAuth → CurrentUser
  permissions.py           # Copy of v1 ROLE_PERMISSIONS (canonical)
  org_permissions.py       # Copy of v1 ORG_ROLE_PERMISSIONS + ORG_TYPE_PERMISSIONS
v2/frontend/src/
  middleware.ts             # PropelAuth route protection
  lib/auth/
    provider.tsx            # AuthProvider wrapper
    hooks.ts                # useUser(), useOrg(), usePermissions()
scripts/
  migrate_users_to_propelauth.py
```

## v1 Source of Truth

| v1 File | What to Extract |
|---------|----------------|
| `tracehub/backend/app/routers/auth.py` (463 lines) | Auth flow, demo user logic, token handling |
| `tracehub/backend/app/services/permissions.py` (283 lines) | `ROLE_PERMISSIONS`, `ROLE_HIERARCHY`, `Permission` enum |
| `tracehub/backend/app/services/org_permissions.py` (615 lines) | `ORG_ROLE_PERMISSIONS`, `ORG_TYPE_PERMISSIONS`, `OrgPermission` enum |
| `tracehub/backend/app/schemas/user.py` (186 lines) | `CurrentUser` schema — the contract to preserve |
| `tracehub/backend/app/models/organization.py` | `ORG_ROLE_HIERARCHY`, `OrgRole`, `OrganizationType` enums |

## Testing Strategy

- Unit test: `role_adapter` produces correct `CurrentUser` for each of 6 system roles
- Unit test: org-type bonus permissions are applied correctly (VIBOTAJ gets 3 extra, BUYER gets 2)
- Unit test: admin bypass gives all permissions
- Unit test: role hierarchy comparisons match v1 behavior
- Integration test: PropelAuth user → `get_current_user_v2()` → `CurrentUser` with correct permissions
- E2E test: login flow on Next.js → API call with PropelAuth token → authorized response
- Migration script dry-run against v1 database copy

## Migration Notes

- v1 JWT auth on Hostinger continues to work — PropelAuth is v2 only
- Demo user (`00000000-0000-0000-0000-000000000001`) is NOT migrated — remove demo fallback in v2
- Password reset emails sent to all migrated users — coordinate with Bolaji for user communication
- PropelAuth free tier supports up to 1,000 MAU — sufficient for current user base
- SAML/SCIM enterprise SSO deferred to Phase 4 (PRD-022 white-label)
