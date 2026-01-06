# TraceHub Quick Start Guide

Get TraceHub up and running in minutes with Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

## Development Setup (5 minutes)

### 1. Clone and Setup

```bash
cd tracehub

# Create environment files
cp .env.example .env
cp frontend/.env.example frontend/.env.development

# Edit .env with your configuration (optional for development)
nano .env
```

### 2. Start Services

```bash
# Using Make (recommended)
make dev

# Or using Docker Compose directly
docker-compose up -d
```

### 3. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. View Logs

```bash
make dev-logs
# or
docker-compose logs -f
```

### 5. Stop Services

```bash
make dev-down
# or
docker-compose down
```

## Production Deployment

### 1. Configure Environment

```bash
# Copy and edit production environment
cp .env.example .env
nano .env
```

**Required variables:**
```bash
DB_PASSWORD=<strong-password>           # Database password
JWT_SECRET=<random-32-char-string>      # JWT secret key
JSONCARGO_API_KEY=<your-api-key>       # Container tracking API key (optional)
CORS_ORIGINS=https://yourdomain.com    # Your domain
```

Generate secure secrets:
```bash
# Generate JWT secret
openssl rand -hex 32

# Generate database password
openssl rand -base64 24
```

### 2. Deploy

```bash
# Deploy to production
./scripts/deploy.sh --environment production

# Or step by step:
make prod-build
make prod-up
make db-migrate
```

### 3. Verify Deployment

```bash
# Check health
./scripts/health-check.sh docker-compose.prod.yml

# Or manually
make health
curl http://localhost/health
curl http://localhost/api/health
```

## Common Commands

### Development

```bash
# Start development environment
make dev

# View logs
make dev-logs

# Rebuild containers
make dev-rebuild

# Access backend shell
make shell-backend

# Access database
make db-shell
```

### Production

```bash
# Deploy to production
./scripts/deploy.sh -e production

# View logs
make prod-logs

# Restart services
make prod-restart

# Create backup
./scripts/backup.sh production

# Check health
./scripts/health-check.sh docker-compose.prod.yml
```

### Database

```bash
# Run migrations
make db-migrate

# Create backup
make db-backup

# Restore from backup
make db-restore FILE=./backups/backup_20260102_120000.sql

# Access database shell
make db-shell
```

### Maintenance

```bash
# Check service health
make health

# View container status
make ps

# Clean up (WARNING: deletes data)
make clean

# Clean everything including images
make clean-all
```

## Directory Structure

```
tracehub/
├── backend/              # FastAPI backend application
│   ├── app/             # Application code
│   ├── Dockerfile       # Backend container image
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend application
│   ├── src/            # Source code
│   ├── Dockerfile      # Frontend container image
│   ├── nginx.conf      # Nginx configuration
│   └── package.json    # Node dependencies
├── scripts/            # Deployment scripts
│   ├── deploy.sh      # Deployment automation
│   ├── backup.sh      # Backup automation
│   └── health-check.sh # Health checking
├── uploads/           # File uploads (gitignored)
├── backups/           # Database backups (gitignored)
├── logs/              # Application logs (gitignored)
├── docker-compose.yml      # Development configuration
├── docker-compose.prod.yml # Production configuration
├── Makefile           # Convenient commands
└── .env               # Environment variables (gitignored)
```

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_USER` | Database username | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `DB_NAME` | Database name | Yes |
| `JWT_SECRET` | Secret key for JWT tokens | Yes |
| `JSONCARGO_API_KEY` | Container tracking API key | No |
| `DEBUG` | Enable debug mode | No |
| `CORS_ORIGINS` | Allowed CORS origins | No |

### Frontend (frontend/.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | /api |
| `VITE_APP_NAME` | Application name | VIBOTAJ TraceHub |
| `VITE_ENABLE_CONTAINER_TRACKING` | Enable tracking | true |
| `VITE_ENABLE_DOCUMENT_UPLOAD` | Enable uploads | true |

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Frontend can't connect to backend

```bash
# Check backend is running
docker-compose ps backend

# Test backend health
curl http://localhost:8000/health

# Test from frontend container
docker-compose exec frontend wget -O- http://backend:8000/health
```

### Database connection errors

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec backend python -c "from app.database import engine; engine.connect()"
```

### Port already in use

```bash
# Find what's using port 80
sudo lsof -i :80

# Use different ports in docker-compose.yml
ports:
  - "8080:80"  # Change to 8080
```

## Backup and Restore

### Create Backup

```bash
# Manual backup
./scripts/backup.sh production

# Automated daily backup (add to crontab)
0 2 * * * cd /path/to/tracehub && ./scripts/backup.sh auto
```

### Restore Backup

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore database
docker-compose -f docker-compose.prod.yml up -d db
docker-compose -f docker-compose.prod.yml exec -T db psql -U tracehub tracehub < ./backups/db_backup.sql

# Restore uploads
tar -xzf ./backups/uploads_backup.tar.gz

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

## SSL/HTTPS Setup

### Using Let's Encrypt

1. Install Certbot:
```bash
sudo apt-get install certbot
```

2. Obtain certificate:
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

3. Update docker-compose.prod.yml:
```yaml
frontend:
  volumes:
    - /etc/letsencrypt/live/yourdomain.com:/etc/nginx/ssl:ro
  ports:
    - "443:443"
```

4. Update nginx.conf with SSL configuration (see README.deployment.md)

## Next Steps

- Review [README.deployment.md](/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/README.deployment.md) for detailed deployment guide
- Configure monitoring and alerts
- Setup automated backups
- Configure SSL/HTTPS for production
- Review security checklist

## Support

For issues:
1. Check logs: `make logs`
2. Run health check: `./scripts/health-check.sh`
3. Review troubleshooting section above
4. Check Docker Compose configuration files

For more help, see the full deployment documentation in README.deployment.md.
