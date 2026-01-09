# PRP: Shipment Creation Feature

**Status:** In Progress
**Priority:** P1 - High
**Sprint:** 10
**Created:** 2026-01-09
**Owner:** Shola

---

## Overview

Enable ADMIN and SUPPLIER users to create shipments via a frontend form with buyer organization linking, ISO 6346 container validation, and sensible error handling. This feature bridges a critical gap where shipments can currently only be created via API or database seeding.

---

## Business Requirements

### User Story
As an **ADMIN or SUPPLIER user**, I want to **create shipments through a UI form**, so that **I can track new container shipments without direct database access**.

### Success Metrics
- Users can create shipments in < 30 seconds
- 100% of container numbers validated against ISO 6346 format
- Buyer organization properly linked for multi-tenant visibility

---

## Functional Requirements

- [ ] **REQ-001:** Add `buyer_organization_id` FK to shipments table (nullable for backward compatibility)
- [ ] **REQ-002:** Validate container numbers against ISO 6346 format (4 letters + 7 digits)
- [ ] **REQ-003:** Provide endpoint to list buyer organizations for dropdown
- [ ] **REQ-004:** Create shipment form with: Reference, Container, Vessel, Buyer, Historical checkbox
- [ ] **REQ-005:** Show "New Shipment" button only to users with `shipments:create` permission
- [ ] **REQ-006:** Display validation errors inline on form submission
- [ ] **REQ-007:** Redirect to shipment detail page after successful creation

---

## Non-Functional Requirements

### Performance
- [ ] Form submission response < 500ms
- [ ] Buyer dropdown loads in < 200ms

### Security
- [ ] Permission check: Only ADMIN, SUPPLIER can create shipments
- [ ] Organization isolation: Users can only link their accessible buyer orgs
- [ ] Input validation: Prevent SQL injection, XSS

### Usability
- [ ] Clear validation error messages
- [ ] Container format hint displayed
- [ ] Mobile responsive form

---

## Technical Approach

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        PHASE DIAGRAM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: DB Schema ──► Phase 2: Validation ──► Phase 3: API   │
│       │                       │                      │          │
│       ▼                       ▼                      ▼          │
│  [Migration]            [ISO 6346]           [/buyers endpoint] │
│                                                                 │
│  Phase 4: Shipment Router ──► Phase 5: Frontend Types          │
│       │                              │                          │
│       ▼                              ▼                          │
│  [buyer_org_id]              [Types + API Client]               │
│                                                                 │
│  Phase 6: Modal Component ──► Phase 7: Dashboard Integration   │
│       │                              │                          │
│       ▼                              ▼                          │
│  [CreateShipmentModal]       [Button + PermissionGuard]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components Affected

1. **Backend Components:**
   - `models/shipment.py` - Add buyer_organization_id FK
   - `schemas/shipment.py` - Add ISO 6346 validator, buyer_organization_id field
   - `routers/shipments.py` - Update create_shipment logic
   - `routers/organizations.py` - Add /buyers endpoint

2. **Frontend Components:**
   - `types/index.ts` - Add ShipmentCreateRequest
   - `api/client.ts` - Add createShipment(), getBuyerOrganizations()
   - `components/CreateShipmentModal.tsx` - NEW FILE
   - `pages/Dashboard.tsx` - Add New Shipment button

3. **Database Changes:**
   - Add `buyer_organization_id` column to shipments table (nullable)
   - Add foreign key constraint to organizations table
   - Add index for performance

### API Changes

**New Endpoints:**
- `GET /api/organizations/buyers` - List buyer organizations for dropdown

**Modified Endpoints:**
- `POST /api/shipments` - Accept optional `buyer_organization_id`

---

## Files to Modify

### Backend
- [ ] `tracehub/backend/app/models/shipment.py` - Add buyer_organization_id FK
- [ ] `tracehub/backend/app/schemas/shipment.py` - Add ISO 6346 validator
- [ ] `tracehub/backend/app/routers/shipments.py` - Validate buyer org on create
- [ ] `tracehub/backend/app/routers/organizations.py` - Add /buyers endpoint
- [ ] `tracehub/backend/alembic/versions/20260109_add_buyer_org_to_shipments.py` - NEW

