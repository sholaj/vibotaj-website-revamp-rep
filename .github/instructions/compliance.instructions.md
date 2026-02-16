---
applyTo: "**/compliance/**,**/models/document.py,**/services/validation.py,**/services/workflow.py,**/schemas/document*.py"
---

# Compliance Rules

TraceHub manages export compliance for Nigerian commodities to EU markets.

## CRITICAL: Horn & Hoof (HS 0506/0507) = NOT covered by EUDR

This is a regulatory fact, not a product decision.

NEVER add to horn/hoof products:
- Geolocation coordinates
- Deforestation statements
- EUDR risk assessment scores
- Due diligence documentation fields

Required documents for horn/hoof:
1. EU TRACES Number (RC1479592)
2. Veterinary Health Certificate
3. Certificate of Origin
4. Bill of Lading
5. Commercial Invoice
6. Packing List

## HS Code → Document Requirements

Always check `docs/COMPLIANCE_MATRIX.md` before modifying compliance logic.

```python
def is_eudr_required(hs_code: str) -> bool:
    """Check if EUDR applies. Horn/hoof (0506/0507) = NO."""
    EUDR_CODES = ['1801', '0901', '1511', '4001', '1201']
    return any(hs_code.startswith(c) for c in EUDR_CODES)
```

## Document Lifecycle States

```
DRAFT → UPLOADED → UNDER_REVIEW → APPROVED / REJECTED → EXPIRED
```

Active states (full pipeline):
```
DRAFT → UPLOADED → VALIDATED → COMPLIANCE_OK → LINKED → ARCHIVED
                        ↓                        ↑
                   COMPLIANCE_FAILED ────────────┘
```

- Only `APPROVED` / `COMPLIANCE_OK` documents count toward compliance
- Expired documents must be flagged, not silently ignored
- Document approval requires `compliance_officer` or `admin` role
- Validation is mandatory before COMPLIANCE_OK
- Role-based transitions enforced (supplier can't approve)

## Bill of Lading Compliance

BoL is the source of truth for shipment details. When parsed:
- Auto-populate shipment fields (container number, vessel, ports)
- Run compliance rules (BOL-001 through BOL-011)
- Decision: APPROVE / HOLD / REJECT based on severity

## Document Validation Rules

Defined in `app/services/validation.py`:
- Type-specific rules (TRACES cert must ref RC1479592, vet cert from Nigerian authority)
- Severity levels: ERROR (reject), WARNING (hold), INFO (log)
- Cross-document checks: Weight tolerance ±5%, container numbers match, HS codes consistent

## Before Any Compliance Code Change

1. Read `docs/COMPLIANCE_MATRIX.md`
2. Verify HS code classification
3. Confirm document requirements
4. Write tests against golden compliance scenarios
5. Get human review if the change affects EUDR logic
