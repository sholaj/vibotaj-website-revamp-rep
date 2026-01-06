# TraceHub Operational Pillars

> Comprehensive guide to TraceHub's operational infrastructure and DevOps practices

## Overview

TraceHub operates on six fundamental operational pillars that enable efficient development, deployment, and management of the platform. This document serves as the authoritative reference for understanding our operational practices.

---

## 1. GitOps - Infrastructure as Code

### Principle
**Everything is versioned in Git. Deployments are driven by Git state.**

### Implementation
- All infrastructure configurations stored in repository
- Branch-based deployment strategy
- Pull Request workflow for all changes
- Audit trail through Git history

### Branch Strategy

```
main (production)
  ↓
  • Manual approval required for merges
  • Blue-green deployment
  • Full testing suite must pass
  
develop (staging)
  ↓
  • Auto-deploy on push
  • Pre-production testing
  • Integration testing environment

feature/* (development)
  ↓
  • Local development
  • CI tests only (no deployment)
  • PR-based code review
```

### Key Files
- `.github/workflows/` - Pipeline definitions
- `tracehub/docker-compose.yml` - Service definitions
- `tracehub/.env.example` - Environment configuration templates
- `tracehub/scripts/` - Deployment automation

### Benefits
✅ Reproducible deployments  
✅ Complete audit trail  
✅ Easy rollback to any previous state  
✅ Infrastructure changes go through code review  

---

## 2. GitHub CLI (`gh` binary)

### Purpose
Command-line interface for GitHub operations, enabling automation and manual intervention.

### Installation
```bash
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Authenticate
gh auth login
```

### Common Operations

#### Workflow Management
```bash
# List workflows
gh workflow list

# Run a workflow manually
gh workflow run deploy-staging.yml

# View workflow runs
gh workflow view deploy-staging.yml

# Watch a workflow run in real-time
gh run watch
```

#### Secret Management
```bash
# Set a repository secret
gh secret set PRODUCTION_SSH_KEY < ~/.ssh/tracehub_prod.pem

# Set secrets from environment variables
gh secret set PRODUCTION_DB_PASSWORD -b "$DB_PASSWORD"

# List secrets
gh secret list

# Delete a secret
gh secret delete OLD_SECRET_NAME
```

#### Pull Request Operations
```bash
# Create PR from current branch
gh pr create --title "feat: add feature" --body "Description"

# List open PRs
gh pr list

# Check out a PR locally
gh pr checkout 123

# Merge PR
gh pr merge 123 --squash
```

#### Release Management
```bash
# Create a release
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes"

# List releases
gh release list

# View release details
gh release view v1.0.0
```

### Integration in Scripts
```bash
#!/bin/bash
# Example: Automated deployment script using gh

# Trigger staging deployment
gh workflow run deploy-staging.yml

# Wait for completion
sleep 60

# Check status
if gh run list --workflow=deploy-staging.yml --limit 1 --json conclusion --jq '.[0].conclusion' | grep -q "success"; then
  echo "Deployment successful!"
else
  echo "Deployment failed!"
  exit 1
fi
```

---

## 3. Hostinger MCP (VPS Management)

### What is MCP?
**Model Context Protocol (MCP)** - A protocol that enables AI assistants (like Claude) to interact with external systems through standardized interfaces.

### Hostinger MCP Server
Direct VPS management through Claude using Hostinger's API.

### Setup in Claude Desktop

**Location:** `~/.config/Claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "inputs": [
    {
      "id": "api_token",
      "type": "promptString",
      "description": "Enter your Hostinger API token (required)"
    }
  ],
  "servers": {
    "hostinger-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "hostinger-api-mcp@latest"
      ],
      "env": {
        "API_TOKEN": "${HOSTINGER_API_TOKEN}"
      }
    }
  }
}
```

### Capabilities

#### VPS Management
- Start/stop/restart VPS instances
- View server status and metrics
- Check resource usage (CPU, RAM, disk)

