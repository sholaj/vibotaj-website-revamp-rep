# TraceHub Compliance Skill

Specialized knowledge for EUDR compliance, HS code classification, document lifecycle, and validation patterns in TraceHub.

## When to Load

Load this skill when working on:
- Compliance logic, rules, or validation
- Document lifecycle state machines
- HS code classification or EUDR checks
- Bill of Lading parsing or compliance rules
- Certificate management (TRACES, vet certs, CoO)

## CRITICAL: Horn & Hoof Exception

**HS 0506 (bone/horn) and HS 0507 (hoof) are NOT covered by EUDR.**

This is a regulatory fact. NEVER add to horn/hoof products:
- Geolocation coordinates
- Deforestation statements
- EUDR risk assessment scores
- Due diligence documentation fields

## HS Code → Regulation Mapping

| HS Code | Product | EUDR Required | Key Documents |
|---------|---------|---------------|---------------|
| 0506 | Bone/Horn | NO | TRACES, Vet Cert, CoO, BoL, Invoice, Packing List |
| 0507 | Hoof | NO | TRACES, Vet Cert, CoO, BoL, Invoice, Packing List |
| 1801 | Cocoa | YES | All above + Geolocation, EUDR Due Diligence |
| 0901 | Coffee | YES | All above + Geolocation, EUDR Due Diligence |
| 1511 | Palm Oil | YES | All above + Geolocation, EUDR Due Diligence |
| 4001 | Rubber | YES | All above + Geolocation, EUDR Due Diligence |
| 1201 | Soy | YES | All above + Geolocation, EUDR Due Diligence |

Always check `docs/COMPLIANCE_MATRIX.md` for the full, authoritative matrix.

## EUDR Check Pattern

```python
def is_eudr_required(hs_code: str) -> bool:
    """Check if EUDR applies. Horn/hoof (0506/0507) = NO."""
    EUDR_CODES = ['1801', '0901', '1511', '4001', '1201']
    return any(hs_code.startswith(c) for c in EUDR_CODES)
```

## Document Lifecycle

### State Machine

```
DRAFT → UPLOADED → VALIDATED → COMPLIANCE_OK → LINKED → ARCHIVED
                        ↓                        ↑
                   COMPLIANCE_FAILED ────────────┘
```

### State Definitions

| State | Description | Who Can Transition |
|-------|-------------|--------------------|
| DRAFT | Created but no file | Any authenticated user |
| UPLOADED | File present, pending validation | System (on upload) |
| VALIDATED | Metadata verified (format, required fields) | compliance_officer, admin |
| COMPLIANCE_OK | Passed compliance rules | compliance_officer, admin |
| COMPLIANCE_FAILED | Failed compliance, needs correction | System (on validation failure) |
| LINKED | Associated with shipment, ready for export | compliance_officer, admin |
| ARCHIVED | Terminal state | admin |

### Rules

- Only COMPLIANCE_OK documents count toward shipment compliance
- Expired documents must be flagged, not silently ignored
- Validation is mandatory before COMPLIANCE_OK
- Supplier cannot approve documents (role-based enforcement)

## Document Validation Rules

Defined in `app/services/validation.py`:

| Rule Type | Examples | Severity |
|-----------|----------|----------|
| Type-specific | TRACES cert must ref RC1479592 | ERROR |
| Type-specific | Vet cert must be from Nigerian authority | ERROR |
| Cross-document | Weight tolerance ±5% | WARNING |
| Cross-document | Container numbers must match | ERROR |
| Cross-document | HS codes must be consistent | ERROR |

## Bill of Lading Compliance Rules

BoL is the source of truth for shipment details:

| Rule | Check | Action |
|------|-------|--------|
| BOL-001 | Container number format (ISO 6346) | REJECT if invalid |
| BOL-002 | Port codes exist in reference data | HOLD if unknown |
| BOL-003 | Weight within declared tolerance | WARNING if >5% |
| BOL-004-011 | See `docs/COMPLIANCE_MATRIX.md` | Varies |

When BoL is parsed:
1. Auto-populate shipment fields (container number, vessel, ports)
2. Run compliance rules BOL-001 through BOL-011
3. Decision: APPROVE / HOLD / REJECT based on highest severity

## Required Documents (Horn/Hoof Exports)

1. **EU TRACES Number** — RC1479592 (VIBOTAJ registration)
2. **Veterinary Health Certificate** — issued by Nigerian authority
3. **Certificate of Origin** — country of origin verification
4. **Bill of Lading** — shipment source of truth
5. **Commercial Invoice** — financial documentation
6. **Packing List** — container contents detail

## Before Any Compliance Code Change

1. Read `docs/COMPLIANCE_MATRIX.md` (authoritative source)
2. Verify HS code classification
3. Confirm document requirements for the product type
4. Write tests against golden compliance scenarios
5. Get human review if the change affects EUDR logic

## Key Files

| File | Purpose |
|------|---------|
| `tracehub/backend/app/services/validation.py` | Document validation rules |
| `tracehub/backend/app/services/workflow.py` | Document state machine transitions |
| `tracehub/backend/app/models/document.py` | Document ORM model |
| `tracehub/backend/app/schemas/document*.py` | Document API schemas |
| `docs/COMPLIANCE_MATRIX.md` | Authoritative HS code → document requirements |
