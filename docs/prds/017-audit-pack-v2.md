# PRD-017: Audit Pack v2

## Problem Statement

The v1 audit pack system works — it generates ZIP files with a PDF index, documents, tracking log, and metadata. But it reads documents from local disk (not Supabase Storage), streams blobs directly (no caching), and the v2 frontend has no dedicated audit pack UI beyond a download button. PRD-017 upgrades the audit pack to use Supabase Storage for both source documents and generated packs, adds signed URL support, and builds a frontend audit pack preview panel.

## Dependencies

- PRD-004 (FastAPI on Railway — backend)
- PRD-005 (Supabase Storage — document storage)
- PRD-012 (Shipment detail — download button exists)
- PRD-016 (Compliance engine — compliance status in audit pack)

## Scope

### Backend: Supabase Storage Integration

**In scope:**
- Fetch documents from Supabase Storage (via StorageBackend protocol) instead of local disk
- Store generated audit pack ZIPs in Supabase Storage `audit-packs` bucket
- Return signed URL for download (1-hour expiry) instead of streaming blob
- Enhanced PDF index page with compliance status from PRD-016
- Cache generated audit packs — regenerate only when documents change
- Audit pack metadata includes compliance decision (APPROVE/HOLD/REJECT)

**Out of scope:**
- Changing the ReportLab PDF generation library
- EUDR-specific report pages (future PRD)
- Email delivery of audit packs (PRD-020)

### Frontend: Audit Pack Panel

**In scope:**
- Audit pack preview card on shipment detail sidebar — shows pack status (ready/generating/outdated)
- Download button with signed URL (opens in new tab)
- Regenerate button when documents have changed since last pack
- Audit pack contents list — shows included documents with status icons
- Pack generation timestamp

**Out of scope:**
- In-browser PDF viewer (browser native PDF handling is sufficient)
- Audit pack comparison (diff between versions)

## Acceptance Criteria

### Backend
1. `GET /api/shipments/{id}/audit-pack` returns signed URL from Supabase Storage (or generates pack first)
2. Generated ZIP is stored in `audit-packs` bucket with key `{org_id}/{shipment_ref}-audit-pack.zip`
3. PDF index includes compliance decision badge and rule summary from PRD-016
4. Audit pack is regenerated when documents are added/removed/updated after last generation
5. Metadata JSON includes `compliance_decision`, `compliance_summary` fields
6. All endpoints filter by organization_id (multi-tenancy)

### Frontend
7. Audit pack card shows generation status (ready/generating/outdated)
8. Download button opens signed URL in new tab
9. Regenerate button triggers pack regeneration
10. Contents list shows included document types with check marks
11. All components have Vitest tests

## API Changes

### Enhanced Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/shipments/{id}/audit-pack` | Get or generate audit pack (returns signed URL) |
| POST | `/api/shipments/{id}/audit-pack/regenerate` | Force regenerate audit pack |
| GET | `/api/shipments/{id}/audit-pack/status` | Get audit pack status without generating |

### Response: Audit Pack Status
```json
{
  "shipment_id": "...",
  "status": "ready",
  "generated_at": "2026-02-16T10:00:00Z",
  "download_url": "https://supabase.co/storage/v1/object/sign/...",
  "expires_at": "2026-02-16T11:00:00Z",
  "contents": [
    { "name": "00-SHIPMENT-INDEX.pdf", "type": "index" },
    { "name": "01-bill_of_lading.pdf", "type": "document", "document_type": "bill_of_lading" },
    { "name": "02-certificate_of_origin.pdf", "type": "document", "document_type": "certificate_of_origin" }
  ],
  "compliance_decision": "APPROVE",
  "document_count": 6,
  "is_outdated": false
}
```

## Frontend Changes

### New Files
- `src/lib/api/audit-pack-types.ts` — AuditPackStatus, AuditPackContent types
- `src/lib/api/audit-pack.ts` — React Query hooks for audit pack endpoints
- `src/components/compliance/audit-pack-card.tsx` — Audit pack status card with download/regenerate

### Modified Files
- `src/app/shipments/[id]/page.tsx` — Replace direct download link with AuditPackCard in sidebar

## Compliance Impact

Audit pack PDF index must respect product type:
- Horn/hoof (0506/0507): Show required docs per COMPLIANCE_MATRIX, NO EUDR section
- EUDR products: Include EUDR compliance section in PDF

## Testing

### Backend (pytest)
- `test_audit_pack_v2.py` — Supabase Storage integration, signed URL generation
- `test_audit_pack_compliance.py` — Compliance status in PDF/metadata
- `test_audit_pack_cache.py` — Regeneration on document change

### Frontend (vitest)
- `audit-pack-types.test.ts` — Type helper tests
- `audit-pack-card.test.tsx` — Status display, download button, regenerate button
