# TraceHub v2 — Universal Agent Instructions

Container tracking & compliance SaaS for VIBOTAJ Global Nigeria Ltd (EU TRACES: RC1479592).
Production: https://tracehub.vibotaj.com

This file is read by all AI coding agents (Claude Code, GitHub Copilot, Gemini).
For tool-specific config see `CLAUDE.md`, `.github/copilot-instructions.md`, or `.github/instructions/`.

## Stack

| Layer | v2 (Target) | v1 (Current) |
|-------|-------------|--------------|
| Frontend | Next.js 15 + TypeScript + Tailwind + Shadcn UI | React 18 + Vite + Tailwind |
| BFF | Next.js API Routes (auth proxy, caching) | — |
| Backend | FastAPI + Pydantic v2 | FastAPI + SQLAlchemy + Alembic |
| Database | Supabase (PostgreSQL + RLS + Realtime + Storage) | PostgreSQL 15 (Docker) |
| Auth | PropelAuth (orgs, 6 roles, SAML/SCIM) | Custom JWT (python-jose) |
| Monitoring | Sentry | — |
| Type Bridge | OpenAPI → Hey API → TypeScript client | — |

## Key Paths

| Path | Purpose |
|------|---------|
| `tracehub/backend/app/routers/` | FastAPI API endpoints |
| `tracehub/backend/app/models/` | SQLAlchemy ORM models |
| `tracehub/backend/app/services/` | Business logic layer |
| `tracehub/backend/app/schemas/` | Pydantic request/response schemas |
| `tracehub/backend/app/config.py` | Pydantic Settings (all config from .env) |
| `tracehub/frontend/src/` | React frontend (v1) |
| `v2/frontend/src/` | Next.js frontend (v2) |
| `tracehub/backend/alembic/` | Database migrations |
| `docs/prds/` | Feature specifications |
| `docs/PLAN.md` | Living sprint plan |
| `docs/COMPLIANCE_MATRIX.md` | HS codes & required documents |

## CRITICAL: Business Rules

### Horn & Hoof (HS 0506/0507) = NOT covered by EUDR

This is a regulatory fact, not a product decision.

NEVER add to horn/hoof products:
- Geolocation coordinates
- Deforestation statements
- EUDR risk assessment scores
- Due diligence documentation fields

Required documents for horn/hoof:
1. EU TRACES Number (RC1479592)
2. Veterinary Health Certificate
3. Certificate of Origin
4. Bill of Lading
5. Commercial Invoice
6. Packing List

Always check `docs/COMPLIANCE_MATRIX.md` before any compliance work.

### Multi-Tenancy Isolation

All database queries MUST filter by `organization_id`. NEVER return data across tenants.

Defense-in-depth layers:
1. JWT contains `org_id` (set by auth middleware)
2. Application-level filtering: `Model.organization_id == current_user.organization_id`
3. Supabase RLS policies (v2)
4. Audit logs capture organization context

### Pydantic Schemas for API Responses

Never build JSON dicts manually. All responses MUST use Pydantic schemas with `ConfigDict(from_attributes=True)`.

```python
class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    reference: str
    organization_id: UUID
```

## Code Standards

### Python
- Pydantic v2 schemas for all API request/response bodies
- `SecretStr` for API keys and secrets
- `pydantic-settings` for configuration (never `os.getenv()`)
- Type hints on all public functions
- Google-style docstrings

### TypeScript
- No `any` types — ever
- Zod for runtime validation at API boundaries
- Shadcn UI components (v2)

### Testing
- TDD: write failing test → implement → refactor
- Backend: pytest + pytest-asyncio
- Frontend: Vitest + Testing Library + Playwright (E2E)
- Every compliance rule must have a test

## Git Flow

- NEVER commit directly to main
- Branch naming: `feature/prd-XXX-short-description`
- Conventional commits: `feat(scope):`, `fix(scope):`, `test(scope):`, `docs:`, `refactor:`
- All commits attributed to Shola (no Co-Authored-By trailers)

## Architecture References

- `.claude/rules/` — domain rules (multi-tenancy, compliance, security, API, Pydantic, testing)
- `.github/instructions/` — path-scoped Copilot instructions
- `docs/prds/` — feature specifications
- `docs/decisions/` — Architecture Decision Records
- `docs/PLAN.md` — living sprint plan
