# TraceHub Production Deployment Guide

## Infrastructure Overview

TraceHub is deployed on **Hostinger VPS** with the following configuration:

| Component | Details |
|-----------|---------|
| **Provider** | Hostinger VPS |
| **VPS ID** | 1243111 |
| **Plan** | KVM 1 (1 CPU, 4GB RAM, 50GB SSD) |
| **OS** | Ubuntu 24.04 with Docker |
| **IP Address** | 82.198.225.150 |
| **IPv6** | 2a02:4780:41:51ca::1 |
| **Domain** | tracehub.vibotaj.com |
| **Data Center** | ID 19 |

## DNS Configuration

DNS records are managed via Hostinger DNS for `vibotaj.com`:

| Record | Type | Value | TTL |
|--------|------|-------|-----|
| `tracehub` | A | 82.198.225.150 | 300 |

## Firewall Rules

Firewall ID: `168536` (tracehub-firewall)

| Protocol | Port | Source | Description |
|----------|------|--------|-------------|
| SSH | 22 | any | Remote access |
| HTTP | 80 | any | Web (redirects to HTTPS) |
| HTTPS | 443 | any | Secure web traffic |

## SSH Access

```bash
# Connect to server
ssh root@82.198.225.150

# Or using hostname
ssh root@tracehub.vibotaj.com
```

SSH key: `shola-macbook` is attached to the VPS.

## Directory Structure

```
/opt/tracehub-app/
└── tracehub/
    ├── docker-compose.prod.yml
    ├── .env
    ├── backend/
    ├── frontend/
    ├── uploads/
    ├── logs/
    │   └── nginx/
    └── backups/
```

## SSL Certificates

SSL certificates are managed by **Let's Encrypt** via Certbot:

```
/etc/letsencrypt/
├── live/
│   └── tracehub.vibotaj.com/
│       ├── fullchain.pem  -> ../../archive/.../fullchain1.pem
│       ├── privkey.pem    -> ../../archive/.../privkey1.pem
│       ├── cert.pem       -> ../../archive/.../cert1.pem
│       └── chain.pem      -> ../../archive/.../chain1.pem
└── archive/
    └── tracehub.vibotaj.com/
        └── (actual certificate files)
```

### Renew SSL Certificate

```bash
# Check certificate status
sudo certbot certificates

# Renew all certificates
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# After renewal, restart nginx
docker restart tracehub-frontend-prod
```

### Generate New Certificate

```bash
# Stop nginx temporarily
docker stop tracehub-frontend-prod

# Generate certificate
sudo certbot certonly --standalone -d tracehub.vibotaj.com

# Restart nginx
docker start tracehub-frontend-prod
```

## Docker Services

### Container Overview

| Container | Image | Ports | Health Check |
|-----------|-------|-------|--------------|
| tracehub-db-prod | postgres:15 | 5432 (internal) | pg_isready |
| tracehub-backend-prod | tracehub-backend | 8000 (internal) | Python urllib |
| tracehub-frontend-prod | tracehub-frontend | 80, 443 | wget |

### Management Commands

```bash
cd /opt/tracehub-app/tracehub

# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs backend --tail 100

# Restart all services
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart frontend

# Stop all services
docker compose -f docker-compose.prod.yml down

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Force recreate
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## Environment Variables

Location: `/opt/tracehub-app/tracehub/.env`

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DB_USER` | PostgreSQL username | Yes | tracehub |
| `DB_PASSWORD` | PostgreSQL password | Yes | - |
| `DB_NAME` | PostgreSQL database name | Yes | tracehub |
| `JSONCARGO_API_KEY` | Container tracking API key | No | - |
| `JWT_SECRET` | JWT signing secret | Yes | - |
| `DEMO_PASSWORD` | Demo user password for POC | Yes | - |
| `ANTHROPIC_API_KEY` | Claude API key for AI document classification | No | - |
| `DEBUG` | Enable debug mode | No | false |
| `ENVIRONMENT` | Environment name (production/staging) | No | production |

**Note:** The following variables have sensible defaults in `backend/app/config.py` and are not required in the `.env` file:
- `CORS_ORIGINS` - Defaults to localhost origins for development
- `MAX_UPLOAD_SIZE` - Defaults to 50MB

### AI Document Classification

TraceHub uses Anthropic's Claude API for intelligent document type detection. When `ANTHROPIC_API_KEY` is configured, the system can:

- Automatically classify uploaded documents (Bill of Lading, Commercial Invoice, Certificates, etc.)
- Extract key fields and reference numbers
- Provide confidence scores and reasoning for classifications

**Setup:**
1. Get an API key from https://console.anthropic.com/settings/keys
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. Restart backend: `docker restart tracehub-backend-prod`

**Verify AI is enabled:**
```bash
docker exec tracehub-backend-prod python -c "
from app.services.document_classifier import document_classifier
print('AI Available:', document_classifier.is_ai_available())
"
```

If AI is not configured, the system falls back to keyword-based classification.

## Deployment Process

### Manual Deployment

```bash
# SSH into server
ssh root@82.198.225.150

# Navigate to project
cd /opt/tracehub-app/tracehub

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

### GitHub Actions (CI/CD)

The repository includes GitHub Actions workflows for automated deployment on push to `main`.

## Monitoring & Health Checks

### Health Endpoints

```bash
# Frontend health
curl -sk https://tracehub.vibotaj.com/health