### Backend Tests (TDD - Write First)
- [ ] `tracehub/backend/tests/test_shipment_creation.py` - NEW: Comprehensive tests
- [ ] `tracehub/backend/tests/test_organizations.py` - Add /buyers endpoint tests

### Frontend
- [ ] `tracehub/frontend/src/types/index.ts` - Add ShipmentCreateRequest, BuyerOrganization
- [ ] `tracehub/frontend/src/api/client.ts` - Add createShipment(), getBuyerOrganizations()
- [ ] `tracehub/frontend/src/components/CreateShipmentModal.tsx` - NEW FILE
- [ ] `tracehub/frontend/src/pages/Dashboard.tsx` - Add button + modal

### Frontend Tests (TDD - Write First)
- [ ] `tracehub/frontend/src/components/__tests__/CreateShipmentModal.test.tsx` - NEW

### E2E Tests
- [ ] `tracehub/frontend/e2e/shipment-creation.spec.ts` - NEW: E2E flow tests

### Documentation
- [ ] `tracehub/CHANGELOG.md` - Version entry

---

## Test Requirements

### Unit Tests (Backend)

**Phase 1: Schema Tests**
- [ ] Test buyer_organization_id accepts valid UUID
- [ ] Test buyer_organization_id is nullable (backward compatible)
- [ ] Test relationship loads correctly

**Phase 2: Validation Tests**
- [ ] Test valid ISO 6346 formats: MRSU3452572, TCNU1234567
- [ ] Test invalid formats rejected: ABC123, MRSU12345678, mrsu1234567
- [ ] Test container auto-uppercased

**Phase 3: Buyer Endpoint Tests**
- [ ] Test GET /organizations/buyers returns only BUYER type orgs
- [ ] Test endpoint requires authentication
- [ ] Test response schema matches OrganizationInfo

**Phase 4: Creation Tests**
- [ ] Test create shipment with valid buyer_organization_id
- [ ] Test create shipment with invalid buyer_organization_id fails
- [ ] Test create shipment without buyer_organization_id succeeds (optional)
- [ ] Test permission denied for VIEWER, COMPLIANCE, LOGISTICS_AGENT
- [ ] Test permission granted for ADMIN, SUPPLIER

### Unit Tests (Frontend)

**Phase 6: Modal Component Tests**
- [ ] Test form renders with all fields
- [ ] Test container validation shows error for invalid format
- [ ] Test buyer dropdown populates from API
- [ ] Test form submission calls createShipment
- [ ] Test error display on API failure
- [ ] Test success callback triggered

### E2E Tests

**Phase 7: Integration Tests**
- [ ] Test admin can see "New Shipment" button
- [ ] Test compliance user cannot see button
- [ ] Test full creation flow: open modal → fill form → submit → redirect
- [ ] Test validation error displayed for invalid container

---

## Compliance Check

**⚠️ CRITICAL: Review before implementation**

### Product Impact
- **Product HS Codes Affected:** None - this is shipment metadata only
- **Product Types:** N/A

### EUDR Applicability
- **EUDR Required:** No
- **Geolocation Required:** No
- **Deforestation Statement Required:** No

This feature handles shipment creation only, not product compliance data.

---

## Dependencies

### External Dependencies
- None (JSONCargo tracking is triggered separately after creation)

### Internal Dependencies
- [ ] Multi-tenancy system (already implemented)
- [ ] Permission system (already implemented)
- [ ] PermissionGuard component (already exists)

---

## Acceptance Criteria

- [ ] **AC-001:** Admin user can create shipment via UI form
- [ ] **AC-002:** Supplier user can create shipment via UI form
- [ ] **AC-003:** Compliance/Logistics/Viewer users cannot see create button
- [ ] **AC-004:** Invalid container format shows validation error
- [ ] **AC-005:** Buyer organization dropdown shows only BUYER type orgs
- [ ] **AC-006:** Created shipment appears in dashboard list
- [ ] **AC-007:** All existing tests continue to pass (no regression)
- [ ] **AC-008:** New unit tests achieve >90% coverage for new code

---

## Security Considerations

### Threats
- Unauthorized shipment creation
- Cross-tenant data leakage via buyer_organization_id
- SQL injection via form inputs

### Mitigations
- Permission check on POST /shipments endpoint
- Validate buyer_organization_id exists and is accessible
- Pydantic validation for all inputs
- Parameterized queries via SQLAlchemy

