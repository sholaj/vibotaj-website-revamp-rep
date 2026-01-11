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

**Status:** ✅ DEPRECATED (January 2026) - Removal planned for v2.0

**Location:** `backend/app/routers/auth.py`

**Issue:** Two user schemas coexisted:
- Legacy `User` schema with `username` property returning email
- New `CurrentUser` schema with full multi-tenancy support

**Fix Applied:**
- Added deprecation docstrings to legacy `User` class
- Added deprecation warning to `get_current_user()` function
- Added `deprecated=True` flag to `GET /api/auth/me` endpoint
- Added HTTP deprecation headers (`Deprecation`, `Sunset`, `Link`) to response
- Sunset date: 2026-06-01

**Migration Guide:**
- Replace: `current_user: User = Depends(get_current_user)`
- With: `current_user: CurrentUser = Depends(get_current_active_user)`
- Replace: `GET /api/auth/me`
- With: `GET /api/auth/me/full`

---

### ARCH-002: Mixed DocumentStatus Enums

**Status:** ✅ DOCUMENTED (January 2026) - Clear workflow defined

**Location:** `backend/app/models/document.py`

**Issue:** DocumentStatus enum had confusing mix of values with unclear usage.

**Fix Applied:**
- Reorganized enum with clear Active vs Deprecated sections
- Added comprehensive docstring documenting:
  - Active workflow states: DRAFT, UPLOADED, VALIDATED, COMPLIANCE_OK, COMPLIANCE_FAILED, LINKED, ARCHIVED
  - Deprecated states: PENDING_VALIDATION, REJECTED, EXPIRED (kept for DB compatibility)
  - Workflow transition diagram
- Added inline deprecation comments for deprecated values

**Active Workflow:**
```
DRAFT -> UPLOADED -> VALIDATED -> COMPLIANCE_OK -> LINKED -> ARCHIVED
                             \-> COMPLIANCE_FAILED -> UPLOADED (retry)
```

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

**Status:** ✅ FIXED (January 2026)

**Location:** `backend/app/models/notification.py`

**Issue:** `user_id` column was VARCHAR(100) storing email instead of UUID FK to users table.

**Fix Applied:**
- Updated model: `user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))`
- Added relationship to User model
- Updated `notifications.py` router to use `str(current_user.id)` instead of `current_user.username`
- Updated `notifications.py` service to convert string IDs to UUID for queries
- Created migration: `20260111_0004_notification_user_id_to_uuid.py`
- Migration looks up user UUIDs from email addresses for existing data
- Added timezone to `read_at` and `created_at` columns

---

### SCHEMA-002: document_contents.validated_by is String

**Status:** ✅ FIXED (January 2026)

**Location:** `backend/app/models/document_content.py`

**Issue:** `validated_by` column stored username as String(100) instead of UUID FK.

**Fix Applied:**
- Updated model: `validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))`
- Also added `timezone=True` to `validated_at` column
- Created migration: `20260111_0003_fix_document_content_validated_by.py`
- Migration handles data conversion from String to UUID (if valid UUID format)

---

### SCHEMA-003: origins.verified_by Missing FK Constraint

**Status:** ✅ FIXED (January 2026)

**Location:** `backend/app/models/origin.py`

**Issue:** `verified_by` was UUID type but lacked FK constraint to users table.

**Fix Applied:**
- Updated model: `verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))`
- Created migration: `20260111_0002_add_origin_verified_by_fk.py`
- Uses SET NULL on delete: if user is deleted, origin remains but verified_by becomes null

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

**Status:** ✅ FIXED (January 2026)

**Location:** `backend/app/routers/shipments.py`, `backend/app/services/access_control.py`

**Issue:** Shipments can have `buyer_organization_id` set, but there's no access control allowing buyer org users to view/upload documents for those shipments.

**Fix Applied:**
- Created `services/access_control.py` with helper functions:
  - `can_access_shipment()` - Check owner OR buyer access
  - `get_accessible_shipments_filter()` - SQLAlchemy filter for accessible shipments
  - `get_accessible_shipment()` - Get shipment by ID with access check
  - `user_is_shipment_owner()` - Check owner-only access for edit/delete
  - `user_is_shipment_buyer()` - Check buyer relationship
