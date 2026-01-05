# ADR-008: Multi-Tenancy Architecture for TraceHub

**Status:** Proposed
**Date:** 2026-01-05
**Sprint:** Sprint 8 - Multi-Organization Isolation
**Decision Makers:** Architecture Team, Security Lead
**Technical Story:** Enable VIBOTAJ to operate as super-admin while supporting multiple buyer organizations with strict data isolation

---

## Table of Contents

1. [Context](#1-context)
2. [Decision Drivers](#2-decision-drivers)
3. [Architecture Options Evaluation](#3-architecture-options-evaluation)
4. [Decision: Option A - Shared Schema with PostgreSQL RLS](#4-decision-option-a---shared-schema-with-postgresql-rls)
5. [Defense-in-Depth Security Model](#5-defense-in-depth-security-model)
6. [Data Model Design](#6-data-model-design)
7. [PostgreSQL RLS Policy Design](#7-postgresql-rls-policy-design)
8. [VIBOTAJ Super-Admin Bypass Mechanism](#8-vibotaj-super-admin-bypass-mechanism)
9. [Invitation-Based Registration System](#9-invitation-based-registration-system)
10. [Threat Model](#10-threat-model)
11. [Migration Strategy](#11-migration-strategy)
12. [Consequences](#12-consequences)

---

## 1. Context

TraceHub is evolving from a single-tenant container tracking and documentation compliance platform to a multi-organization system. The current state includes:

**Current Architecture:**
- Single PostgreSQL database (no tenant isolation)
- 6 user roles: admin, compliance, logistics_agent, buyer, supplier, viewer
- JWT-based authentication with role in token payload
- Existing tables: users, shipments, documents, products, parties, origins, container_events, notifications, audit_logs, document_contents, reference_registry

**Business Requirements:**
- VIBOTAJ operates as the platform owner (super-admin)
- German buyers and African suppliers need isolated views of their data
- Historical shipments must be linked to correct buyer accounts
- Future SaaS model requires clean tenant boundaries
- EUDR compliance requires audit-ready organization-scoped records

**Non-Negotiable Outcomes:**
1. Zero cross-organization data access
2. Invitation-based self-service registration (7-day expiry, single-use)
3. Server-side role enforcement (UI reflects, never defines security)
4. Audit logs with organization context
5. Historical shipments linked to buyer accounts

---

## 2. Decision Drivers

| Driver | Weight | Description |
|--------|--------|-------------|
| Security | Critical | Zero tolerance for cross-tenant data leakage |
| Operational Simplicity | High | Single database to manage, backup, monitor |
| Query Performance | High | No additional joins or complexity for tenant filtering |
| Migration Risk | High | Existing data must be preserved and correctly assigned |
| Future Scalability | Medium | Support 50-100 organizations in SaaS phase |
| Development Velocity | Medium | Minimal changes to existing query patterns |
| Cost Efficiency | Medium | Shared infrastructure reduces per-tenant overhead |

---

## 3. Architecture Options Evaluation

### Option A: Single DB, Shared Schema + organization_id + PostgreSQL RLS (RECOMMENDED)

**Description:** All tenants share one database and schema. Each table has an `organization_id` column. PostgreSQL Row-Level Security (RLS) enforces isolation at the database layer.

```
+------------------+
|   PostgreSQL     |
|  +------------+  |
|  | shipments  |  |  <-- RLS Policy: current_setting('app.organization_id')
|  | org_id=1   |  |
|  | org_id=2   |  |
|  | org_id=3   |  |
|  +------------+  |
+------------------+
```

**Pros:**
- Database-enforced isolation (defense in depth)
- Single schema to maintain
- Efficient queries with proper indexing
- Easy cross-tenant analytics for super-admin
- Lower operational overhead

**Cons:**
- Requires careful RLS policy design
- All queries must set session context
- Noisy neighbor risk (mitigated by connection pooling)

**Verdict:** Best balance of security, simplicity, and scalability.

---

### Option B: Single DB, App-Level Tenant Scoping (No RLS)

**Description:** Application code adds `WHERE organization_id = ?` to every query. No database-level enforcement.

```python
# Every query manually filtered
def get_shipments(db, org_id):
    return db.query(Shipment).filter(Shipment.organization_id == org_id).all()
```

**Pros:**
- Simple to implement initially
- No RLS complexity
- Works with any database

**Cons:**
- Single point of failure (one missed filter = data leak)
- No defense in depth
- Audit burden on every code change
- Security reviews required for every query

**Verdict:** REJECTED - Unacceptable security risk for compliance-focused platform.

---

### Option C: Schema-per-Tenant

**Description:** Each organization gets a separate PostgreSQL schema within the same database.

```
+------------------+
|   PostgreSQL     |
|  +------------+  |
|  | org_1      |  |  <-- schema
|  |  shipments |  |
|  +------------+  |
|  +------------+  |
|  | org_2      |  |  <-- schema
|  |  shipments |  |
|  +------------+  |
+------------------+
```

**Pros:**
- Strong logical isolation
- Easy per-tenant backup/restore
- No RLS complexity

**Cons:**
- Schema migration complexity (N schemas to update)
- Connection pool per schema
- Cross-tenant queries require UNION across schemas
- Operational overhead scales with tenant count

**Verdict:** REJECTED - Operational complexity too high for expected scale.

---

### Option D: Database-per-Tenant

**Description:** Each organization gets a completely separate database.

**Pros:**
- Strongest isolation
- Easy compliance with data residency requirements
- Independent scaling per tenant

**Cons:**
- Highest operational overhead
- Expensive for small tenants
- Cross-tenant analytics requires federation
- Connection management complexity

**Verdict:** REJECTED - Overkill for current scale; consider for enterprise tier later.

---

## 4. Decision: Option A - Shared Schema with PostgreSQL RLS

We will implement **Single Database, Shared Schema with organization_id and PostgreSQL Row-Level Security**.

**Rationale:**
1. **Defense in Depth:** RLS provides database-level isolation even if application code has bugs
2. **Operational Simplicity:** One database to backup, monitor, and maintain
3. **Query Efficiency:** Single table scans with index on organization_id
4. **Audit Compliance:** All actions traceable to organization context
5. **Migration Safety:** Existing data can be assigned to organizations incrementally
6. **Future SaaS Ready:** Architecture supports 100+ organizations efficiently

---

## 5. Defense-in-Depth Security Model

### Four-Layer Security Architecture

```
+-----------------------------------------------------------------------+
|                        LAYER 4: AUDIT & MONITORING                    |
|   - All actions logged with organization context                      |
|   - Anomaly detection for cross-tenant access attempts                |
|   - Compliance reporting per organization                             |
+-----------------------------------------------------------------------+
                                    |
+-----------------------------------------------------------------------+
|                        LAYER 3: DATABASE (RLS)                        |
|   - PostgreSQL Row-Level Security policies                            |
|   - Session variable: app.organization_id                             |
|   - Policies ON by default, PERMISSIVE for super-admin                |
+-----------------------------------------------------------------------+
                                    |
+-----------------------------------------------------------------------+
|                        LAYER 2: APPLICATION                           |
|   - Middleware extracts organization from JWT                         |
|   - Sets PostgreSQL session variable before queries                   |
|   - All queries implicitly scoped by RLS                              |
|   - Additional application-level validation for edge cases            |
+-----------------------------------------------------------------------+
                                    |
+-----------------------------------------------------------------------+
|                        LAYER 1: API GATEWAY                           |
|   - JWT validation and extraction                                     |
|   - Rate limiting per organization                                    |
|   - Request logging with correlation IDs                              |
|   - IP allowlisting (optional per org)                                |
+-----------------------------------------------------------------------+
```

### Layer Implementation Details

#### Layer 1: API Gateway / FastAPI Middleware

```python
# /app/middleware/tenant_context.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt
from ..config import get_settings

class TenantContextMiddleware(BaseHTTPMiddleware):
    """Extract organization context from JWT and attach to request state."""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        # Skip for auth endpoints
        if request.url.path.startswith("/api/auth"):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, settings.jwt_secret,
                                    algorithms=[settings.jwt_algorithm])
                request.state.organization_id = payload.get("organization_id")
                request.state.user_id = payload.get("sub")
                request.state.is_super_admin = payload.get("is_super_admin", False)
            except Exception:
                pass

        response = await call_next(request)
        return response
```

#### Layer 2: Database Session with Tenant Context

```python
# /app/database.py - Enhanced with tenant context

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

def set_tenant_context(session: Session, organization_id: str, is_super_admin: bool = False):
    """Set PostgreSQL session variables for RLS."""
    if is_super_admin:
        # Super-admin bypasses RLS
        session.execute(text("SET app.bypass_rls = 'true'"))
        session.execute(text("SET app.organization_id = ''"))
    else:
        session.execute(text("SET app.bypass_rls = 'false'"))
        session.execute(text(f"SET app.organization_id = '{organization_id}'"))

@contextmanager
def get_tenant_db(organization_id: str, is_super_admin: bool = False):
    """Get database session with tenant context set."""
    db = SessionLocal()
    try:
        set_tenant_context(db, organization_id, is_super_admin)
        yield db
    finally:
        db.close()
```

#### Layer 3: PostgreSQL RLS Policies

See Section 7 for complete RLS policy definitions.

#### Layer 4: Audit Logging with Organization Context

```python
# /app/services/audit_log.py - Enhanced

async def log_action(
    db: Session,
    action: str,
    user_id: str,
    organization_id: str,  # NEW: Required field
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    request: Request = None
):
    """Log action with mandatory organization context."""
    audit_entry = AuditLog(
        user_id=user_id,
        organization_id=organization_id,  # NEW
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        timestamp=datetime.utcnow()
    )
    db.add(audit_entry)
    db.commit()
```

---

## 6. Data Model Design

### New Entity: Organizations

```
+-------------------+
|   organizations   |
+-------------------+
| id (UUID, PK)     |
| name              |
| slug (unique)     |
| type (enum)       |  -- 'platform_owner', 'buyer', 'supplier'
| is_active         |
| settings (JSONB)  |
| created_at        |
| updated_at        |
+-------------------+
```

### Entity Relationship Diagram

```
                                    +-------------------+
                                    |   organizations   |
                                    +-------------------+
                                    | id (PK)           |
                                    | name              |
                                    | slug              |
                                    | type              |
                                    +-------------------+
                                              |
                                              | 1
                                              |
              +-------------------------------+-------------------------------+
              |                               |                               |
              | *                             | *                             | *
    +-------------------+           +-------------------+           +-------------------+
    |      users        |           |    shipments      |           |     parties       |
    +-------------------+           +-------------------+           +-------------------+
    | id (PK)           |           | id (PK)           |           | id (PK)           |
    | organization_id   |--+        | organization_id   |--+        | organization_id   |--+
    | email             |  |        | reference         |  |        | company_name      |  |
    | role              |  |        | container_number  |  |        | type              |  |
    | party_id (FK)     |--|------->| buyer_id (FK)     |--|------->| ...               |  |
    +-------------------+  |        | supplier_id (FK)  |  |        +-------------------+  |
                           |        +-------------------+  |                               |
                           |                  |            |                               |
                           |                  | 1          |                               |
                           |                  |            |                               |
                           |     +------------+------------+------------+                  |
                           |     |            |            |            |                  |
                           |     | *          | *          | *          | *                |
                           |  +--------+  +--------+  +--------+  +-------------+          |
                           |  |products|  |documents|  |origins |  |container_   |          |
                           |  +--------+  +--------+  +--------+  |events       |          |
                           |  |org_id  |  |org_id  |  |org_id  |  +-------------+          |
                           |  +--------+  +--------+  +--------+  |org_id       |          |
                           |                                      +-------------+          |
                           |                                                               |
                           +---------------------------------------------------------------+
                                        All entities linked to organization_id
```

### Tables Requiring organization_id Addition

| Table | Current State | Migration Strategy |
|-------|---------------|-------------------|
| users | No org_id | Add column, assign to VIBOTAJ initially |
| shipments | No org_id | Derive from buyer_id -> party -> organization |
| documents | No org_id | Inherit from shipment.organization_id |
| products | No org_id | Inherit from shipment.organization_id |
| parties | No org_id | Add column, map existing buyers/suppliers |
| origins | No org_id | Inherit from product.shipment.organization_id |
| container_events | No org_id | Inherit from shipment.organization_id |
| notifications | No org_id | Add column, derive from user.organization_id |
| audit_logs | No org_id | Add column (critical for compliance) |
| document_contents | No org_id | Inherit from document.organization_id |
| reference_registry | No org_id | Inherit from shipment.organization_id |

### New Table: Invitations

```sql
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'viewer',
    token VARCHAR(64) NOT NULL UNIQUE,  -- Cryptographically random
    invited_by UUID NOT NULL REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,  -- 7 days from creation
    used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT token_not_reused CHECK (used_at IS NULL OR used_at <= CURRENT_TIMESTAMP)
);

CREATE INDEX idx_invitations_token ON invitations(token) WHERE used_at IS NULL;
CREATE INDEX idx_invitations_email ON invitations(email);
CREATE INDEX idx_invitations_org ON invitations(organization_id);
```

---

## 7. PostgreSQL RLS Policy Design

### Enable RLS on All Tenant Tables

```sql
-- Migration: 002_add_multi_tenancy.sql

-- 1. Add organization_id to all tables
ALTER TABLE users ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE shipments ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE documents ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE products ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE parties ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE origins ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE container_events ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE notifications ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE audit_logs ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE document_contents ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE reference_registry ADD COLUMN organization_id UUID REFERENCES organizations(id);

-- 2. Create indexes for performance
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_shipments_org ON shipments(organization_id);
CREATE INDEX idx_documents_org ON documents(organization_id);
CREATE INDEX idx_products_org ON products(organization_id);
CREATE INDEX idx_parties_org ON parties(organization_id);
CREATE INDEX idx_origins_org ON origins(organization_id);
CREATE INDEX idx_container_events_org ON container_events(organization_id);
CREATE INDEX idx_notifications_org ON notifications(organization_id);
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_document_contents_org ON document_contents(organization_id);
CREATE INDEX idx_reference_registry_org ON reference_registry(organization_id);

-- 3. Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE parties ENABLE ROW LEVEL SECURITY;
ALTER TABLE origins ENABLE ROW LEVEL SECURITY;
ALTER TABLE container_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE reference_registry ENABLE ROW LEVEL SECURITY;

-- 4. Force RLS for table owner (critical security)
ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE shipments FORCE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;
ALTER TABLE parties FORCE ROW LEVEL SECURITY;
ALTER TABLE origins FORCE ROW LEVEL SECURITY;
ALTER TABLE container_events FORCE ROW LEVEL SECURITY;
ALTER TABLE notifications FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE document_contents FORCE ROW LEVEL SECURITY;
ALTER TABLE reference_registry FORCE ROW LEVEL SECURITY;
```

### RLS Policy Definitions

```sql
-- ============================================================
-- RLS POLICIES: Core pattern for all tenant tables
-- ============================================================

-- Helper function to check if current session is super-admin
CREATE OR REPLACE FUNCTION is_super_admin() RETURNS BOOLEAN AS $$
BEGIN
    RETURN COALESCE(current_setting('app.bypass_rls', true), 'false') = 'true';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Helper function to get current organization
CREATE OR REPLACE FUNCTION current_organization_id() RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.organization_id', true), '')::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- SHIPMENTS TABLE POLICIES
-- ============================================================

-- SELECT: Users can only see shipments in their organization
CREATE POLICY shipments_select_policy ON shipments
    FOR SELECT
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- INSERT: Users can only create shipments in their organization
CREATE POLICY shipments_insert_policy ON shipments
    FOR INSERT
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- UPDATE: Users can only update shipments in their organization
CREATE POLICY shipments_update_policy ON shipments
    FOR UPDATE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- DELETE: Users can only delete shipments in their organization
CREATE POLICY shipments_delete_policy ON shipments
    FOR DELETE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- ============================================================
-- USERS TABLE POLICIES
-- ============================================================

-- SELECT: Users can see other users in their organization
CREATE POLICY users_select_policy ON users
    FOR SELECT
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- INSERT: Only super-admin can create users (invitations handled separately)
CREATE POLICY users_insert_policy ON users
    FOR INSERT
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- UPDATE: Users can only update users in their organization
CREATE POLICY users_update_policy ON users
    FOR UPDATE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- DELETE: Users can only delete users in their organization
CREATE POLICY users_delete_policy ON users
    FOR DELETE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- ============================================================
-- DOCUMENTS TABLE POLICIES
-- ============================================================

CREATE POLICY documents_select_policy ON documents
    FOR SELECT
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

CREATE POLICY documents_insert_policy ON documents
    FOR INSERT
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

CREATE POLICY documents_update_policy ON documents
    FOR UPDATE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

CREATE POLICY documents_delete_policy ON documents
    FOR DELETE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- ============================================================
-- PARTIES TABLE POLICIES (Special: Cross-org visibility for trades)
-- ============================================================

-- Parties may need cross-org visibility for buyer/supplier relationships
CREATE POLICY parties_select_policy ON parties
    FOR SELECT
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
        -- Allow seeing parties involved in shared shipments
        OR id IN (
            SELECT buyer_id FROM shipments
            WHERE organization_id = current_organization_id()
            UNION
            SELECT supplier_id FROM shipments
            WHERE organization_id = current_organization_id()
        )
    );

CREATE POLICY parties_insert_policy ON parties
    FOR INSERT
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

CREATE POLICY parties_update_policy ON parties
    FOR UPDATE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

CREATE POLICY parties_delete_policy ON parties
    FOR DELETE
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- ============================================================
-- AUDIT_LOGS TABLE POLICIES (Special: Append-only for non-admin)
-- ============================================================

-- SELECT: Users can only see audit logs for their organization
CREATE POLICY audit_logs_select_policy ON audit_logs
    FOR SELECT
    USING (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- INSERT: Anyone can create audit logs (for their organization)
CREATE POLICY audit_logs_insert_policy ON audit_logs
    FOR INSERT
    WITH CHECK (
        is_super_admin()
        OR organization_id = current_organization_id()
    );

-- UPDATE: Only super-admin can update audit logs (immutability)
CREATE POLICY audit_logs_update_policy ON audit_logs
    FOR UPDATE
    USING (is_super_admin());

-- DELETE: Only super-admin can delete audit logs (immutability)
CREATE POLICY audit_logs_delete_policy ON audit_logs
    FOR DELETE
    USING (is_super_admin());

-- ============================================================
-- Apply similar policies to remaining tables
-- ============================================================

-- PRODUCTS
CREATE POLICY products_select_policy ON products FOR SELECT
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY products_insert_policy ON products FOR INSERT
    WITH CHECK (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY products_update_policy ON products FOR UPDATE
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY products_delete_policy ON products FOR DELETE
    USING (is_super_admin() OR organization_id = current_organization_id());

-- ORIGINS
CREATE POLICY origins_select_policy ON origins FOR SELECT
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY origins_insert_policy ON origins FOR INSERT
    WITH CHECK (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY origins_update_policy ON origins FOR UPDATE
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY origins_delete_policy ON origins FOR DELETE
    USING (is_super_admin() OR organization_id = current_organization_id());

-- CONTAINER_EVENTS
CREATE POLICY container_events_select_policy ON container_events FOR SELECT
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY container_events_insert_policy ON container_events FOR INSERT
    WITH CHECK (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY container_events_update_policy ON container_events FOR UPDATE
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY container_events_delete_policy ON container_events FOR DELETE
    USING (is_super_admin() OR organization_id = current_organization_id());

-- NOTIFICATIONS
CREATE POLICY notifications_select_policy ON notifications FOR SELECT
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY notifications_insert_policy ON notifications FOR INSERT
    WITH CHECK (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY notifications_update_policy ON notifications FOR UPDATE
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY notifications_delete_policy ON notifications FOR DELETE
    USING (is_super_admin() OR organization_id = current_organization_id());

-- DOCUMENT_CONTENTS
CREATE POLICY document_contents_select_policy ON document_contents FOR SELECT
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY document_contents_insert_policy ON document_contents FOR INSERT
    WITH CHECK (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY document_contents_update_policy ON document_contents FOR UPDATE
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY document_contents_delete_policy ON document_contents FOR DELETE
    USING (is_super_admin() OR organization_id = current_organization_id());

-- REFERENCE_REGISTRY
CREATE POLICY reference_registry_select_policy ON reference_registry FOR SELECT
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY reference_registry_insert_policy ON reference_registry FOR INSERT
    WITH CHECK (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY reference_registry_update_policy ON reference_registry FOR UPDATE
    USING (is_super_admin() OR organization_id = current_organization_id());
CREATE POLICY reference_registry_delete_policy ON reference_registry FOR DELETE
    USING (is_super_admin() OR organization_id = current_organization_id());
```

---

## 8. VIBOTAJ Super-Admin Bypass Mechanism

### Design Principles

1. **Explicit Activation:** Super-admin mode must be explicitly requested, not default
2. **Audit Trail:** All super-admin actions are logged with elevated privilege marker
3. **Time-Limited Sessions:** Super-admin bypass should have shorter token expiry
4. **Minimal Scope:** Prefer organization switching over global bypass when possible

### Implementation

#### Organization Model Enhancement

```python
# /app/models/organization.py

class OrganizationType(str, enum.Enum):
    """Types of organizations."""
    PLATFORM_OWNER = "platform_owner"  # VIBOTAJ
    BUYER = "buyer"
    SUPPLIER = "supplier"
    PARTNER = "partner"

class Organization(Base):
    """Organization entity for multi-tenancy."""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)  # URL-safe identifier
    type = Column(Enum(OrganizationType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Settings (JSONB for flexibility)
    settings = Column(JSONB, default={})
    # Example settings:
    # {
    #   "allowed_document_types": [...],
    #   "eudr_required": true,
    #   "notification_preferences": {...}
    # }

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization")
    shipments = relationship("Shipment", back_populates="organization")
```

#### User Model Enhancement

```python
# /app/models/user.py - Enhanced

class User(Base):
    """User entity with organization context."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Super-admin flag (only for PLATFORM_OWNER org users)
    is_super_admin = Column(Boolean, default=False, nullable=False)

    # Optional link to party (for buyer/supplier users)
    party_id = Column(UUID(as_uuid=True), ForeignKey("parties.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    party = relationship("Party")
```

#### JWT Token Enhancement

```python
# /app/routers/auth.py - Enhanced token creation

def create_access_token(user: User, mode: str = "normal") -> str:
    """
    Create JWT token with organization context.

    Args:
        user: User model instance
        mode: "normal" or "super_admin" (only for platform owner users)
    """
    settings = get_settings()

    # Determine if super-admin mode is allowed and requested
    can_be_super_admin = (
        user.is_super_admin and
        user.organization.type == OrganizationType.PLATFORM_OWNER
    )
    is_super_admin = mode == "super_admin" and can_be_super_admin

    # Super-admin tokens have shorter expiry (1 hour vs 8 hours)
    expiry_hours = 1 if is_super_admin else settings.jwt_expiration_hours
    expire = datetime.utcnow() + timedelta(hours=expiry_hours)

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "organization_id": str(user.organization_id),
        "is_super_admin": is_super_admin,
        "exp": expire
    }

    return jwt.encode(token_data, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    mode: str = Query("normal", regex="^(normal|super_admin)$"),
    db: Session = Depends(get_db)
):
    """Login endpoint with optional super-admin mode."""
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Validate super-admin mode request
    if mode == "super_admin":
        if not user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not authorized for super-admin mode"
            )
        if user.organization.type != OrganizationType.PLATFORM_OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super-admin mode only available for platform owner"
            )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(user, mode=mode)
    return Token(access_token=access_token, token_type="bearer")
```

#### Organization Switching (Preferred over Global Bypass)

```python
@router.post("/switch-organization/{org_id}", response_model=Token)
async def switch_organization(
    org_id: UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Super-admin can switch to view data as a specific organization.
    Creates a new token scoped to the target organization.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super-admins can switch organizations"
        )

    # Verify target organization exists
    target_org = db.query(Organization).filter(Organization.id == org_id).first()
    if not target_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Create token with switched context (not super-admin in new context)
    settings = get_settings()
    token_data = {
        "sub": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role.value,
        "organization_id": str(org_id),
        "original_organization_id": str(current_user.organization_id),  # Audit trail
        "is_super_admin": False,  # Normal privileges in switched context
        "is_switched": True,  # Flag for audit
        "exp": datetime.utcnow() + timedelta(hours=1)  # Short expiry
    }

    access_token = jwt.encode(token_data, settings.jwt_secret,
                              algorithm=settings.jwt_algorithm)

    # Audit log
    await log_action(
        db=db,
        action="organization.switch",
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        resource_type="organization",
        resource_id=str(org_id),
        details={"target_org_name": target_org.name}
    )

    return Token(access_token=access_token, token_type="bearer")
```

---

## 9. Invitation-Based Registration System

### Invitation Flow

```
+-------------+     1. Create Invitation     +-------------+
|   Admin     | --------------------------> |  Database   |
|  (Org A)    |                             | (invitation)|
+-------------+                             +-------------+
                                                   |
                                                   | 2. Email sent
                                                   v
                                            +-------------+
                                            |   Email     |
                                            |  Service    |
                                            +-------------+
                                                   |
                                                   | 3. User clicks link
                                                   v
                                            +-------------+
                                            |  New User   |
                                            | Registration|
                                            +-------------+
                                                   |
                                                   | 4. Validate token
                                                   | 5. Create user
                                                   | 6. Mark invitation used
                                                   v
                                            +-------------+
                                            |   User      |
                                            | (in Org A)  |
                                            +-------------+
```

### Invitation Model

```python
# /app/models/invitation.py

class Invitation(Base):
    """Invitation for user registration."""

    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization")
    inviter = relationship("User")

    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid."""
        return (
            self.used_at is None and
            self.expires_at > datetime.utcnow()
        )

    @staticmethod
    def generate_token() -> str:
        """Generate cryptographically secure token."""
        import secrets
        return secrets.token_urlsafe(48)
```

### Invitation API Endpoints

```python
# /app/routers/invitations.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import datetime, timedelta
from ..models.invitation import Invitation
from ..models.user import User, UserRole
from ..services.email import send_invitation_email

router = APIRouter()

class InvitationCreate(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER

class InvitationResponse(BaseModel):
    id: UUID
    email: str
    role: str
    expires_at: datetime
    invitation_url: str

class RegistrationRequest(BaseModel):
    token: str
    full_name: str
    password: str


@router.post("/invite", response_model=InvitationResponse)
async def create_invitation(
    invitation_data: InvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create invitation for a new user (org admin only)."""

    # Permission check: must be admin or have user management permission
    if not has_permission(current_user.role, Permission.USERS_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invite users"
        )

    # Role hierarchy check: can't invite higher roles
    if not can_manage_role(current_user.role, invitation_data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot invite user with role {invitation_data.role.value}"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invitation_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Check for pending invitation
    pending = db.query(Invitation).filter(
        Invitation.email == invitation_data.email,
        Invitation.organization_id == current_user.organization_id,
        Invitation.used_at.is_(None),
        Invitation.expires_at > datetime.utcnow()
    ).first()

    if pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pending invitation already exists for this email"
        )

    # Create invitation
    invitation = Invitation(
        organization_id=current_user.organization_id,
        email=invitation_data.email,
        role=invitation_data.role,
        token=Invitation.generate_token(),
        invited_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Send email in background
    invitation_url = f"{settings.frontend_url}/register?token={invitation.token}"
    background_tasks.add_task(
        send_invitation_email,
        email=invitation.email,
        invitation_url=invitation_url,
        inviter_name=current_user.full_name,
        organization_name=current_user.organization.name
    )

    # Audit log
    await log_action(
        db=db,
        action="invitation.create",
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        resource_type="invitation",
        resource_id=str(invitation.id),
        details={"invited_email": invitation.email, "role": invitation.role.value}
    )

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role.value,
        expires_at=invitation.expires_at,
        invitation_url=invitation_url
    )


@router.post("/register")
async def register_with_invitation(
    registration: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new user using an invitation token."""

    # Find and validate invitation
    invitation = db.query(Invitation).filter(
        Invitation.token == registration.token
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation token"
        )

    if invitation.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been used"
        )

    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )

    # Check if user already exists (race condition protection)
    existing_user = db.query(User).filter(User.email == invitation.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create user
    user = User(
        organization_id=invitation.organization_id,
        email=invitation.email,
        hashed_password=get_password_hash(registration.password),
        full_name=registration.full_name,
        role=invitation.role,
        is_active=True
    )

    db.add(user)

    # Mark invitation as used
    invitation.used_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Audit log (using bypass since user just created)
    audit_entry = AuditLog(
        user_id=str(user.id),
        organization_id=str(invitation.organization_id),
        action="user.register",
        resource_type="user",
        resource_id=str(user.id),
        details={
            "invitation_id": str(invitation.id),
            "invited_by": str(invitation.invited_by)
        }
    )
    db.add(audit_entry)
    db.commit()

    # Generate login token
    access_token = create_access_token(user)

    return {
        "message": "Registration successful",
        "access_token": access_token,
        "token_type": "bearer"
    }
```

---

## 10. Threat Model

### Threat Categories and Mitigations

| Threat | Severity | Mitigation |
|--------|----------|------------|
| **T1: Cross-tenant data access via API manipulation** | Critical | RLS policies enforce at database level; app cannot bypass |
| **T2: SQL injection bypassing RLS** | Critical | Parameterized queries only; no raw SQL construction |
| **T3: JWT token tampering** | High | Signed tokens with verified algorithm; reject "none" alg |
| **T4: Invitation token enumeration** | Medium | Cryptographically random 48-byte tokens; rate limiting |
| **T5: Session hijacking** | High | Short token expiry; HTTPS only; secure cookie flags |
| **T6: Privilege escalation via role manipulation** | High | Role stored server-side; JWT role verified against DB |
| **T7: Super-admin abuse** | Medium | All super-admin actions logged; short session expiry |
| **T8: Horizontal privilege escalation** | High | organization_id in token verified against resource |
| **T9: Audit log tampering** | Medium | Audit logs append-only for non-super-admin (RLS) |
| **T10: Invitation replay attack** | Medium | Single-use tokens; used_at timestamp check |

### Security Testing Requirements

```yaml
# Security test matrix for Sprint 8

unit_tests:
  - rls_policy_enforcement
  - token_validation
  - invitation_expiry
  - role_permission_checks
  - organization_boundary_enforcement

integration_tests:
  - cross_tenant_query_blocked
  - super_admin_audit_trail
  - invitation_flow_complete
  - organization_switching_audit

penetration_tests:
  - jwt_manipulation_attempts
  - sql_injection_via_filters
  - idor_via_resource_ids
  - rate_limit_bypass
  - session_fixation
```

---

## 11. Migration Strategy

### Phase 1: Schema Migration (Week 1)

```sql
-- Step 1: Create organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('platform_owner', 'buyer', 'supplier', 'partner')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Insert VIBOTAJ as platform owner
INSERT INTO organizations (name, slug, type)
VALUES ('VIBOTAJ', 'vibotaj', 'platform_owner');

-- Step 3: Add organization_id columns (nullable initially)
ALTER TABLE users ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE shipments ADD COLUMN organization_id UUID REFERENCES organizations(id);
-- ... (all tables)

-- Step 4: Populate organization_id for existing data
UPDATE users SET organization_id = (SELECT id FROM organizations WHERE slug = 'vibotaj');
UPDATE shipments SET organization_id = (SELECT id FROM organizations WHERE slug = 'vibotaj');
-- ... (all tables)

-- Step 5: Make organization_id NOT NULL
ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE shipments ALTER COLUMN organization_id SET NOT NULL;
-- ... (all tables)
```

### Phase 2: Buyer Organization Creation (Week 1-2)

```sql
-- Create organizations for existing buyers
INSERT INTO organizations (name, slug, type)
SELECT DISTINCT
    p.company_name,
    lower(regexp_replace(p.company_name, '[^a-zA-Z0-9]', '-', 'g')),
    'buyer'
FROM parties p
WHERE p.type = 'buyer';

-- Update shipments to correct organization based on buyer
UPDATE shipments s
SET organization_id = (
    SELECT o.id
    FROM organizations o
    JOIN parties p ON lower(regexp_replace(p.company_name, '[^a-zA-Z0-9]', '-', 'g')) = o.slug
    WHERE p.id = s.buyer_id
)
WHERE EXISTS (
    SELECT 1 FROM parties p WHERE p.id = s.buyer_id AND p.type = 'buyer'
);
```

### Phase 3: Enable RLS (Week 2)

```sql
-- Enable RLS (after all data migrated)
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipments FORCE ROW LEVEL SECURITY;
-- ... (all tables)

-- Create policies
-- ... (as defined in Section 7)
```

### Phase 4: Application Updates (Week 2-3)

1. Deploy tenant context middleware
2. Update JWT token generation with organization_id
3. Update all API endpoints to use tenant-scoped sessions
4. Deploy invitation system
5. Update frontend to handle organization context

### Rollback Plan

```sql
-- Emergency rollback: Disable RLS
ALTER TABLE shipments DISABLE ROW LEVEL SECURITY;
-- ... (all tables)

-- Note: organization_id columns remain but are ignored
-- Full rollback requires data migration plan
```

---

## 12. Consequences

### Positive Consequences

1. **Strong Security Posture:** Database-enforced isolation eliminates entire class of cross-tenant vulnerabilities
2. **Compliance Ready:** Audit logs with organization context satisfy EUDR and SOC2 requirements
3. **SaaS Foundation:** Architecture supports future multi-tenant commercial offering
4. **Operational Simplicity:** Single database reduces backup, monitoring, and maintenance overhead
5. **Query Efficiency:** RLS adds minimal overhead with proper indexing

### Negative Consequences

1. **Migration Complexity:** Existing data requires careful organization assignment
2. **Development Overhead:** All new features must consider tenant context
3. **Testing Complexity:** Tests must verify tenant isolation for every data access path
4. **Super-Admin UX:** Switching organizations adds friction to platform-wide operations

### Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RLS policy bugs causing data leakage | Low | Critical | Comprehensive test suite; security audit |
| Performance degradation from RLS | Medium | Medium | Index optimization; query analysis |
| Migration data corruption | Medium | High | Dry-run migration; backup before execution |
| Forgotten organization context in new code | Medium | High | Middleware enforcement; code review checklist |

---

## Appendix A: File Changes Summary

### New Files to Create

| File | Purpose |
|------|---------|
| `/app/models/organization.py` | Organization entity |
| `/app/models/invitation.py` | Invitation entity |
| `/app/middleware/tenant_context.py` | Tenant context middleware |
| `/app/routers/invitations.py` | Invitation API endpoints |
| `/app/routers/organizations.py` | Organization management (super-admin) |
| `/migrations/002_add_multi_tenancy.sql` | Schema migration |
| `/migrations/003_enable_rls_policies.sql` | RLS policies |

### Files to Modify

| File | Changes |
|------|---------|
| `/app/models/user.py` | Add organization_id, is_super_admin |
| `/app/models/shipment.py` | Add organization_id |
| `/app/models/document.py` | Add organization_id |
| `/app/models/party.py` | Add organization_id |
| `/app/models/audit_log.py` | Add organization_id (required) |
| `/app/models/notification.py` | Add organization_id |
| `/app/routers/auth.py` | Add organization to JWT; super-admin mode |
| `/app/database.py` | Add tenant context session management |
| `/app/services/permissions.py` | Add organization-aware permission checks |
| `/app/main.py` | Register tenant middleware |

---

## Appendix B: Verification Checklist

Before deployment, verify:

- [ ] All tables have organization_id column
- [ ] All tables have RLS enabled and forced
- [ ] All RLS policies created and tested
- [ ] JWT tokens include organization_id
- [ ] Middleware sets PostgreSQL session variables
- [ ] Super-admin bypass works correctly
- [ ] Organization switching creates audit trail
- [ ] Invitation flow complete and secure
- [ ] Historical data correctly assigned to organizations
- [ ] Cross-tenant query tests all pass
- [ ] Performance benchmarks acceptable
- [ ] Rollback procedure documented and tested

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
**Author:** Architecture Team
**Review Status:** Pending Security Review
