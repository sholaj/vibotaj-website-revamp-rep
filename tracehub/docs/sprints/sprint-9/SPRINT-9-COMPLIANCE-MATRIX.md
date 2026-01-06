# Sprint 9: Compliance Matrix Implementation

**Sprint Duration:** 1 week
**Sprint Goal:** Align codebase with COMPLIANCE_MATRIX.md requirements using TDD
**Status:** ACTIVE
**Created:** 2026-01-06

---

## Sprint Overview

The compliance matrix (`docs/COMPLIANCE_MATRIX.md`) defines the single source of truth for HS codes and document requirements. This sprint ensures the codebase fully implements these requirements with proper validation, test coverage, and enforcement.

**Key Principle:** Work back-to-front with TDD (Test-Driven Development)
1. Write failing tests first
2. Implement minimum code to pass tests
3. Refactor for clarity
4. Move to next layer

---

## Gap Analysis Summary

| Gap | Severity | Layer |
|-----|----------|-------|
| Missing `is_eudr_required()` centralized function | High | Backend + Frontend |
| Missing product types (0714, 0902, 0910) in REQUIRED_DOCUMENTS | High | Backend |
| No validation rules for EU_TRACES_CERTIFICATE | Medium | Backend |
| No validation rules for VETERINARY_HEALTH_CERTIFICATE | Medium | Backend |
| No enforcement preventing EUDR fields on non-EUDR products | Medium | Backend |
| Hardcoded HS codes in frontend (not centralized) | Low | Frontend |
| Skipped integration tests | Low | Backend |

---

## Sprint Backlog

### Phase 1: Core Backend Logic (TDD)

#### Task 1.1: Centralized EUDR Check Function

**Priority:** High
**TDD Order:** Tests first

**Test File:** `tracehub/backend/tests/test_compliance.py`

```python
# Tests to write FIRST:
def test_is_eudr_required_cocoa_beans():
    """HS 1801 (cocoa) requires EUDR."""
    assert is_eudr_required("1801") is True
    assert is_eudr_required("1801.00") is True

def test_is_eudr_required_horn_hoof():
    """HS 0506/0507 (horn/hoof) does NOT require EUDR."""
    assert is_eudr_required("0506") is False
    assert is_eudr_required("0507") is False
    assert is_eudr_required("0506.90.00") is False

def test_is_eudr_required_other_products():
    """Non-EUDR product categories."""
    assert is_eudr_required("0714.20") is False  # Sweet potato
    assert is_eudr_required("0902.10") is False  # Hibiscus
    assert is_eudr_required("0910.11") is False  # Ginger

def test_is_eudr_required_eudr_products():
    """All EUDR-covered HS codes."""
    assert is_eudr_required("0901") is True  # Coffee
    assert is_eudr_required("1511") is True  # Palm oil
    assert is_eudr_required("4001") is True  # Rubber
    assert is_eudr_required("1201") is True  # Soya
```

**Implementation:** `tracehub/backend/app/services/compliance.py`

```python
EUDR_HS_CODES = ['1801', '0901', '1511', '4001', '1201']

def is_eudr_required(hs_code: str) -> bool:
    """Check if EUDR applies based on HS code.

    Horn/hoof (0506/0507) = NO
    Cocoa (1801), Coffee (0901), Palm Oil (1511), Rubber (4001), Soya (1201) = YES
    """
    prefix = hs_code[:4]
    return any(prefix.startswith(code) for code in EUDR_HS_CODES)
```

**Acceptance Criteria:**
- [ ] All test cases pass
- [ ] Function exported from compliance.py
- [ ] Used by existing EUDR validation logic
- [ ] Documented in module docstring

---

#### Task 1.2: Missing Product Type Document Requirements

**Priority:** High
**TDD Order:** Tests first

**Tests to add:**

```python
@pytest.mark.parametrize("hs_code,destination,expected_docs", [
    # Sweet Potato Pellets (HS 0714.20)
    ("0714", "DE", [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
    ]),
    # Hibiscus Flowers (HS 0902.10)
    ("0902", "DE", [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
    ]),
    # Dried Ginger (HS 0910.11)
    ("0910", "DE", [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
    ]),
])
def test_get_required_documents_plant_products(hs_code, destination, expected_docs):
    """Plant products require Phyto, CoO, Quality, BOL, Invoice."""
    result = get_required_documents(hs_code, destination)
    for doc in expected_docs:
        assert doc in result, f"{doc} should be required for {hs_code}"
```

