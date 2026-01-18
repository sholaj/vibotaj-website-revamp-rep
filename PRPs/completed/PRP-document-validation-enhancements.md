# PRP: Document Validation Enhancements

**Status:** Draft
**Priority:** P1 - High
**Sprint:** 16
**Created:** 2026-01-17
**Owner:** Shola

---

## Overview

Enhance the existing document validation rules engine with additional business rules for Horn & Hoof shipment compliance. This PRP extends the already-implemented rules engine (Phase 1-4 complete) with new validation rules and improved audit capabilities.

### Business Value
- **Compliance Assurance:** Ensure every Horn & Hoof shipment has all required documents before export
- **Error Prevention:** Catch missing, duplicate, or invalid documents before delays
- **Regulatory Readiness:** Meet EU import requirements for animal by-products
- **Audit Trail:** Maintain comprehensive validation logs for regulatory audits

---

## Current State (Already Implemented)

The validation rules engine is already in place with these rules:

| Rule ID | Name | Status |
|---------|------|--------|
| PRESENCE_001 | Required Documents Present | ✅ Implemented |
| UNIQUE_001 | No Duplicate Documents | ✅ Implemented |
| RELEVANCE_001 | Document Content Relevance (AI) | ✅ Implemented |
| HORN_HOOF_002 | Vet Cert Issue Date | ✅ Implemented |
| HORN_HOOF_003 | Vet Cert Authorized Signer | ✅ Implemented |

**Files:**
- `app/services/document_rules/` - Rules engine
- `app/routers/document_validation.py` - API endpoints
- `tests/test_document_validation_rules.py` - 26 tests
- `tests/test_document_validation_api.py` - 20 tests

---

## Required Documents (Horn & Hoof)

Per `docs/COMPLIANCE_MATRIX.md`, Horn & Hoof shipments (HS 0506/0507) require:

| Document | Purpose | Validation Rules |
|----------|---------|------------------|
| EU TRACES Certificate | Animal by-product traceability | Presence, RC1479592 reference |
| Veterinary Health Certificate | Animal health certification | Presence, Issue date, Authority |
| Certificate of Origin | Country of origin proof | Presence |
| Bill of Lading | Shipping manifest | Presence, Container match |
| Commercial Invoice | Commercial terms | Presence |
| Packing List | Contents detail | Presence |
| Export Declaration | Customs clearance | Presence |

---

## New Rules to Implement

### Rule: BOL_MATCH_001 - Bill of Lading Container Match

**Description:** Bill of Lading container number must match shipment container number.

**Logic:**
```python
if bol.container_number != shipment.container_number:
    return WARNING("Container mismatch: BOL has {bol}, shipment has {shipment}")
```

**Severity:** WARNING (not blocking - allows manual review)

### Rule: BOL_MATCH_002 - Bill of Lading Vessel Match

**Description:** Bill of Lading vessel name should match shipment vessel name (if provided).

**Logic:**
```python
if shipment.vessel_name and bol.vessel_name:
    if normalize(bol.vessel_name) != normalize(shipment.vessel_name):
        return WARNING("Vessel mismatch")
```

**Severity:** WARNING

### Rule: AUDIT_001 - Validation Audit Trail

**Description:** All validation runs must be logged with full context.

**Logged Data:**
- Validation timestamp
- User who triggered validation
- Shipment ID and reference
- All rule results (pass/fail/warning)
- Document IDs validated
- Override actions (if any)

---

## Functional Requirements

### FR-1: Document Presence Validation (EXISTS)
- [x] Validate all 7 required documents are present
- [x] Flag shipments with missing documents

### FR-2: Document Uniqueness Validation (EXISTS)
- [x] Ensure only one document of each type per shipment
- [x] Flag shipments with duplicate documents

### FR-3: Bill of Lading Cross-Validation (NEW)
- [ ] Validate BOL container number matches shipment container number
- [ ] Validate BOL vessel name matches shipment vessel name (if provided)
- [ ] Generate WARNING (not error) for mismatches to allow manual review

### FR-4: Veterinary Health Certificate Validation (EXISTS + ENHANCE)
- [x] Validate issue date is on or before ship departure date (ETD)
- [x] Validate issuing authority contains Nigerian terms
- [ ] **NEW:** Extract and validate veterinarian signature field

### FR-5: Validation Audit Logging (EXISTS + ENHANCE)
- [x] Log all validation runs with timestamp, user, shipment ID
- [x] Log individual rule results
- [ ] **NEW:** Support deletion of flagged shipments with audit trail
- [ ] **NEW:** Log override actions with reason

### FR-6: Modular Rule System (EXISTS)
- [x] Rules implemented as pluggable components
- [x] Support rule priorities (critical, warning, info)
- [x] Support conditional rules by product type
- [ ] **NEW:** Support rule versioning for regulatory changes

---

## Technical Approach

### New Rule Implementation

