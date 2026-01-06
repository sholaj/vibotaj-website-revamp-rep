# TraceHub Deployment Quick Reference

> **One-page reference for common deployment operations**

## Quick Commands

### Local Development
```bash
cd tracehub
make dev              # Start local environment
make dev-logs         # View logs
make dev-down         # Stop local environment
make health           # Check service health
```

### Testing
```bash
make test             # Run backend tests
make test-frontend    # Run frontend tests
make test-coverage    # Run with coverage report
```

### Database Operations
```bash
# Migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                               # Apply migrations
alembic downgrade -1                               # Rollback one step
alembic current                                    # Show current revision
alembic history                                    # Show migration history

# Backup & Restore
make db-backup                                     # Create backup
make db-restore FILE=backup.sql                    # Restore from backup
```

### Deployment

#### Deploy to Staging (Automatic)
```bash
git checkout develop
git pull origin develop
# Make changes
git add .
git commit -m "feat: description"
git push origin develop
# GitHub Actions automatically deploys to staging
```

#### Deploy to Production (Manual Approval)
```bash
git checkout main
git pull origin main
git merge develop
git push origin main
# Go to GitHub → Actions → Approve deployment
```

#### Manual VPS Deployment
```bash
ssh user@tracehub.vibotaj.com
cd /home/tracehub/production
git pull origin main
./scripts/deploy.sh -e production
```

### Rollback

#### Rollback Deployment
```bash
ssh user@tracehub.vibotaj.com
cd /home/tracehub/production
./scripts/rollback.sh -e production -t deployment
```

#### Rollback Database
```bash
./scripts/rollback.sh -e production -t database
# Or specific backup:
./scripts/rollback.sh -e production -t database -b backups/backup_20260103.sql
```

### Monitoring

#### Health Checks
```bash
# Backend
curl https://tracehub.vibotaj.com/api/health

# Frontend
curl https://tracehub.vibotaj.com/health

# Docker health
docker-compose ps
```

#### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 backend
```

#### System Status
```bash
docker stats                    # Resource usage
df -h                          # Disk space
docker system df               # Docker disk usage
netstat -tlnp | grep :8000    # Port status
```

### Troubleshooting

#### Service Won't Start
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

#### Database Issues
```bash
# Check database connection
docker-compose exec backend ping db

# Check database status
docker-compose exec db pg_isready -U tracehub

# Access database
docker-compose exec db psql -U tracehub tracehub

# Check database size
docker-compose exec db psql -U tracehub -c "SELECT pg_size_pretty(pg_database_size('tracehub'));"
```

#### Out of Disk Space
```bash
# Clean Docker
docker system prune -a --volumes

# Clean old backups (keep last 10)
cd /home/tracehub/production/backups
ls -t backup_*.sql | tail -n +11 | xargs rm

# Clean logs older than 30 days
find /home/tracehub/production/logs -name "*.log" -mtime +30 -delete
```

#### Reset Everything (DANGER!)
```bash
docker-compose down -v
docker system prune -a --volumes
# Restore from backup!
```

## Environment URLs

| Environment | URL | Backend Port | Frontend Port | DB Port |
|-------------|-----|--------------|---------------|---------|
| Production  | https://tracehub.vibotaj.com | 8000 | 3000 | 5432 |
| Staging     | https://staging.tracehub.vibotaj.com | 8100 | 3100 | 5532 |
| Local       | http://localhost | 8000 | 80 | 5432 |

## GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-ci.yml` | PR/Push to main/develop | Lint, test backend |
| `frontend-ci.yml` | PR/Push to main/develop | Lint, test frontend |
| `build-and-push.yml` | Push to main/develop | Build Docker images |
| `deploy-staging.yml` | Push to develop | Deploy to staging |
| `deploy-production.yml` | Push to main | Deploy to production |
| `database-migrations.yml` | Changes to migrations | Validate migrations |

## Important File Locations

### On VPS
```
/home/tracehub/production/
├── docker-compose.yml          # Production compose file
├── .env.production             # Production secrets
├── uploads/                    # User uploads
├── logs/                       # Application logs
├── backups/                    # Database backups
└── scripts/                    # Deployment scripts
```

### In Repository
```
tracehub/
├── .github/workflows/          # CI/CD workflows
├── backend/
│   ├── alembic/               # Database migrations
│   ├── app/                   # Application code
│   └── Dockerfile             # Backend Docker image
├── frontend/
│   ├── src/                   # Frontend code
│   └── Dockerfile             # Frontend Docker image
├── docker-compose.yml         # Development compose
├── docker-compose.prod.yml    # Production compose
├── docker-compose.staging.yml # Staging compose
└── scripts/                   # Deployment scripts
```

## GitHub Secrets (Admin Only)

