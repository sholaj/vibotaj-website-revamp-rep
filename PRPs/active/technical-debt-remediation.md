# PRP: Technical Debt & Gap Remediation

**Status:** Draft
**Priority:** P1
**Sprint:** 15 (Proposed)
**Created:** 2026-01-13
**Author:** Claude Code

## Overview

This PRP addresses critical technical debt and architectural gaps identified in the TraceHub application. The issues span data model inconsistencies between Backend (FastAPI/SQLAlchemy) and Frontend (React/TypeScript), multi-tenancy security vulnerabilities, and UI/UX navigation problems.

### Business Value

- **Security**: Fix document visibility bug that causes uploaded documents to be inaccessible
- **Reliability**: Eliminate 500 errors on shipment deletion
- **Maintainability**: Align frontend/backend models to reduce mapping bugs
- **User Experience**: Improve dashboard navigation and status visibility

## Requirements

### Functional Requirements

#### Critical (P0)
- [ ] **FR-001**: Documents uploaded via `/api/documents/upload` must have `organization_id` assigned from current user
- [ ] **FR-002**: Shipment deletion must work without 500 errors
- [ ] **FR-003**: Frontend `ShipmentStatus` must include `customs` status

#### High Priority (P1)
- [ ] **FR-004**: Standardize shipment status naming between backend and frontend
- [ ] **FR-005**: Align document field naming (`file_size` vs `file_size_bytes`, etc.)
- [ ] **FR-006**: Dashboard should show overview stats, not just shipment list

#### Medium Priority (P2)
- [ ] **FR-007**: Party/organization handling consistency
- [ ] **FR-008**: Improve shipment reference validation flexibility

### Non-Functional Requirements

- [ ] **NFR-001**: No breaking changes to existing API contracts
- [ ] **NFR-002**: Database migrations must be backwards compatible
- [ ] **NFR-003**: All changes must maintain multi-tenancy security
- [ ] **NFR-004**: Test coverage for all modified endpoints

## Technical Approach

### Phase 1: Critical Security Fixes (Sprint 15.1)

#### TICKET-SEC-001: Fix Document organization_id Assignment

**Root Cause Analysis:**
In `tracehub/backend/app/routers/documents.py:200-217`, the `Document` object is created without `organization_id`:

```python
# CURRENT (BROKEN)
document = Document(
    shipment_id=shipment_id,
    document_type=final_document_type,
    # ... other fields
    # organization_id is MISSING
)
```

**Fix:**
```python
# FIXED
document = Document(
    shipment_id=shipment_id,
    document_type=final_document_type,
    organization_id=current_user.organization_id,  # ADD THIS
    # ... other fields
)
```

**Impact:** All document queries filter by `organization_id`, so documents without this field return 404.

#### TICKET-SEC-002: Fix Shipment Deletion 500 Error

**Root Cause Analysis:**
The deletion cascade in `tracehub/backend/app/routers/shipments.py:436-443` attempts to delete related records, but may encounter foreign key constraint violations from:
- `ReferenceRegistry` table (references documents)
- `DocumentContent` table (references documents)
- `AuditLog` table (references shipments)
- `Origin` table (references shipments)

**Fix:**
Add explicit deletion of all dependent tables in correct order:
1. `ReferenceRegistry` (FK to Document)
2. `DocumentContent` (FK to Document)
3. `Document` (FK to Shipment)
4. `Origin` (FK to Shipment)
5. `ContainerEvent` (FK to Shipment)
6. `Product` (FK to Shipment)
7. `Shipment`

### Phase 2: Data Model Alignment (Sprint 15.2)

#### TICKET-001: Standardize ShipmentStatus Enums

**Current State:**
| Backend (Python) | Frontend (TypeScript) | Database Value |
|------------------|----------------------|----------------|
| `DRAFT` | `created` | `draft` |
| `DOCS_PENDING` | `docs_pending` | `docs_pending` |
| `DOCS_COMPLETE` | `docs_complete` | `docs_complete` |
| `IN_TRANSIT` | `in_transit` | `in_transit` |
| `ARRIVED` | `arrived` | `arrived` |
| `CUSTOMS` | **MISSING** | `customs` |
| `DELIVERED` | `delivered` | `delivered` |
| `ARCHIVED` | `closed` | `archived` |

**Resolution:**
1. Add `customs` to frontend `ShipmentStatus` type
2. Change frontend `created` to `draft` (matches DB)
3. Change frontend `closed` to `archived` (matches DB)

**Migration Strategy:** Frontend-only changes, no database migration required.

#### TICKET-002: Unify Document Field Naming

**Current State:**
| Backend Field | Frontend Field | Recommended |
|---------------|----------------|-------------|
| `file_size` | `file_size_bytes` | `file_size` (keep backend) |
| `document_date` | `issue_date` | `document_date` (keep backend) |
| `issuer` | `issuing_authority` | `issuer` (keep backend) |

**Resolution:** Update frontend interface to match backend column names. Serializers can map if needed.

#### TICKET-003: Add Missing DocumentStatus Cases

Frontend already has good coverage. Backend has deprecated states that need UI handling for legacy data.

### Phase 3: UX Improvements (Sprint 15.3)

#### TICKET-005 & TICKET-006: Dashboard Navigation Fix

**Current State:**
- "Dashboard" nav item → Shows shipment list (labeled "Shipments")
- "Analytics" nav item → Shows the actual dashboard stats

