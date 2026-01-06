
# TraceHub - Project Context

> Single source of truth for AI-assisted development

## Project

**TraceHub** - Container tracking & compliance platform for VIBOTAJ Global Nigeria Ltd
**EU TRACES:** RC1479592 | **Production:** https://tracehub.vibotaj.com
**Stack:** FastAPI (Python 3.11) + React 18 (TypeScript) + PostgreSQL

## Team

- **CEO/CTO:** Shola | **COO:** Bolaji Jibodu (bolaji@vibotaj.com)
- **Buyers:** HAGES, Witatrade, Beckman GBH, De Lochting (Belgium)

---

## CRITICAL BUSINESS RULES

### EUDR Compliance - READ FIRST

**Horn & Hoof (HS 0506/0507) = NOT covered by EUDR**

NEVER add to horn/hoof products:
- Geolocation coordinates
- Deforestation statements
- EUDR risk scores

REQUIRED documents for horn/hoof:
- EU TRACES (RC1479592)
- Veterinary Health Cert
- Certificate of Origin
- Bill of Lading
- Commercial Invoice
- Packing List

**Check `docs/COMPLIANCE_MATRIX.md` before any compliance work.**

---

## Code Standards

### Python
- Formatter: Black (line-length=88)
- Linter: ruff
- Type hints: Required for public functions
- Docstrings: Google style

### TypeScript
- Formatter: Prettier
- Linter: ESLint (strict)
- No `any` types

### Commits
```
feat(scope): description
fix(scope): description
docs: description
test: description
refactor: description
```

---

## GitOps Workflow - MANDATORY

**Follow this deployment pipeline for ALL changes:**

```
feature branch -> test locally -> develop -> staging -> main -> production
```

### Branch Strategy

| Branch | Purpose | Deploys To |
|--------|---------|------------|
| `feature/*` | New features, bug fixes | Local only |
| `develop` | Integration branch | **Staging** (auto) |
| `main` | Production-ready code | **Production** (auto) |

### Development Process

1. **Create feature branch** from `main`:
   ```bash
   git checkout main && git pull
   git checkout -b feature/my-feature
   ```

2. **Develop & test locally**:
   - Run `make test && make lint`
   - Test with local Docker: `docker-compose up`
   - Validate UI with Puppeteer

3. **Push to develop** for staging:
   ```bash
   git checkout develop && git pull
   git merge feature/my-feature
   git push origin develop  # Triggers staging deployment
   ```

4. **Verify on staging**:
   - URL: https://staging.tracehub.vibotaj.com
   - Run smoke tests
   - Verify database migrations

5. **Merge to main** for production:
   ```bash
   git checkout main && git pull
   git merge develop
   git push origin main  # Triggers production deployment
   ```

### NEVER Skip Steps
- Don't push directly to `main` without staging verification
- Don't deploy to production without testing on staging
- Don't merge untested code to `develop`

---

## Coding Workflow

1. **Before coding:** Check `docs/COMPLIANCE_MATRIX.md` and `docs/decisions/`
2. **Complex features:** Create PRP in `PRPs/active/`
3. **Write tests first** (TDD)
4. **Run before commit:** `make test && make lint`
5. **Update:** CHANGELOG.md

---

## Security - CRITICAL

- **NEVER** commit secrets - use `.env` only
- **ALWAYS** run pre-commit hooks
- **CHECK** diffs for API keys before push

---

## Key Paths

### TraceHub Application
| Path | Purpose |
|------|---------|
| `tracehub/README.md` | Quick start guide |
| `tracehub/backend/` | FastAPI backend (Python) |
| `tracehub/frontend/` | React frontend (TypeScript) |
| `tracehub/scripts/` | Deployment & backup scripts |

### Core Documentation (tracehub/)
| Document | Purpose |
|----------|---------|
| `DEPLOYMENT.md` | VPS infrastructure, Docker, SSL, deployment |
| `DEVOPS.md` | CI/CD pipelines, GitHub Actions, GitOps |
| `FRONTEND.md` | UI/UX specs, feature requirements |
| `FRONTEND_QUICK_REFERENCE.md` | Design tokens, component patterns |
| `ROADMAP.md` | Sprint planning, feature backlog |
| `CHANGELOG.md` | Version history |

