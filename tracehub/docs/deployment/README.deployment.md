# TraceHub Deployment Guide

This guide covers deploying TraceHub using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [SSL/HTTPS Setup](#ssl-https-setup)
6. [Database Backups](#database-backups)
7. [Monitoring and Logs](#monitoring-and-logs)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- Make (optional, for using Makefile commands)

### Installation

```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

## Development Deployment

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd vibotaj-website-revamp-rep/tracehub

# Setup environment
make setup

# Edit .env files with your configuration
nano .env
nano frontend/.env

# Start development environment
make dev

# Or without Make:
docker-compose up -d
```

### Access Points

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

### Development Commands

```bash
# View logs
make dev-logs
# or
docker-compose logs -f

# Stop services
make dev-down
# or
docker-compose down

# Rebuild containers
make dev-rebuild
# or
docker-compose down && docker-compose build && docker-compose up -d

# Access backend shell
make shell-backend
# or
docker-compose exec backend /bin/bash

# Access database
make db-shell
# or
docker-compose exec db psql -U tracehub -d tracehub
```

## Production Deployment

### 1. Initial Setup

```bash
# Copy environment template
cp .env.example .env

# Edit production environment variables
nano .env
```

**Required environment variables:**
```bash
DB_PASSWORD=<strong-database-password>
JWT_SECRET=<random-secret-key-min-32-chars>
VIZION_API_KEY=<your-vizion-api-key>
CORS_ORIGINS=https://yourdomain.com
```

### 2. Build and Deploy

```bash
# Build production images
make prod-build
# or
docker-compose -f docker-compose.prod.yml build

# Start production services
make prod-up
# or
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
make db-migrate
# or
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check service health
make health
```

### 3. Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoints
curl http://localhost:80/health
curl http://localhost/api/health
```

## Environment Configuration

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `JWT_SECRET` | Secret key for JWT tokens | Yes | - |
| `VIZION_API_KEY` | API key for container tracking | Yes | - |
| `DEBUG` | Enable debug mode | No | false |
| `CORS_ORIGINS` | Allowed CORS origins | No | * |
| `MAX_UPLOAD_SIZE` | Max file upload size (bytes) | No | 10485760 |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | /api |
| `VITE_APP_NAME` | Application name | VIBOTAJ TraceHub |
| `VITE_ENABLE_CONTAINER_TRACKING` | Enable container tracking | true |
| `VITE_ENABLE_DOCUMENT_UPLOAD` | Enable document uploads | true |

### Generating Secrets

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate strong password
openssl rand -base64 24
```

## SSL/HTTPS Setup

### Using Let's Encrypt with Nginx

1. **Install Certbot**:
```bash
sudo apt-get install certbot python3-certbot-nginx
```

2. **Create nginx SSL configuration**:
```bash
# Create SSL version of nginx config
cat > tracehub/frontend/nginx-ssl.conf << 'EOF'
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    root /usr/share/nginx/html;
    index index.html;

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
```

3. **Update docker-compose.prod.yml**:
```yaml
frontend:
  volumes:
    - /etc/letsencrypt/live/yourdomain.com:/etc/nginx/ssl:ro
    - ./frontend/nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
  ports:
    - "80:80"
    - "443:443"
```

4. **Obtain SSL certificate**:
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

## Database Backups

### Manual Backup

```bash
# Create backup
make db-backup
# or
mkdir -p ./backups
docker-compose exec db pg_dump -U tracehub tracehub > ./backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/tracehub && make db-backup > /dev/null 2>&1
```

### Restore from Backup

```bash
# Restore from specific backup file
make db-restore FILE=./backups/backup_20260102_020000.sql
# or
docker-compose exec -T db psql -U tracehub tracehub < ./backups/backup_20260102_020000.sql
```

### Backup Retention Script

```bash
#!/bin/bash
# Keep only last 30 days of backups
find ./backups -name "backup_*.sql" -mtime +30 -delete
```

## Monitoring and Logs

### View Logs

```bash
# All services
make logs

# Specific service
make logs-backend
make logs-frontend
make logs-db

# Production logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Log Rotation

Add logrotate configuration:

```bash
sudo cat > /etc/logrotate.d/tracehub << 'EOF'
/path/to/tracehub/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker-compose -f /path/to/tracehub/docker-compose.prod.yml restart frontend > /dev/null
    endscript
}
EOF
```

### Health Checks

```bash
# Check all services
make health

# Manual health checks
curl http://localhost:80/health
curl http://localhost/api/health

# Check container status
docker-compose ps
```

## Troubleshooting

### Common Issues

#### 1. Frontend Can't Connect to Backend

```bash
# Check backend is running
docker-compose ps backend

# Check backend logs
docker-compose logs backend

# Verify backend health
curl http://localhost:8000/health

# Test from frontend container
docker-compose exec frontend wget -O- http://backend:8000/health
```

#### 2. Database Connection Errors

```bash
# Check database is running
docker-compose ps db

# Test database connection
docker-compose exec backend python -c "from app.database import engine; engine.connect()"

# Check database logs
docker-compose logs db

# Verify credentials
docker-compose exec db psql -U tracehub -d tracehub -c "SELECT version();"
```

#### 3. File Upload Issues

```bash
# Check uploads directory permissions
ls -la uploads/

# Fix permissions
sudo chown -R 1000:1000 uploads/
chmod -R 755 uploads/

# Check backend logs for errors
docker-compose logs backend | grep -i upload
```

#### 4. Container Build Failures

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check disk space
df -h
```

### Reset Everything

```bash
# WARNING: This will delete all data!
make clean-all

# Or manually:
docker-compose down -v --rmi all
docker-compose -f docker-compose.prod.yml down -v --rmi all
rm -rf uploads/* logs/*
```

### Performance Optimization

```bash
# Monitor resource usage
docker stats

# Limit container resources (docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 512M
```

## Security Checklist

- [ ] Change default passwords in .env
- [ ] Generate strong JWT_SECRET (min 32 chars)
- [ ] Configure CORS_ORIGINS to specific domains
- [ ] Enable SSL/HTTPS in production
- [ ] Don't expose database port (5432) publicly
- [ ] Use secrets management for sensitive data
- [ ] Regular security updates: `docker-compose pull`
- [ ] Enable firewall and limit exposed ports
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity

## Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Database credentials set
- [ ] API keys configured
- [ ] SSL certificates obtained
- [ ] Firewall rules configured
- [ ] DNS records updated

### Deployment

- [ ] Build production images
- [ ] Start services
- [ ] Run database migrations
- [ ] Verify health checks
- [ ] Test frontend accessibility
- [ ] Test API endpoints
- [ ] Check logs for errors

### Post-Deployment

- [ ] Setup automated backups
- [ ] Configure log rotation
- [ ] Setup monitoring/alerts
- [ ] Document deployment
- [ ] Test disaster recovery
- [ ] Update documentation

## Support

For issues and questions:
- Check logs: `make logs`
- Review this documentation
- Check Docker Compose files
- Contact: [support contact]
