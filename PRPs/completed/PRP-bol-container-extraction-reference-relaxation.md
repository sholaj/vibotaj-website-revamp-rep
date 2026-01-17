# PRP: BOL Container Extraction & Shipment Reference Relaxation

**Status:** ✅ Completed (2026-01-17)
**Priority:** P1 - High
**Sprint:** 12
**Created:** 2026-01-15
**Owner:** Shola

---

## Overview

Address two data quality issues discovered during historic shipment import:

1. **Shipment Reference Format Relaxation**: Current historic shipments use placeholder references like `VIBO-HIST-BECKMANN-001` which don't conform to real-world formats. The system should accept flexible reference formats without rigid validation.

2. **AI-Powered Container Number Extraction**: Several historic shipments have placeholder container numbers (e.g., `WITATRADE-CNT-002`, `BECKMANN-CNT-001`) because the actual container numbers weren't extracted from uploaded Bill of Lading documents. The AI document classifier should automatically extract container numbers from BOL documents and update shipment records.

### Problem Evidence

| Reference | Container (Current) | Issue |
|-----------|---------------------|-------|
| VIBO-HIST-WITATRADE-002 | WITATRADE-CNT-002 | Placeholder - not ISO 6346 compliant |
| VIBO-HIST-BECKMANN-001 | BECKMANN-CNT-001 | Placeholder - not ISO 6346 compliant |
| VIBO-HIST-BECKMANN-002 | BECKMANN-CNT-002 | Placeholder - not ISO 6346 compliant |

### Business Value

- **Data Quality**: Accurate container numbers enable tracking via JSONCargo API
- **Compliance**: Correct references improve audit trail accuracy
- **Automation**: Reduces manual data entry errors
- **Historic Import**: Enables proper onboarding of existing customer shipment data

---

## Requirements

### Functional Requirements

#### Feature 1: Shipment Reference Format Relaxation

- [ ] **REQ-001**: Remove strict reference format validation (currently no validation exists, confirm)
- [ ] **REQ-002**: Allow alphanumeric references up to 50 characters
- [ ] **REQ-003**: Allow special characters: `-`, `_`, `/`, `.`
- [ ] **REQ-004**: Maintain uniqueness constraint per organization
- [ ] **REQ-005**: Auto-generate reference if not provided (format: `VIBO-{YYYY}-{SEQ}` for VIBOTAJ)

#### Feature 2: AI Container Number Extraction from BOL

- [ ] **REQ-006**: Extract container number from BOL during document upload
- [ ] **REQ-007**: Validate extracted container against ISO 6346 format
- [ ] **REQ-008**: Suggest container number update if shipment has placeholder
- [ ] **REQ-009**: Allow user to confirm/reject auto-extracted container number
- [ ] **REQ-010**: Update shipment record upon user confirmation
- [ ] **REQ-011**: Log extraction confidence score for audit

#### Feature 3: Batch Container Update for Existing Shipments

- [ ] **REQ-012**: Admin endpoint to trigger re-extraction for shipments with placeholder containers
- [ ] **REQ-013**: Script to process historic shipments and extract missing container numbers
- [ ] **REQ-014**: Report showing extraction results and confidence scores

### Non-Functional Requirements

- [ ] **NFR-001**: Extraction processing time < 5 seconds per document
- [ ] **NFR-002**: Confidence threshold for auto-suggestion: 85%+
- [ ] **NFR-003**: Fallback to manual entry if AI unavailable
- [ ] **NFR-004**: Audit log all container number changes

---

## Technical Approach

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BOL CONTAINER EXTRACTION FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Document Upload ──► PDF Processor ──► Text Extraction                      │
│        │                                    │                               │
│        ▼                                    ▼                               │
│  Document Classifier ◄──────────────── AI Analysis                          │
│        │                                    │                               │
│        ▼                                    ▼                               │
│  [Type: BOL?] ─────YES────► Shipment Data Extractor                         │
│        │                           │                                        │
│        NO                          ▼                                        │
│        │                    Extract Container Number                        │
│        ▼                           │                                        │
│     Skip                           ▼                                        │
│                            ISO 6346 Validation                              │
│                                    │                                        │
│                         ┌─────────┴─────────┐                               │
│                         ▼                   ▼                               │
│                    [Valid]             [Invalid]                            │
│                         │                   │                               │
│                         ▼                   ▼                               │
│              Store Suggested          Log Warning                           │
│              Container Number         Skip Update                           │
│                         │                                                   │
│                         ▼                                                   │
│              [Shipment Has Placeholder?]                                    │
│                    │         │                                              │
│                   YES        NO                                             │
│                    │         │                                              │
│                    ▼         ▼                                              │
│              Prompt User    Store as                                        │
│              for Update     Alternative                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation Strategy

