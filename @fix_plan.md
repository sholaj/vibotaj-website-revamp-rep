# Ralph Fix Plan - BOL Container Extraction & Reference Relaxation

**PRP:** `PRPs/active/PRP-bol-container-extraction-reference-relaxation.md`
**Sprint:** 12
**TDD Approach:** Write tests first (RED), then implement (GREEN), then refactor

---

## Phase 1: Reference Format Relaxation (Backend) ✅ COMPLETE

### TEST-001: Write Reference Format Tests First
- [ ] Create `tracehub/backend/tests/test_shipment_reference.py` with:
  - [ ] `test_reference_accepts_standard_format()` - VIBO-2026-001 valid
  - [ ] `test_reference_accepts_historic_format()` - VIBO-HIST-FELIX-001 valid
  - [ ] `test_reference_accepts_customer_format()` - HAGES/2024/INV-001 valid
  - [ ] `test_reference_accepts_special_chars()` - ABC-123_456.789 valid
  - [ ] `test_reference_rejects_empty()` - Empty string rejected
  - [ ] `test_reference_rejects_too_long()` - >50 chars rejected
  - [ ] `test_reference_uniqueness_per_organization()` - Same ref in diff orgs allowed
- [ ] Run tests - expect PASS (no strict validation currently exists)

### IMPL-001: Verify Reference Validation is Flexible
- [ ] In `tracehub/backend/app/schemas/shipment.py`, confirm no strict regex on reference field
- [ ] Add `@field_validator('reference')` for basic validation (non-empty, max 50 chars, allowed chars)
- [ ] Update ShipmentCreate schema docstring to document allowed formats
- [ ] Run tests - all should PASS

---

## Phase 2: Container Extraction Service Enhancement (Backend) ✅ COMPLETE

### TEST-002: Write Container Extraction Tests First
- [ ] Create `tracehub/backend/tests/test_container_extraction.py` with:
  - [ ] `test_extract_container_from_bol_text()` - Extract MRSU3452572 from sample BOL
  - [ ] `test_extract_container_with_spaces()` - 'MRSU 3452572' normalizes to 'MRSU3452572'
  - [ ] `test_extract_container_with_dashes()` - 'MRSU-345-2572' normalizes correctly
  - [ ] `test_extract_multiple_containers_returns_first()` - First valid container returned
  - [ ] `test_reject_invalid_container_format()` - 'BECKMANN-CNT-001' rejected
  - [ ] `test_is_placeholder_container()` - Detect placeholder patterns
  - [ ] `test_extraction_returns_confidence_score()` - Returns 0.0-1.0 confidence
- [ ] Run tests - expect FAIL (extraction not yet enhanced)

### IMPL-002: Enhance ShipmentDataExtractor
- [ ] In `tracehub/backend/app/services/shipment_data_extractor.py`:
  - [ ] Add new regex patterns for Container No., Equipment No., Unit No. formats (~line 100)
  - [ ] Add `is_placeholder_container(container: str) -> bool` function
  - [ ] Add `extract_container_with_confidence(text: str) -> Tuple[str, float]` method
  - [ ] Add confidence scoring based on pattern match quality
- [ ] Run tests - all should PASS

---

## Phase 3: Document Model Enhancement (Backend) ✅ COMPLETE

### TEST-003: Write Document Field Tests First
- [ ] In `tracehub/backend/tests/test_documents.py`, add:
  - [ ] `test_document_stores_extracted_container()` - Document can store extracted container
  - [ ] `test_document_stores_extraction_confidence()` - Document stores confidence score
  - [ ] `test_bol_upload_triggers_extraction()` - Uploading BOL extracts container
  - [ ] `test_extraction_result_in_upload_response()` - API returns extracted data