**Resolution:**
1. Rename "Dashboard" nav to "Shipments"
2. Create true Dashboard component showing:
   - Shipment summary cards (in transit, delivered, pending)
   - Document completion metrics
   - Recent activity feed
   - Quick action buttons
3. Move current Analytics widgets to Dashboard

## Files to Modify

### Phase 1: Critical Security

| File | Changes |
|------|---------|
| `tracehub/backend/app/routers/documents.py` | Add `organization_id=current_user.organization_id` to Document creation (~line 201) |
| `tracehub/backend/app/routers/shipments.py` | Add ReferenceRegistry, DocumentContent, Origin deletion before Document deletion (~line 436) |

### Phase 2: Data Model Alignment

| File | Changes |
|------|---------|
| `tracehub/frontend/src/types/index.ts` | Update `ShipmentStatus` type: `draft`, `customs`, `archived` |
| `tracehub/frontend/src/types/index.ts` | Update `Document` interface field names |
| `tracehub/frontend/src/components/ComplianceStatus.tsx` | Handle `customs` status display |
| `tracehub/frontend/src/pages/Dashboard.tsx` | Handle `customs` and `archived` statuses |

### Phase 3: UX Improvements

| File | Changes |
|------|---------|
| `tracehub/frontend/src/components/Layout.tsx` | Rename nav items |
| `tracehub/frontend/src/pages/Dashboard.tsx` | Refactor to show overview stats |
| `tracehub/frontend/src/App.tsx` | Update routing if needed |

## Test Requirements

### Unit Tests

- [ ] `test_document_upload_sets_organization_id` - Verify org_id is set on upload
- [ ] `test_document_visible_after_upload` - Verify uploader can retrieve their document
- [ ] `test_shipment_delete_success` - Verify clean deletion without errors
- [ ] `test_shipment_delete_with_documents` - Verify cascade works correctly

### Integration Tests

- [ ] `test_full_document_upload_workflow` - Upload → View → Delete
- [ ] `test_shipment_lifecycle_with_customs` - Create → Customs → Delivered

### E2E Tests

- [ ] `test_dashboard_shows_stats` - Verify dashboard displays overview
- [ ] `test_shipment_status_customs_display` - Verify customs status renders correctly

## Compliance Check

**Product HS Codes Affected:** None directly
**EUDR Applicable:** No - this is infrastructure/technical debt work
**Required Documents:** N/A

**Multi-Tenancy Impact:**
- Phase 1 FIXES a multi-tenancy security vulnerability (document visibility)
- All changes maintain organization-based data isolation

## Dependencies

- PostgreSQL database access for migration testing
- Existing test fixtures for shipment/document CRUD

## Acceptance Criteria

### Phase 1 (Critical)
- [ ] Documents uploaded have `organization_id` populated
- [ ] User can view documents immediately after upload (no 404)
- [ ] Shipment deletion returns 204 No Content (no 500 errors)
- [ ] All existing tests pass

### Phase 2 (Data Alignment)
- [ ] Frontend `ShipmentStatus` includes all 8 backend statuses
- [ ] `customs` status displays correctly in UI
- [ ] Document field names consistent across stack
- [ ] No TypeScript errors after type updates

### Phase 3 (UX)
- [ ] Dashboard shows overview statistics on login
- [ ] Navigation labels match page content
- [ ] Quick actions available from dashboard

## Security Considerations

1. **Multi-Tenancy Enforcement**: The document visibility fix is security-critical. Without `organization_id`, documents bypass tenant isolation.

2. **Cascade Deletion**: Ensure audit logs are preserved even when shipments are deleted (soft delete or null FK).

3. **No Privilege Escalation**: Status changes through API must still enforce role permissions.

## Rollout Plan

### Phase 1 (Hotfix - Immediate)
1. Apply document.py fix
2. Apply shipments.py fix
3. Run existing test suite
4. Deploy to staging → verify → deploy to production
5. Backfill `organization_id` for existing documents (data migration script)

### Phase 2 (Next Sprint)
1. Frontend type updates
2. Component updates for new statuses
3. Full regression testing
4. Deploy

### Phase 3 (Following Sprint)
1. Dashboard redesign
2. Navigation restructure
3. UX testing
4. Deploy

## Appendix: Detailed Gap Analysis

### A. ShipmentStatus Enum Comparison

```
Backend (shipment.py:12-21)          Frontend (index.ts:326-333)
─────────────────────────────        ────────────────────────────
DRAFT = "draft"                      'created'        ← MISMATCH
DOCS_PENDING = "docs_pending"        'docs_pending'   ✓
DOCS_COMPLETE = "docs_complete"      'docs_complete'  ✓
IN_TRANSIT = "in_transit"            'in_transit'     ✓
ARRIVED = "arrived"                  'arrived'        ✓
CUSTOMS = "customs"                  (missing)        ← MISSING
DELIVERED = "delivered"              'delivered'      ✓
ARCHIVED = "archived"                'closed'         ← MISMATCH
```

### B. Document Field Mapping

```
Backend (document.py)                Frontend (index.ts)
─────────────────────                ────────────────────
file_size (Integer)                  file_size_bytes (number)
document_date (DateTime)             issue_date (string)
issuer (String)                      issuing_authority (string)
```

### C. DocumentStatus Already Aligned

Both backend and frontend use same values (case-insensitive matching via serializers).

---

**Next Steps:** Await approval, then implement Phase 1 immediately as hotfix.
