# PRD-012: Shipment Detail + Document Management

## Problem Statement

The shipment list page (PRD-011) links to `/shipments/{id}` but no detail page exists yet. Users need to view full shipment info, manage documents (upload, review, approve/reject), see tracking events, and check compliance status — all of which exist in v1 and must be rebuilt in v2.

## Dependencies

- PRD-009 (design system — Shadcn components, domain composites)
- PRD-010 (auth — OrgProvider, role-based access)
- PRD-011 (shipment types, React Query hooks, status badge)

## Acceptance Criteria

### Shipment Detail Page (`/shipments/[id]`)
- [ ] 2-column layout: main content (2/3) + sidebar (1/3)
- [ ] Header: back link, reference + status badge, container number
- [ ] Shipment info card: vessel/voyage, B/L number, route (POL → POD), ETD/ETA, shipper, consignee, cargo/products
- [ ] Tabs: Documents (count badge), Tracking (event count badge)
- [ ] Loading, error, and not-found states
- [ ] Breadcrumbs: Dashboard > Shipments > {reference}

### Document Management
- [ ] Document list: type, reference, status badge, issue date, download button
- [ ] Missing documents section: red-highlighted list of required but absent doc types
- [ ] Upload modal: drag & drop + click-to-browse, document type selector, reference field, file validation (PDF/JPEG/PNG/DOCX, max 50MB)
- [ ] Document review panel (sheet/dialog): document info, status badge, download/delete actions
- [ ] Approve/reject flows: approve with optional notes, reject with required reason
- [ ] Delete with required reason (min 5 chars)
- [ ] Validation issues display: errors (blocking), warnings, overridable issues

### Tracking Timeline
- [ ] Vertical timeline: most recent first, connected dots
- [ ] Event: type icon, label, timestamp + relative time, location, vessel/voyage
- [ ] "Latest" badge on most recent event
- [ ] Empty state when no events

### Compliance Sidebar
- [ ] Document status card: overall badge (complete/incomplete), progress bar, missing docs list
- [ ] EUDR card: only shown for EUDR-applicable products (NOT horn/hoof 0506/0507)
- [ ] Quick actions: Upload Document, Download Audit Pack

### Types to Add
- [ ] `ShipmentDetail` (extends Shipment with bl_number, products, exporter/importer, etc.)
- [ ] `Document` type (id, type, status, file_path, reference_number, etc.)
- [ ] `DocumentStatus` aligned with backend lifecycle
- [ ] `ContainerEvent` type
- [ ] `ComplianceStatus` type
- [ ] React Query hooks: `useShipmentDetail`, `useShipmentDocuments`, `useShipmentEvents`
- [ ] Mutation hooks: `useUploadDocument`, `useApproveDocument`, `useRejectDocument`, `useDeleteDocument`

## API Changes

No backend changes — consume existing v1/v2 endpoints:
- `GET /api/shipments/{id}` → shipment detail
- `GET /api/shipments/{id}/documents` → document list + required types
- `GET /api/shipments/{id}/events` → tracking events
- `POST /api/documents/upload` → file upload
- `POST /api/documents/{id}/approve` → approval
- `POST /api/documents/{id}/reject` → rejection
- `DELETE /api/documents/{id}` → deletion

## Database Changes

None.

## Frontend Changes

### New Files
- `app/shipments/[id]/page.tsx` — detail page
- `components/shipments/shipment-info.tsx` — info card
- `components/shipments/shipment-header.tsx` — header with back link + actions
- `components/documents/document-list.tsx` — document table + missing docs
- `components/documents/document-upload-modal.tsx` — upload dialog
- `components/documents/document-review-panel.tsx` — review sheet
- `components/documents/document-actions.tsx` — approve/reject/delete flows
- `components/tracking/tracking-timeline.tsx` — event timeline
- `components/compliance/compliance-status.tsx` — compliance sidebar card
- `components/compliance/eudr-status-card.tsx` — EUDR card (conditional)
- `lib/api/document-types.ts` — pure document types
- `lib/api/documents.ts` — React Query hooks for documents
- `lib/api/tracking-types.ts` — container event types

### Modified Files
- `lib/api/shipment-types.ts` — add `ShipmentDetail`, extended fields
- `lib/api/shipments.ts` — add `useShipmentDetail` hook

## Compliance Impact

- EUDR card MUST NOT appear for horn/hoof (HS 0506/0507) — check `docs/COMPLIANCE_MATRIX.md`
- Document required types vary by product — compliance matrix drives this
- Approval requires `compliance_officer` or `admin` role
