# TraceHub DevOps & GitOps Implementation Plan

## Current State Assessment

| Area | Current | Issues |
|------|---------|--------|
| Deployment | Manual SSH → git pull → docker compose | No automation, error-prone |
| CI/CD | None | No automated testing or deployment |
| Environments | Production only | No staging for testing |
| Database | `Base.metadata.create_all()` on startup | No versioned migrations |
| Secrets | `.env` files | Not encrypted, no rotation |
| Monitoring | Basic health checks | No alerting, no APM |
| Rollback | Manual git revert | No automated rollback |

---

## Target Architecture

```
                    +------------------+
                    |   GitHub Repo    |
                    |   main/staging   |
                    +--------+---------+
                             |
              Push to branch |
                             v
                    +--------+---------+
                    | GitHub Actions   |
                    | CI Pipeline      |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
    +----v----+        +-----v-----+       +-----v-----+
    | Lint &  |        | Run Tests |       |  Build    |
    | Type    |        | (pytest)  |       |  Docker   |
    | Check   |        |           |       |  Images   |
    +---------+        +-----------+       +-----+-----+
                                                 |
                             +-------------------+
                             |
              +-------- main branch --------+
              |                             |
    +---------v----------+       +----------v---------+
    | Deploy to Staging  |       | (Manual Approve)   |
    | tracehub-stg.      |       | Deploy to Prod     |
    | vibotaj.com        |       | tracehub.vibotaj.  |
    +--------------------+       | com                |
                                 +--------------------+
```

---

## Phase 1: GitHub Actions CI/CD (Sprint 6)

### Workflow Files

#### `.github/workflows/ci.yml` - Continuous Integration

```yaml
name: CI

on:
  push:
    branches: [main, staging, develop]
  pull_request:
    branches: [main, staging]

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE: ghcr.io/${{ github.repository }}/tracehub-backend
  FRONTEND_IMAGE: ghcr.io/${{ github.repository }}/tracehub-frontend

jobs:
  # ============================================
  # Backend Jobs
  # ============================================
  backend-lint:
    name: Backend Lint & Type Check
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: tracehub/backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install ruff mypy
          pip install -r requirements.txt

      - name: Run Ruff (linter)
        run: ruff check app/

      - name: Run MyPy (type check)
        run: mypy app/ --ignore-missing-imports

  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: tracehub/backend
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: tracehub_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt pytest pytest-cov pytest-asyncio httpx

      - name: Run tests with coverage
        run: |
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=term
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/tracehub_test
          JWT_SECRET: test-secret-key
          DEBUG: true

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: coverage.xml

  # ============================================
  # Frontend Jobs
  # ============================================
  frontend-lint:
    name: Frontend Lint & Type Check
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: tracehub/frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: tracehub/frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

      - name: Run TypeScript check
        run: npm run type-check

  frontend-build:
    name: Frontend Build
    runs-on: ubuntu-latest
    needs: frontend-lint
    defaults:
      run:
        working-directory: tracehub/frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: tracehub/frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: tracehub/frontend/dist

  # ============================================
  # Docker Build Jobs
  # ============================================
  build-images:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [backend-lint, backend-test, frontend-build]
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (backend)
        id: meta-backend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.BACKEND_IMAGE }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: tracehub/backend
          push: true
          tags: ${{ steps.meta-backend.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Extract metadata (frontend)
        id: meta-frontend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.FRONTEND_IMAGE }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: tracehub/frontend
          push: true
          tags: ${{ steps.meta-frontend.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

#### `.github/workflows/deploy-staging.yml` - Staging Deployment

```yaml
name: Deploy to Staging

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/tracehub-app/tracehub

            # Pull latest code
            git fetch origin main
            git reset --hard origin/main

            # Pull latest images
            docker compose pull

            # Run database migrations
            docker compose exec -T backend alembic upgrade head

            # Restart services with zero-downtime
            docker compose up -d --no-deps --build backend
            docker compose up -d --no-deps --build frontend

            # Health check
            sleep 10
            curl -f http://localhost:8000/health || exit 1

            echo "Staging deployment complete!"
```

#### `.github/workflows/deploy-production.yml` - Production Deployment

```yaml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version/commit to deploy'
        required: true
        default: 'main'

jobs:
  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.version }}

      - name: Create deployment record
        run: |
          echo "Deploying version: ${{ github.event.inputs.version }}"
          echo "Deployed by: ${{ github.actor }}"
          echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.PRODUCTION_SSH_KEY }}
          script: |
            cd /opt/tracehub-app/tracehub

            # Backup current version
            BACKUP_TAG=$(date +%Y%m%d_%H%M%S)
            docker tag tracehub-backend:latest tracehub-backend:backup_${BACKUP_TAG} || true
            docker tag tracehub-frontend:latest tracehub-frontend:backup_${BACKUP_TAG} || true

            # Pull specific version
            git fetch origin
            git checkout ${{ github.event.inputs.version }}

            # Run database migrations
            docker compose exec -T backend alembic upgrade head

            # Rolling restart (backend first)
            docker compose up -d --no-deps --build backend
            sleep 15
            curl -f http://localhost:8000/health || (docker compose logs backend && exit 1)

            # Then frontend
            docker compose up -d --no-deps --build frontend
            sleep 10
            curl -f http://localhost/health || (docker compose logs frontend && exit 1)

            echo "Production deployment complete!"

      - name: Notify on success
        if: success()
        run: echo "Deployment successful!"

      - name: Notify on failure
        if: failure()
        run: echo "Deployment failed! Check logs."
