# PRP: Fix Validation Report & Audit Pack Download in Production

## Status: ✅ Complete - Deployed to Production

## Problem Statement

On production (tracehub.vibotaj.com), the shipment detail page shows:
1. **"Failed to load validation report"** error in the Shipment Validation panel
2. **Download Audit Pack** button may also be failing

**Affected Shipment:** VIBO-2026-001 (Container: MRSU3452572)
**Environment:** Production
**Reported:** January 17, 2026

## Screenshot Analysis

From the provided screenshot:
- Shipment: VIBO-2026-001 (In Transit)
- Container: MRSU3452572
- Vessel: RHINE MAERSK / 550N
- B/L: 262495038
- Route: Apapa, Lagos → Hamburg
- ETD/ETA: Dec 13 → Jan 15, 2026
- Documents: 7 uploaded
- Document Status shows "Documentation Incomplete" with 7/7 required but lists EU TRACES and Export Declaration as missing (contradictory UI)

## Investigation Plan

### Phase 1: Reproduce and Diagnose

1. **Check production logs for errors**
   ```bash
   ssh root@82.198.225.150
   docker logs tracehub-backend-prod --tail 200 | grep -E "validation|audit"
   ```

2. **Test API endpoints directly**
   ```bash
   # Get validation report
   curl -H "Authorization: Bearer $TOKEN" \
     https://tracehub.vibotaj.com/api/shipments/{id}/validation

   # Get audit pack
   curl -H "Authorization: Bearer $TOKEN" \
     https://tracehub.vibotaj.com/api/shipments/{id}/audit-pack
   ```

3. **Check if endpoints exist in production deployment**
   - Verify `document_validation.py` router is mounted
   - Verify routes are accessible

### Phase 2: Root Cause Analysis

Possible causes:
1. **Missing router registration** - `document_validation` router not included in main.py
2. **Database migration missing** - validation tables don't exist
3. **Missing dependencies** - validation service imports failing
4. **CORS/Auth issues** - endpoint returning 401/403
5. **Frontend API path mismatch** - calling wrong endpoint URL

### Phase 3: Fix Implementation

Based on diagnosis, implement appropriate fix:
- Add missing router registration
- Run pending migrations
- Fix import errors
- Update frontend API client

## API Endpoints to Verify

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/validation/shipments/{id}` | GET | Get validation report |
| `/api/validation/shipments/{id}` | POST | Run validation |
| `/api/shipments/{id}/audit-pack` | GET | Download audit pack |

## Files to Check

### Backend
- `backend/app/main.py` - Router registrations
- `backend/app/routers/document_validation.py` - Validation endpoints
- `backend/app/routers/shipments.py` - Audit pack endpoint
- `backend/app/services/document_rules/` - Validation logic

### Frontend
- `frontend/src/api/client.ts` - API client methods
- `frontend/src/components/ShipmentValidationPanel.tsx` - Validation UI

## Success Criteria

- [ ] "Run Validation" button works and shows results
- [ ] Validation report loads without errors
- [ ] "Download Audit Pack" downloads a ZIP file with all documents
- [ ] No console errors in browser DevTools
- [ ] No 500 errors in backend logs

## Rollback Plan

If fix introduces new issues:
1. Revert commit
2. Redeploy previous version: `git checkout HEAD~1 && docker-compose up -d --build`

## Root Cause Analysis

**Bug 1: Audit Pack 500 Error**
- **File:** `backend/app/services/audit_pack.py` lines 103-110
- **Issue:** Code referenced `shipment.buyer` and `shipment.supplier` which don't exist
- **Actual model attributes:** `shipment.importer_name`, `shipment.exporter_name`, `shipment.buyer_organization_id`
- **Error:** `AttributeError: 'Shipment' object has no attribute 'buyer'`

**Bug 2: Validation Report 404 Error**
- **File:** `backend/app/routers/document_validation.py`
- **Issue:** Frontend calls `GET /api/validation/shipments/{id}` but backend only had `GET /shipments/{id}/status`
- **Error:** `404 Not Found`

## Fix Implemented

1. **audit_pack.py** - Updated metadata generation to use correct attributes:
   ```python
   "buyer": {
       "name": shipment.importer_name,
       "organization_id": str(shipment.buyer_organization_id) if shipment.buyer_organization_id else None,
   },
   "exporter": {
       "name": shipment.exporter_name,
       "organization_id": str(shipment.organization_id) if shipment.organization_id else None,
   },
   ```

2. **document_validation.py** - Added new GET endpoint:
   ```python
   @router.get("/shipments/{shipment_id}")
   async def get_validation_report(shipment_id: UUID, ...)
   ```
   This endpoint runs validation and returns the full report (matching frontend expectations).

## Timeline

- **P0 Priority**: Fix within 4 hours
- Deploy to staging first, verify, then production
