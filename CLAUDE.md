# TraceHub v2 — Project Context

Container tracking & compliance SaaS for VIBOTAJ Global Nigeria Ltd (EU TRACES: RC1479592).
Production: https://tracehub.vibotaj.com

## Stack

### v2 Target (Super Pack)
- **Frontend:** Next.js 15 + TypeScript + Tailwind + Shadcn UI (Vercel)
- **BFF:** Next.js API Routes (auth proxy, caching, client shaping)
- **Backend:** FastAPI + Pydantic v2 (Railway/Render — business logic, OCR, PDF gen, compliance)
- **Database:** Supabase (PostgreSQL + RLS + Realtime + Storage)
- **Auth:** PropelAuth (organizations, 6+ roles, SAML/SCIM, FastAPI SDK)
- **Monitoring:** Sentry
- **Type Bridge:** OpenAPI → Hey API → TypeScript client

### v1 Current (being migrated)
- **Frontend:** React 18 + Vite + Tailwind (Docker/Nginx)
- **Backend:** FastAPI + SQLAlchemy + Alembic (Docker)
- **Database:** PostgreSQL 15 (self-hosted Docker)
- **Auth:** Custom JWT (python-jose)
- **Hosting:** Hostinger VPS (82.198.225.150)

## Commands
```bash
make test              # Backend pytest + frontend vitest
make lint              # Black + ruff + eslint
make format            # Auto-format all code
make validate          # lint + test + security-scan
make security-scan     # detect-secrets + credential grep
```

## Key Paths
| Path | Purpose |
|------|---------|
| `tracehub/backend/app/routers/` | FastAPI API endpoints |
| `tracehub/backend/app/models/` | SQLAlchemy ORM models |
| `tracehub/backend/app/services/` | Business logic layer |
| `tracehub/backend/app/schemas/` | Pydantic request/response schemas |
| `tracehub/backend/app/config.py` | Pydantic Settings (all config from .env) |
| `tracehub/frontend/src/` | React frontend (v1) |
| `tracehub/backend/alembic/` | Database migrations |
| `docs/prds/` | Feature specifications |
| `docs/PLAN.md` | Living sprint plan |
| `docs/COMPLIANCE_MATRIX.md` | HS codes & required documents |

## CRITICAL: Business Rules

**Horn & Hoof (HS 0506/0507) = NOT covered by EUDR.** NEVER add geolocation, deforestation statements, or EUDR risk scores to horn/hoof products. Required docs: EU TRACES, Vet Health Cert, CoO, BoL, Invoice, Packing List. Check `docs/COMPLIANCE_MATRIX.md` before any compliance work.

## CRITICAL: Multi-Tenancy

All database queries MUST filter by `organization_id`. NEVER return data across tenants. v2 adds Supabase RLS as defense-in-depth — but application-level filtering remains mandatory. See `.claude/rules/multi-tenancy.md` for required patterns.

## Git Flow
IMPORTANT: NEVER commit directly to main. Every PRD gets a feature branch.
- Branch naming: `feature/prd-XXX-short-description`
- Create the feature branch from `main` BEFORE writing any code
- All commits for a PRD go on its feature branch
- When PRD is complete (tests pass, lint clean): merge to main via PR
- Only docs-only changes may go directly to main
- NEVER add `Co-Authored-By` trailers to commits. All commits are attributed to Shola.
- Conventional commits: `feat(scope):`, `fix(scope):`, `test(scope):`, `docs:`, `refactor:`

## Execution Rules
IMPORTANT: Act autonomously. Do NOT ask for confirmation before:
- Reading, writing, or editing files
- Running tests, linting, or type checking
- Creating new files or directories
- Making git commits on feature branches
- Running any make/poetry/npm command

IMPORTANT: Only pause and ask when:
- The task is ambiguous and you genuinely don't know what I want
- You need to make a destructive or irreversible architectural decision
- A test reveals a design problem that needs human judgment
- Anything touches EUDR compliance logic (double-check with COMPLIANCE_MATRIX.md)

IMPORTANT: After completing work, always:
1. Run `make validate` (lint + test + security-scan)
2. If all pass, `git add && git commit` with conventional commit message (on feature branch)
3. Update `docs/PLAN.md` to reflect completed work
4. Report what you did in 3-5 bullet points

## Code Standards

### Python (Backend)
- Formatter: Black (line-length=88), Linter: ruff
- Type hints required on all public functions
- Pydantic v2 schemas for ALL API responses — never build JSON dicts manually
- `SecretStr` for API keys and secrets in config
- `pydantic-settings` for configuration — never `os.getenv()`
- All domain data uses Pydantic models
- Google-style docstrings

### TypeScript (Frontend)
- Formatter: Prettier, Linter: ESLint (strict)
- No `any` types — ever
- Zod for runtime validation at API boundaries

### Testing
- Tests first (TDD): write failing test → implement → refactor
- Backend: pytest + pytest-asyncio
- Frontend: Vitest + Testing Library + Playwright (E2E)

## Team
- **CEO/CTO:** Shola | **COO:** Bolaji Jibodu (bolaji@vibotaj.com)
- **Buyers:** HAGES, Witatrade, Beckman GBH, De Lochting (Belgium)

## Architecture References
- `.claude/rules/` — domain rules (multi-tenancy, compliance, security, API, Pydantic, testing)
- `.claude/commands/` — slash commands (new-feature, tdd, review, deploy, report, status, fix-issue)
- `docs/prds/` — feature specifications (numbered, one per feature branch)
- `docs/decisions/` — Architecture Decision Records
- `docs/PLAN.md` — living sprint plan with decisions log and PRD roadmap