**Implementation:** Add to `REQUIRED_DOCUMENTS` dict in compliance.py

**Acceptance Criteria:**
- [ ] Tests pass for sweet potato (0714)
- [ ] Tests pass for hibiscus (0902)
- [ ] Tests pass for ginger (0910)
- [ ] Correct document types per COMPLIANCE_MATRIX.md

---

#### Task 1.3: EU TRACES and Veterinary Health Validation Rules

**Priority:** Medium
**TDD Order:** Tests first

**Tests to add:**

```python
def test_validate_eu_traces_certificate():
    """EU TRACES must have reference RC1479592."""
    valid_doc = Document(
        document_type=DocumentType.EU_TRACES_CERTIFICATE,
        reference_number="RC1479592",
        # ... other required fields
    )
    issues = validate_document(valid_doc)
    assert len(issues) == 0

def test_validate_eu_traces_wrong_reference():
    """EU TRACES with wrong reference number fails."""
    invalid_doc = Document(
        document_type=DocumentType.EU_TRACES_CERTIFICATE,
        reference_number="RC9999999",
    )
    issues = validate_document(invalid_doc)
    assert any("RC1479592" in str(i) for i in issues)

def test_validate_veterinary_health_certificate():
    """Vet Health must be from Nigerian authority."""
    valid_doc = Document(
        document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE,
        issuing_authority="Federal Ministry of Agriculture Nigeria",
    )
    issues = validate_document(valid_doc)
    assert len(issues) == 0

def test_validate_veterinary_health_wrong_authority():
    """Vet Health from non-Nigerian authority fails."""
    invalid_doc = Document(
        document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE,
        issuing_authority="German Veterinary Office",
    )
    issues = validate_document(invalid_doc)
    assert any("Nigerian" in str(i) or "Nigeria" in str(i) for i in issues)
```

**Implementation:** Add to `VALIDATION_RULES` in validation.py

**Acceptance Criteria:**
- [ ] EU_TRACES validation checks for RC1479592
- [ ] VET_HEALTH validation checks for Nigerian authority
- [ ] Clear error messages for failures

---

#### Task 1.4: EUDR Field Prevention for Non-EUDR Products

**Priority:** Medium
**TDD Order:** Tests first

**Tests to add:**

```python
def test_prevent_eudr_fields_on_horn_hoof_origin():
    """Origins for horn/hoof should not have EUDR fields populated."""
    # Create a product with horn/hoof HS code
    product = Product(hs_code="0506.90.00", name="Buffalo Horn")

    # Attempt to create origin with EUDR fields should warn/fail
    origin_data = {
        "geolocation_lat": 9.0820,
        "geolocation_lng": 8.6753,
        "deforestation_free_statement": "This product is deforestation-free",
    }

    with pytest.raises(ValidationError) as exc:
        validate_origin_for_product(origin_data, product)

    assert "EUDR fields not applicable" in str(exc.value)

def test_allow_eudr_fields_on_cocoa_origin():
    """Origins for cocoa should allow EUDR fields."""
    product = Product(hs_code="1801.00.00", name="Cocoa Beans")

    origin_data = {
        "geolocation_lat": 6.5244,
        "geolocation_lng": 3.3792,
        "deforestation_free_statement": "Certified deforestation-free",
    }

    # Should not raise
    validate_origin_for_product(origin_data, product)
```

**Implementation:** Add validation to origin service

**Acceptance Criteria:**
- [ ] Non-EUDR products reject geolocation data
- [ ] Non-EUDR products reject deforestation statements
- [ ] EUDR products accept these fields
- [ ] Clear error messages explain why

---

### Phase 2: Frontend Implementation (TDD)

#### Task 2.1: Centralized isEUDRRequired Utility

**Priority:** Medium
**TDD Order:** Tests first

**Test File:** `tracehub/frontend/src/utils/__tests__/compliance.test.ts`

