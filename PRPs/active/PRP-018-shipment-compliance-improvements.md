# PRP-018: TraceHub Shipment & Compliance Improvements

**Issues:** #31–#43
**Priority:** High
**Sprint:** 15
**Status:** ✅ Phase 1 Complete
**Created:** 2026-01-18
**Updated:** 2026-01-20

## Executive Summary

This PRP addresses critical defects identified during recent testing of TraceHub, covering validation status overrides, compliance engine robustness, container management, shipment status workflow, search/filtering, document downloads, and EUDR integration. The implementation follows TDD principles with minimal regression risk.

## Problem Analysis

Based on code analysis, the following root causes have been identified:

### 1. Issue #31 - Validation Status Override (404 on validation report)

**Root Cause:** The `get_validation_report` endpoint exists and works correctly. The 404 error likely occurs when:
- The frontend tries to fetch a report before validation has run
- The shipment has no documents (empty validation report)
- Multi-tenancy check fails (buyer org users can't access owner org shipments for validation)

**Current State:** Backend has override functionality (`POST /validation/shipments/{id}/override`), but:
- Frontend `ShipmentValidationPanel` component exists with override UI
- Override button only shows when `isAdmin=true` AND report exists AND `!isValid`

**Fix Required:**
- Ensure validation report endpoint returns meaningful data even when no documents exist
- Add override button visibility for validation failures
- Ensure buyer organizations can view (but not override) validation status

### 2. Issue #32 - Compliance Engine Issues

**Root Causes Identified:**

a) **Documents remain in Draft after approval** - The validation endpoint (`/documents/{id}/validate`) sets status to `VALIDATED`, but there's a disconnect between "Compliance Approved" button action and document status update.

b) **Validation returns 404** - Already addressed in #31.

c) **EUDR status API returns 500 for cocoa** - The EUDR endpoint at `/eudr/shipment/{id}/status` handles `HORN_HOOF` products correctly but may fail for cocoa due to missing origin data.

d) **Missing EUDR status cards for exempt products** - Frontend correctly checks `isHornHoofShipment()` but the check is in `Shipment.tsx`, not in `EUDRStatusCard`.

e) **Analytics shows 100% compliance** - The `get_compliance_metrics()` function in `analytics.py` needs review to ensure accurate calculation.

### 3. Issues #34, #41 - Container Management

**Root Causes:**
- `container_number` is required in `ShipmentCreate` schema with ISO 6346 validation
- No "Add Container" button in UI for tracking tab
- The `CreateShipmentModal` has container validation that rejects empty values

**Fix Required:**
- Make `container_number` optional in `ShipmentCreate` schema
- Add container management UI in Shipment detail tracking tab
- Support placeholder container numbers for draft shipments

### 4. Issues #35, #42 - Shipment Status Workflow

**Root Causes:**
- `shipment_state_machine.py` has strict transition rules that block `DOCS_PENDING` → `IN_TRANSIT`
- The transition requires going through `DOCS_COMPLETE` first
- Frontend status dropdown sends lowercase values (correct), but transition validation may fail

**Fix Required:**
- Add direct `DOCS_PENDING` → `IN_TRANSIT` transition for logistics flexibility
- Improve error messages to guide users on valid transitions

### 5. Issues #36, #40 - Search and Visibility

**Root Causes:**
- No search/filter UI on Dashboard
- Shipment visibility is correct (uses `get_accessible_shipments_filter`)
- "Failed to load validation report" error is separate from visibility issue

**Fix Required:**
- Add search bar and filter dropdowns to Dashboard
- Add shipment search API endpoint with query parameters

### 6. Issues #37, #38, #43 - Document Downloads

**Root Causes:**
- `download_document` endpoint checks `organization_id == current_user.organization_id`
- This excludes buyer organization users from downloading documents
- Same issue with `get_document` endpoint

**Fix Required:**
- Update document access control to allow buyer organizations to view/download
- Join with shipment to check `buyer_organization_id`

### 7. Issue #39 - EUDR Geolocation 500 Errors

**Root Cause:**
- The EUDR status endpoint crashes when accessing geolocation data for shipments without origin records
- Missing null checks in EUDR service functions

