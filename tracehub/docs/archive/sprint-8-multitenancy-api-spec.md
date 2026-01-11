# TraceHub Sprint 8: Multi-Tenancy API Specification

**Version:** 1.0.0
**Date:** 2026-01-05
**Author:** API Designer
**Status:** Draft

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Data Models](#data-models)
4. [JWT Token Structure](#jwt-token-structure)
5. [Organizations API](#organizations-api)
6. [Invitations API](#invitations-api)
7. [Organization Membership API](#organization-membership-api)
8. [Session Management API](#session-management-api)
9. [Updated Authentication Flow](#updated-authentication-flow)
10. [Permission Scoping](#permission-scoping)
11. [Error Handling](#error-handling)
12. [Rate Limiting](#rate-limiting)
13. [Migration Strategy](#migration-strategy)

---

## Overview

This specification defines the API endpoints required to implement multi-tenancy in TraceHub. The design enables:

- **Organizations** as the primary tenant boundary
- **Role-based access** within organizations
- **Cross-organization access** for VIBOTAJ super-admins
- **Invitation-based onboarding** for buyers, suppliers, and agents
- **Organization switching** for users belonging to multiple organizations

### Base URL

```
Production: https://api.tracehub.vibotaj.com/api/v1
Staging:    https://api-staging.tracehub.vibotaj.com/api/v1
```

---

## Design Principles

1. **Tenant Isolation**: All data queries are scoped by `organization_id` unless the user has system-level access
2. **Backward Compatibility**: Existing endpoints continue to work; organization context is derived from JWT
3. **Explicit Over Implicit**: Organization context is always explicit in the JWT, never inferred
4. **Auditability**: All organization and membership changes are logged
5. **Secure by Default**: Invitation tokens are cryptographically secure, single-use, and time-limited

---

## Data Models

### Organization Types

```python
class OrganizationType(str, Enum):
    """Types of organizations in the system."""
    VIBOTAJ = "vibotaj"           # Platform owner - full system access
    BUYER = "buyer"               # Importing companies (German partners)
    SUPPLIER = "supplier"         # Exporting companies (African suppliers)
    LOGISTICS_AGENT = "logistics_agent"  # Freight forwarders, customs agents
```

### Organization Entity

```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string (unique, url-safe)",
  "type": "OrganizationType",
  "status": "active | suspended | pending_setup",
  "settings": {
    "default_currency": "EUR",
    "timezone": "Europe/Berlin",
    "notification_preferences": {},
    "compliance_settings": {
      "eudr_enabled": true,
      "auto_validate_documents": false
    }
  },
  "contact_email": "string",
  "contact_phone": "string | null",
  "address": {
    "street": "string",
    "city": "string",
    "postal_code": "string",
    "country": "DE"
  },
  "tax_id": "string | null",
  "registration_number": "string | null",
  "logo_url": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "created_by": "uuid"
}
```

### Organization Membership

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "organization_id": "uuid",
  "org_role": "admin | manager | member | viewer",
  "is_primary": "boolean",
  "status": "active | suspended | pending",
  "joined_at": "datetime",
  "invited_by": "uuid | null",
  "invitation_id": "uuid | null"
}
```

### Invitation Entity

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "email": "string",
  "org_role": "admin | manager | member | viewer",
  "token_hash": "string (stored hashed)",
  "status": "pending | accepted | expired | revoked",
  "expires_at": "datetime",
  "created_at": "datetime",
  "created_by": "uuid",
  "accepted_at": "datetime | null",
  "accepted_by": "uuid | null",
  "metadata": {
    "custom_message": "string | null",
    "redirect_url": "string | null"
  }
}
```

---

## JWT Token Structure

### Current Structure (Legacy)

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "admin",
  "exp": 1704499200
}
```

### New Structure (Multi-tenant)

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "system_role": "user | system_admin",
  "org_id": "uuid",
  "org_type": "vibotaj | buyer | supplier | logistics_agent",
  "org_role": "admin | manager | member | viewer",
  "permissions": ["shipments:read", "documents:upload"],
  "iat": 1704412800,
  "exp": 1704499200
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | UUID | Unique user identifier |
| `email` | string | User's email address |
| `system_role` | enum | System-wide role: `user` (normal) or `system_admin` (VIBOTAJ staff) |
| `org_id` | UUID | Currently active organization |
| `org_type` | enum | Type of the active organization |
| `org_role` | enum | User's role within the active organization |
| `permissions` | array | Computed permissions based on org_role and org_type |
| `iat` | int | Token issued at timestamp |
| `exp` | int | Token expiration timestamp |

---

## Organizations API

### Base Path: `/api/v1/organizations`

---

### POST /organizations

Create a new organization. Only VIBOTAJ system admins can create organizations.

**Authorization:** `system_role == system_admin`

**Request Body:**

```json
{
  "name": "Hamburg Import GmbH",
  "slug": "hamburg-import",
  "type": "buyer",
  "contact_email": "admin@hamburg-import.de",
  "contact_phone": "+49 40 123456",
  "address": {
    "street": "Speicherstadt 42",
    "city": "Hamburg",
    "postal_code": "20457",
    "country": "DE"
  },
  "tax_id": "DE123456789",
  "settings": {
    "default_currency": "EUR",
    "timezone": "Europe/Berlin"
  }
}
```

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Hamburg Import GmbH",
  "slug": "hamburg-import",
  "type": "buyer",
  "status": "active",
  "contact_email": "admin@hamburg-import.de",
  "created_at": "2026-01-05T10:30:00Z",
  "created_by": "system-admin-user-id"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | `ORG_SLUG_EXISTS` | Organization slug already taken |
| 400 | `INVALID_ORG_TYPE` | Invalid organization type |
| 403 | `INSUFFICIENT_PERMISSIONS` | User is not a system admin |

---

### GET /organizations

List organizations. VIBOTAJ admins see all; others see only their memberships.

**Authorization:** Authenticated user

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page (max 100) |
| `type` | string | null | Filter by organization type |
| `status` | string | null | Filter by status |
| `search` | string | null | Search by name or slug |
| `sort` | string | `created_at` | Sort field |
| `order` | string | `desc` | Sort order |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Hamburg Import GmbH",
      "slug": "hamburg-import",
      "type": "buyer",
      "status": "active",
      "member_count": 5,
      "created_at": "2026-01-05T10:30:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

---

### GET /organizations/{org_id}

Get organization details.

**Authorization:**
- VIBOTAJ system admins: Any organization
- Others: Only organizations they are members of

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Hamburg Import GmbH",
  "slug": "hamburg-import",
  "type": "buyer",
  "status": "active",
  "settings": {
    "default_currency": "EUR",
    "timezone": "Europe/Berlin",
    "notification_preferences": {
      "email_on_shipment_update": true,
      "email_on_document_upload": true
    },
    "compliance_settings": {
      "eudr_enabled": true,
      "auto_validate_documents": false
    }
  },
  "contact_email": "admin@hamburg-import.de",
  "contact_phone": "+49 40 123456",
  "address": {
    "street": "Speicherstadt 42",
    "city": "Hamburg",
    "postal_code": "20457",
    "country": "DE"
  },
  "tax_id": "DE123456789",
  "logo_url": null,
  "member_count": 5,
  "shipment_count": 23,
  "created_at": "2026-01-05T10:30:00Z",
  "updated_at": "2026-01-05T14:00:00Z"
}
```

---

### PATCH /organizations/{org_id}

Update organization details.

**Authorization:**
- VIBOTAJ system admins: Any organization
- Organization admins: Their own organization

**Request Body:** (all fields optional)

```json
{
  "name": "Hamburg Import GmbH - Updated",
  "contact_email": "new-admin@hamburg-import.de",
  "settings": {
    "notification_preferences": {
      "email_on_shipment_update": false
    }
  }
}
```

**Response:** `200 OK` - Returns updated organization

---

### DELETE /organizations/{org_id}

Soft-delete (suspend) an organization. Only VIBOTAJ system admins.

**Authorization:** `system_role == system_admin`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hard_delete` | bool | false | Permanently delete (requires confirmation) |

**Response:** `200 OK`

```json
{
  "message": "Organization suspended successfully",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "suspended"
}
```

---

### GET /organizations/{org_id}/shipments

List shipments for an organization (convenience endpoint).

**Authorization:** Member of organization with `shipments:list` permission

**Query Parameters:** Same as `/api/shipments`

**Response:** Same as `/api/shipments` but filtered by organization

---

### GET /organizations/{org_id}/stats

Get organization statistics and metrics.

**Authorization:** Member of organization

**Response:** `200 OK`

```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "period": "last_30_days",
  "shipments": {
    "total": 23,
    "in_transit": 5,
    "delivered": 15,
    "pending_docs": 3
  },
  "documents": {
    "total": 156,
    "pending_validation": 12,
    "compliance_ok": 134,
    "compliance_failed": 10
  },
  "compliance": {
    "eudr_compliant_shipments": 20,
    "eudr_pending_shipments": 3,
    "avg_document_completion": 0.92
  }
}
```

---

## Invitations API

### Base Path: `/api/v1/invitations`

---

### POST /invitations

Create and send an invitation to join an organization.

**Authorization:** Organization admin or manager

**Request Body:**

```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "new.member@example.com",
  "org_role": "member",
  "custom_message": "Welcome to our team! Please join our organization.",
  "redirect_url": "https://app.tracehub.vibotaj.com/onboarding"
}
```

**Response:** `201 Created`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_name": "Hamburg Import GmbH",
  "email": "new.member@example.com",
  "org_role": "member",
  "status": "pending",
  "invitation_url": "https://app.tracehub.vibotaj.com/invite/abc123xyz789...",
  "expires_at": "2026-01-12T10:30:00Z",
  "created_at": "2026-01-05T10:30:00Z"
}
```

**Token Generation:**

```python
# Token format: base64url(random_bytes(32))
# Stored as: SHA-256 hash
# Expiry: 7 days from creation
# Usage: Single-use (invalidated on acceptance)
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | `EMAIL_ALREADY_MEMBER` | User is already a member of this organization |
| 400 | `INVITATION_EXISTS` | Pending invitation already exists for this email |
| 403 | `CANNOT_INVITE_HIGHER_ROLE` | Cannot invite someone to a higher role than your own |

---

### GET /invitations

List invitations for organizations the user manages.

**Authorization:** Organization admin or manager

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `organization_id` | uuid | null | Filter by organization |
| `status` | string | null | Filter by status: `pending`, `accepted`, `expired`, `revoked` |
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "organization_id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_name": "Hamburg Import GmbH",
      "email": "new.member@example.com",
      "org_role": "member",
      "status": "pending",
      "expires_at": "2026-01-12T10:30:00Z",
      "created_at": "2026-01-05T10:30:00Z",
      "created_by_name": "Admin User"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

---

### GET /invitations/{invitation_id}

Get invitation details.

**Authorization:** Creator of invitation, organization admin, or the invitee

**Response:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_name": "Hamburg Import GmbH",
  "organization_type": "buyer",
  "email": "new.member@example.com",
  "org_role": "member",
  "status": "pending",
  "custom_message": "Welcome to our team!",
  "expires_at": "2026-01-12T10:30:00Z",
  "created_at": "2026-01-05T10:30:00Z",
  "created_by_name": "Admin User"
}
```

---

### POST /invitations/validate

Validate an invitation token (public endpoint for invitation landing page).

**Authorization:** None (public)

**Request Body:**

```json
{
  "token": "abc123xyz789..."
}
```

**Response:** `200 OK`

```json
{
  "valid": true,
  "invitation_id": "660e8400-e29b-41d4-a716-446655440001",
  "organization_name": "Hamburg Import GmbH",
  "organization_type": "buyer",
  "email": "new.member@example.com",
  "org_role": "member",
  "expires_at": "2026-01-12T10:30:00Z",
  "requires_registration": true,
  "custom_message": "Welcome to our team!"
}
```

**Error Response:** `400 Bad Request`

```json
{
  "valid": false,
  "error": "INVITATION_EXPIRED",
  "message": "This invitation has expired. Please request a new one."
}
```

---

### POST /invitations/accept

Accept an invitation and join the organization.

**Authorization:** Authenticated user (email must match invitation)

**Request Body:**

```json
{
  "token": "abc123xyz789..."
}
```

**Response:** `200 OK`

```json
{
  "message": "Successfully joined organization",
  "membership": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "user_id": "880e8400-e29b-41d4-a716-446655440003",
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "organization_name": "Hamburg Import GmbH",
    "org_role": "member",
    "joined_at": "2026-01-05T11:00:00Z"
  },
  "new_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | `INVITATION_EXPIRED` | Invitation has expired |
| 400 | `INVITATION_ALREADY_USED` | Invitation has already been accepted |
| 400 | `EMAIL_MISMATCH` | Authenticated user's email does not match invitation |
| 404 | `INVITATION_NOT_FOUND` | Invalid token |

---

### POST /invitations/{invitation_id}/resend

Resend invitation email with a new token.

**Authorization:** Organization admin or original inviter

**Response:** `200 OK`

```json
{
  "message": "Invitation resent successfully",
  "new_expires_at": "2026-01-12T11:00:00Z"
}
```

---

### DELETE /invitations/{invitation_id}

Revoke a pending invitation.

**Authorization:** Organization admin or original inviter

**Response:** `200 OK`

```json
{
  "message": "Invitation revoked",
  "id": "660e8400-e29b-41d4-a716-446655440001"
}
```

---

## Organization Membership API

### Base Path: `/api/v1/organizations/{org_id}/members`

---

### GET /organizations/{org_id}/members

List all members of an organization.

**Authorization:** Member of organization

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page |
| `role` | string | null | Filter by org_role |
| `status` | string | null | Filter by status |
| `search` | string | null | Search by name or email |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "user_id": "880e8400-e29b-41d4-a716-446655440003",
      "email": "john@hamburg-import.de",
      "full_name": "John Schmidt",
      "org_role": "admin",
      "status": "active",
      "is_primary": true,
      "joined_at": "2026-01-01T00:00:00Z",
      "last_active_at": "2026-01-05T09:00:00Z"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440004",
      "user_id": "880e8400-e29b-41d4-a716-446655440005",
      "email": "maria@hamburg-import.de",
      "full_name": "Maria Weber",
      "org_role": "member",
      "status": "active",
      "is_primary": true,
      "joined_at": "2026-01-03T10:00:00Z",
      "last_active_at": "2026-01-05T08:30:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

---

### POST /organizations/{org_id}/members

Add an existing user to the organization (for VIBOTAJ admins).

**Authorization:** VIBOTAJ system admin or organization admin

**Request Body:**

```json
{
  "user_id": "880e8400-e29b-41d4-a716-446655440003",
  "org_role": "member"
}
```

**Response:** `201 Created`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440006",
  "user_id": "880e8400-e29b-41d4-a716-446655440003",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_role": "member",
  "status": "active",
  "joined_at": "2026-01-05T11:30:00Z"
}
```

---

### GET /organizations/{org_id}/members/{member_id}

Get details of a specific membership.

**Authorization:** Member of organization

**Response:** `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "user_id": "880e8400-e29b-41d4-a716-446655440003",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "user": {
    "email": "john@hamburg-import.de",
    "full_name": "John Schmidt"
  },
  "org_role": "admin",
  "status": "active",
  "is_primary": true,
  "joined_at": "2026-01-01T00:00:00Z",
  "invited_by": null,
  "permissions": [
    "shipments:read",
    "shipments:create",
    "documents:read",
    "documents:upload",
    "members:manage"
  ]
}
```

---

### PATCH /organizations/{org_id}/members/{member_id}

Update a member's role or status.

**Authorization:** Organization admin (cannot modify self or higher roles)

**Request Body:**

```json
{
  "org_role": "manager",
  "status": "active"
}
```

**Response:** `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440004",
  "user_id": "880e8400-e29b-41d4-a716-446655440005",
  "org_role": "manager",
  "status": "active",
  "updated_at": "2026-01-05T12:00:00Z"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 403 | `CANNOT_MODIFY_SELF` | Cannot change your own role |
| 403 | `CANNOT_MODIFY_HIGHER_ROLE` | Cannot modify member with equal or higher role |
| 400 | `LAST_ADMIN` | Cannot demote the last admin |

---

### DELETE /organizations/{org_id}/members/{member_id}

Remove a member from the organization.

**Authorization:** Organization admin (cannot remove self)

**Response:** `200 OK`

```json
{
  "message": "Member removed from organization",
  "user_id": "880e8400-e29b-41d4-a716-446655440005"
}
```

---

### POST /organizations/{org_id}/members/{member_id}/suspend

Suspend a member's access.

**Authorization:** Organization admin

**Request Body:**

```json
{
  "reason": "Temporary access revocation pending review"
}
```

**Response:** `200 OK`

```json
{
  "message": "Member suspended",
  "member_id": "770e8400-e29b-41d4-a716-446655440004",
  "status": "suspended"
}
```

---

### POST /organizations/{org_id}/members/{member_id}/reactivate

Reactivate a suspended member.

**Authorization:** Organization admin

**Response:** `200 OK`

```json
{
  "message": "Member reactivated",
  "member_id": "770e8400-e29b-41d4-a716-446655440004",
  "status": "active"
}
```

---

## Session Management API

### Base Path: `/api/v1/session`

---

### GET /session/organizations

Get all organizations the current user belongs to.

**Authorization:** Authenticated user

**Response:** `200 OK`

```json
{
  "user_id": "880e8400-e29b-41d4-a716-446655440003",
  "current_organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "organizations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Hamburg Import GmbH",
      "slug": "hamburg-import",
      "type": "buyer",
      "org_role": "admin",
      "is_primary": true,
      "is_current": true
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "name": "VIBOTAJ",
      "slug": "vibotaj",
      "type": "vibotaj",
      "org_role": "member",
      "is_primary": false,
      "is_current": false
    }
  ]
}
```

---

### POST /session/switch-org

Switch the active organization context. Returns a new JWT with updated claims.

**Authorization:** Authenticated user (must be member of target organization)

**Request Body:**

```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440010"
}
```

**Response:** `200 OK`

```json
{
  "message": "Organization context switched",
  "organization": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "name": "VIBOTAJ",
    "type": "vibotaj"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "permissions": [
    "shipments:read",
    "shipments:create",
    "documents:read",
    "documents:upload"
  ]
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 403 | `NOT_A_MEMBER` | User is not a member of the target organization |
| 403 | `MEMBERSHIP_SUSPENDED` | User's membership in target organization is suspended |

---

### POST /session/set-primary

Set the user's primary/default organization.

**Authorization:** Authenticated user (must be member of target organization)

**Request Body:**

```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:** `200 OK`

```json
{
  "message": "Primary organization updated",
  "primary_organization_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### GET /session/context

Get full session context including user, organization, and permissions.

**Authorization:** Authenticated user

**Response:** `200 OK`

```json
{
  "user": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "email": "john@hamburg-import.de",
    "full_name": "John Schmidt",
    "system_role": "user"
  },
  "organization": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Hamburg Import GmbH",
    "slug": "hamburg-import",
    "type": "buyer"
  },
  "membership": {
    "org_role": "admin",
    "is_primary": true,
    "joined_at": "2026-01-01T00:00:00Z"
  },
  "permissions": [
    "shipments:read",
    "shipments:create",
    "shipments:update",
    "documents:read",
    "documents:upload",
    "documents:validate",
    "members:manage",
    "invitations:create"
  ],
  "can_switch_organizations": true,
  "organization_count": 2
}
```

---

## Updated Authentication Flow

### POST /auth/login (Updated)

Login now returns organization context.

**Request Body:**

```json
{
  "username": "john@hamburg-import.de",
  "password": "securePassword123"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "email": "john@hamburg-import.de",
    "full_name": "John Schmidt"
  },
  "organization": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Hamburg Import GmbH",
    "type": "buyer"
  },
  "organizations_count": 2,
  "permissions": ["shipments:read", "documents:upload"]
}
```

### POST /auth/register (Updated for Invitation Flow)

Register with an invitation token.

**Request Body:**

```json
{
  "email": "new.member@example.com",
  "password": "securePassword123",
  "full_name": "New Member",
  "invitation_token": "abc123xyz789..."
}
```

**Response:** `201 Created`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "880e8400-e29b-41d4-a716-446655440009",
    "email": "new.member@example.com",
    "full_name": "New Member"
  },
  "organization": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Hamburg Import GmbH",
    "type": "buyer"
  },
  "membership": {
    "org_role": "member",
    "joined_at": "2026-01-05T12:00:00Z"
  }
}
```

---

## Permission Scoping

### Organization-Scoped Permissions

All data operations are scoped by the current organization in the JWT:

```python
# Example middleware logic
def get_organization_filter(current_user: CurrentUser):
    if current_user.system_role == "system_admin":
        return None  # No filter - can see all
    return {"organization_id": current_user.org_id}
```

### Shipment Access Rules

| User Type | Access |
|-----------|--------|
| VIBOTAJ system_admin | All shipments |
| VIBOTAJ member | Shipments where VIBOTAJ is supplier |
| Buyer organization | Shipments where organization is buyer |
| Supplier organization | Shipments where organization is supplier |
| Logistics agent | Shipments assigned to the agent |

### Document Access Rules

| Permission | Conditions |
|------------|------------|
| `document.view` | `document.shipment.organization_id == user.org_id` OR `system_role == system_admin` |
| `document.approve` | org_type in [`vibotaj`, `buyer`] AND `org_role` in [`admin`, `manager`] |
| `document.upload` | `org_role` in [`admin`, `manager`, `member`] AND shipment belongs to org |

### Organization Role Permissions

```json
{
  "admin": [
    "members:manage",
    "members:invite",
    "settings:manage",
    "shipments:*",
    "documents:*"
  ],
  "manager": [
    "members:invite",
    "shipments:read",
    "shipments:update",
    "documents:*"
  ],
  "member": [
    "shipments:read",
    "documents:read",
    "documents:upload"
  ],
  "viewer": [
    "shipments:read",
    "documents:read"
  ]
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "request_id": "req_abc123"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_A_MEMBER` | 403 | User is not a member of the organization |
| `MEMBERSHIP_SUSPENDED` | 403 | User's membership is suspended |
| `ORG_NOT_FOUND` | 404 | Organization not found |
| `MEMBER_NOT_FOUND` | 404 | Member not found |
| `INVITATION_NOT_FOUND` | 404 | Invitation not found |
| `INVITATION_EXPIRED` | 400 | Invitation has expired |
| `INVITATION_ALREADY_USED` | 400 | Invitation already accepted |
| `EMAIL_MISMATCH` | 400 | Email does not match invitation |
| `EMAIL_ALREADY_MEMBER` | 400 | User is already a member |
| `ORG_SLUG_EXISTS` | 400 | Organization slug already taken |
| `LAST_ADMIN` | 400 | Cannot remove/demote last admin |
| `CANNOT_MODIFY_SELF` | 400 | Cannot modify own role |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limiting

### Limits by Endpoint Category

| Category | Limit | Window |
|----------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Invitation creation | 20 requests | 1 hour |
| Invitation validation | 30 requests | 1 minute |
| Organization CRUD | 100 requests | 1 minute |
| Member management | 50 requests | 1 minute |
| Session operations | 60 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704499200
Retry-After: 60
```

### Rate Limit Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "limit": 100,
      "window": "1 minute",
      "retry_after": 60
    }
  }
}
```

---

## Migration Strategy

### Phase 1: Schema Migration

1. Create `organizations` table
2. Create `organization_memberships` table
3. Create `invitations` table
4. Add `organization_id` to `shipments`, `documents`, `parties`

### Phase 2: Data Migration

1. Create default VIBOTAJ organization
2. Assign all existing users to VIBOTAJ organization
3. Create buyer/supplier organizations from existing parties
4. Link shipments to appropriate organizations

### Phase 3: API Migration

1. Deploy new endpoints alongside existing ones
2. Update JWT token structure with backward compatibility
3. Add organization context to all data queries
4. Deprecate non-scoped endpoints

### Phase 4: Frontend Migration

1. Update authentication flow to handle organization context
2. Add organization switcher component
3. Update all API calls to use scoped endpoints
4. Implement invitation acceptance flow

### Backward Compatibility

During migration, the API will support both old and new JWT formats:

```python
def get_organization_from_token(token_payload: dict) -> UUID:
    # New format
    if "org_id" in token_payload:
        return UUID(token_payload["org_id"])

    # Legacy format - assume VIBOTAJ organization
    return DEFAULT_VIBOTAJ_ORG_ID
```

---

## Appendix: OpenAPI Schema Snippets

### Organization Schema

```yaml
Organization:
  type: object
  required:
    - id
    - name
    - slug
    - type
    - status
  properties:
    id:
      type: string
      format: uuid
    name:
      type: string
      minLength: 2
      maxLength: 255
    slug:
      type: string
      pattern: ^[a-z0-9-]+$
      minLength: 2
      maxLength: 50
    type:
      $ref: '#/components/schemas/OrganizationType'
    status:
      type: string
      enum: [active, suspended, pending_setup]
    settings:
      $ref: '#/components/schemas/OrganizationSettings'
    contact_email:
      type: string
      format: email
    created_at:
      type: string
      format: date-time
```

### Invitation Schema

```yaml
Invitation:
  type: object
  required:
    - id
    - organization_id
    - email
    - org_role
    - status
    - expires_at
  properties:
    id:
      type: string
      format: uuid
    organization_id:
      type: string
      format: uuid
    email:
      type: string
      format: email
    org_role:
      type: string
      enum: [admin, manager, member, viewer]
    status:
      type: string
      enum: [pending, accepted, expired, revoked]
    expires_at:
      type: string
      format: date-time
    created_at:
      type: string
      format: date-time
```

### Membership Schema

```yaml
OrganizationMembership:
  type: object
  required:
    - id
    - user_id
    - organization_id
    - org_role
    - status
  properties:
    id:
      type: string
      format: uuid
    user_id:
      type: string
      format: uuid
    organization_id:
      type: string
      format: uuid
    org_role:
      type: string
      enum: [admin, manager, member, viewer]
    status:
      type: string
      enum: [active, suspended, pending]
    is_primary:
      type: boolean
    joined_at:
      type: string
      format: date-time
```

---

**End of Specification**