#### DNS Configuration
- List DNS zones and records
- Create/update/delete DNS records
- Configure subdomains (e.g., staging.tracehub.vibotaj.com)

#### SSL Management
- View SSL certificate status
- Install/renew SSL certificates
- Configure Let's Encrypt auto-renewal

#### Website Management
- List hosted websites
- View website details
- Manage website settings

### Example Usage in Claude

```
Human: "Check the status of our TraceHub VPS"
Claude: [Uses Hostinger MCP to query VPS status]```

### Security Note
⚠️ **Never commit Hostinger API token to repository!**  
Store in `.secrets/hostinger.env` (git-ignored)

### References
- Full Hostinger configuration: `docs/_archive/root-cleanup/HOSTINGER_CONFIG.md`
- Hostinger API documentation: https://developers.hostinger.com

---

## 4. GitHub Actions (CI/CD Pipeline)

### Architecture

GitHub Actions provides our complete CI/CD infrastructure with parallel testing, containerized builds, and automated deployments.

### Workflow Files

All workflows are located in `.github/workflows/`:

#### 1. `backend-ci.yml` - Backend Continuous Integration
**Triggers:** Push/PR to `main` or `develop` affecting backend code

**Jobs:**
- **Lint & Test**
  - Python 3.11 setup
  - Install dependencies
  - flake8 linting
  - black formatting check
  - mypy type checking
  - pytest with coverage
  - Upload coverage to Codecov

- **Security Scan**
  - safety check (dependency vulnerabilities)
  - bandit scan (code security issues)
  - Upload security reports

**Status:** Must pass before merge allowed

#### 2. `frontend-ci.yml` - Frontend Continuous Integration
**Triggers:** Push/PR to `main` or `develop` affecting frontend code

**Jobs:**
- Node.js 20 setup
- ESLint (strict mode)
- TypeScript type checking (no `any` types)
- Build validation
- npm audit for vulnerabilities

**Status:** Must pass before merge allowed

#### 3. `build-and-push.yml` - Docker Image Builder
**Triggers:** Push to `main` or `develop` branches

**Process:**
1. Build backend Docker image
2. Build frontend Docker image
3. Tag with branch name and git SHA
4. Scan images with Trivy (vulnerability scanner)
5. Push to GitHub Container Registry (GHCR)

**Artifacts:**
- `ghcr.io/{org}/{repo}/tracehub-backend:develop-{sha}`
- `ghcr.io/{org}/{repo}/tracehub-frontend:develop-{sha}`
- `ghcr.io/{org}/{repo}/tracehub-backend:main-{sha}`
- `ghcr.io/{org}/{repo}/tracehub-frontend:main-{sha}`

#### 4. `deploy-staging.yml` - Staging Deployment
**Triggers:** Push to `develop` branch (automatic)

**Process:**
1. Setup SSH to VPS
2. Add VPS to known hosts
3. Create deployment directory (`/home/tracehub/staging`)
4. Copy docker-compose and scripts
5. Create `.env.staging` from GitHub secrets
6. Login to GHCR
7. Pull latest Docker images
8. Backup database
9. Stop existing containers
10. Start new containers
11. Wait for health checks
12. Run database migrations
13. Execute smoke tests
14. Clean up old images

**Rollback:** Automatic on failure

**Notifications:** GitHub issue created on failure

#### 5. `deploy-production.yml` - Production Deployment
**Triggers:** Push to `main` branch (requires manual approval)

**Strategy:** Blue-Green Deployment

**Process:**
1. Setup SSH to VPS
2. Pull latest images
3. **Backup database** (critical!)
4. Deploy to "green" environment (new containers with different ports)
5. Health check green environment
6. Run migrations on green
7. Smoke tests on green
8. Switch nginx/traffic to green
9. Monitor stability (30 seconds)
10. Remove old "blue" deployment
11. External health checks

**Approval Required:** GitHub environment protection rule

**Rollback:** Manual or automatic on health check failure