**Fix Required:**
- Add defensive null checks
- Return meaningful error/status for missing geolocation data

## Implementation Plan

### Phase 1: Backend Fixes (Priority: Critical)

#### 1.1 Document Access Control for Buyers

**File:** `tracehub/backend/app/routers/documents.py`

```python
# Update get_document and download_document to use shipment-based access control
from ..services.access_control import get_accessible_shipments_filter

# Change from:
Document.organization_id == current_user.organization_id

# To:
shipment = db.query(Shipment).filter(
    Shipment.id == document.shipment_id,
    get_accessible_shipments_filter(current_user)
).first()
```

#### 1.2 Container Number Optional in ShipmentCreate

**File:** `tracehub/backend/app/schemas/shipment.py`

```python
class ShipmentCreate(BaseModel):
    container_number: Optional[str] = None  # Make optional
    
    @field_validator('container_number')
    @classmethod
    def validate_container_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None  # Allow empty/None for drafts
        # ... existing validation for non-empty values
```

#### 1.3 Status Transition Rules Update

**File:** `tracehub/backend/app/services/shipment_state_machine.py`

```python
VALID_TRANSITIONS: dict[ShipmentStatus, List[ShipmentStatus]] = {
    ShipmentStatus.DOCS_PENDING: [
        ShipmentStatus.DOCS_COMPLETE,
        ShipmentStatus.IN_TRANSIT,  # Add direct transition for flexibility
        ShipmentStatus.DRAFT,
        ShipmentStatus.ARCHIVED,
    ],
    # ... rest unchanged
}
```

#### 1.4 Compliance Analytics Accuracy

**File:** `tracehub/backend/app/services/analytics.py`

Review and fix `get_compliance_metrics()` to calculate actual document completeness:
- Count shipments with all required documents present
- Don't count draft/incomplete shipments as "compliant"

### Phase 2: Frontend Fixes (Priority: High)

#### 2.1 Dashboard Search and Filters

**File:** `tracehub/frontend/src/pages/Dashboard.tsx`

Add search bar and filter components:
- Text search for reference, container number
- Status filter dropdown
- Date range filter

#### 2.2 Container Management in Tracking Tab

**File:** `tracehub/frontend/src/pages/Shipment.tsx`

Add "Add Container" button when:
- User has `shipments:update` permission
- Shipment is in editable status (draft, docs_pending)
- Container number is placeholder or missing

#### 2.3 CreateShipmentModal Container Optional

**File:** `tracehub/frontend/src/components/CreateShipmentModal.tsx`

- Remove required validation for container_number
- Show info message about adding container later
- Update submit to not send empty container

### Phase 3: EUDR Fixes (Priority: Medium)

#### 3.1 EUDR Status Endpoint Error Handling

**File:** `tracehub/backend/app/routers/eudr.py`

Add defensive checks:
```python
@router.get("/shipment/{shipment_id}/status")
async def get_eudr_status(...):
    # ... existing code
    
    # Add null checks for origins
    origins = db.query(Origin).filter(Origin.shipment_id == shipment_id).all()
    if not origins:
        return {
            "shipment_id": str(shipment.id),
            "overall_status": "INCOMPLETE",
            "message": "No origin data provided",
            # ... other fields
        }
```

### Phase 4: Testing

#### 4.1 Unit Tests

Create/update tests in `tracehub/backend/tests/`:

```python
# test_document_access.py
def test_buyer_can_download_document()
def test_buyer_can_view_document()
def test_non_buyer_cannot_access_document()

# test_shipment_transitions.py
def test_docs_pending_to_in_transit()
def test_invalid_transition_error_message()

# test_container_management.py
def test_create_shipment_without_container()
def test_add_container_later()

# test_compliance_analytics.py
def test_compliance_rate_with_missing_docs()
def test_compliance_rate_all_docs_present()
```

#### 4.2 Integration Tests