- Updated all shipment endpoints to use access control:
  - Read endpoints (list, get, documents, events, audit-pack): Allow owner OR buyer
  - Write endpoints (update, delete): Owner only, buyers get 403 with clear message

**Affected Endpoints (Now Support Buyer Access):**
- `GET /api/shipments` - Lists shipments where user is owner OR buyer
- `GET /api/shipments/{id}` - View details if owner OR buyer
- `GET /api/shipments/{id}/documents` - View documents if owner OR buyer
- `GET /api/shipments/{id}/events` - View events if owner OR buyer
- `GET /api/shipments/{id}/audit-pack` - Download audit pack if owner OR buyer
- `PATCH /api/shipments/{id}` - Update (owner only, 403 for buyers)
- `DELETE /api/shipments/{id}` - Delete (owner only, 403 for buyers)

---

### FEAT-002: EUDR Field Validation for Horn & Hoof

**Status:** ✅ FIXED (January 2026)

**Location:** `backend/app/routers/eudr.py`

**Issue:** No validation prevented EUDR fields (geolocation, risk_level) from being set on Horn & Hoof products (HS 0506/0507), which are NOT covered by EUDR per COMPLIANCE_MATRIX.md.

**Fix Applied:**
- Added ProductType.HORN_HOOF checks to all EUDR endpoints
- `verify_origin` - Rejects geolocation/deforestation fields for Horn & Hoof
- `get_origin_risk` - Returns "not_applicable" status for Horn & Hoof
- `get_eudr_status` - Returns NOT_APPLICABLE with 100% compliance for Horn & Hoof
- `validate_shipment_eudr` - Returns exempt status with no action items for Horn & Hoof
- `get_eudr_report` - Returns EUDR Exemption Notice for Horn & Hoof

**Affected Endpoints (Now Handle Horn & Hoof Exemption):**
- `GET /api/eudr/shipment/{id}/status`
- `POST /api/eudr/shipment/{id}/validate`
- `GET /api/eudr/shipment/{id}/report`
- `POST /api/eudr/origin/{id}/verify`
- `GET /api/eudr/origin/{id}/risk`

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

**Status:** ✅ FIXED (January 2026)

**Issue:** No automated tests verifying data isolation between organizations.

**Fix Applied:**
Created `backend/tests/test_multi_tenancy.py` with comprehensive test coverage:
- `TestShipmentIsolation` - Verifies users can only see their org's shipments
- `TestDocumentIsolation` - Verifies users can only access their org's documents
- `TestAuditLogIsolation` - Verifies SEC-001 fix (audit logs filtered by org)
- `TestDuplicateCheckIsolation` - Verifies SEC-002 fix (duplicate check respects org)
- `TestEUDRIsolation` - Verifies EUDR endpoints respect org boundaries

**Test Approach:**
- Creates VIBOTAJ (exporter) and HAGES (buyer) organizations
- Creates users, shipments, documents, audit logs for each org
- Verifies cross-org access returns 404 (not 403, to avoid existence leaking)

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
| ARCH-001 | ✅ Deprecated | 10 | - |
| ARCH-002 | ✅ Documented | 10 | - |
| ARCH-003 | ✅ Fixed | 10 | - |
| ARCH-004 | Backlog | 11 | - |
| ARCH-005 | Documented | - | - |
| SCHEMA-001 | ✅ Fixed | 11 | - |
| SCHEMA-002 | ✅ Fixed | 11 | - |
| SCHEMA-003 | ✅ Fixed | 11 | - |
| SCHEMA-004 | Backlog | 12 | - |
| FEAT-001 | ✅ Fixed | 11 | - |
| FEAT-002 | ✅ Fixed | 10 | - |
| FEAT-003 | Backlog | 12 | - |
| FE-001 | Backlog | - | - |
| FE-002 | Backlog | - | - |
| TEST-001 | ✅ Fixed | 10 | - |
| TEST-002 | Backlog | 12 | - |