#### 6. `database-migrations.yml` - Migration CI
**Triggers:** Changes to `tracehub/backend/alembic/` or `tracehub/backend/app/models/`

**Jobs:**
- Validate migrations are reversible
- Test migrations on fresh PostgreSQL database
- Check for model/migration drift
- Generate migration summary as PR comment

### Secrets Management in GitHub Actions

**Repository Secrets (Settings → Secrets → Actions):**

```bash
# Staging
STAGING_SSH_KEY         # SSH private key
STAGING_HOST           # VPS hostname
STAGING_USER           # SSH username
STAGING_DB_PASSWORD    # PostgreSQL password
STAGING_JWT_SECRET     # JWT signing key
VIZION_API_KEY         # Container tracking API
DEMO_PASSWORD          # Demo account password

# Production
PRODUCTION_SSH_KEY
PRODUCTION_HOST
PRODUCTION_USER
PRODUCTION_DB_PASSWORD
PRODUCTION_JWT_SECRET
# VIZION_API_KEY (shared)
# DEMO_PASSWORD (shared)
```

### Pipeline Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│                   Git Push (develop)                     │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│  Backend CI   │         │  Frontend CI  │
│  • Lint       │         │  • ESLint     │
│  • Test       │         │  • TypeScript │
│  • Security   │         │  • Build      │
└───────┬───────┘         └───────┬───────┘
        │                         │
        └────────────┬────────────┘
                     ▼
          ┌──────────────────┐
          │ Build & Push     │
          │ Docker Images    │
          │ → GHCR           │
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │ Deploy Staging   │
          │ (Automatic)      │
          │ • SSH to VPS     │
          │ • DB Backup      │
          │ • Pull Images    │
          │ • Migrations     │
          │ • Health Checks  │
          └────────┬─────────┘
                   │
                   ▼
          [Staging Environment]
```

### Benefits
✅ Parallel testing reduces CI time  
✅ Automated deployments reduce human error  
✅ Security scanning in every build  
✅ Audit trail through GitHub Actions logs  
✅ Easy rollback to any previous image  

---

## 5. Multi-Environment Strategy

### Philosophy
**Single VPS, Port-Isolated Environments**

Both staging and production run on the same Hostinger VPS to optimize costs during POC phase, while maintaining complete isolation through port separation and distinct Docker networks.

### Environment Configuration

| Environment | Backend | Frontend | Database | Domain | Auto-Deploy |
|-------------|---------|----------|----------|--------|-------------|
| **Production** | 8000 | 3000 | 5432 | https://tracehub.vibotaj.com | ❌ Manual |
| **Staging** | 8100 | 3100 | 5532 | https://staging.tracehub.vibotaj.com | ✅ Auto |

### Directory Structure on VPS

```
/home/tracehub/
├── production/
│   ├── docker-compose.yml          # Production service definitions
│   ├── .env.production             # Production environment variables
│   ├── uploads/                    # Document storage
│   ├── logs/                       # Application logs
│   └── backups/                    # Database backups
│       ├── backup_20260106_120000.sql
│       └── backup_20260105_120000.sql
├── staging/
│   ├── docker-compose.yml
│   ├── .env.staging
│   ├── uploads/
│   ├── logs/
│   └── backups/
├── shared/
│   └── ssl/                        # SSL certificates (Let's Encrypt)
│       ├── tracehub.vibotaj.com/
│       └── staging.tracehub.vibotaj.com/
└── scripts/
    ├── deploy.sh                   # Deployment automation
    ├── rollback.sh                 # Rollback automation
    └── backup.sh                   # Database backup script
```

### Docker Network Isolation

Each environment has its own Docker network:
- `tracehub-network-prod` (Production)
- `tracehub-network-staging` (Staging)

This ensures complete container isolation between environments.

### Environment Variables

#### Staging (`.env.staging`)
```env
ENVIRONMENT=staging
DB_USER=tracehub_staging
DB_PASSWORD=<secret>
DB_NAME=tracehub_staging
DB_HOST=db
DB_PORT=5432
INTERNAL_DB_PORT=5532  # External port mapping