```typescript
import { isEUDRRequired, EUDR_HS_CODES, HORN_HOOF_HS_CODES } from '../compliance';

describe('isEUDRRequired', () => {
  test('returns false for horn/hoof products', () => {
    expect(isEUDRRequired('0506')).toBe(false);
    expect(isEUDRRequired('0507')).toBe(false);
    expect(isEUDRRequired('0506.90.00')).toBe(false);
  });

  test('returns true for cocoa beans', () => {
    expect(isEUDRRequired('1801')).toBe(true);
    expect(isEUDRRequired('1801.00')).toBe(true);
  });

  test('returns false for plant products not in EUDR', () => {
    expect(isEUDRRequired('0714.20')).toBe(false);  // Sweet potato
    expect(isEUDRRequired('0902.10')).toBe(false);  // Hibiscus
    expect(isEUDRRequired('0910.11')).toBe(false);  // Ginger
  });

  test('returns true for all EUDR products', () => {
    EUDR_HS_CODES.forEach(code => {
      expect(isEUDRRequired(code)).toBe(true);
    });
  });
});
```

**Implementation:** `tracehub/frontend/src/utils/compliance.ts`

```typescript
export const EUDR_HS_CODES = ['1801', '0901', '1511', '4001', '1201'];
export const HORN_HOOF_HS_CODES = ['0506', '0507'];

export const isEUDRRequired = (hsCode: string): boolean => {
  const prefix = hsCode.substring(0, 4);
  return EUDR_HS_CODES.some(code => prefix.startsWith(code));
};

export const isHornHoofProduct = (hsCode: string): boolean => {
  const prefix = hsCode.substring(0, 4);
  return HORN_HOOF_HS_CODES.some(code => prefix.startsWith(code));
};
```

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Single source of truth for HS code classification
- [ ] Exported from utils/compliance.ts

---

#### Task 2.2: Update Components to Use Centralized Utility

**Priority:** Low
**Files to Update:**
- `tracehub/frontend/src/pages/Shipment.tsx` - Remove hardcoded HORN_HOOF_HS_CODES
- `tracehub/frontend/src/components/EUDRStatusCard.tsx` - Use isEUDRRequired

**Acceptance Criteria:**
- [ ] No hardcoded HS codes in components
- [ ] All components import from utils/compliance.ts
- [ ] Existing functionality preserved

---

## Definition of Done

- [ ] All new tests written BEFORE implementation (TDD)
- [ ] 100% test pass rate
- [ ] No TypeScript/Python type errors
- [ ] Linting passes (`make lint`)
- [ ] COMPLIANCE_MATRIX.md fully implemented
- [ ] CHANGELOG.md updated
- [ ] Code reviewed

---

## Test Execution Order

Run tests in this order to verify TDD progress:

```bash
# 1. Backend unit tests
cd tracehub/backend
pytest tests/test_compliance.py -v

# 2. Backend validation tests
pytest tests/test_validation.py -v

# 3. Frontend unit tests
cd tracehub/frontend
npm test -- --testPathPattern=compliance

# 4. Full test suite
cd tracehub
make test
```

---

## File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `backend/tests/test_compliance.py` | Modify | Add is_eudr_required tests |
| `backend/app/services/compliance.py` | Modify | Add is_eudr_required(), extend REQUIRED_DOCUMENTS |
| `backend/tests/test_validation.py` | Modify | Add EU_TRACES, VET_HEALTH validation tests |
| `backend/app/services/validation.py` | Modify | Add EU_TRACES, VET_HEALTH validation rules |
| `backend/app/services/origin.py` | Modify | Add EUDR field prevention logic |
| `frontend/src/utils/compliance.ts` | Create | Centralized compliance utilities |
| `frontend/src/utils/__tests__/compliance.test.ts` | Create | Frontend compliance tests |
| `frontend/src/pages/Shipment.tsx` | Modify | Use centralized utility |
| `CHANGELOG.md` | Modify | Document changes |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing functionality | Low | High | Comprehensive test coverage before changes |
| EUDR field prevention too strict | Medium | Medium | Make it a warning, not hard block initially |
| Missing edge cases in HS code matching | Low | Medium | Parametrized tests with real HS codes |

---

## Notes

- Sprint 8 established multi-tenancy foundation (COMPLETED)
- Sprint 7 (OCR & AI Detection) is PLANNED, not blocking
- This sprint focuses on data integrity and compliance correctness
- EUDR field prevention should be a warning initially, upgraded to error after validation

---

**Sprint Created:** 2026-01-06
**Sprint Lead:** TraceHub Development Team
