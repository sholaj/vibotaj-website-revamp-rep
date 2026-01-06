# ADR 001: Remove EUDR from Horn & Hoof Products

## Status
Accepted - January 2026

## Context

Horn and hoof products (HS codes 0506 and 0507) were incorrectly configured with EUDR (EU Deforestation Regulation) compliance features in the TraceHub system. This included geolocation coordinates, deforestation statements, and EUDR risk scoring fields.

After thorough research and consultation with the EUDR regulation text (EU 2023/1115), we confirmed that:

1. **EUDR Annex I** lists only specific commodities: cattle, cocoa, coffee, oil palm, rubber, soya, and wood
2. **Horn and hoof** (HS 0506/0507) are animal by-products, NOT covered by EUDR
3. These products fall under **veterinary and sanitary regulations**, not deforestation rules

## Decision

We will **remove all EUDR-related fields and workflows** from horn and hoof product processing:

### To Remove:
- Geolocation coordinate fields (latitude, longitude, polygon data)
- Deforestation-free statements
- EUDR risk assessment scores
- EUDR compliance status indicators
- EUDR audit bundle generation for these products

### To Keep:
- EU TRACES number (RC1479592) - required for animal products
- Veterinary Health Certificate requirements
- All standard export documentation (Certificate of Origin, Bill of Lading, etc.)
- The EUDR module code itself (for future cocoa product expansion)

## Consequences

### Positive:
- **Simplified workflow** for current business operations
- **Correct regulatory compliance** posture
- **Reduced data collection burden** on suppliers
- **Clearer user interface** without irrelevant fields
- **Faster shipment processing** with fewer validation steps

### Negative:
- Need to update existing shipment records that have EUDR data
- Need to retrain users who were entering EUDR information
- Need to update documentation and training materials

### Neutral:
- EUDR code remains in codebase for future use (cocoa expansion)
- System still validates EUDR for products that require it (HS 1801)

## Implementation Plan

1. **Database Migration**
   - Add `eudr_applicable` boolean field to products table
   - Set to `false` for all HS 0506/0507 products
   - Set to `true` for future EUDR products (cocoa, coffee, etc.)

2. **Backend Changes**
   - Update compliance validation logic to check `eudr_applicable` field
   - Skip EUDR validation for non-applicable products
   - Update API responses to exclude EUDR fields when not applicable

3. **Frontend Changes**
   - Hide EUDR form fields for horn/hoof products
   - Update dashboard to not show EUDR status for these products
   - Remove EUDR sections from shipment detail views

4. **Documentation Updates**
   - Update `COMPLIANCE_MATRIX.md` with correct requirements
   - Create this ADR to document the decision
   - Update user guides and training materials

5. **Data Cleanup**
   - Archive existing EUDR data for horn/hoof shipments
   - Update compliance status for affected shipments

## Validation

Before marking this complete, verify:
- [ ] Horn/hoof products (HS 0506/0507) do not show EUDR fields
- [ ] Cocoa products (HS 1801) still require EUDR fields
- [ ] API documentation reflects the changes
- [ ] All tests pass with new compliance logic
- [ ] `COMPLIANCE_MATRIX.md` is used as source of truth

## References

- EU Regulation 2023/1115 (EUDR)
- EUDR Annex I - List of relevant commodities
- `docs/COMPLIANCE_MATRIX.md` - TraceHub compliance requirements
- HS Code Classification System

## Related Decisions

- None (this is the first ADR)

## Notes

This decision was made in Sprint 8 as part of the multi-tenancy implementation. The HAGES customer onboarding process highlighted the confusion around EUDR requirements for horn/hoof products, prompting this correction.

---

**Decision Date:** 2026-01-06  
**Implementation Date:** 2026-01-06  
**Review Date:** 2026-07-01 (or when expanding to EUDR products)
