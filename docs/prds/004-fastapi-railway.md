# PRD-004: FastAPI on Railway

**Status:** Specified
**Complexity:** Medium
**Target:** Week 2
**Dependencies:** PRD-002 (Supabase schema — DATABASE_URL)
**Branch:** `feature/prd-004-fastapi-railway`

---

## Problem

v1 FastAPI runs in a Docker container on Hostinger VPS (82.198.225.150) with SSH + rsync deployments, no auto-scaling, no health monitoring, and manual process management. A single VPS failure takes down the entire backend. No CI/CD pipeline — deployments are manual SSH sessions.

## Acceptance Criteria

1. FastAPI deploys to Railway from `main` branch with auto-deploy on push
2. Deploy only triggers on changes to `tracehub/backend/` path
3. All env vars configured in Railway dashboard:
   - `DATABASE_URL` → Supabase direct connection (port 5432, NOT PgBouncer 6543)
   - `PROPELAUTH_AUTH_URL`, `PROPELAUTH_API_KEY` (placeholder until PRD-003)
   - `SENTRY_DSN` (placeholder until PRD-006)
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS` (Vercel preview URLs + production domain)
   - All existing v1 env vars (JSONCargo API key, Claude API key, SendGrid, etc.)
4. Health checks pass: `GET /health`, `GET /health/ready`, `GET /health/live`
5. RLS middleware sets `app.current_org_id` and `app.is_system_admin` per-request
6. `auto_seed_if_empty()` disabled when `ENVIRONMENT=production`
7. Hostinger VPS continues running as fallback during transition
8. Railway service has resource limits configured (prevent runaway costs)

## Technical Approach

### 1. Railway Project Setup

```bash
railway login
railway init  # or link to existing project
railway link
```

Configure:
- **Service name:** `tracehub-backend`
- **Root directory:** `tracehub/backend/`
- **Build command:** `pip install -r requirements.txt` (or Poetry if configured)
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health check:** `GET /health`

### 2. Railway Configuration File

```toml
# tracehub/backend/railway.toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

### 3. Database Connection (Supabase)

Critical: Use Supabase **direct connection** string, not the pooler:

```
# Direct (port 5432) — CORRECT for SQLAlchemy
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres

# Session pooler (port 5432 via pooler) — OK for SQLAlchemy
# Transaction pooler (port 6543) — BREAKS SQLAlchemy prepared statements
```

SQLAlchemy uses server-side prepared statements which are incompatible with PgBouncer transaction mode (port 6543).

### 4. RLS Middleware

New middleware that sets PostgreSQL session variables for RLS policies (from PRD-002):

```python
# Middleware added to FastAPI app
@app.middleware("http")
async def set_rls_context(request: Request, call_next):
    """Set PostgreSQL session variables for RLS."""
    user = get_optional_current_user(request)
    if user:
        async with db.begin():
            await db.execute(text(
                f"SET LOCAL app.current_org_id = '{user.organization_id}'"
            ))
            await db.execute(text(
                f"SET LOCAL app.is_system_admin = '{user.role == 'admin'}'"
            ))
    response = await call_next(request)
    return response
```

### 5. Environment-Gated Seeding

Modify `main.py` lifespan to skip auto-seeding in production:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... table creation, enum checks ...
    if settings.ENVIRONMENT != "production":
        await auto_seed_if_empty()
    yield
```

### 6. CORS Configuration

Update CORS origins to include Vercel:

```python
CORS_ORIGINS = [
    "https://tracehub-v2.vercel.app",        # Production
    "https://tracehub-v2-*.vercel.app",       # Preview deploys
    "http://localhost:3000",                    # Local dev
    settings.CORS_ORIGINS,                     # Additional from env
]
```

## Files to Create/Modify

```
tracehub/backend/
  railway.toml                    # NEW: Railway deployment config
  Procfile                        # NEW: Alternative start command (Railway reads both)
  app/
    middleware/
      rls_context.py              # NEW: RLS session variable middleware
    main.py                       # MODIFY: environment-gated seeding, CORS update
    config.py                     # MODIFY: add ENVIRONMENT field
```

## v1 Reference Files

| v1 File | What to Reference |
|---------|------------------|
| `tracehub/backend/app/main.py` (421 lines) | Lifespan, router mounts, middleware stack, health endpoints |
| `tracehub/backend/app/config.py` | Pydantic Settings — all env vars |
| `tracehub/backend/requirements.txt` or `pyproject.toml` | Dependencies for build |
| `tracehub/backend/Dockerfile` | Current Docker build for reference |

## Critical Notes

- **Port 5432 not 6543:** SQLAlchemy + PgBouncer transaction mode = broken prepared statements. Use Supabase direct connection only.
- **Ephemeral filesystem:** Railway containers have no persistent disk. File uploads at `./uploads/` will be lost on redeploy. PRD-005 (Supabase Storage) resolves this — until then, document upload is broken on Railway.
- **`auto_seed_if_empty()`:** This function in `main.py` checks if the database is empty and seeds sample data. On a fresh Supabase database, it WILL fire. Gate behind `ENVIRONMENT != "production"`.
- **Worker count:** Start with 2 workers. Railway's starter plan has 512MB RAM — monitor and adjust.
- **Rate limits:** v1 has IP-based rate limits (login: 10/min, tracking: 50/min). These work on Railway since each request has a unique client IP via proxy headers.

## Testing Strategy

- Railway deploy succeeds from `main` branch push
- `GET /health` returns 200 with version and environment
- `GET /health/ready` confirms database connectivity (Supabase)
- `GET /health/live` returns 200 (liveness probe)
- API endpoints return correct data with Supabase database
- RLS middleware correctly sets session variables (verify via `SELECT current_setting('app.current_org_id')`)
- Auto-seed does NOT run when `ENVIRONMENT=production`
- CORS allows requests from Vercel preview deploy URLs

## Migration Notes

- Hostinger VPS continues running v1 — Railway is v2 only
- DNS switch happens in Phase 4 cutover (api.tracehub.vibotaj.com → Railway)
- Railway free tier: 500 hours/month, 512MB RAM, 1 vCPU — sufficient for dev/staging
- Production upgrade to Pro plan ($5/month) when traffic justifies it
- Logs visible in Railway dashboard — no SSH needed
