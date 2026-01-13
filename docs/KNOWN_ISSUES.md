# Known Issues & Tech Debt

## Security & Multi-Tenancy
- **[CRITICAL] Document Visibility**: Documents uploaded via `POST /api/documents/upload` do not have `organization_id` assigned. This results in the document being inaccessible to the uploader when `organization_id` filtering is applied.
  - *Impact*: Users receive 404 when trying to view documents they just uploaded.
  - *Fix Required*: Assign `organization_id` from `current_user` during document creation in `routers/documents.py`.
