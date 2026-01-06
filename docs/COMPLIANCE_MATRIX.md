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

## Changes Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-06 | Initial creation | Establish single source of truth |
| 2026-01-06 | Confirmed Horn/Hoof NOT EUDR | HS 0506/0507 not in EUDR Annex I |

---

**Last Updated:** 2026-01-06  
**Maintained By:** TraceHub Development Team  
**Review Frequency:** Before any compliance-related code changes