#### Phase 1: Reference Format Relaxation (Backend)

1. **Audit current validation** - Confirm no strict format validation exists
2. **Add flexible validator** - Allow common reference patterns
3. **Auto-generation service** - Generate references when not provided
4. **Update tests** - Ensure flexibility while maintaining uniqueness

#### Phase 2: Enhanced Container Extraction (Backend)

1. **Improve regex patterns** - Add more BOL container number formats
2. **AI extraction prompt** - Use Claude to extract container with context
3. **Confidence scoring** - Return extraction confidence
4. **Suggested container field** - Store AI suggestion on document model

#### Phase 3: Shipment Update Flow (Backend + Frontend)

1. **New endpoint** - `PATCH /shipments/{id}/container` for targeted updates
2. **Document-shipment linking** - Auto-populate suggestion on BOL upload
3. **UI notification** - Show "Container number detected" banner
4. **Confirmation flow** - User approves/rejects suggested update

#### Phase 4: Batch Processing Script

1. **Admin script** - Re-process existing BOL documents
2. **Dry-run mode** - Preview changes before applying
3. **Results report** - Summary of extraction success/failure

---

## Files to Modify

### Backend

| File | Changes |
|------|---------|
| `app/models/shipment.py` | Add `suggested_container_number` field (optional) |
| `app/models/document.py` | Add `extracted_container_number`, `extraction_confidence` fields |
| `app/schemas/shipment.py` | Relax reference validation, add container update schema |
| `app/services/shipment_data_extractor.py` | Improve container regex patterns, add AI extraction |
| `app/services/document_classifier.py` | Add container extraction to BOL classification |
| `app/routers/shipments.py` | Add `PATCH /shipments/{id}/container` endpoint |
| `app/routers/documents.py` | Return extracted container in upload response |
| `alembic/versions/20260115_*.py` | Migration for new fields |

### Backend Scripts

| File | Purpose |
|------|---------|
| `scripts/extract_containers_from_bols.py` | **NEW** - Batch extraction script |
| `scripts/create_historic_shipments.py` | Update to use real container numbers |

### Frontend

| File | Changes |
|------|---------|
| `src/types/index.ts` | Add `extractedContainerNumber`, `extractionConfidence` to Document type |
| `src/components/DocumentUploadModal.tsx` | Show extracted container suggestion |
| `src/pages/ShipmentDetail.tsx` | Show container update prompt if placeholder detected |
| `src/api/client.ts` | Add `updateShipmentContainer()` method |

### Tests

| File | Purpose |
|------|---------|
| `tests/test_container_extraction.py` | **NEW** - Container extraction tests |
| `tests/test_shipment_reference.py` | **NEW** - Reference format flexibility tests |
| `tests/test_shipment_data_extractor.py` | Update for new extraction logic |

---

## Test Requirements

### Unit Tests (TDD - Write First)

#### Reference Format Tests
```python
# tests/test_shipment_reference.py

def test_reference_accepts_standard_format():
    """VIBO-2026-001 should be valid"""

def test_reference_accepts_historic_format():
    """VIBO-HIST-FELIX-001 should be valid"""

def test_reference_accepts_customer_format():
    """HAGES/2024/INV-001 should be valid"""

def test_reference_accepts_alphanumeric_with_special_chars():
    """ABC-123_456.789 should be valid"""

def test_reference_rejects_empty():
    """Empty string should be rejected"""

def test_reference_rejects_too_long():
    """Reference > 50 chars should be rejected"""

def test_reference_uniqueness_per_organization():
    """Same reference in different orgs should be allowed"""
```

