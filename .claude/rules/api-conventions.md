# API Conventions

## FastAPI Backend (v1 + v2)

### Structure
```
tracehub/backend/app/
  routers/       — one file per resource (shipments, documents, organizations, ...)
  services/      — business logic layer (never import routers)
  models/        — SQLAlchemy ORM models
  schemas/       — Pydantic request/response schemas
  config.py      — Pydantic Settings
```

### Rules

- All request/response bodies are Pydantic models from `schemas/`
- Never build JSON dicts manually — always use `.model_dump()`
- Use dependency injection for settings, DB sessions, auth
- API versioning: `/api/` prefix (v1), `/v2/` prefix (v2)
- Health check at `GET /health` — no auth required
- All other endpoints require authentication

### Naming
- Resource endpoints: plural nouns (`/shipments`, `/documents`, `/organizations`)
- Actions: verbs as sub-paths (`/shipments/{id}/approve`, `/documents/{id}/reject`)
- Query params for filtering: `?status=active&organization_id=...`

### Error Handling
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"code": "SHIPMENT_NOT_FOUND", "message": f"Shipment {id} not found"}
)
```

Standard error codes:
| Code | Status | When |
|------|--------|------|
| `AUTHENTICATION_REQUIRED` | 401 | Missing or expired token |
| `FORBIDDEN` | 403 | Insufficient role/permissions |
| `SHIPMENT_NOT_FOUND` | 404 | Invalid shipment ID |
| `DOCUMENT_NOT_FOUND` | 404 | Invalid document ID |
| `VALIDATION_ERROR` | 422 | Invalid request body |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Next.js BFF (v2)

### Structure
```
app/
  api/                — Next.js API routes (BFF layer)
    auth/             — PropelAuth callbacks
    shipments/        — Proxy to FastAPI with auth headers
    documents/        — Proxy to FastAPI with auth headers
  (dashboard)/        — Protected app routes
  (auth)/             — Login/signup pages
```

### Rules
- BFF proxies to FastAPI — never duplicate business logic
- Add auth headers from PropelAuth session
- Cache responses where appropriate (ISR, SWR)
- Shape responses for frontend consumption (remove internal fields)

## Type Bridge (OpenAPI → Hey API)

Pydantic models → OpenAPI spec → Hey API → TypeScript client + Zod schemas

```bash
# Generate TypeScript client from FastAPI OpenAPI spec
npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/lib/api/generated
```

- Pydantic stays the source of truth for all types
- Never manually define TypeScript types that mirror backend models
- Zod schemas auto-generated for runtime validation