- [ ] Run tests - expect FAIL (fields don't exist yet)

### IMPL-003: Add Document Fields and Migration
- [ ] Create migration `tracehub/backend/alembic/versions/20260115_add_container_extraction_fields.py`:
  - [ ] Add `extracted_container_number` VARCHAR(20) nullable to documents table
  - [ ] Add `extraction_confidence` FLOAT nullable to documents table
- [ ] In `tracehub/backend/app/models/document.py`:
  - [ ] Add `extracted_container_number = Column(String(20), nullable=True)`
  - [ ] Add `extraction_confidence = Column(Float, nullable=True)`
- [ ] In `tracehub/backend/app/schemas/document.py`:
  - [ ] Add fields to Document response schema
- [ ] Run migration: `cd tracehub/backend && alembic upgrade head`
- [ ] Run tests - should PASS

---

## Phase 4: BOL Upload Integration (Backend) ✅ COMPLETE

### TEST-004: Write Upload Integration Tests First
- [ ] In `tracehub/backend/tests/test_bol_upload.py`, add:
  - [ ] `test_upload_bol_extracts_container()` - Upload PDF, verify extraction
  - [ ] `test_extraction_stored_in_document()` - Check DB record has extracted data
  - [ ] `test_extraction_returned_in_response()` - API response includes extraction
  - [ ] `test_non_bol_upload_no_extraction()` - Invoice upload skips extraction
- [ ] Run tests - expect FAIL (integration not wired)

### IMPL-004: Wire Extraction into Document Upload
- [ ] In `tracehub/backend/app/routers/documents.py`:
  - [ ] After document classification (~line 220), if type is BILL_OF_LADING:
    - [ ] Call `shipment_data_extractor.extract_container_with_confidence(text)`
    - [ ] Store result in `document.extracted_container_number`
    - [ ] Store confidence in `document.extraction_confidence`
  - [ ] Include extracted data in upload response
- [ ] Run tests - should PASS

---

## Phase 5: Shipment Container Update API (Backend) ✅ COMPLETE

### TEST-005: Write Container Update Endpoint Tests First
- [ ] In `tracehub/backend/tests/test_shipment_container_update.py`, add:
  - [ ] `test_update_container_success()` - PATCH /shipments/{id}/container works
  - [ ] `test_update_container_validates_iso6346()` - Invalid format rejected
  - [ ] `test_update_container_requires_permission()` - VIEWER cannot update
  - [ ] `test_update_container_logs_change()` - Audit trail created
  - [ ] `test_update_container_from_placeholder()` - Placeholder replaced
- [ ] Run tests - expect FAIL (endpoint doesn't exist)

### IMPL-005: Create Container Update Endpoint
- [ ] In `tracehub/backend/app/routers/shipments.py`:
  - [ ] Add schema `ContainerUpdateRequest(container_number: str)`
  - [ ] Add `@router.patch("/{shipment_id}/container")` endpoint
  - [ ] Validate container against ISO 6346
  - [ ] Update shipment record
  - [ ] Log change in audit (old_value, new_value)
  - [ ] Return updated shipment
- [ ] Run tests - should PASS

---

## Phase 6: Frontend Container Suggestion (Frontend) ✅ COMPLETE

### TEST-006: Write Frontend Component Tests First
- [ ] Create `tracehub/frontend/src/components/__tests__/ContainerSuggestion.test.tsx`:
  - [ ] `test_renders_suggestion_when_available()` - Shows extracted container
  - [ ] `test_shows_confidence_badge()` - Displays confidence percentage
  - [ ] `test_accept_button_calls_api()` - Accept triggers update
  - [ ] `test_dismiss_hides_suggestion()` - Dismiss removes banner
  - [ ] `test_hidden_when_no_suggestion()` - No banner without suggestion
- [ ] Run tests - expect FAIL (component doesn't exist)

### IMPL-006: Create ContainerSuggestion Component
- [ ] Create `tracehub/frontend/src/components/ContainerSuggestion.tsx`:
  - [ ] Props: `extractedContainer`, `confidence`, `shipmentId`, `onAccept`, `onDismiss`
  - [ ] Render info banner with extracted container
  - [ ] Show confidence as percentage badge
  - [ ] Accept and Dismiss buttons
- [ ] In `tracehub/frontend/src/types/index.ts`:
  - [ ] Add `extracted_container_number?: string` to Document type
  - [ ] Add `extraction_confidence?: number` to Document type
- [ ] In `tracehub/frontend/src/api/client.ts`:
  - [ ] Add `updateShipmentContainer(shipmentId: string, container: string)` method
- [ ] Run tests - should PASS

---

## Phase 7: Shipment Detail Integration (Frontend) ✅ COMPLETE

### TEST-007: Write Integration Tests First
- [ ] In `tracehub/frontend/src/pages/__tests__/ShipmentDetail.test.tsx`:
  - [ ] `test_shows_suggestion_for_placeholder_container()` - Banner appears
  - [ ] `test_hides_suggestion_for_valid_container()` - No banner for ISO 6346 container
  - [ ] `test_updates_container_on_accept()` - Container updates after accept
- [ ] Run tests - expect FAIL (integration not wired)

### IMPL-007: Integrate ContainerSuggestion into ShipmentDetail
- [ ] In `tracehub/frontend/src/pages/ShipmentDetail.tsx`:
  - [ ] Import ContainerSuggestion component
  - [ ] Check if shipment has placeholder container (pattern: `-CNT-`)
  - [ ] Check if any BOL document has extracted_container_number
  - [ ] If both true, render ContainerSuggestion banner
  - [ ] Handle accept/dismiss callbacks
- [ ] Run tests - should PASS

---

## Phase 8: Batch Processing Script (Backend) ✅ COMPLETE

### TEST-008: Write Script Tests First
- [ ] Create `tracehub/backend/tests/test_batch_container_extraction.py`:
  - [ ] `test_identifies_placeholder_containers()` - Finds shipments with placeholders
  - [ ] `test_extracts_from_bol_documents()` - Processes BOL documents
  - [ ] `test_dry_run_no_changes()` - Dry run doesn't modify DB
  - [ ] `test_generates_report()` - Creates results report
- [ ] Run tests - expect FAIL (script doesn't exist)

### IMPL-008: Create Batch Extraction Script
- [ ] Create `tracehub/backend/scripts/extract_containers_from_bols.py`:
  - [ ] Query shipments with placeholder containers (LIKE '%-CNT-%')
  - [ ] For each shipment, find BOL documents
  - [ ] Extract container number from BOL text
  - [ ] In dry-run mode: log what would change
  - [ ] In apply mode: update shipment.container_number
  - [ ] Generate JSON report with results
- [ ] Add CLI args: `--dry-run`, `--env`, `--shipment-id`
- [ ] Run tests - should PASS

---

## Phase 9: Fix Historic Shipments (Production) 🔄 IN PROGRESS

### PROD-001: Run Batch Extraction on Staging
- [ ] SSH to VPS: `ssh root@82.198.225.150`
- [ ] Run dry-run: `docker exec tracehub-backend-staging python scripts/extract_containers_from_bols.py --env staging --dry-run`
- [ ] Review output for correct extractions
- [ ] If correct, run: `docker exec tracehub-backend-staging python scripts/extract_containers_from_bols.py --env staging`
- [ ] Verify updated containers in staging UI

### PROD-002: Run Batch Extraction on Production
- [ ] Run dry-run: `docker exec tracehub-backend python scripts/extract_containers_from_bols.py --env production --dry-run`
- [ ] Review output
- [ ] Run: `docker exec tracehub-backend python scripts/extract_containers_from_bols.py --env production`
- [ ] Verify these shipments have real container numbers:
  - [ ] VIBO-HIST-WITATRADE-002 (was: WITATRADE-CNT-002)
  - [ ] VIBO-HIST-BECKMANN-001 (was: BECKMANN-CNT-001)
  - [ ] VIBO-HIST-BECKMANN-002 (was: BECKMANN-CNT-002)

---

## Phase 10: Deployment & Verification 🔄 IN PROGRESS

### DEPLOY-001: Deploy to Staging
- [ ] Run all backend tests: `cd tracehub/backend && pytest -v`
- [ ] Run all frontend tests: `cd tracehub/frontend && npm test`
- [ ] Commit with message: `feat(documents): add BOL container extraction with TDD`
- [ ] Push to develop: `git checkout develop && git merge feature/bol-container-extraction && git push`
- [ ] Verify staging deployment succeeds

### DEPLOY-002: Deploy to Production
- [ ] Verify all staging tests pass
- [ ] Verify container extraction works in staging UI
- [ ] Merge to main: `git checkout main && git merge develop && git push`
- [ ] Verify production deployment succeeds
- [ ] Run batch extraction script on production

---

## Completed

- [x] PRP created: `PRPs/active/PRP-bol-container-extraction-reference-relaxation.md`
- [x] Fix plan created with TDD phases

---

## Test Commands

```bash
# Backend tests
cd tracehub/backend
pytest tests/test_shipment_reference.py -v
pytest tests/test_container_extraction.py -v
pytest tests/test_bol_upload.py -v
pytest tests/test_shipment_container_update.py -v
pytest tests/test_batch_container_extraction.py -v
pytest -v  # All tests

# Frontend tests
cd tracehub/frontend
npm test -- ContainerSuggestion
npm test -- ShipmentDetail
npm test  # All tests
```

---

## Notes

- **TDD Approach**: Each phase starts with TEST- task (write failing tests), then IMPL- task (make tests pass)
- **ISO 6346 Format**: 4 letters + 7 digits (e.g., MRSU3452572)
- **Placeholder Pattern**: Contains `-CNT-` (e.g., BECKMANN-CNT-001)
- **AI Extraction**: Uses regex patterns first, AI as enhancement
- **Confidence Threshold**: 85%+ for auto-suggestion
- Always run tests after each change
- Follow GitOps: feature branch -> develop -> main
