# PRD-002: Supabase Setup + Schema Migration + RLS

**Status:** Done
**Complexity:** High
**Target:** Week 1
**Dependencies:** None
**Branch:** `feature/prd-002-supabase-schema`

---

## Problem

v1 runs PostgreSQL 15 in a Docker container on Hostinger VPS with no Row-Level Security, no managed backups, and manual SSH access for database operations. Multi-tenancy relies entirely on application-level `organization_id` filtering — a single missed filter leaks data across tenants. 15 tables and 12+ enums need to be replicated with RLS as defense-in-depth.

## Acceptance Criteria

1. Supabase project created with dev environment (staging added in Phase 2)
2. All 15 tables created via numbered SQL migrations matching v1 SQLAlchemy models exactly
3. All 12 enums created in correct dependency order
4. All 40+ indexes replicated from v1 models
5. RLS enabled on all 15 tables with `organization_id` tenant isolation
6. Admin bypass policy for system admin operations
7. Buyer-specific RLS on `shipments` (buyers see shipments where `buyer_organization_id` matches)
8. Seed data: 2 orgs (VIBOTAJ, HAGES), 4 users, sample shipments and documents
9. TypeScript types generated via `supabase gen types typescript`
10. v1 database on Hostinger is completely untouched

## Technical Approach

### 1. Supabase Project Setup

```bash
supabase init  # Creates v2/supabase/ with config.toml
supabase link --project-ref <project-id>
```

### 2. Enum Creation Order (migration 001)

Enums must be created before tables that reference them:

```sql
-- 001_create_enums.sql
CREATE TYPE userrole AS ENUM ('admin', 'compliance', 'logistics_agent', 'buyer', 'supplier', 'viewer');
CREATE TYPE organizationtype AS ENUM ('vibotaj', 'buyer', 'supplier', 'logistics_agent');
CREATE TYPE organizationstatus AS ENUM ('active', 'suspended', 'pending_setup');
CREATE TYPE orgrole AS ENUM ('admin', 'manager', 'member', 'viewer');
CREATE TYPE membershipstatus AS ENUM ('active', 'suspended', 'pending');
CREATE TYPE invitationstatus AS ENUM ('pending', 'accepted', 'expired', 'revoked');
CREATE TYPE shipmentstatus AS ENUM ('draft', 'docs_pending', 'docs_complete', 'in_transit', 'arrived', 'customs', 'delivered', 'archived');
CREATE TYPE producttype AS ENUM ('horn_hoof', 'sweet_potato', 'hibiscus', 'ginger', 'cocoa', 'other');
CREATE TYPE documenttype AS ENUM ('bill_of_lading', 'commercial_invoice', 'packing_list', 'certificate_of_origin', 'phytosanitary_certificate', 'fumigation_certificate', 'sanitary_certificate', 'insurance_certificate', 'customs_declaration', 'contract', 'eudr_due_diligence', 'quality_certificate', 'eu_traces_certificate', 'veterinary_health_certificate', 'export_declaration', 'other');
CREATE TYPE documentstatus AS ENUM ('draft', 'uploaded', 'validated', 'compliance_ok', 'compliance_failed', 'linked', 'archived', 'pending_validation', 'rejected', 'expired');
CREATE TYPE eventstatus AS ENUM ('booked', 'gate_in', 'loaded', 'departed', 'in_transit', 'transshipment', 'arrived', 'discharged', 'gate_out', 'delivered', 'other');
CREATE TYPE risklevel AS ENUM ('low', 'medium', 'high', 'critical');
```

### 3. Table Creation (migrations 002-010)

Tables in dependency order:

| Migration | Tables | Depends On |
|-----------|--------|-----------|
| 002 | `organizations` | enums |
| 003 | `users` | organizations |
| 004 | `organization_memberships`, `invitations` | organizations, users |
| 005 | `shipments` | organizations |
| 006 | `documents`, `document_issues` | organizations, shipments |
| 007 | `document_contents` | documents |
| 008 | `compliance_results` | documents, organizations |
| 009 | `container_events`, `notifications` | shipments, users |
| 010 | `origins`, `products`, `reference_registry`, `audit_logs` | shipments, organizations |

### 4. All 15 Tables

| # | Table | Tenant Column | Special RLS |
|---|-------|--------------|-------------|
| 1 | `organizations` | `id` (self) | Members see own org only |
| 2 | `users` | `organization_id` | Self + admin access |
| 3 | `organization_memberships` | `organization_id` | Members see own org |
| 4 | `invitations` | `organization_id` | Org admins + invitee |
| 5 | `shipments` | `organization_id` | + `buyer_organization_id` for buyer orgs |
| 6 | `documents` | `organization_id` (nullable) | Nullable backward compat |
| 7 | `document_issues` | `organization_id` | Standard tenant filter |
| 8 | `document_contents` | via `documents` join | Follows document access |
| 9 | `compliance_results` | `organization_id` | Standard tenant filter |
| 10 | `container_events` | `organization_id` | Standard tenant filter |
| 11 | `notifications` | `user_id` | User sees own notifications |
| 12 | `origins` | `organization_id` | Standard tenant filter |
| 13 | `products` | `organization_id` | Standard tenant filter |
| 14 | `reference_registry` | via `shipments` join | Follows shipment access |
| 15 | `audit_logs` | `organization_id` | Admin-only access |