### Required Secrets
```
STAGING_SSH_KEY              # SSH key for staging
STAGING_HOST                 # VPS hostname
STAGING_USER                 # SSH username
STAGING_DB_PASSWORD          # Staging database password
STAGING_JWT_SECRET           # Staging JWT secret
PRODUCTION_SSH_KEY           # SSH key for production
PRODUCTION_HOST              # VPS hostname
PRODUCTION_USER              # SSH username
PRODUCTION_DB_PASSWORD       # Production database password
PRODUCTION_JWT_SECRET        # Production JWT secret
VIZION_API_KEY              # Vizion API key (shared)
DEMO_PASSWORD               # Demo user password
```

### Setting Secrets
```bash
# Using GitHub CLI
gh secret set SECRET_NAME -b "value"

# Or via web UI:
# Repository → Settings → Secrets and variables → Actions
```

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| DevOps Lead | [Name] | [Email/Phone] |
| Backend Lead | [Name] | [Email/Phone] |
| CTO | [Name] | [Email/Phone] |
| Hostinger Support | - | support@hostinger.com |

## Emergency Procedures

### System Down
1. Check GitHub Actions for failed deployments
2. SSH to VPS: `ssh user@tracehub.vibotaj.com`
3. Check Docker: `docker-compose ps`
4. View logs: `docker-compose logs -f`
5. Restart if needed: `docker-compose restart`
6. If still down: `./scripts/rollback.sh -e production -t deployment`

### Database Corruption
1. Stop backend: `docker-compose stop backend`
2. Create emergency backup: `docker-compose exec db pg_dump -U tracehub tracehub > emergency.sql`
3. Restore from backup: `./scripts/rollback.sh -e production -t database`
4. Restart: `docker-compose up -d`

### Security Incident
1. Rotate all secrets immediately
2. Review access logs: `docker-compose logs | grep -i "auth\|error"`
3. Block suspicious IPs in firewall
4. Notify security team
5. Conduct post-mortem

## Performance Targets

| Metric | Target | Command to Check |
|--------|--------|------------------|
| API Response (p95) | <200ms | Check logs/monitoring |
| Database Query (p95) | <100ms | Check pg_stat_statements |
| Deployment Time | <5min | Check GitHub Actions |
| Uptime | >99.5% | Check monitoring |
| Disk Usage | <80% | `df -h` |

## Common Error Solutions

### "Port already in use"
```bash
sudo lsof -t -i:8000 | xargs kill -9
docker-compose down
docker-compose up -d
```

### "Database connection refused"
```bash
docker-compose restart db
docker-compose logs db
# Check DATABASE_URL in .env
```

### "Migration failed"
```bash
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
# If still fails, rollback database
```

### "Out of memory"
```bash
docker stats  # Check which container
docker-compose restart <service>
# Add memory limits to docker-compose.yml
```

## Maintenance Schedule

### Daily (Automated)
- Database backups (2 AM)
- Log rotation
- Health checks

### Weekly (Manual)
- Review logs for errors
- Check disk space
- Review security alerts
- Update dependencies (if needed)

### Monthly
- Database vacuum and analyze
- Review and clean old backups
- Performance review
- Security audit

## Useful Docker Commands

```bash
# Container management
docker-compose up -d              # Start containers
docker-compose down               # Stop containers
docker-compose restart <service>  # Restart service
docker-compose ps                 # Show status
docker-compose logs -f <service>  # Follow logs

# Image management
docker images                     # List images
docker pull <image>              # Pull image
docker rmi <image>               # Remove image
docker image prune -a            # Remove unused images

# Volume management
docker volume ls                  # List volumes
docker volume prune              # Remove unused volumes

# System cleanup
docker system df                  # Show disk usage
docker system prune              # Clean up all unused
docker system prune -a --volumes # Aggressive cleanup
```

## Quick Health Check Script

```bash
#!/bin/bash
# Save as: health-check.sh

echo "=== TraceHub Health Check ==="
echo ""

# Backend
echo -n "Backend: "
curl -sf https://tracehub.vibotaj.com/api/health > /dev/null && echo "✓ OK" || echo "✗ FAIL"

# Frontend
echo -n "Frontend: "
curl -sf https://tracehub.vibotaj.com/ > /dev/null && echo "✓ OK" || echo "✗ FAIL"

# Database
echo -n "Database: "
docker-compose exec db pg_isready -U tracehub > /dev/null 2>&1 && echo "✓ OK" || echo "✗ FAIL"

# Disk Space
echo ""
echo "Disk Space:"
df -h | grep -E '/$|/home'

# Docker Status
echo ""
echo "Docker Containers:"
docker-compose ps
```

---

**For detailed information, see:**
- Full documentation: `DEVOPS.md`
- Sprint plan: `DEVOPS_SPRINT_PLAN.md`
- Architecture: `ARCHITECTURE.md`

**Last Updated**: 2026-01-03
