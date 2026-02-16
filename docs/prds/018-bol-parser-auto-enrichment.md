# PRD-018: BoL Parser + Auto-Enrichment Pipeline

## Problem Statement

The v1 BoL parser works — it uses regex patterns to extract 8+ fields from Bill of Lading PDFs, runs 15 compliance rules, and syncs data to shipments. But parsing must be triggered manually, regex is brittle for non-standard formats, and there's no cross-document validation. PRD-018 adds automatic parsing on upload, improves extraction reliability, and integrates the BoL pipeline with the v2 frontend.

## Dependencies

- PRD-004 (FastAPI on Railway — backend)
- PRD-005 (Supabase Storage — document storage)
- PRD-012 (Shipment detail — document management UI)
- PRD-016 (Enhanced compliance engine — compliance status)

## Scope

### Backend: Auto-Parse Pipeline

**In scope:**
- Auto-trigger BoL parsing when a `bill_of_lading` document is uploaded
- Fetch BoL PDF from Supabase Storage (via StorageBackend) instead of local disk
- Run compliance rules automatically after parsing
- Auto-sync shipment fields from parsed BoL data
- Store parse results with confidence scores per field
- Cross-document weight validation (BoL gross weight vs Packing List)
- Expose parse status and results via API

**Out of scope:**
- AI/LLM-powered extraction (PRD-019 will add Claude-based parsing)
- Replacing the regex parser engine (enhance, don't rewrite)
- Cloud OCR (Tesseract fallback sufficient for now)
- Dynamic rule configuration UI (future)

### Frontend: BoL Parse Results Panel

**In scope:**
- Parse status indicator on document card (parsed/pending/failed)
- BoL parsed fields display (extracted data with confidence scores)
- Sync preview panel — shows what fields would be updated on shipment
- One-click sync button to apply BoL data to shipment
- Compliance results display integrated with PRD-016 rules table

**Out of scope:**
- In-browser BoL editing/correction
- AI re-extraction trigger (PRD-019)

## Acceptance Criteria

### Backend
1. When a `bill_of_lading` document is uploaded, parsing starts automatically
2. Parse results (fields + confidence) stored on the document
3. Compliance rules run automatically after parse
4. If confidence > 70%, auto-sync to shipment (only placeholder/empty fields)
5. Sync preview endpoint returns current vs BoL values
6. Cross-document validation: BoL weight vs Packing List weight (5% tolerance)
7. All endpoints filter by organization_id (multi-tenancy)
8. StorageBackend used for PDF retrieval

### Frontend
9. Document card shows parse status badge (Parsed/Pending/Failed)
10. Parsed fields panel shows extracted data with confidence indicators
11. Sync preview shows current → new values for each field
12. Apply sync button updates shipment and shows success feedback
13. All components have Vitest tests

## API Changes

### New/Enhanced Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/documents/{id}/bol/parsed` | Get parsed BoL data + confidence |
| POST | `/api/documents/{id}/bol/parse` | Trigger manual re-parse (existing, enhanced) |
| GET | `/api/documents/{id}/bol/sync-preview` | Preview sync changes (existing, enhanced) |
| POST | `/api/documents/{id}/bol/sync` | Apply BoL data to shipment (existing, enhanced) |

### Response: Parsed BoL Data
```json
{
  "document_id": "...",
  "parse_status": "parsed",
  "parsed_at": "2026-02-16T10:00:00Z",
  "confidence_score": 0.85,
  "fields": {
    "bol_number": { "value": "MSC1234567", "confidence": 0.95 },
    "shipper": { "value": "VIBOTAJ Global Nigeria Ltd", "confidence": 0.90 },
    "consignee": { "value": "HAGES GmbH", "confidence": 0.88 },
    "container_number": { "value": "MSCU1234567", "confidence": 0.92 },
    "vessel_name": { "value": "RHINE MAERSK", "confidence": 0.85 },
    "voyage_number": { "value": "550N", "confidence": 0.80 },
    "port_of_loading": { "value": "NGAPP", "confidence": 0.75 },
    "port_of_discharge": { "value": "DEHAM", "confidence": 0.78 }
  },
  "compliance": {
    "decision": "APPROVE",
    "rules_passed": 14,
    "rules_failed": 1,
    "rules_total": 15
  }
}
```

### Response: Sync Preview
```json
{
  "changes": [
    {
      "field": "container_number",
      "current": "BECKMANN-CNT-001",
      "new_value": "MSCU1234567",
      "is_placeholder": true,
      "will_update": true
    },
    {
      "field": "vessel_name",
      "current": null,
      "new_value": "RHINE MAERSK",
      "is_placeholder": true,
      "will_update": true
    }
  ],
  "auto_synced": false
}
```

## Frontend Changes

### New Files
- `src/lib/api/bol-types.ts` — BolParsedData, BolField, SyncPreview types
- `src/lib/api/bol.ts` — React Query hooks for BoL endpoints
- `src/components/documents/bol-parsed-fields.tsx` — Parsed BoL data display
- `src/components/documents/bol-sync-preview.tsx` — Sync preview with apply button

### Modified Files
- `src/components/documents/document-list.tsx` — Add parse status badge to BoL docs
- `src/app/shipments/[id]/page.tsx` — Add BoL panel to document review

## Compliance Impact

Respects product type per COMPLIANCE_MATRIX.md:
- Horn/hoof (0506/0507): Run BOL-HH-001 through BOL-HH-003 (TRACES, vet cert, approved consignee). NO EUDR.
- EUDR products: Standard BoL rules only (no EUDR-specific BoL rules yet).

Cross-document validation: BoL gross weight vs Packing List gross weight must be within 5% tolerance.

## Testing

### Backend (pytest)
- `test_bol_auto_parse.py` — Auto-parse on upload, StorageBackend integration
- `test_bol_sync_v2.py` — Enhanced sync with confidence threshold
- `test_bol_cross_validation.py` — Weight tolerance between documents

### Frontend (vitest)
- `bol-types.test.ts` — Type helper tests
- `bol-parsed-fields.test.tsx` — Field display with confidence indicators
- `bol-sync-preview.test.tsx` — Preview display, apply button
