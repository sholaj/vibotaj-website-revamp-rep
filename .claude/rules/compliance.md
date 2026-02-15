# Compliance Rules

TraceHub manages export compliance for Nigerian commodities to EU markets.

## CRITICAL: Horn & Hoof (HS 0506/0507)

**NOT covered by EUDR.** This is a regulatory fact, not a product decision.

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
PENDING → UPLOADED → UNDER_REVIEW → APPROVED / REJECTED → EXPIRED
```

- Only `APPROVED` documents count toward compliance
- Expired documents must be flagged, not silently ignored
- Document approval requires a user with `compliance_officer` or `admin` role

## Bill of Lading Compliance

BoL is the source of truth for shipment details. When parsed:
- Auto-populate shipment fields (container number, vessel, ports)
- Run compliance rules (BOL-001 through BOL-011)
- Decision: APPROVE / HOLD / REJECT based on severity

See `docs/COMPLIANCE_MATRIX.md` for full BoL rule definitions.

## Before Any Compliance Code Change

1. Read `docs/COMPLIANCE_MATRIX.md`
2. Verify HS code classification
3. Confirm document requirements
4. Write tests against golden compliance scenarios
5. Get human review if the change affects EUDR logic
