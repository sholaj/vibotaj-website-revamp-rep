# Known Issues & Tech Debt

## Security & Multi-Tenancy
- [RESOLVED] **Document Visibility**: Documents uploaded via `POST /api/documents/upload` now correctly have `organization_id` assigned.
  - *Fix Applied*: `documents.py` updated to set `organization_id` from `current_user`.

## Database Migrations
- [RESOLVED] **Migration Idempotency**: Migrations failing when columns/constraints already exist.
  - *Affected*: `20260112_0001_add_eudr_origin_fields.py`, `20260115_0001_reference_per_org_unique.py`, `20260115_0002_add_document_extraction_fields.py`
  - *Error*: `column "deforestation_free_statement" of relation "origins" already exists`
  - *Fix Applied*: Made all migrations idempotent by checking existence before add/drop operations.
  - *Pattern*: Use `column_exists()` and `constraint_exists()` helper functions before DDL operations.