### Architecture (tracehub/docs/architecture/)
| Document | Purpose |
|----------|---------|
| `ARCHITECTURE.md` | System diagrams, container flow |
| `COMPONENT_HIERARCHY.md` | React component tree |
| `ADR-008-multi-tenancy-architecture.md` | Multi-tenancy design |

### Sprint Documentation (tracehub/docs/sprints/)
| Path | Purpose |
|------|---------|
| `sprint-7/` | OCR & AI document detection |
| `sprint-8/` | Multi-tenancy migration (complete) |
| `sprint-9/` | Compliance matrix updates |
| `SPRINT_BACKLOG.md` | Current sprint tasks |

### Project-Wide Docs (docs/)
| Document | Purpose |
|----------|---------|
| `COMPLIANCE_MATRIX.md` | HS codes & required documents |
| `decisions/` | Architecture decision records |
| `architecture/` | High-level system design |

---

## Architecture References

| Document | Purpose |
|----------|---------|
| `docs/COMPLIANCE_MATRIX.md` | HS codes & required documents |
| `docs/decisions/` | Architecture Decision Records |
| `tracehub/backend/alembic/versions/` | Database migration history |
| `tracehub/backend/app/routers/` | API endpoint implementations |
| `tracehub/backend/app/models/` | SQLAlchemy data models |
| `CHANGELOG.md` | Release history and changes |

---

## Multi-Tenancy Implementation - IMPORTANT

All API routers MUST implement organization-based data isolation.

### Required Pattern for All Endpoints

**1. Import the correct dependency:**
```python
from ..routers.auth import get_current_active_user
from ..schemas.auth import CurrentUser
```

**2. Use CurrentUser in function signature:**
```python
async def endpoint_name(
    current_user: CurrentUser = Depends(get_current_active_user)
):
```

**3. Filter all queries by organization_id:**
```python
query = db.query(Model).filter(Model.organization_id == current_user.organization_id)
```

### NEVER Use Legacy Pattern
```python
# WRONG - Does not include organization_id
from ..routers.auth import get_current_user, User
current_user: User = Depends(get_current_user)
```

### Router Reference

| Router | Endpoints | Data Filtering |
|--------|-----------|----------------|
| `shipments.py` | 12 | organization_id |
| `documents.py` | 15 | organization_id |
| `tracking.py` | 5 | organization_id |
| `eudr.py` | 9 | organization_id |
| `notifications.py` | 6 | user_id |
| `audit.py` | 3 | admin access |

### Multi-Tenancy Principles
- **Data Isolation:** Users only see their organization's data
- **Security:** Prevents cross-tenant data leakage
- **Compliance:** Required for multi-buyer support

---

## Browser UI Testing

**Puppeteer MCP Server** is installed for automated browser testing.

### Available Tools
After Claude Code restart, these puppeteer tools are available:
- `puppeteer_launch` - Launch browser instance
- `puppeteer_navigate` - Navigate to URL
- `puppeteer_screenshot` - Capture screenshots
- `puppeteer_click` - Click elements
- `puppeteer_type` - Type text into inputs
- `puppeteer_get_text` - Extract text from elements
- `puppeteer_evaluate` - Execute JavaScript
- `puppeteer_wait_for_selector` - Wait for elements

### Example: Test Login Flow
```
1. Launch browser: puppeteer_launch
2. Navigate: puppeteer_navigate to https://tracehub.vibotaj.com
3. Type email: puppeteer_type in email input
4. Type password: puppeteer_type in password input
5. Click login: puppeteer_click on login button
6. Screenshot: puppeteer_screenshot to verify
```

### Management
```bash
npx puppeteer-mcp-claude status    # Check installation
npx puppeteer-mcp-claude uninstall # Remove if needed
```

---

## Test Accounts

### HAGES Organization (Buyer)
| User | Email | Password |
|------|-------|----------|
| Helge Bischoff (owner) | helge.bischoff@hages.de | Hages2026Helge! |
| Mats Morten Jarsetz (admin) | mats.jarsetz@hages.de | Hages2026Mats! |
| Eike Pannen (admin) | eike.pannen@hages.de | Hages2026Eike! |

### VIBOTAJ Organization (Exporter)
| User | Email | Notes |
|------|-------|-------|
| Admin | admin@vibotaj.com | System admin |
| Shola | shola@vibotaj.com | CEO/CTO |
