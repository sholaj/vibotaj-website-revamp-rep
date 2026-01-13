# Ralph Fix Plan - TraceHub Technical Debt Remediation

## Phase 1: Critical Security Fixes ✅ COMPLETE

### SEC-001: Fix Document organization_id Assignment ✅
- [x] In `tracehub/backend/app/routers/documents.py`, add `organization_id=current_user.organization_id` to Document creation (~line 201)
- [x] Add test `test_document_upload_sets_organization_id` to verify org_id is set
- [x] Add test `test_document_visible_after_upload` to verify uploader can retrieve document
- [x] Add test `test_document_not_visible_to_other_org` to verify cross-org isolation

### SEC-002: Fix Shipment Deletion 500 Error ✅
- [x] In `tracehub/backend/app/routers/shipments.py`, add deletion of ReferenceRegistry before Document deletion (~line 436)
- [x] Add deletion of DocumentContent before Document deletion
- [x] Add deletion of Origin, ContainerEvents, Products before Shipment deletion
- [x] Add test `test_shipment_delete_with_all_relations` to verify clean cascade deletion
- [x] Add test for deletion with documents, origins, container events, and products

## Phase 2: Data Model Alignment ✅ COMPLETE

### TICKET-001: Standardize ShipmentStatus Enums ✅
- [x] In `tracehub/frontend/src/types/index.ts`, update ShipmentStatus type to use `draft` instead of `created`
- [x] Add `customs` to frontend ShipmentStatus type
- [x] Change `closed` to `archived` in frontend ShipmentStatus type
- [x] Update `tracehub/frontend/src/pages/Dashboard.tsx` to handle all 8 statuses
- [x] Update `tracehub/frontend/src/pages/Shipment.tsx` to handle all 8 statuses

### TICKET-002: Unify Document Field Naming ✅
- [x] In `tracehub/frontend/src/types/index.ts`, update Document interface: `file_size_bytes` → `file_size`
- [x] Update Document interface: `issue_date` → `document_date`
- [x] Update Document interface: `issuing_authority` → `issuer`
- [x] Update `DocumentReviewPanel.tsx` to use new field names
- [x] Update `DocumentList.tsx` to use new field names
- [x] Update `api/client.ts` to use new field names

## Phase 3: UX Improvements ✅ COMPLETE

### TICKET-005/006: Fix Dashboard Navigation ✅
- [x] In `tracehub/frontend/src/components/Layout.tsx`, rename "Dashboard" nav item to "Shipments"
- [x] Rename "Analytics" nav item to "Dashboard" (shows overview stats)
- [x] Navigation now correctly reflects page content

## Completed

- [x] Project initialization
- [x] Multi-tenancy architecture (Sprint 8)
- [x] Compliance matrix updates (Sprint 9)
- [x] Architecture cleanup (Sprint 10)
- [x] Schema fixes, buyer access (Sprint 11)
- [x] Cache invalidation pattern fix (phases 1-2)
- [x] Organization member management (Sprint 13)
- [x] Compliance feature hardening (Sprint 14)
- [x] Ralph autonomous development setup
- [x] PRP created for technical debt remediation
- [x] **Phase 1: Security fixes (SEC-001, SEC-002)** - Commit `fee09b4`
- [x] **Phase 2: Data model alignment (TICKET-001, TICKET-002)** - Commit `fee09b4`
- [x] **Phase 3: UX improvements (TICKET-005/006)** - Commit `fee09b4`

## Test Results

- 3 tests for SEC-001 (document organization isolation) - PASSING
- 5 tests for SEC-002 (cascade deletion scenarios) - PASSING
- All 8 new tests passing

## Notes

- **All critical security fixes complete**
- Always check `docs/COMPLIANCE_MATRIX.md` before compliance work
- Horn/hoof products (HS 0506/0507) are NOT covered by EUDR
- All queries MUST filter by `organization_id` (multi-tenancy)
- Follow GitOps: feature branch -> develop -> main
- Run tests after each change: `cd tracehub/backend && pytest`
- Frontend tests: `cd tracehub/frontend && npm test`
