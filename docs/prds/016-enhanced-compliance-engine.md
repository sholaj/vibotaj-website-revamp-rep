# PRD-016: Enhanced Compliance Engine

## Problem Statement

The v1 backend has an excellent compliance foundation — BoL rules engine, document workflow states, and a validation runner — but these pieces aren't fully connected. Document state transitions aren't persisted, validation results aren't generalized beyond BoL, and the v2 frontend has no way to display compliance rule results or manage overrides. PRD-016 formalizes the state machine, unifies the validation engine, and builds the frontend to visualize it all.

## Dependencies

- PRD-004 (FastAPI on Railway — backend)
- PRD-012 (Shipment detail — compliance status components)

## Scope

### Backend: State Machine + Validation Unification

**In scope:**
- Document transition history table (`document_transitions`) — persists every state change with actor, reason, timestamp
- Auto-validation hook: when document moves UPLOADED → VALIDATED, run ValidationRunner and persist results
- Generalize ComplianceResult to work for all document types (not just BoL)
- Shipment-level compliance aggregation: derive status from document compliance states
- Compliance decision endpoint: returns aggregate APPROVE/HOLD/REJECT for a shipment
- Override endpoint enhancement: admin can override compliance at document or shipment level

**Out of scope:**
- New BoL parsing logic (PRD-018)
- AI classification (PRD-019)
- New validation rules beyond what v1 already defines

### Frontend: Compliance Visualization

**In scope:**
- Compliance rules table — shows rule results (id, name, passed/failed, severity, message) for a shipment
- Document state stepper — visual timeline of document state transitions
- Compliance override dialog — admin can override a failed rule with reason
- Shipment compliance summary — aggregate status card with decision badge
- Integration into shipment detail page (PRD-012)

**Out of scope:**
- Compliance analytics (already in PRD-014)
- EUDR-specific forms (future PRD)

## Acceptance Criteria

### Backend
1. Every document state transition is persisted to `document_transitions` with actor_id, from_state, to_state, reason, timestamp
2. Moving a document to VALIDATED auto-runs validation rules and stores results in `compliance_results`
3. `GET /api/validation/shipments/{id}` returns full validation report with all rule results
4. `GET /api/validation/shipments/{id}/status` returns aggregate compliance decision (APPROVE/HOLD/REJECT)
5. `POST /api/validation/shipments/{id}/override` allows admin to override compliance with reason
6. All endpoints filter by organization_id (multi-tenancy)

### Frontend
7. Compliance rules table renders for shipment with rule name, status icon, severity badge, message
8. Document state stepper shows transition history with timestamps
9. Override dialog allows admin to enter reason and submit
10. Shipment compliance card shows aggregate decision with color-coded badge
11. All components have Vitest tests

## Database Changes

### New table: `document_transitions`
```sql
CREATE TABLE document_transitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id),
  from_state VARCHAR(50) NOT NULL,
  to_state VARCHAR(50) NOT NULL,
  actor_id UUID REFERENCES users(id),
  reason TEXT,
  metadata JSONB DEFAULT '{}',
  organization_id UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### Extend `compliance_results`
- Add `shipment_id` UUID FK (nullable, for shipment-level results)
- Add `document_type` VARCHAR (to track which doc type the rule applies to)

## API Changes

### New/Enhanced Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/validation/shipments/{id}` | Full validation report (enhanced) |
| GET | `/api/validation/shipments/{id}/status` | Aggregate compliance decision |
| GET | `/api/validation/shipments/{id}/transitions` | Document transition history |
| POST | `/api/validation/shipments/{id}/override` | Override compliance (admin) |
| DELETE | `/api/validation/shipments/{id}/override` | Clear override |

### Response: Compliance Report
```json
{
  "shipment_id": "...",
  "decision": "HOLD",
  "summary": { "total_rules": 15, "passed": 12, "failed": 2, "warnings": 1 },
  "results": [
    { "rule_id": "BOL-001", "rule_name": "Shipper name required", "passed": true, "severity": "ERROR" },
    { "rule_id": "PRESENCE_001", "rule_name": "Required documents present", "passed": false, "severity": "ERROR", "message": "Missing: Veterinary Health Certificate" }
  ],
  "override": null
}
```

## Frontend Changes

### New Files
- `src/lib/api/compliance-types.ts` — ComplianceReport, RuleResult, TransitionHistory, Override types
- `src/lib/api/compliance.ts` — React Query hooks for validation endpoints
- `src/components/compliance/compliance-rules-table.tsx` — Rule results table with severity badges
- `src/components/compliance/document-state-stepper.tsx` — Visual transition timeline
- `src/components/compliance/compliance-override-dialog.tsx` — Override form with reason
- `src/components/compliance/shipment-compliance-card.tsx` — Aggregate decision card

### Modified Files
- `src/app/shipments/[id]/page.tsx` — Add compliance tab with rules table, override capability

## Compliance Impact

CRITICAL: Must respect horn/hoof exclusion. EUDR rules MUST NOT be applied to HS 0506/0507. The `get_rules_for_product_type()` function already handles this — PRD-016 must preserve this behavior.

## Testing

### Backend (pytest)
- `test_document_transitions.py` — transition persistence, actor tracking
- `test_compliance_engine.py` — validation on state change, result persistence
- `test_compliance_aggregation.py` — shipment-level decision logic
- `test_compliance_override.py` — admin override workflow
- `test_horn_hoof_exclusion.py` — verify EUDR rules not applied to 0506/0507

### Frontend (vitest)
- `compliance-types.test.ts` — Type helper tests
- `compliance-rules-table.test.tsx` — Renders rules, severity badges, pass/fail icons
- `document-state-stepper.test.tsx` — Renders transitions timeline
- `compliance-override-dialog.test.tsx` — Form validation, submit handler
- `shipment-compliance-card.test.tsx` — Decision badge, summary counts
