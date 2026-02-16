# TraceHub Deployment Skill

Specialized knowledge for Hostinger VPS deployment, Docker Compose, Nginx, SSL, and the staging→production pipeline.

## When to Load

Load this skill when working on:
- Deployment, infrastructure, or DevOps tasks
- Docker Compose configuration
- Nginx configuration or SSL certificates
- GitHub Actions CI/CD workflows
- Server troubleshooting or monitoring
- Database backup/restore operations

## Infrastructure Overview

| Component | Details |
|-----------|---------|
| Provider | Hostinger VPS |
| VPS ID | 1243111 |
| Plan | KVM 1 (1 CPU, 4GB RAM, 50GB SSD) |
| OS | Ubuntu 24.04 with Docker |
| IP | 82.198.225.150 |
| Domain | tracehub.vibotaj.com |

## Environment URLs

| Environment | URL | Backend Port | Frontend Port |
|-------------|-----|--------------|---------------|
| Production | https://tracehub.vibotaj.com | 8000 | 443 |
| Staging | https://staging.tracehub.vibotaj.com | 8100 | 3100 |
| Local | http://localhost | 8000 | 80 |

## Docker Services

| Container | Image | Ports | Health Check |
|-----------|-------|-------|--------------|
| tracehub-db-prod | postgres:15 | 5432 (internal) | pg_isready |
| tracehub-backend-prod | tracehub-backend | 8000 (internal) | Python urllib |
| tracehub-frontend-prod | tracehub-frontend | 80, 443 | wget |

## Server Directory Structure

```
/opt/tracehub-app/
└── tracehub/
    ├── docker-compose.prod.yml
    ├── .env
    ├── backend/
    ├── frontend/
    ├── uploads/
    ├── logs/nginx/
    └── backups/
```

## Deployment Process

### Manual Deployment

```bash
ssh root@82.198.225.150
cd /opt/tracehub-app/tracehub
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

### GitOps Pipeline

```
feature/* → develop (staging auto-deploys) → main (production auto-deploys)
```

Never push directly to `main`; always verify on staging first.

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-ci.yml` | PR/Push | Lint, test backend |
| `frontend-ci.yml` | PR/Push | Lint, test frontend |
| `deploy-staging.yml` | Push to develop | Deploy to staging |
| `deploy-production.yml` | Push to main | Deploy to production |

## Docker Compose Commands

```bash
cd /opt/tracehub-app/tracehub

# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs backend --tail 100

# Restart all / specific service
docker compose -f docker-compose.prod.yml restart
docker compose -f docker-compose.prod.yml restart frontend

# Stop / Start
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Force recreate
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## SSL Certificates

Managed by Let's Encrypt via Certbot:

```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# After renewal, restart nginx
docker restart tracehub-frontend-prod
```

Certificate paths:
```
/etc/letsencrypt/live/tracehub.vibotaj.com/
    fullchain.pem
    privkey.pem
    cert.pem
    chain.pem
```

## Database Operations

```bash
# Access PostgreSQL
docker exec -it tracehub-db-prod psql -U tracehub -d tracehub

# Create backup
docker exec tracehub-db-prod pg_dump -U tracehub tracehub > /opt/tracehub-app/tracehub/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup.sql | docker exec -i tracehub-db-prod psql -U tracehub -d tracehub

# Seed data
docker exec tracehub-backend-prod python -m seed_data
```

### Alembic Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Environment Variables

Location: `/opt/tracehub-app/tracehub/.env`

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_USER` | Yes | PostgreSQL username |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `DB_NAME` | Yes | PostgreSQL database name |
| `JSONCARGO_API_KEY` | Yes | Container tracking API key |
| `JWT_SECRET` | Yes | JWT signing secret |
| `DEMO_PASSWORD` | Yes | Demo user password for POC |
| `ANTHROPIC_API_KEY` | No | Claude API key for AI doc classification |
| `DEBUG` | No | Enable debug mode (default: false) |
| `ENVIRONMENT` | No | production/staging (default: production) |

## Health Checks

```bash
# Frontend health
curl -sk https://tracehub.vibotaj.com/health

# Backend health (returns 401 if auth working)
curl -sk https://tracehub.vibotaj.com/api/auth/me

# Direct backend health (from server)
docker exec tracehub-frontend-prod wget -qO- http://backend:8000/health

# Container health status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Rollback

```bash
# Deployment rollback
./scripts/rollback.sh -e production -t deployment

# Database rollback
./scripts/rollback.sh -e production -t database -b backups/backup_YYYYMMDD.sql
```

## Firewall

Firewall ID: 168536 (tracehub-firewall)

| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | SSH | any | Remote access |
| 80 | HTTP | any | Redirects to HTTPS |
| 443 | HTTPS | any | Secure web traffic |

## Security Notes

- SSH: key-based authentication only (shola-macbook key attached)
- Database: not exposed externally (internal Docker network only)
- SSL: enforced via nginx redirect (HTTP → HTTPS)
- Secrets: all in `.env` (not committed to git)

## Troubleshooting

### Frontend Not Starting
1. Check logs: `docker logs tracehub-frontend-prod --tail 50`
2. Verify certs: `ls -la /etc/letsencrypt/live/tracehub.vibotaj.com/`
3. Ensure docker-compose mounts `/etc/letsencrypt`

### Backend Not Responding
1. Check logs: `docker logs tracehub-backend-prod --tail 100`
2. Verify DB: `docker exec tracehub-backend-prod python -c "from app.database import engine; engine.connect()"`
3. Check network: `docker exec tracehub-frontend-prod wget -qO- http://backend:8000/health`

### Database Connection Issues
1. Check health: `docker exec tracehub-db-prod pg_isready -U tracehub`
2. Verify `.env` variables
3. Check logs: `docker logs tracehub-db-prod --tail 50`

## Key Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | Production Docker Compose |
| `docker-compose.staging.yml` | Staging Docker Compose |
| `docker-compose.yml` | Local development |
| `tracehub/frontend/nginx.conf` | Production Nginx config |
| `tracehub/DEPLOYMENT.md` | Full deployment guide |
| `.github/workflows/deploy-*.yml` | CI/CD workflows |
| `scripts/rollback.sh` | Rollback script |