```

---

## Phase 2: Database Migrations with Alembic (Sprint 6)

### Setup Commands

```bash
cd tracehub/backend

# Initialize Alembic
alembic init alembic

# Configure alembic.ini
# Set: sqlalchemy.url = %(DATABASE_URL)s

# Edit alembic/env.py to import models
```

### `alembic/env.py` Configuration

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import *  # Import all models

config = context.config

# Override sqlalchemy.url from environment
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Migration Workflow

```bash
# Generate new migration after model changes
alembic revision --autogenerate -m "Add notification preferences"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

---

## Phase 3: Environment Management

### Environment Configuration

| Environment | URL | Branch | Auto-Deploy |
|-------------|-----|--------|-------------|
| Development | localhost:8000 | Any | No |
| Staging | tracehub-stg.vibotaj.com | main | Yes |
| Production | tracehub.vibotaj.com | main (manual) | No |

### GitHub Environments Setup

1. Go to Repository → Settings → Environments
2. Create `staging` environment:
   - Add secrets: `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
   - No protection rules (auto-deploy)

3. Create `production` environment:
   - Add secrets: `PRODUCTION_HOST`, `PRODUCTION_USER`, `PRODUCTION_SSH_KEY`
   - Enable protection rules:
     - Required reviewers: 1
     - Wait timer: 0 minutes

### Secrets Required

```
# GitHub Repository Secrets

# Staging
STAGING_HOST=<staging-ip>
STAGING_USER=root
STAGING_SSH_KEY=<private-key>

# Production
PRODUCTION_HOST=82.198.225.150
PRODUCTION_USER=root
PRODUCTION_SSH_KEY=<private-key>

# External Services
VIZION_API_KEY=<key>
SENDGRID_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
SENTRY_DSN=<dsn>
```

---

## Phase 4: Rollback Procedures

### Automatic Rollback (in deploy script)

```bash
#!/bin/bash
# deploy-with-rollback.sh

set -e

BACKUP_TAG=$(date +%Y%m%d_%H%M%S)

# Backup current images
docker tag tracehub-backend:latest tracehub-backend:backup_${BACKUP_TAG}
docker tag tracehub-frontend:latest tracehub-frontend:backup_${BACKUP_TAG}

# Deploy new version
docker compose up -d --build

# Health check with timeout
HEALTH_CHECK_ATTEMPTS=5
for i in $(seq 1 $HEALTH_CHECK_ATTEMPTS); do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "Health check passed!"
        exit 0
    fi
    echo "Health check attempt $i failed, waiting..."
    sleep 10
done

# Rollback on failure
echo "Health checks failed! Rolling back..."
docker tag tracehub-backend:backup_${BACKUP_TAG} tracehub-backend:latest
docker tag tracehub-frontend:backup_${BACKUP_TAG} tracehub-frontend:latest
docker compose up -d --no-build

# Notify
echo "ROLLBACK COMPLETE - deployment failed"
exit 1
```

### Manual Rollback Commands

```bash
# List recent backups
docker images | grep backup

# Rollback to specific backup
docker tag tracehub-backend:backup_20260103_120000 tracehub-backend:latest
docker compose up -d --no-build backend

# Rollback database migration
docker compose exec backend alembic downgrade -1

# Rollback git to previous commit
git log --oneline -10
git checkout <previous-commit>
docker compose up -d --build
```

---

## Phase 5: Monitoring & Alerting (Sprint 7)

### Sentry Integration

```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=settings.environment,
    )
```

### Health Check Endpoints

```python
# Already exists, enhance with:
@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db)):
    """Check if app is ready to receive traffic"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(503, detail=f"Not ready: {e}")

@router.get("/health/live")
async def liveness():
    """Check if app is alive"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
```

### Uptime Monitoring

- Use Uptime Robot (free tier) or Better Uptime
- Monitor endpoints:
  - `https://tracehub.vibotaj.com/health`
  - `https://tracehub.vibotaj.com/api/health/ready`
- Alert via email/Slack on downtime

---

## Implementation Sprint Plan

### Sprint 6 DevOps Tasks (8 hours)

| Task | Hours | Description |
|------|-------|-------------|
| D6.1 | 2 | Create GitHub Actions CI workflow |
| D6.2 | 1 | Create staging deployment workflow |
| D6.3 | 1 | Create production deployment workflow |
| D6.4 | 2 | Set up Alembic migrations |
| D6.5 | 1 | Configure GitHub environments & secrets |
| D6.6 | 1 | Create rollback scripts |

### Sprint 7 DevOps Tasks (4 hours)

| Task | Hours | Description |
|------|-------|-------------|
| D7.1 | 1 | Integrate Sentry error tracking |
| D7.2 | 1 | Set up uptime monitoring |
| D7.3 | 1 | Add deployment notifications (Slack) |
| D7.4 | 1 | Document runbook for operations |

---

## Cost Estimate

| Service | Monthly Cost | Purpose |
|---------|--------------|---------|
| GitHub Actions | $0 | 2000 free minutes/month |
| Uptime Robot | $0 | Free tier (50 monitors) |
| Sentry | $0 | Free tier (5K errors/month) |
| **Total** | **$0** | Using free tiers |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Deployment frequency | 2+ per sprint |
| Lead time for changes | < 1 hour |
| Change failure rate | < 10% |
| Mean time to recovery | < 15 minutes |
| Test coverage | > 70% |
