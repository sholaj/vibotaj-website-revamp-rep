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

## 🚨 CRITICAL BUSINESS RULES

### EUDR Compliance - READ FIRST

**Horn & Hoof (HS 0506/0507) = NOT covered by EUDR**

NEVER add to horn/hoof products:
- ❌ Geolocation coordinates
- ❌ Deforestation statements
- ❌ EUDR risk scores

REQUIRED documents for horn/hoof:
- ✅ EU TRACES (RC1479592)
- ✅ Veterinary Health Cert
- ✅ Certificate of Origin
- ✅ Bill of Lading
- ✅ Commercial Invoice
- ✅ Packing List

**Check `docs/COMPLIANCE_MATRIX.md` before any compliance work.**

---

## Operational Pillars

TraceHub operates on a modern DevOps infrastructure with the following pillars:

### 1. GitOps Workflow
- **Version Control:** Git with GitHub as central repository
- **Branch Strategy:** 
  - `main` → Production (manual approval required)
  - `develop` → Staging (auto-deploy)
  - `feature/*` → Development branches
- **Principle:** All infrastructure and deployment configurations are versioned in Git
- **Automation:** GitHub Actions drives all CI/CD processes

### 2. GitHub CLI (`gh` binary)
- **Purpose:** Command-line interface for GitHub operations
- **Common Operations:**
  ```bash
  gh workflow run deploy-staging.yml           # Trigger deployments
  gh secret set PRODUCTION_SSH_KEY < key.pem   # Manage secrets
  gh pr create --title "feat: ..." --body "..." # Create PRs
  gh repo view --web                            # View repository
  ```
- **Integration:** Used in automation scripts and manual operations

### 3. Hostinger MCP (VPS Management)
- **Provider:** Hostinger API via MCP (Model Context Protocol)
- **Configuration:** See `docs/_archive/root-cleanup/HOSTINGER_CONFIG.md`
- **Claude Integration:** MCP server enables Claude to manage VPS directly
- **Setup in Claude:**
  ```json
  {
    "servers": {
      "hostinger-mcp": {
        "type": "stdio",
        "command": "npx",
        "args": ["hostinger-api-mcp@latest"],
        "env": {"API_TOKEN": "${HOSTINGER_API_TOKEN}"}
      }
    }
  }
  ```
- **Capabilities:** VPS management, DNS updates, SSL configuration

### 4. GitHub Actions (CI/CD Pipeline)
- **Workflows:** Located in `.github/workflows/`
  - `backend-ci.yml` - Backend linting, tests, security scan
  - `frontend-ci.yml` - Frontend linting, type checking, build validation
  - `build-and-push.yml` - Docker image builds to GHCR
  - `deploy-staging.yml` - Auto-deploy to staging environment
  - `deploy-production.yml` - Manual deploy to production (blue-green)
  - `database-migrations.yml` - Migration validation and testing
- **Container Registry:** GitHub Container Registry (GHCR) for Docker images
- **Artifact Storage:** GitHub Actions artifacts for builds and reports

### 5. Multi-Environment Strategy
**Single VPS, Port-Isolated Environments:**

| Environment | Backend | Frontend | Database | Domain |
|-------------|---------|----------|----------|--------|
| **Production** | :8000 | :3000 | :5432 | https://tracehub.vibotaj.com |
| **Staging** | :8100 | :3100 | :5532 | https://staging.tracehub.vibotaj.com |

**Directory Structure on VPS:**
```
/home/tracehub/
├── production/
│   ├── docker-compose.yml
│   ├── .env.production
│   └── backups/
└── staging/
    ├── docker-compose.yml
    ├── .env.staging
    └── backups/
```

### 6. Deployment Pipeline Flow
```
Code Push → GitHub Actions
    ↓
Lint & Test (parallel)
    ↓
Build Docker Images → GHCR
    ↓
Deploy to Environment
    ↓
Database Migration
    ↓
Health Checks & Smoke Tests
    ↓
Success ✓ / Auto-Rollback on Failure
```

**For full details, see:**
- `tracehub/DEVOPS.md` - Complete DevOps documentation
- `docs/DEPLOYMENT.md` - Deployment procedures
- `.github/workflows/` - Pipeline definitions

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

## Workflow

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

| Path | Purpose |
|------|---------|
| `docs/COMPLIANCE_MATRIX.md` | HS codes & required documents |
| `docs/decisions/` | Architecture decisions |
| `tracehub/` | Main application code |
| `PRPs/active/` | Current implementation blueprints |

---

## Current Focus

**Sprint 8: EUDR Correction & Multi-Tenancy**
- [ ] Remove EUDR fields from horn/hoof products
- [ ] Implement organization model
- [ ] Onboard HAGES as pilot customer