### 5. RLS Policy Pattern

```sql
-- Standard tenant isolation
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenant_isolation" ON shipments
  USING (
    organization_id = (current_setting('app.current_org_id'))::uuid
    OR (current_setting('app.is_system_admin', true))::boolean = true
  );

-- Buyer access for shipments
CREATE POLICY "buyer_access" ON shipments FOR SELECT
  USING (
    buyer_organization_id = (current_setting('app.current_org_id'))::uuid
  );
```

The FastAPI backend sets `app.current_org_id` and `app.is_system_admin` via `SET LOCAL` at the start of each request (middleware in PRD-004).

### 6. Index Replication

All 40+ indexes from v1 models replicated in migration files. Key indexes:

- `organizations`: slug (unique), type+status (composite), name
- `organization_memberships`: user_id+org_id (unique), org_id+role (composite), user_id+is_primary
- `invitations`: email, token_hash (unique), org_id+email, status, expires_at
- `users`: email (unique), organization_id
- `shipments`: organization_id, buyer_organization_id, product_type, org_id+reference (unique)
- `documents`: organization_id
- `document_issues`: document_id, shipment_id, rule_id, severity, is_overridden, organization_id
- `compliance_results`: document_id, organization_id
- `container_events`: shipment_id, organization_id, event_time
- `notifications`: user_id, user_id+read, user_id+created_at
- `origins`: shipment_id, organization_id
- `products`: shipment_id, organization_id
- `reference_registry`: reference_number, shipment_id+reference_number+document_type (unique)
- `audit_logs`: organization_id, request_id, timestamp, username+timestamp, action+timestamp, resource_type+resource_id

## Files to Create

```
v2/supabase/
  config.toml
  migrations/
    001_create_enums.sql
    002_create_organizations.sql
    003_create_users.sql
    004_create_memberships_invitations.sql
    005_create_shipments.sql
    006_create_documents.sql
    007_create_document_contents.sql
    008_create_compliance_results.sql
    009_create_events_notifications.sql
    010_create_origins_products_registry_audit.sql
    011_enable_rls.sql
    012_create_indexes.sql
  seed.sql
```

## v1 Source of Truth

| v1 File | What to Extract |
|---------|----------------|
| `tracehub/backend/app/models/user.py` | `users` table + `UserRole` enum |
| `tracehub/backend/app/models/organization.py` | `organizations`, `organization_memberships`, `invitations` + 4 enums |
| `tracehub/backend/app/models/shipment.py` | `shipments` + `ShipmentStatus`, `ProductType` enums |
| `tracehub/backend/app/models/document.py` | `documents`, `document_issues` + `DocumentType`, `DocumentStatus` enums |
| `tracehub/backend/app/models/document_content.py` | `document_contents` table |
| `tracehub/backend/app/models/compliance_result.py` | `compliance_results` table |
| `tracehub/backend/app/models/container_event.py` | `container_events` + `EventStatus` enum |
| `tracehub/backend/app/models/notification.py` | `notifications` + `NotificationType` enum (app-level, not DB enum) |
| `tracehub/backend/app/models/origin.py` | `origins` + `RiskLevel` enum |
| `tracehub/backend/app/models/product.py` | `products` table |
| `tracehub/backend/app/models/reference_registry.py` | `reference_registry` table |
| `tracehub/backend/app/models/audit_log.py` | `audit_logs` table |

## Critical Notes

- `documents.organization_id` is **nullable** in v1 (backward compatibility from Sprint 10) — preserve this
- `document_issues` has its own `organization_id` column (denormalized for query performance)
- `shipments.buyer_organization_id` needs dual RLS: owner org + buyer org can both read
- `reference_registry` has a composite unique constraint on `(shipment_id, reference_number, document_type)`
- Deprecated `DocumentStatus` values (`pending_validation`, `rejected`, `expired`) must remain in the enum for v1 data migration
- `NotificationType` is defined as a Python enum in v1 but may be stored as VARCHAR — verify column type
- `audit_logs` has no foreign keys to users (stores `username` as text for immutability)

## Testing Strategy

- `supabase db reset` completes without errors (all migrations apply cleanly)
- Seed data loads successfully
- RLS verification: query as org A user cannot see org B data
- RLS verification: buyer org can see shipments where `buyer_organization_id` matches
- RLS verification: admin bypass works with `app.is_system_admin = true`
- `supabase gen types typescript` generates without errors
- Column types match v1 SQLAlchemy model definitions exactly

## Migration Notes

- v1 database on Hostinger is untouched — this creates a parallel schema in Supabase
- Actual data migration (pg_dump → Supabase) happens during Phase 4 cutover
- RLS policies use `current_setting()` — FastAPI middleware must set these per-request (PRD-004)
- Supabase direct connection (port 5432) required for SQLAlchemy — NOT PgBouncer (port 6543)
