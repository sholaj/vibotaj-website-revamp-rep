
# TraceHub Compliance Matrix

> Single source of truth for HS codes and document requirements

## Quick Reference

| Product | HS Code | EUDR | Primary Docs |
|---------|---------|------|--------------|
| Horn & Hoof | 0506, 0507 | ❌ NO | TRACES, Vet Health, CoO |
| Sweet Potato Pellets | 0714.20 | ❌ NO | Phyto, CoO, Quality |
| Hibiscus Flowers | 0902.10 | ❌ NO | Phyto, CoO |
| Dried Ginger | 0910.11 | ❌ NO | Phyto, CoO |
| Cocoa Beans | 1801 | ✅ YES | All + EUDR Package |

---

## Horn & Hoof (HS 0506, 0507)

**EUDR Applicable: NO** - Not in EUDR Annex I

| Document | Required | Validation |
|----------|----------|------------|
| EU TRACES Number | ✅ | Must be RC1479592 |
| Veterinary Health Certificate | ✅ | Nigerian authority |
| Certificate of Origin | ✅ | Country: Nigeria |
| Bill of Lading | ✅ | Container match |
| Commercial Invoice | ✅ | Weight match |
| Packing List | ✅ | Count match |

**NEVER ADD:**
- ❌ Geolocation coordinates
- ❌ Deforestation statements
- ❌ EUDR risk assessment

---

## Sweet Potato Pellets (HS 0714.20)

**EUDR Applicable: NO**

| Document | Required | Validation |
|----------|----------|------------|
| Phytosanitary Certificate | ✅ | Nigerian authority |
| Certificate of Origin | ✅ | Country: Nigeria |
| Quality Certificate | ✅ | Moisture <13% |
| Bill of Lading | ✅ | Container match |
| Commercial Invoice | ✅ | Weight match |

---

## Hibiscus Flowers (HS 0902.10)

**EUDR Applicable: NO**

| Document | Required | Validation |
|----------|----------|------------|
| Phytosanitary Certificate | ✅ | Nigerian authority |
| Certificate of Origin | ✅ | Country: Nigeria |
| Quality Certificate | ✅ | Grade specification |
| Bill of Lading | ✅ | Container match |
| Commercial Invoice | ✅ | Weight match |

---

## Dried Ginger (HS 0910.11)

**EUDR Applicable: NO**

| Document | Required | Validation |
|----------|----------|------------|
| Phytosanitary Certificate | ✅ | Nigerian authority |
| Certificate of Origin | ✅ | Country: Nigeria |
| Quality Certificate | ✅ | Moisture & grade |
| Bill of Lading | ✅ | Container match |
| Commercial Invoice | ✅ | Weight match |

---

## Cocoa Beans (HS 1801) - FUTURE

**EUDR Applicable: YES**

Requires all standard docs PLUS:
- Geolocation (polygon coordinates)
- Deforestation-free statement
- Risk assessment
- Due diligence documentation

---

## Validation Code Reference

```python
def is_eudr_required(hs_code: str) -> bool:
    """Check if EUDR applies. Horn/hoof (0506/0507) = NO."""
    EUDR_CODES = ['1801', '0901', '1511', '4001', '1201']
    return any(hs_code.startswith(c) for c in EUDR_CODES)
```

```typescript
const isEUDRRequired = (hsCode: string): boolean => {
  const EUDR_CODES = ['1801', '0901', '1511', '4001', '1201'];
  return EUDR_CODES.some(code => hsCode.startsWith(code));
};
```

---

## Document Type Codes

| Code | Description | Required For |
|------|-------------|--------------|
| `TRACES` | EU TRACES Number | Horn/Hoof only |
| `VET_HEALTH` | Veterinary Health Certificate | Horn/Hoof only |
| `PHYTO` | Phytosanitary Certificate | Plant products |
| `COO` | Certificate of Origin | All products |
| `BOL` | Bill of Lading | All shipments |
| `INVOICE` | Commercial Invoice | All shipments |
| `PACKING` | Packing List | All shipments |
| `QUALITY` | Quality Certificate | Specified products |
| `EUDR_STATEMENT` | EUDR Due Diligence | EUDR products only |
| `GEOLOCATION` | Geolocation Data | EUDR products only |

---

## Business Rules

1. **Always check HS code first** before determining document requirements
2. **Horn & Hoof (0506/0507) NEVER require EUDR fields** - this is critical
3. **All shipments require:** Bill of Lading, Commercial Invoice, Certificate of Origin
4. **Animal products (Horn/Hoof) require:** EU TRACES + Veterinary Health Certificate
5. **Plant products require:** Phytosanitary Certificate
6. **EUDR products (future) require:** All standard docs + EUDR package

---

## Bill of Lading Compliance Rules

### Source of Truth Principle
**When a Bill of Lading is uploaded and parsed, it becomes the authoritative source for shipment details.**

### Compliance Decision Logic

| Decision | Condition | Action |
|----------|-----------|--------|
| **APPROVE** | All rules pass OR only INFO failures | Proceed with shipment |
| **HOLD** | WARNING failures (no ERRORs) | Review required |
| **REJECT** | ERROR severity failures | Cannot proceed |

### Compliance Rules

| Rule ID | Name | Severity | Validation |
|---------|------|----------|------------|
| BOL-001 | Shipper Name Required | ERROR | Not "Unknown Shipper" placeholder |
| BOL-002 | Consignee Name Required | ERROR | Not "Unknown Consignee" placeholder |
| BOL-003 | Container ISO 6346 Format | WARNING | 4 letters + 7 digits (e.g., MSKU1234567) |
| BOL-004 | BoL Number Required | ERROR | Not "UNKNOWN" placeholder |
| BOL-005 | Port of Loading Required | WARNING | Should be specified |
| BOL-006 | Cargo Description Required | WARNING | At least one cargo item |
| BOL-007 | Container Required | WARNING | At least one container |
| BOL-008 | Port of Discharge Required | WARNING | Should be specified |
| BOL-009 | Vessel Name Present | INFO | Helps with tracking |
| BOL-010 | Voyage Number Present | INFO | Helps with tracking |
| BOL-011 | Confidence Score Threshold | INFO | Parser confidence >= 50% |

### Shipment Auto-Population

When a BoL is parsed, these shipment fields are automatically updated:

| BoL Field | Shipment Field | Behavior |
|-----------|----------------|----------|
| `bol_number` | `bl_number` | Always update |
| `containers[0].number` | `container_number` | Update if placeholder |
| `vessel_name` | `vessel_name` | Update if present |
| `voyage_number` | `voyage_number` | Update if present |
| `port_of_loading` | `pol_code` | Extract UN/LOCODE |
| `port_of_discharge` | `pod_code` | Extract UN/LOCODE |
| `shipped_on_board_date` | `atd` | Update departure date |

### Placeholder Detection

Container numbers matching these patterns are replaced:
- `*-CNT-*` (e.g., BECKMANN-CNT-001, HAGES-CNT-002)
- `TBD`, `TBC`, `PENDING`, `PLACEHOLDER`
- `N/A`, `NA`, Empty/null values

---

## Changes Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-06 | Initial creation | Establish single source of truth |
| 2026-01-06 | Confirmed Horn/Hoof NOT EUDR | HS 0506/0507 not in EUDR Annex I |
| 2026-01-16 | Added BoL Compliance Rules | Sprint 12 - BoL parsing & rules engine |

---

**Last Updated:** 2026-01-16
**Maintained By:** TraceHub Development Team
**Review Frequency:** Before any compliance-related code changes