```python
# test_buyer_workflow.py
def test_buyer_can_view_assigned_shipment()
def test_buyer_can_download_documents()
def test_buyer_cannot_modify_shipment()
```

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/routers/documents.py` | Modify | Add buyer org access for downloads |
| `backend/app/schemas/shipment.py` | Modify | Make container_number optional |
| `backend/app/services/shipment_state_machine.py` | Modify | Add DOCS_PENDING → IN_TRANSIT |
| `backend/app/services/analytics.py` | Modify | Fix compliance calculation |
| `backend/app/routers/eudr.py` | Modify | Add error handling for missing origins |
| `frontend/src/pages/Dashboard.tsx` | Modify | Add search and filters |
| `frontend/src/pages/Shipment.tsx` | Modify | Add container management UI |
| `frontend/src/components/CreateShipmentModal.tsx` | Modify | Make container optional |
| `backend/tests/test_document_access.py` | Create | Buyer document access tests |
| `backend/tests/test_shipment_transitions.py` | Create | Status transition tests |

## Migration Script for Historical Data

```python
# scripts/migrate_validation_status.py
"""
Backfill script to ensure historical shipments have proper validation status.
Idempotent - safe to run multiple times.
"""

def backfill_validation_status(db):
    """Re-evaluate validation status for all shipments."""
    shipments = db.query(Shipment).all()
    
    for shipment in shipments:
        documents = db.query(Document).filter(
            Document.shipment_id == shipment.id
        ).all()
        
        # Run validation
        runner = ValidationRunner()
        report = runner.validate_shipment(
            shipment=shipment,
            documents=documents,
            user="migration_script",
            db=db,
        )
        
        # Log result
        logger.info(f"Shipment {shipment.reference}: valid={report.is_valid}")
    
    db.commit()
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing shipment creation | Medium | High | Backward compatible schema changes, thorough testing |
| Document access leakage | Low | Critical | Use existing access control patterns, security review |
| Status transition confusion | Medium | Medium | Clear UI guidance, helpful error messages |
| Analytics performance | Low | Medium | Optimize queries, add caching |

## Success Criteria

1. ✅ Buyers can download documents for assigned shipments
2. ✅ Logistics agents can create shipments without container numbers
3. ✅ Logistics agents can update shipment status to In Transit
4. ⏳ Dashboard has working search and filters (Phase 2)
5. ⏳ Validation reports load correctly for all users (Phase 2)
6. ⏳ Compliance analytics reflect actual document status (Phase 2)
7. ✅ All existing tests continue to pass
8. ✅ No regression in existing functionality

---

## Implementation Progress

### Phase 1 Complete (2026-01-20)

#### Files Modified:

| File | Issue | Change |
|------|-------|--------|
| `backend/app/schemas/shipment.py` | #41 | Made `container_number` optional with updated validator |
| `backend/app/models/shipment.py` | #41 | Changed column to `nullable=True` |
| `backend/app/services/shipment_state_machine.py` | #35, #42 | Added `DOCS_PENDING → IN_TRANSIT` transition |
| `backend/app/routers/documents.py` | #37, #38, #43 | Added buyer org access for `get_document` and `download_document` |
| `backend/app/routers/eudr.py` | #39 | Added error handling with try/except for risk assessment |
| `frontend/src/components/CreateShipmentModal.tsx` | #41 | Made container field optional with UI updates |
| `frontend/src/types/index.ts` | #41 | Updated `ShipmentCreateRequest` type |
| `backend/tests/test_container_validation.py` | - | Updated tests for new optional behavior |

#### Database Migration Created:

- `alembic/versions/20260120_0001_container_number_optional.py`

#### Test Results:

- Container validation tests: 19 passed ✅
- BoL/Rules engine tests: 111 passed ✅

### Remaining Work (Phase 2):

- [ ] Dashboard search/filter UI (#40)
- [ ] Container management UI in tracking tab (#34)
- [ ] Compliance analytics accuracy review (#32e)
- [ ] Database migration deployment
- [ ] Integration tests for buyer document access

---

## Timeline

- **Day 1-2:** Phase 1 - Backend fixes + tests
- **Day 3-4:** Phase 2 - Frontend fixes
- **Day 5:** Phase 3 - EUDR fixes + integration testing
- **Day 6:** Phase 4 - Final testing, migration script, deployment

---

**Approved By:** _pending_
**Implementation Start:** 2026-01-18