JWT_SECRET=<secret>
CORS_ORIGINS=https://staging.tracehub.vibotaj.com

VIZION_API_KEY=<secret>
DEMO_PASSWORD=<secret>

BACKEND_PORT=8100
FRONTEND_PORT=3100

DOCKER_BACKEND_IMAGE=ghcr.io/.../tracehub-backend:develop-abc123
DOCKER_FRONTEND_IMAGE=ghcr.io/.../tracehub-frontend:develop-abc123
```

#### Production (`.env.production`)
```env
ENVIRONMENT=production
DB_USER=tracehub_prod
DB_PASSWORD=<secret>
DB_NAME=tracehub_prod
DB_HOST=db
DB_PORT=5432
INTERNAL_DB_PORT=5432  # External port mapping

JWT_SECRET=<secret>
CORS_ORIGINS=https://tracehub.vibotaj.com

VIZION_API_KEY=<secret>
DEMO_PASSWORD=<secret>

BACKEND_PORT=8000
FRONTEND_PORT=3000

DOCKER_BACKEND_IMAGE=ghcr.io/.../tracehub-backend:main-xyz789
DOCKER_FRONTEND_IMAGE=ghcr.io/.../tracehub-frontend:main-xyz789
```

### Nginx Configuration

Nginx reverse proxy routes traffic based on domain:

```nginx
# Staging
server {
    listen 80;
    server_name staging.tracehub.vibotaj.com;
    
    location / {
        proxy_pass http://localhost:3100;
    }
    
    location /api {
        proxy_pass http://localhost:8100;
    }
}