#### Container Extraction Tests
```python
# tests/test_container_extraction.py

def test_extract_container_from_bol_text():
    """Extract MRSU3452572 from BOL text"""

def test_extract_container_with_spaces():
    """Extract 'MRSU 3452572' and normalize to 'MRSU3452572'"""

def test_extract_container_with_dashes():
    """Extract 'MRSU-3452572' and normalize"""

def test_extract_multiple_containers_returns_first():
    """When multiple containers in text, return first valid one"""

def test_reject_invalid_container_format():
    """'BECKMANN-CNT-001' should not pass ISO 6346 validation"""

def test_ai_extraction_confidence_score():
    """AI extraction should return confidence 0.0-1.0"""

def test_fallback_to_regex_when_ai_unavailable():
    """When Claude unavailable, use regex patterns"""
```

#### Integration Tests
```python
# tests/test_bol_upload_extraction.py

def test_bol_upload_extracts_container():
    """Uploading BOL PDF should extract and return container number"""

def test_bol_extraction_suggests_update_for_placeholder():
    """When shipment has placeholder container, suggest update"""

def test_container_update_endpoint():
    """PATCH /shipments/{id}/container should update container"""

def test_container_update_requires_permission():
    """Only ADMIN/SUPPLIER can update container"""
```

### E2E Tests
```python
# e2e/container-extraction.spec.ts

test('upload BOL and see extracted container suggestion')
test('confirm container update from suggestion')
test('reject container suggestion keeps original')
```

---

## Compliance Check

**Product HS Codes Affected:** None - this is shipment/document metadata only

**EUDR Applicable:** No

**Required Documents:** N/A - this feature improves metadata accuracy, not document requirements

**Compliance Impact:**
- Improves audit trail by capturing accurate container numbers
- No EUDR fields affected
- No geolocation data involved

---

## Dependencies

### External
- **Anthropic API** - Claude Haiku for AI extraction (existing)
- **Tesseract OCR** - For scanned BOL documents (existing)

### Internal
- **PDF Processor Service** - Text extraction (existing)
- **Document Classifier** - BOL detection (existing)
- **Shipment Data Extractor** - Field extraction (existing, to be enhanced)

---

## Acceptance Criteria

### Feature 1: Reference Relaxation
- [ ] **AC-001**: System accepts references in formats: `VIBO-2026-001`, `VIBO-HIST-*`, `CUSTOMER/YEAR/NUM`
- [ ] **AC-002**: References with `-`, `_`, `/`, `.` characters are valid
- [ ] **AC-003**: Duplicate reference in same organization is rejected
- [ ] **AC-004**: Empty reference triggers auto-generation

### Feature 2: Container Extraction
- [ ] **AC-005**: BOL upload extracts container number with 85%+ confidence
- [ ] **AC-006**: Extracted container is validated against ISO 6346
- [ ] **AC-007**: UI shows "Container detected: XXXX" after BOL upload
- [ ] **AC-008**: User can accept/reject suggested container update

### Feature 3: Batch Processing
- [ ] **AC-009**: Script identifies shipments with placeholder containers
- [ ] **AC-010**: Script re-processes BOL documents and extracts containers
- [ ] **AC-011**: Report shows extraction results with confidence scores
- [ ] **AC-012**: No data lost during batch processing (dry-run first)

### General
- [ ] **AC-013**: All existing tests pass (no regression)
- [ ] **AC-014**: New tests achieve >90% coverage for new code
- [ ] **AC-015**: Extraction works for scanned PDFs via OCR

---

## Security Considerations

### Threats
- Data integrity: Incorrect container extraction corrupting shipment data
- Unauthorized updates: Non-admin users modifying container numbers

### Mitigations
- Require user confirmation for AI-suggested updates
- Permission check on container update endpoint (ADMIN/SUPPLIER only)
- Audit log all container changes with before/after values
- Dry-run mode for batch scripts

### Checklist
- [ ] Container updates logged in audit trail
- [ ] Permission checks enforced on update endpoint
- [ ] AI suggestions require user confirmation
- [ ] Batch script has dry-run mode

---

## Rollout Plan

### Phase 1: Backend Changes (Staging)
1. Deploy migration for new document fields
2. Deploy enhanced extraction service
3. Test extraction on staging BOL documents
4. Verify no regression in document upload

