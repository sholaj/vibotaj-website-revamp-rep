# TraceHub DevOps Documentation

## Table of Contents
1. [CI/CD Architecture](#cicd-architecture)
2. [Environment Strategy](#environment-strategy)
3. [GitHub Actions Workflows](#github-actions-workflows)
4. [Database Migrations](#database-migrations)
5. [Deployment Procedures](#deployment-procedures)
6. [Rollback Procedures](#rollback-procedures)
7. [Secrets Management](#secrets-management)
8. [Monitoring & Health Checks](#monitoring--health-checks)
9. [Troubleshooting](#troubleshooting)

---

## CI/CD Architecture

### Overview

TraceHub uses a GitOps-based CI/CD pipeline with GitHub Actions for automated testing, building, and deployment.

```
┌─────────────┐
│   Develop   │──────► Staging (Auto-deploy)
│   Branch    │
└─────────────┘

┌─────────────┐
│    Main     │──────► Production (Manual approval)
│   Branch    │
└─────────────┘

┌─────────────┐
│Pull Request │──────► Tests only (no deploy)
└─────────────┘
```

### Pipeline Stages

1. **Build & Test**: Parallel testing of backend, frontend, and database migrations
2. **Docker Build**: Build and push images to GitHub Container Registry (GHCR)
3. **Deploy**: Environment-specific deployment with health checks
4. **Monitor**: Post-deployment validation and alerting

---

## Environment Strategy

### Single VPS Multi-Environment Setup

Both staging and production run on the same Hostinger VPS with port isolation:

```
/home/tracehub/
├── production/
│   ├── docker-compose.yml
│   ├── .env.production
│   ├── uploads/
│   ├── logs/
│   └── backups/
├── staging/
│   ├── docker-compose.yml
│   ├── .env.staging
│   ├── uploads/
│   ├── logs/
│   └── backups/
└── shared/
    └── ssl/
```

### Port Allocation

| Environment | Backend | Frontend | Database |
|-------------|---------|----------|----------|
| Production  | 8000    | 3000     | 5432     |
| Staging     | 8100    | 3100     | 5532     |

### Domain Mapping

- **Production**: https://tracehub.vibotaj.com
- **Staging**: https://staging.tracehub.vibotaj.com

---

## GitHub Actions Workflows

### 1. Backend CI (`backend-ci.yml`)

**Triggers**: Push to `main`/`develop` or PRs affecting backend code

**Jobs**:
- Linting (flake8, black)
- Type checking (mypy)
- Unit tests with coverage
- Security scanning (safety, bandit)

**Status**: Must pass before merge

### 2. Frontend CI (`frontend-ci.yml`)

**Triggers**: Push to `main`/`develop` or PRs affecting frontend code

**Jobs**:
- ESLint
- TypeScript type checking
- Build validation
- npm audit

**Status**: Must pass before merge

### 3. Build and Push (`build-and-push.yml`)

**Triggers**: Push to `main` or `develop` branches

**Jobs**:
- Build Docker images for backend and frontend
- Tag images with branch name and git SHA
- Push to GitHub Container Registry
- Vulnerability scanning with Trivy

**Artifacts**:
- `ghcr.io/{repo}/tracehub-backend:develop-{sha}`
- `ghcr.io/{repo}/tracehub-frontend:develop-{sha}`
- `ghcr.io/{repo}/tracehub-backend:main-{sha}`
- `ghcr.io/{repo}/tracehub-frontend:main-{sha}`

### 4. Deploy to Staging (`deploy-staging.yml`)

**Triggers**: Push to `develop` branch (automatic)

**Process**:
1. Setup SSH connection to VPS
2. Copy deployment files
3. Create `.env.staging` from secrets
4. Pull latest Docker images
5. Backup database
6. Deploy with rolling update
7. Run database migrations
8. Execute smoke tests
9. Clean up old images

**Rollback**: Automatic on failure

### 5. Deploy to Production (`deploy-production.yml`)

**Triggers**: Push to `main` branch (requires manual approval)

**Process** (Blue-Green Deployment):
1. Setup SSH connection
2. Pull latest images
3. **Backup database** (critical!)
4. Deploy to "green" environment
5. Wait for green to be healthy
6. Run migrations on green
7. Execute smoke tests on green
8. Switch traffic to green
9. Monitor stability (30s)
10. Remove old "blue" deployment
11. External health checks

**Approval**: Required in GitHub environment settings

### 6. Database Migrations CI (`database-migrations.yml`)

**Triggers**: Changes to `alembic/` or `app/models/` directories

**Jobs**:
- Validate migrations are reversible
- Test migrations on fresh database
- Check for model/migration drift
- Generate migration summary for PRs

---

## Database Migrations

### Using Alembic

TraceHub uses Alembic for database schema versioning.

#### Generate New Migration

```bash
# After modifying models in app/models/
cd tracehub/backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in alembic/versions/
# Edit if necessary to add custom logic or data migrations
```

#### Apply Migrations

```bash
# Locally
alembic upgrade head

# In Docker
docker-compose exec backend alembic upgrade head

# In production (via deployment script)
ssh user@vps
cd /home/tracehub/production
docker-compose exec -T backend alembic upgrade head
```

#### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

#### Migration Best Practices

1. **Always test migrations locally** before committing
2. **Write reversible migrations** (proper downgrade functions)
3. **Backup database** before running migrations in production
4. **Test on staging first** before production
5. **Use transactions** for data migrations
6. **Avoid breaking changes** when possible (use multi-step migrations)

#### Migration File Naming

Alembic auto-generates filenames like:
```
20260103_1430_a1b2c3d4_add_user_roles.py
```

Format: `YYYYMMDD_HHMM_{revision}_{description}.py`

---

## Deployment Procedures

### Deploy to Staging

**Automatic** when you push to `develop`:

```bash
git checkout develop
git pull origin develop
# Make changes
git add .
git commit -m "feat: add feature X"
git push origin develop
# GitHub Actions automatically deploys to staging
```

**Manual** deployment:

```bash
# Trigger workflow manually
gh workflow run deploy-staging.yml
```

### Deploy to Production

**Requires approval** when pushing to `main`:

```bash
# Merge develop into main
git checkout main
git pull origin main
git merge develop
git push origin main

# GitHub Actions will:
# 1. Run all tests
# 2. Build Docker images
# 3. Wait for manual approval
# 4. Deploy with blue-green strategy
```

**Approve deployment**:
1. Go to GitHub repository → Actions
2. Find the "Deploy to Production" workflow run
3. Click "Review deployments"
4. Approve the production environment

### Manual VPS Deployment

If GitHub Actions is unavailable:

```bash
# SSH into VPS
ssh user@tracehub.vibotaj.com

# Navigate to environment
cd /home/tracehub/production  # or staging

# Pull latest code
git pull origin main  # or develop

# Pull images (if using pre-built images)
docker-compose pull

# Deploy
./scripts/deploy.sh -e production

# Or use manual steps
docker-compose down
docker-compose build
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

---

## Rollback Procedures

### Automatic Rollback

Deployments automatically rollback if:
- Health checks fail
- Database migrations fail
- Smoke tests fail

### Manual Rollback

#### 1. Rollback Deployment (Blue-Green)

```bash
cd /home/tracehub/production
./scripts/rollback.sh -e production -t deployment
```

This switches back to the previous "blue" deployment if it still exists.

#### 2. Rollback Database

```bash
# Rollback to latest backup
./scripts/rollback.sh -e production -t database

# Rollback to specific backup
./scripts/rollback.sh -e production -t database -b backups/backup_20260103_120000.sql
```

#### 3. Manual Rollback Steps

```bash
# 1. List available backups
ls -lh backups/

# 2. Stop backend to prevent DB connections
docker-compose stop backend

# 3. Restore database
docker-compose exec -T db psql -U tracehub tracehub < backups/backup_20260103_120000.sql

# 4. Restart backend
docker-compose start backend

# 5. Verify health
curl http://localhost:8000/health
```

#### 4. Rollback Specific Migration

```bash
# SSH to VPS
ssh user@tracehub.vibotaj.com
cd /home/tracehub/production

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# Restart backend
docker-compose restart backend
```

### Rollback Checklist

- [ ] Identify the issue (deployment or database)
- [ ] Check available backups: `ls -lh backups/`
- [ ] Notify team of rollback in progress
- [ ] Execute rollback procedure
- [ ] Verify health checks pass
- [ ] Check application functionality
- [ ] Monitor logs for errors
- [ ] Document incident and root cause

---

## Secrets Management

### GitHub Secrets

Configure these secrets in GitHub repository settings:

#### Staging Environment

```
STAGING_SSH_KEY         - Private SSH key for VPS access
STAGING_HOST           - VPS hostname (e.g., tracehub.vibotaj.com)
STAGING_USER           - SSH username
STAGING_DB_PASSWORD    - Database password
STAGING_JWT_SECRET     - JWT signing secret
VIZION_API_KEY         - Vizion API key (shared)
DEMO_PASSWORD          - Demo user password
```

#### Production Environment

```
PRODUCTION_SSH_KEY      - Private SSH key for VPS access
PRODUCTION_HOST        - VPS hostname
PRODUCTION_USER        - SSH username
PRODUCTION_DB_PASSWORD - Database password
PRODUCTION_JWT_SECRET  - JWT signing secret
VIZION_API_KEY         - Vizion API key (shared)
DEMO_PASSWORD          - Demo user password
```

### Setting Up GitHub Secrets

```bash
# Using GitHub CLI
gh secret set PRODUCTION_SSH_KEY < ~/.ssh/tracehub_production_rsa
gh secret set PRODUCTION_HOST -b "tracehub.vibotaj.com"
gh secret set PRODUCTION_DB_PASSWORD -b "your-secure-password"

# Or via GitHub web interface:
# Repository → Settings → Secrets and variables → Actions → New repository secret
```

### Environment Files on VPS

Never commit `.env.production` or `.env.staging` files!

**Creating on VPS**:

```bash
# Copy example
cp .env.production.example .env.production

# Edit with secure values
nano .env.production

# Set restrictive permissions
chmod 600 .env.production
```

---

## Monitoring & Health Checks

### Health Endpoints

#### Backend Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "database": "connected"}
```

#### Frontend Health Check
```bash
curl http://localhost/health
# Response: 200 OK
```

### Docker Health Checks

All services have built-in health checks:

```bash
# Check service health
docker-compose ps

# Example output:
# NAME                  STATUS
# tracehub-backend-prod healthy
# tracehub-db-prod      healthy
# tracehub-frontend-prod healthy
```

### Monitoring Commands

```bash
# View all logs
docker-compose logs -f

# Backend logs only
docker-compose logs -f backend

# Database logs
docker-compose logs -f db

# Check resource usage
docker stats

# Check disk space
df -h

# Check database size
docker-compose exec db psql -U tracehub -c "SELECT pg_size_pretty(pg_database_size('tracehub'));"
```

### Automated Monitoring (Future)

Planned integrations:
- [ ] Prometheus + Grafana for metrics
- [ ] Sentry for error tracking
- [ ] Uptime monitoring (UptimeRobot/StatusCake)
- [ ] Log aggregation (ELK stack or Loki)

---

## Troubleshooting

### Common Issues

#### 1. Deployment Fails with "Unhealthy Services"

```bash
# Check service status
docker-compose ps

# Check logs for specific service
docker-compose logs backend

# Check health endpoint
curl http://localhost:8000/health

# Common causes:
# - Database connection issues
# - Missing environment variables
# - Port conflicts
```

**Solution**:
```bash
# Check database connectivity
docker-compose exec backend ping db

# Verify environment variables
docker-compose exec backend env | grep DATABASE_URL

# Restart services
docker-compose restart
```

#### 2. Database Migration Fails

```bash
# Check current migration status
docker-compose exec backend alembic current

# Check migration history
docker-compose exec backend alembic history

# Manually run migration with verbose output
docker-compose exec backend alembic upgrade head --verbose
```

**Solution**:
```bash
# If migration is stuck, rollback and retry
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head

# If corrupted, restore from backup
./scripts/rollback.sh -e production -t database
```

#### 3. Container Won't Start

```bash
# Check container logs
docker logs tracehub-backend-prod

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Check Docker daemon
sudo systemctl status docker
```

**Solution**:
```bash
# Free up port
docker-compose down
sudo kill -9 $(sudo lsof -t -i:8000)

# Restart Docker daemon
sudo systemctl restart docker

# Rebuild container
docker-compose build --no-cache backend
docker-compose up -d
```

#### 4. Out of Disk Space

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Find large directories
du -sh /home/tracehub/* | sort -hr
```

**Solution**:
```bash
# Clean Docker resources
docker system prune -a --volumes
docker volume prune

# Remove old backups (keep last 10)
cd /home/tracehub/production/backups
ls -t backup_*.sql | tail -n +11 | xargs rm

# Remove old logs
cd /home/tracehub/production/logs
find . -name "*.log" -mtime +30 -delete
```

#### 5. SSH Connection Issues

```bash
# Test SSH connection
ssh -vvv user@tracehub.vibotaj.com

# Check SSH key
ssh-keygen -lf ~/.ssh/tracehub_production_rsa

# Verify key on server
cat ~/.ssh/authorized_keys
```

**Solution**:
```bash
# Regenerate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/tracehub_production_rsa

# Copy to server
ssh-copy-id -i ~/.ssh/tracehub_production_rsa user@tracehub.vibotaj.com

# Update GitHub secret
gh secret set PRODUCTION_SSH_KEY < ~/.ssh/tracehub_production_rsa
```

### Emergency Procedures

#### Complete System Down

1. **Check VPS status** on Hostinger control panel
2. **SSH to VPS** and check Docker daemon: `systemctl status docker`
3. **Restart Docker**: `sudo systemctl restart docker`
4. **Restart services**: `cd /home/tracehub/production && docker-compose up -d`
5. **Check health**: `curl http://localhost:8000/health`

#### Database Corruption

1. **Stop backend** immediately: `docker-compose stop backend`
2. **Create emergency backup**: `docker-compose exec db pg_dump -U tracehub tracehub > emergency_backup.sql`
3. **Restore from latest good backup**: `./scripts/rollback.sh -t database`
4. **Verify data integrity**: Connect to DB and check critical tables
5. **Restart services**: `docker-compose up -d`

#### Security Incident

1. **Immediately rotate all secrets**:
   ```bash
   # Generate new secrets
   NEW_JWT_SECRET=$(openssl rand -hex 32)
   NEW_DB_PASSWORD=$(openssl rand -base64 32)

   # Update .env files
   # Update GitHub secrets
   # Restart services
   ```

2. **Review access logs**:
   ```bash
   docker-compose logs | grep -i "auth\|login\|error"
   ```

3. **Block suspicious IPs** in firewall
4. **Notify team** and security lead
5. **Conduct post-mortem** and update security policies

---

## Performance Optimization

### Docker Image Size

```bash
# Check image sizes
docker images | grep tracehub

# Optimize Dockerfile with multi-stage builds (already implemented)
# Use .dockerignore to exclude unnecessary files
```

### Database Performance

```bash
# Monitor query performance
docker-compose exec db psql -U tracehub -c "SELECT * FROM pg_stat_activity;"

# Analyze slow queries
docker-compose exec db psql -U tracehub -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Vacuum database
docker-compose exec db psql -U tracehub -c "VACUUM ANALYZE;"
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Maintenance Tasks

### Weekly

- [ ] Check disk space: `df -h`
- [ ] Review logs for errors: `docker-compose logs --since 7d | grep -i error`
- [ ] Verify backups exist: `ls -lh backups/`

### Monthly

- [ ] Update dependencies (security patches)
- [ ] Review and clean old backups
- [ ] Performance review (response times, error rates)
- [ ] Security audit (`npm audit`, `safety check`)

### Quarterly

- [ ] Review and update documentation
- [ ] Disaster recovery drill (test rollback procedures)
- [ ] Infrastructure review (resource utilization)
- [ ] Cost optimization review

---

## Contact & Escalation

### DevOps Team
- **Primary**: [Your DevOps Lead]
- **Secondary**: [Backup Contact]
- **Escalation**: [CTO/Technical Lead]

### On-Call Procedures
1. Check #alerts channel
2. Review GitHub Actions logs
3. SSH to VPS and investigate
4. Execute rollback if necessary
5. Document incident
6. Post-mortem within 48 hours

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FastAPI Deployment Best Practices](https://fastapi.tiangolo.com/deployment/)

---

**Last Updated**: 2026-01-03
**Version**: 1.0
**Maintained by**: TraceHub DevOps Team
