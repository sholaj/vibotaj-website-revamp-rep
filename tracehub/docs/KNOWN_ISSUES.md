# TraceHub Known Issues & Tech Debt

> Last updated: January 2026

This document tracks known issues, security concerns, and technical debt identified during the platform stabilization review.

---

## Security Issues (P0)

### SEC-001: Audit Router Missing Organization Filter

**Status:** ✅ FIXED (January 2026)

**Location:** `backend/app/routers/audit.py`, `backend/app/services/audit_log.py`

**Issue:** The audit log endpoints returned system-wide logs without filtering by organization.

**Fix Applied:**
- Added `organization_id` parameter to `query()`, `count()`, and `get_recent_activity()` methods in `audit_log.py`
- Updated all audit router endpoints to pass `current_user.organization_id` to service methods

**Affected Endpoints (Now Secure):**
- `GET /api/audit/`
- `GET /api/audit/recent`
- `GET /api/audit/summary`

---

### SEC-002: Document Duplicate Check Missing Org Filter

**Status:** ✅ FIXED (January 2026)

**Location:** `backend/app/routers/documents.py:1078-1084, 1131-1137`

**Issue:** The duplicate document check endpoints didn't verify that the shipment belongs to the user's organization before querying.

**Fix Applied:**
- Added organization_id filter to shipment query before checking duplicates
- Both endpoints now verify `Shipment.organization_id == current_user.organization_id`

**Affected Endpoints (Now Secure):**
- `GET /api/documents/shipments/{shipment_id}/duplicates`
- `GET /api/documents/check-duplicate`

---

## Architecture Issues (P1)

### ARCH-001: Dual User Schema System

**Status:** 🟡 Medium Priority

**Location:** `backend/app/schemas/user.py`, `backend/app/routers/auth.py`

**Issue:** Two user schemas coexist:
- Legacy `User` schema with `username` property returning email
- New `CurrentUser` schema with full multi-tenancy support

**Impact:** Code complexity, potential confusion, maintenance burden.

**Recommendation:** Deprecate legacy `User` schema, migrate all endpoints to use `CurrentUser`.

---

### ARCH-002: Mixed DocumentStatus Enums

**Status:** 🟡 Medium Priority

**Location:** `backend/app/models/document.py`

**Issue:** DocumentStatus enum has two sets of values:
- Current: `UPLOADED`, `PENDING_VALIDATION`, `VALIDATED`, `REJECTED`, `EXPIRED`
- Legacy: `DRAFT`, `COMPLIANCE_OK`, `COMPLIANCE_FAILED`, `LINKED`, `ARCHIVED`

**Impact:** Confusion about valid status values, potential data inconsistency.

**Recommendation:**
1. Audit existing documents for legacy status usage
2. Create migration to update legacy statuses
3. Remove legacy enum values

---

### ARCH-003: Unused Party Table

**Status:** 🟢 Low Priority

**Location:** `backend/app/models/party.py`

**Issue:** The `parties` table was designed for supplier/buyer relationships but is unused. Shipments now use `exporter_name` and `importer_name` string fields instead.

**Impact:** Dead code, database bloat.

**Recommendation:**
1. Confirm no data exists in parties table
2. Create migration to drop table
3. Remove model and any references

---

### ARCH-004: Organization Membership Redundancy

**Status:** 🟡 Medium Priority

**Location:** `backend/app/models/user.py`, `backend/app/models/organization.py`

**Issue:** Two patterns for user-organization association:
- `User.organization_id` - Legacy direct FK
- `OrganizationMembership` - New membership model with roles

**Impact:** Unclear which source of truth to use, potential data inconsistency.

**Recommendation:** Complete migration to membership-only model:
1. Ensure all users have OrganizationMembership records
2. Update queries to use membership table
3. Deprecate `User.organization_id` (keep for backward compatibility initially)

---

### ARCH-005: Notification System User-Scoped

**Status:** 🟢 Low Priority - May Be Intentional

**Location:** `backend/app/routers/notifications.py`

**Issue:** Notifications use `user_id` (string) instead of `organization_id`. Users can potentially receive notifications across organizations if they have access to multiple.

**Impact:** May be intentional design for multi-org users.

**Recommendation:** Document this behavior. If unintentional, add organization scoping.

---

## Schema Issues (P2)

### SCHEMA-001: notifications.user_id is String

**Status:** 🟡 Medium Priority

**Location:** `backend/app/models/notification.py`

**Issue:** `user_id` column is VARCHAR(100) instead of UUID FK to users table.

**Impact:** No referential integrity, cannot join to users table efficiently.

**Fix:** Create migration to change column type and add FK constraint.

---

### SCHEMA-002: document_contents.validated_by is String

**Status:** 🟡 Medium Priority