### Checklist
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] SQL injection prevented (SQLAlchemy ORM)
- [ ] XSS prevention (React auto-escapes)
- [ ] Permission checks enforced

---

## Rollout Plan

### Phase 1-4: Backend (No UI changes)
- Deploy to staging
- Run backend test suite
- Verify existing functionality unaffected

### Phase 5-6: Frontend Components
- Deploy modal component (not wired to Dashboard yet)
- Run frontend unit tests

### Phase 7: Dashboard Integration
- Add button to Dashboard
- Deploy complete feature
- Run E2E tests
- Monitor for errors

### Rollback Plan
- Each phase is independently deployable
- Migration is additive (nullable column) - no rollback needed
- Frontend button can be hidden via permission check without code deploy

---

## Implementation Phases (TDD)

### Phase 1: Database Schema (Backend)
**Goal:** Add buyer_organization_id FK without breaking existing code

1. RED: Write test for buyer_organization_id field
2. GREEN: Add migration and model field
3. REFACTOR: Add index for performance

**Files:**
- `tests/test_shipment_creation.py` (new tests)
- `alembic/versions/20260109_*.py` (migration)
- `models/shipment.py` (FK field)

**Verification:** `pytest tests/test_shipment_creation.py -v`

---

### Phase 2: ISO 6346 Validation (Backend)
**Goal:** Validate container numbers client-side and server-side

1. RED: Write tests for valid/invalid container formats
2. GREEN: Add Pydantic field_validator
3. REFACTOR: Extract regex to constant

**Files:**
- `tests/test_shipment_creation.py` (validation tests)
- `schemas/shipment.py` (validator)

**Verification:** `pytest tests/test_shipment_creation.py::TestContainerValidation -v`

---

### Phase 3: Buyer Organizations Endpoint (Backend)
**Goal:** Provide dropdown data for buyer selection

1. RED: Write tests for GET /organizations/buyers
2. GREEN: Add endpoint to organizations router
3. REFACTOR: Optimize query

**Files:**
- `tests/test_organizations.py` (new tests)
- `routers/organizations.py` (endpoint)

**Verification:** `pytest tests/test_organizations.py::TestBuyerOrganizations -v`

---

### Phase 4: Shipment Creation Update (Backend)
**Goal:** Accept and validate buyer_organization_id in create

1. RED: Write tests for create with buyer_organization_id
2. GREEN: Update router to handle new field
3. REFACTOR: Add permission validation for buyer org access

**Files:**
- `tests/test_shipment_creation.py` (creation tests)
- `routers/shipments.py` (update logic)
- `schemas/shipment.py` (add field to ShipmentCreate)

**Verification:** `pytest tests/test_shipment_creation.py::TestShipmentCreationWithBuyer -v`

---

### Phase 5: Frontend Types & API Client
**Goal:** Add TypeScript types and API methods

1. Add ShipmentCreateRequest interface
2. Add BuyerOrganization interface
3. Add createShipment() method
4. Add getBuyerOrganizations() method

**Files:**
- `types/index.ts`
- `api/client.ts`

**Verification:** `npm run typecheck`

---

### Phase 6: CreateShipmentModal Component
**Goal:** Build form component with validation

1. RED: Write Jest tests for modal rendering and validation
2. GREEN: Implement CreateShipmentModal component
3. REFACTOR: Extract validation logic

**Files:**
- `components/__tests__/CreateShipmentModal.test.tsx` (tests first)
- `components/CreateShipmentModal.tsx` (component)

**Verification:** `npm test -- CreateShipmentModal`

---

### Phase 7: Dashboard Integration & E2E
**Goal:** Wire up button and test full flow

1. RED: Write E2E tests for creation flow
2. GREEN: Add button to Dashboard with PermissionGuard
3. REFACTOR: Add loading states

**Files:**
- `e2e/shipment-creation.spec.ts` (E2E tests)
- `pages/Dashboard.tsx` (integration)

**Verification:** `npx playwright test shipment-creation.spec.ts`

---

## Notes

- JSONCargo tracking is NOT triggered automatically on creation
- User must manually refresh tracking from shipment detail page
- This maintains existing behavior and avoids API rate limit issues
- buyer_organization_id is optional to maintain backward compatibility with existing shipments

---

**Last Updated:** 2026-01-09
**Status:** In Progress
