---
applyTo: "tracehub/backend/**/*.py,v2/backend/**/*.py"
---

# Python API Conventions

## FastAPI Structure

```
tracehub/backend/app/
  routers/       — one file per resource (shipments, documents, organizations)
  services/      — business logic layer (never import routers)
  models/        — SQLAlchemy ORM models
  schemas/       — Pydantic request/response schemas
  config.py      — Pydantic Settings
```

## Router Rules

- All request/response bodies are Pydantic models from `schemas/`
- Never build JSON dicts manually — always use `.model_dump()` or `model_validate()`
- Use dependency injection for settings, DB sessions, auth
- API versioning: `/api/` prefix (v1), `/v2/` prefix (v2)
- Health check at `GET /health` — no auth required
- All other endpoints require authentication

## Naming

- Resource endpoints: plural nouns (`/shipments`, `/documents`, `/organizations`)
- Actions: verbs as sub-paths (`/shipments/{id}/approve`, `/documents/{id}/reject`)
- Query params for filtering: `?status=active&organization_id=...`

## Error Handling

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

## Pydantic Schemas

All request/response models live in `tracehub/backend/app/schemas/`.

```python
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime

class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    reference: str
    status: ShipmentStatus
    organization_id: UUID
    created_at: datetime
```

### Schema Rules

- `ConfigDict(from_attributes=True)` for ORM model conversion
- Separate Create/Update/Response models — never expose internal fields in responses
- Use `Field()` with constraints: `min_length`, `ge`, `le`, `max_length`
- Use `StrEnum` for status fields — never bare strings
- Use `UUID` for all IDs
- Use `datetime` with timezone awareness

## Settings

All config via `pydantic-settings` in `tracehub/backend/app/config.py`.

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    database_url: str = "postgresql://..."
    jwt_secret: SecretStr = SecretStr("change-me")
```

- `SecretStr` for ALL secrets (API keys, tokens, passwords)
- `@lru_cache` on `get_settings()` for singleton
- Never `os.getenv()` — always via Settings

## Validation

- Validators on the model, not in service logic
- Use `field_validator` for complex validation (e.g., ISO 6346 container numbers)
- Use `model_validator` for cross-field validation
- Return clear error messages that the frontend can display

## Next.js BFF (v2)

```
app/
  api/                — Next.js API routes (BFF layer)
    auth/             — PropelAuth callbacks
    shipments/        — Proxy to FastAPI with auth headers
    documents/        — Proxy to FastAPI with auth headers
  (dashboard)/        — Protected app routes
  (auth)/             — Login/signup pages
```

- BFF proxies to FastAPI — never duplicate business logic
- Add auth headers from PropelAuth session
- Cache responses where appropriate (ISR, SWR)

## Type Bridge (OpenAPI → Hey API)

Pydantic models → OpenAPI spec → Hey API → TypeScript client + Zod schemas.
Pydantic stays the source of truth for all types. Never manually define TypeScript types that mirror backend models.

## Anti-Patterns

- Never use `dict` for structured data — make a model
- Never use `Any` — find the right type
- Never use `model_dump()` to convert between model types — use explicit mapping
- Never put validation outside models — validators belong on the model
- Never return raw SQLAlchemy objects from API endpoints — convert to Pydantic