# Backend health (via proxy)
curl -sk https://tracehub.vibotaj.com/api/auth/me
# Returns 401 if working (auth required)

# Direct backend health (from server)
docker exec tracehub-frontend-prod wget -qO- http://backend:8000/health
```

### Container Health Status

```bash
# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Detailed health info
docker inspect --format='{{.State.Health.Status}}' tracehub-backend-prod
```

## Database Management

### Access PostgreSQL

```bash
# From host
docker exec -it tracehub-db-prod psql -U tracehub -d tracehub

# Run SQL
docker exec tracehub-db-prod psql -U tracehub -d tracehub -c "SELECT COUNT(*) FROM shipments;"
```

### Backup Database

```bash
# Create backup
docker exec tracehub-db-prod pg_dump -U tracehub tracehub > /opt/tracehub-app/tracehub/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup.sql | docker exec -i tracehub-db-prod psql -U tracehub -d tracehub
```

### Seed Data

```bash
docker exec tracehub-backend-prod python -m seed_data
```

## Troubleshooting

### Frontend Not Starting

1. Check SSL certificates are mounted:
   ```bash
   docker logs tracehub-frontend-prod --tail 50
   ```

2. Verify cert files exist:
   ```bash
   ls -la /etc/letsencrypt/live/tracehub.vibotaj.com/
   ls -la /etc/letsencrypt/archive/tracehub.vibotaj.com/
   ```

3. Ensure docker-compose mounts `/etc/letsencrypt`:
   ```yaml
   volumes:
     - /etc/letsencrypt:/etc/letsencrypt:ro
   ```

### Backend Not Responding

1. Check logs:
   ```bash
   docker logs tracehub-backend-prod --tail 100
   ```

2. Verify database connection:
   ```bash
   docker exec tracehub-backend-prod python -c "from app.database import engine; engine.connect()"
   ```

3. Check network connectivity:
   ```bash
   docker exec tracehub-frontend-prod wget -qO- http://backend:8000/health
   ```

### Database Connection Issues

1. Check DB container is healthy:
   ```bash
   docker exec tracehub-db-prod pg_isready -U tracehub
   ```

2. Verify environment variables in `.env`

3. Check database logs:
   ```bash
   docker logs tracehub-db-prod --tail 50
   ```

## Hostinger MCP API Reference

The following Hostinger API endpoints are available via MCP tools:

### VPS Management

| Function | Description |
|----------|-------------|
| `VPS_getVirtualMachinesV1` | List all VPS instances |
| `VPS_getVirtualMachineDetailsV1` | Get VPS details |
| `VPS_restartVirtualMachineV1` | Restart VPS |
| `VPS_startVirtualMachineV1` | Start VPS |
| `VPS_stopVirtualMachineV1` | Stop VPS |

### Firewall

| Function | Description |
|----------|-------------|
| `VPS_getFirewallListV1` | List firewalls |
| `VPS_getFirewallDetailsV1` | Get firewall rules |
| `VPS_createFirewallRuleV1` | Add firewall rule |
| `VPS_deleteFirewallRuleV1` | Remove firewall rule |

### SSH Keys

| Function | Description |
|----------|-------------|
| `VPS_getPublicKeysV1` | List SSH keys |
| `VPS_getAttachedPublicKeysV1` | Keys attached to VPS |
| `VPS_attachPublicKeyV1` | Attach key to VPS |

### DNS

| Function | Description |
|----------|-------------|
| `DNS_getDNSRecordsV1` | List DNS records |
| `DNS_updateDNSRecordsV1` | Update DNS records |

## Security Notes

1. **SSH Access**: Only key-based authentication is enabled
2. **Firewall**: Only ports 22, 80, 443 are open
3. **Database**: Not exposed externally (internal Docker network only)
4. **SSL**: Enforced via nginx redirect (HTTP -> HTTPS)
5. **Secrets**: All sensitive data in `.env` file (not committed to git)

## Quick Reference

### Common Commands Cheatsheet

```bash
# Local Development
make dev              # Start local environment
make dev-logs         # View logs
make dev-down         # Stop local environment
make test             # Run backend tests

# Database Migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                               # Apply migrations
alembic downgrade -1                               # Rollback one step

# Deployment to Production
ssh root@82.198.225.150
cd /opt/tracehub-app/tracehub
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build

# Rollback
./scripts/rollback.sh -e production -t deployment
./scripts/rollback.sh -e production -t database -b backups/backup_YYYYMMDD.sql
```

### Environment URLs

| Environment | URL | Backend Port | Frontend Port |
|-------------|-----|--------------|---------------|
| Production  | https://tracehub.vibotaj.com | 8000 | 443 |
| Staging     | https://staging.tracehub.vibotaj.com | 8100 | 3100 |
| Local       | http://localhost | 8000 | 80 |

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-ci.yml` | PR/Push | Lint, test backend |
| `frontend-ci.yml` | PR/Push | Lint, test frontend |
| `deploy-staging.yml` | Push to develop | Deploy to staging |
| `deploy-production.yml` | Push to main | Deploy to production |

---

## Contact

- **Server Provider**: Hostinger
- **Domain Registrar**: Hostinger
- **Support**: https://www.hostinger.com/support