```python
# app/services/document_rules/bol_rules.py

class BolContainerMatchRule(ValidationRule):
    """Validates BOL container number matches shipment."""

    rule_id = "BOL_MATCH_001"
    name = "Bill of Lading Container Match"
    description = "BOL container number must match shipment container number"
    severity = RuleSeverity.WARNING
    category = RuleCategory.CROSS_FIELD

    def validate(self, context: ValidationContext) -> RuleResult:
        bols = context.documents_by_type.get(DocumentType.BILL_OF_LADING, [])

        if not bols:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="No Bill of Lading to validate",
                category=self.category
            )

        bol = bols[0]
        shipment = context.shipment

        # Get BOL container from extracted fields
        bol_container = self._get_bol_container(bol, context)

        if not bol_container:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message="Could not extract container number from Bill of Lading",
                category=self.category,
                document_id=str(bol.id)
            )

        if bol_container != shipment.container_number:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Container mismatch: BOL has '{bol_container}', shipment has '{shipment.container_number}'",
                category=self.category,
                document_id=str(bol.id),
                details={
                    "bol_container": bol_container,
                    "shipment_container": shipment.container_number
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="BOL container matches shipment",
            category=self.category
        )

    def _get_bol_container(self, bol: Document, context: ValidationContext) -> Optional[str]:
        """Extract container number from BOL document."""
        doc_id = str(bol.id)
        if doc_id in context.classifications:
            classification = context.classifications[doc_id].classification
            if classification and classification.detected_fields:
                return classification.detected_fields.get("container_number")
        return None
```

### Register New Rules

```python
# app/services/document_rules/registry.py

def register_default_rules(registry: RuleRegistry = None):
    # ... existing rules ...

    from .bol_rules import BolContainerMatchRule, BolVesselMatchRule

    rules = [
        # Existing
        RequiredDocumentsPresentRule(),
        NoDuplicateDocumentsRule(),
        DocumentRelevanceRule(),
        VetCertIssueDateRule(),
        VetCertAuthorizedSignerRule(),
        # NEW
        BolContainerMatchRule(),
        BolVesselMatchRule(),
    ]
```

---

## Files to Modify

### New Files
| File | Purpose |
|------|---------|
| `app/services/document_rules/bol_rules.py` | BOL cross-validation rules |

### Modified Files
| File | Changes |
|------|---------|
| `app/services/document_rules/registry.py` | Register new BOL rules |
| `tests/test_document_validation_rules.py` | Add BOL rule tests |

---

## Test Requirements

### Unit Tests (TDD)

```python
class TestBolContainerMatchRule:
    """Test BOL_MATCH_001 rule."""

    def test_passes_when_containers_match(self):
        """GIVEN BOL container matches shipment container
        WHEN validation runs
        THEN it should pass."""

    def test_warns_when_containers_mismatch(self):
        """GIVEN BOL container differs from shipment container
        WHEN validation runs
        THEN it should return WARNING with both values."""

    def test_passes_when_no_bol_present(self):
        """GIVEN no BOL document
        WHEN validation runs
        THEN it should pass with INFO message."""

    def test_warns_when_container_not_extractable(self):
        """GIVEN BOL without extractable container number
        WHEN validation runs
        THEN it should warn about extraction failure."""


class TestBolVesselMatchRule:
    """Test BOL_MATCH_002 rule."""

    def test_passes_when_vessels_match(self):
        """GIVEN BOL vessel matches shipment vessel
        WHEN validation runs
        THEN it should pass."""

    def test_warns_when_vessels_mismatch(self):
        """GIVEN BOL vessel differs from shipment vessel
        WHEN validation runs
        THEN it should return WARNING."""

    def test_passes_when_shipment_has_no_vessel(self):
        """GIVEN shipment has no vessel name
        WHEN validation runs
        THEN it should skip check and pass."""
```

---

## Compliance Check

**Product HS Codes:** 0506.10, 0506.90, 0507.10, 0507.90 (Horn & Hoof)
**EUDR Applicable:** NO - Horn & Hoof NOT covered by EUDR

**NEVER add to Horn & Hoof validation:**
- Geolocation coordinates
- Deforestation statements
- EUDR risk scores

---

## Acceptance Criteria

- [ ] BOL_MATCH_001 validates container number match
- [ ] BOL_MATCH_002 validates vessel name match (optional)
- [ ] New rules registered in registry
- [ ] All unit tests pass
- [ ] Audit log captures all validation events
- [ ] Override actions logged with reason
- [ ] No EUDR fields added for Horn & Hoof

---

## Rollout Plan

### Phase 1: Implementation (Sprint 16)
- [ ] Write failing tests for BOL rules
- [ ] Implement BolContainerMatchRule
- [ ] Implement BolVesselMatchRule
- [ ] Register rules in registry
- [ ] All tests pass

### Phase 2: Integration
- [ ] Deploy to staging
- [ ] Test with real BOL documents
- [ ] Verify audit logging
- [ ] Deploy to production

---

## Future Enhancements

1. **Rule Versioning:** Track rule changes for regulatory compliance
2. **Custom Rules:** Per-organization rule configuration
3. **Real-time Validation:** Validate during document upload
4. **Notification System:** Alert when validation fails
5. **Delete with Audit:** Allow deletion of flagged shipments with full audit trail

---

**Last Updated:** 2026-01-17
**Status:** Draft