### Phase 2: Frontend Changes (Staging)
1. Deploy container suggestion UI
2. Test user confirmation flow
3. Verify extraction displays correctly

### Phase 3: Batch Script (Staging)
1. Run extraction script in dry-run mode
2. Review results report
3. Run actual extraction on approval
4. Verify updated container numbers

### Phase 4: Production Deployment
1. Deploy backend + frontend together
2. Run batch script in dry-run on production
3. Review and approve batch updates
4. Monitor for issues

### Rollback Plan
- Document fields are additive (no breaking changes)
- Batch script logs original values for rollback
- UI gracefully handles missing suggestion fields
- Can revert to previous extraction logic if issues

---

## Container Extraction Patterns

### Current Regex Patterns (shipment_data_extractor.py)
```python
"container_number": [
    r'\b([A-Z]{4}\s*\d{7})\b',
    r'\b([A-Z]{4}[-\s]?\d{6,7}[-\s]?\d?)\b',
    r'(?:Container|CNTR|CTR)[\s:]*#?\s*([A-Z]{4}\s*\d{7})',
],
```

### Enhanced Patterns (to add)
```python
"container_number": [
    # Existing patterns
    r'\b([A-Z]{4}\s*\d{7})\b',
    r'\b([A-Z]{4}[-\s]?\d{6,7}[-\s]?\d?)\b',
    r'(?:Container|CNTR|CTR)[\s:]*#?\s*([A-Z]{4}\s*\d{7})',

    # New patterns for common BOL formats
    r'Container\s*No\.?\s*:?\s*([A-Z]{4}\d{7})',
    r'CNTR\s*#?\s*:?\s*([A-Z]{4}\d{7})',
    r'Equipment\s*No\.?\s*:?\s*([A-Z]{4}\d{7})',
    r'Unit\s*No\.?\s*:?\s*([A-Z]{4}\d{7})',
    r'(?:^|\s)([A-Z]{3}U\d{7})(?:\s|$)',  # Standard ISO prefix ending in U
],
```

### AI Extraction Prompt
```
Extract the container number from this Bill of Lading text.
Container numbers follow ISO 6346 format: 4 letters (owner code ending in U, J, or Z) + 7 digits.
Examples: MRSU3452572, TCNU1234567, MSKU9876543

Text:
{document_text}

Return JSON: {"container_number": "XXXX1234567", "confidence": 0.95}
If no container found, return: {"container_number": null, "confidence": 0.0}
```

---

## Implementation Phases (TDD)

### Phase 1: Reference Relaxation (1-2 hours)
**Goal:** Ensure flexible reference formats are accepted

1. **RED**: Write reference format tests
2. **GREEN**: Implement/verify flexible validation
3. **REFACTOR**: Add auto-generation for empty references

### Phase 2: Enhanced Extraction Service (2-3 hours)
**Goal:** Improve container extraction from BOL text

1. **RED**: Write container extraction tests
2. **GREEN**: Add new regex patterns + AI extraction
3. **REFACTOR**: Return confidence scores

### Phase 3: Database & API Changes (2-3 hours)
**Goal:** Store and expose extracted container data

1. **RED**: Write API tests for container update
2. **GREEN**: Add migration, endpoint, document fields
3. **REFACTOR**: Add permission checks

### Phase 4: Frontend Integration (2-3 hours)
**Goal:** Display suggestions and enable updates

1. **RED**: Write component tests
2. **GREEN**: Add UI for container suggestion
3. **REFACTOR**: Add loading states and error handling

### Phase 5: Batch Processing Script (2-3 hours)
**Goal:** Fix existing placeholder containers

1. **RED**: Test script in dry-run mode
2. **GREEN**: Implement extraction and update logic
3. **REFACTOR**: Generate results report

---

## Notes

- ISO 6346 container format: 4 letters (last is U, J, or Z) + 6 serial digits + 1 check digit = 11 chars
- Current `create_historic_shipments.py` uses placeholder values when real containers unknown
- BOL is the authoritative source for container numbers
- Multiple containers per shipment are possible but rare for VIBOTAJ (single-container shipments)
- AI extraction should use Claude Haiku (fast, cost-effective) with regex fallback

---

**Last Updated:** 2026-01-15
**Status:** Draft - Awaiting Review