# Production
server {
    listen 80;
    server_name tracehub.vibotaj.com;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

### Benefits of This Strategy
✅ Cost-effective for POC phase  
✅ Complete environment isolation  
✅ Staging mirrors production configuration  
✅ Easy to migrate to separate VPS later  
✅ Shared SSL certificate management  

### Future Migration Path
When scaling to production, environments can be split:
- **Staging:** Keep on current VPS
- **Production:** Move to dedicated VPS or cloud (AWS/GCP)
- Same Docker configurations work on any host
- Update DNS and nginx configuration only

---

## 6. Continuous Integration & Deployment Flow

### Complete CI/CD Pipeline

```
Developer
    ↓
 Feature Branch (feature/*)
    ↓
 git push origin feature/*
    ↓
┌──────────────────────────┐
│   CI Tests Run           │
│   • Backend CI           │
│   • Frontend CI          │
│   • No deployment        │
└────────────┬─────────────┘
             ↓
      Create Pull Request
             ↓
      Code Review + Tests Pass
             ↓
      Merge to develop
             ↓
┌──────────────────────────┐
│   Build & Test           │
│   • Run all CI tests     │
│   • Build Docker images  │
│   • Tag with SHA         │
│   • Push to GHCR         │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│   Deploy to Staging      │
│   (Automatic)            │
│   • SSH to VPS           │
│   • Backup DB            │
│   • Pull images          │
│   • Run migrations       │
│   • Health checks        │
└────────────┬─────────────┘
             ↓
   Staging Testing & Validation
             ↓
      Merge develop → main
             ↓
┌──────────────────────────┐
│   Build Production       │
│   • Build Docker images  │
│   • Tag with SHA         │
│   • Push to GHCR         │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│   Manual Approval        │
│   • Review changes       │
│   • Check staging status │
│   • Approve in GitHub    │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│   Deploy to Production   │
│   (Blue-Green)           │
│   • Backup DB            │
│   • Deploy "green"       │
│   • Run migrations       │
│   • Health checks        │
│   • Switch traffic       │
│   • Remove "blue"        │
└────────────┬─────────────┘
             ↓
   Production Monitoring
```

### Deployment Timing

| Environment | Trigger | Timing | Approval |
|-------------|---------|--------|----------|
| Staging | Push to `develop` | Immediate (< 5 min) | None |
| Production | Push to `main` | After approval | Required |

### Health Check Requirements

All deployments must pass health checks:

#### Backend Health
```bash
GET /health
Response: {"status": "healthy", "database": "connected"}
```

#### Frontend Health
```bash
GET /
Response: 200 OK (React app loads)
```

#### Database Health
```bash
docker-compose exec db pg_isready
Response: accepting connections
```

### Rollback Triggers

Automatic rollback occurs if:
- Health checks fail after deployment
- Database migrations fail
- Smoke tests fail
- Container fails to start

Manual rollback available via:
```bash
./scripts/rollback.sh -e production -t deployment
```

---

## Summary: How It All Works Together

### Day-to-Day Development Flow

1. **Developer writes code** on feature branch
2. **Push to GitHub** triggers CI tests
3. **Create PR** → Code review
4. **Merge to develop** → Auto-deploy to staging
5. **Test on staging** → Validate changes
6. **Merge to main** → Wait for approval
7. **Approve** → Auto-deploy to production

### Tool Interactions

```
GitHub (Source Control)
    ↓
GitHub Actions (CI/CD Orchestration)
    ↓
GitHub CLI (Workflow Management)
    ↓
Docker Images → GHCR (Container Registry)
    ↓
SSH Deployment → Hostinger VPS
    ↓
Hostinger MCP ← Claude (Infrastructure Management)
```

### Key Principles

1. **GitOps** - All changes through Git
2. **Automation** - Minimize manual steps
3. **Testing** - Verify before deploy
4. **Isolation** - Separate environments
5. **Monitoring** - Health checks at every step
6. **Rollback** - Fast recovery from issues

---

## Quick Reference

### Common Tasks

| Task | Command/Action |
|------|----------------|
| Deploy to staging | Push to `develop` branch (automatic) |
| Deploy to production | Merge to `main`, approve in GitHub |
| Manual staging deploy | `gh workflow run deploy-staging.yml` |
| Check deployment status | GitHub → Actions → View workflow |
| View VPS status | Use Hostinger MCP in Claude |
| Rollback production | `ssh user@vps && cd production && ./scripts/rollback.sh` |
| Check logs | `ssh user@vps && cd production && docker-compose logs -f` |
| Add GitHub secret | `gh secret set SECRET_NAME -b "value"` |
| List workflows | `gh workflow list` |

### Emergency Procedures

**Production is down:**
1. Check GitHub Actions for failed deployment
2. SSH to VPS: `ssh user@tracehub.vibotaj.com`
3. Check container status: `cd production && docker-compose ps`
4. Check logs: `docker-compose logs -f backend`
5. Rollback if needed: `./scripts/rollback.sh -e production -t deployment`

**Database issues:**
1. Check database health: `docker-compose exec db pg_isready`
2. View recent backups: `ls -lh backups/`
3. Rollback if needed: `./scripts/rollback.sh -e production -t database`

**DNS/SSL issues:**
1. Use Hostinger MCP to check DNS records
2. Verify SSL certificates: `ls -lh shared/ssl/tracehub.vibotaj.com/`
3. Check nginx configuration: `nginx -t`

---

## Further Reading

- **DevOps Details:** [`tracehub/DEVOPS.md`](../tracehub/DEVOPS.md)
- **Deployment Procedures:** [`DEPLOYMENT.md`](DEPLOYMENT.md)
- **Architecture Overview:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Hostinger Configuration:** [`_archive/root-cleanup/HOSTINGER_CONFIG.md`](_archive/root-cleanup/HOSTINGER_CONFIG.md)
- **Infrastructure Docs:** [`infrastructure/`](infrastructure/)
  - SSL Configuration
  - DNS Configuration
  - Backup Strategy

---

**Last Updated:** January 6, 2026  
**Maintained by:** DevOps Team (Shola, Claude AI Agents)  
**Version:** 1.0.0