**Location:** `backend/app/models/document.py`

**Issue:** `validated_by` column stores username as string instead of UUID FK.

**Impact:** No referential integrity to users table.

**Fix:** Create migration to change to UUID FK.

---

### SCHEMA-003: origins.verified_by Missing FK Constraint

**Status:** 🟡 Medium Priority

**Location:** `backend/app/models/origin.py`

**Issue:** `verified_by` is UUID type but lacks FK constraint to users table.

**Impact:** No referential integrity enforcement.

**Fix:** Add FK constraint in migration.

---

### SCHEMA-004: Inconsistent DateTime Timezone Handling

**Status:** 🟢 Low Priority

**Location:** Multiple models

**Issue:** Some DateTime columns use `timezone=True`, others don't:
- With timezone: documents, products, origins, container_events
- Without timezone: shipments, users, organizations

**Impact:** Potential timezone confusion when querying across tables.

**Fix:** Standardize all DateTime columns to include timezone.

---

## Missing Features (P2)

### FEAT-001: Buyer Organization Access Control

**Status:** 🟡 Medium Priority

**Location:** `backend/app/routers/documents.py`

**Issue:** Shipments can have `buyer_organization_id` set, but there's no access control allowing buyer org users to view/upload documents for those shipments.

**Impact:** Buyers cannot access shipments assigned to them.

**Fix:** Implement `OrgContext.can_access_shipment()` checks using the org_permissions service.

---

### FEAT-002: EUDR Field Validation for Horn & Hoof

**Status:** 🟡 Medium Priority

**Location:** `backend/app/routers/eudr.py`

**Issue:** No validation prevents EUDR fields (geolocation, risk_level) from being set on Horn & Hoof products (HS 0506/0507), which are NOT covered by EUDR per COMPLIANCE_MATRIX.md.

**Impact:** Data inconsistency, compliance confusion.

**Fix:** Add validation in origin creation/update endpoints:
```python
if shipment.product_type == ProductType.HORN_HOOF:
    if origin_data.latitude or origin_data.longitude or origin_data.risk_level:
        raise HTTPException(400, "EUDR fields not applicable for Horn & Hoof products")
```

---

### FEAT-003: Shipment Status Transition Validation

**Status:** 🟢 Low Priority

**Location:** `backend/app/routers/tracking.py`

**Issue:** Shipment status can be updated to any value without validating allowed transitions.

**Impact:** Invalid state transitions possible (e.g., DELIVERED → DRAFT).

**Fix:** Implement state machine for shipment status transitions.

---

## Frontend Issues

### FE-001: No Component API Documentation

**Status:** 🟢 Low Priority

**Issue:** No documentation for component props, usage patterns, or examples.

**Impact:** Developer onboarding difficulty.

**Fix:** Create component documentation or use Storybook.

---

### FE-002: Large Bundle Size

**Status:** 🟢 Low Priority

**Location:** `frontend/src/`

**Issue:** Main JS bundle is ~800KB, exceeding recommended 500KB.

**Impact:** Slower initial page load.

**Fix:** Implement code splitting, lazy loading for routes.

---

## Testing Gaps

### TEST-001: Missing Multi-Tenancy Tests

**Status:** 🟡 Medium Priority

**Issue:** No automated tests verifying data isolation between organizations.

**Impact:** Security regressions could go undetected.

**Fix:** Add integration tests that:
1. Create users in different organizations
2. Verify User A cannot access User B's shipments/documents
3. Verify audit logs are properly filtered

---

### TEST-002: Missing EUDR Compliance Tests

**Status:** 🟢 Low Priority

**Issue:** No automated tests for EUDR validation logic, especially Horn & Hoof exemptions.

**Fix:** Add unit tests for compliance service.

---

## Resolution Tracking

| Issue ID | Status | Sprint | Assignee |
|----------|--------|--------|----------|
| SEC-001 | ✅ Fixed | Current | - |
| SEC-002 | ✅ Fixed | Current | - |
| ARCH-001 | Backlog | 10 | - |
| ARCH-002 | Backlog | 10 | - |
| ARCH-003 | Backlog | 10 | - |
| ARCH-004 | Backlog | 11 | - |
| ARCH-005 | Documented | - | - |
| SCHEMA-001 | Backlog | 11 | - |
| SCHEMA-002 | Backlog | 11 | - |
| SCHEMA-003 | Backlog | 11 | - |
| SCHEMA-004 | Backlog | 12 | - |
| FEAT-001 | Backlog | 11 | - |
| FEAT-002 | Backlog | 10 | - |
| FEAT-003 | Backlog | 12 | - |
| FE-001 | Backlog | - | - |
| FE-002 | Backlog | - | - |
| TEST-001 | Backlog | 10 | - |
| TEST-002 | Backlog | 10 | - |
