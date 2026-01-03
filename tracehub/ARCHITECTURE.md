# TraceHub Deployment Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ HTTPS (443) / HTTP (80)
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     FRONTEND CONTAINER                           │
│                    (Nginx + React SPA)                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Static Files (/index.html, /assets/*)                  │   │
│  │  - React application bundle                              │   │
│  │  - CSS, images, fonts                                    │   │
│  │  - Gzip compression                                      │   │
│  │  - Cache headers (1 year for assets)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Reverse Proxy (/api/*)                                 │   │
│  │  - Proxies to backend:8000                              │   │
│  │  - Adds security headers                                │   │
│  │  - Handles CORS                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Port: 80, 443                                                  │
│  Health: /health                                                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ Internal Network (tracehub-network)
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     BACKEND CONTAINER                            │
│                    (FastAPI + Python 3.11)                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  REST API Endpoints                                      │   │
│  │  - /api/health                                           │   │
│  │  - /api/shipments                                        │   │
│  │  - /api/documents                                        │   │
│  │  - /api/tracking                                         │   │
│  │  - /api/auth                                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Business Logic                                          │   │
│  │  - Document lifecycle management                        │   │
│  │  - Container tracking integration                       │   │
│  │  - EUDR compliance validation                           │   │
│  │  - File upload handling                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Port: 8000 (internal only)                                     │
│  Health: /health                                                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ PostgreSQL Protocol
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     DATABASE CONTAINER                           │
│                      (PostgreSQL 15)                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Tables                                                  │   │
│  │  - shipments                                             │   │
│  │  - documents                                             │   │
│  │  - tracking_events                                       │   │
│  │  - users                                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Persistent Volume                                       │   │
│  │  - tracehub_postgres_data                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Port: 5432 (internal only)                                     │
│  Health: pg_isready                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Container Communication Flow

### User Request Flow
```
1. User Browser
   ↓ HTTP/HTTPS Request
2. Frontend Container (Nginx)
   ├── Static files → Serve directly
   └── /api/* requests
       ↓ Proxy
3. Backend Container (FastAPI)
   ├── Business logic
   └── Database queries
       ↓ PostgreSQL protocol
4. Database Container (PostgreSQL)
   ↓ Query results
5. Backend → Response
   ↓ Proxy response
6. Frontend → User
```

### External API Integration
```
Backend Container
   ↓ HTTPS
External APIs
   - JSONCargo API (container tracking)
   - Future: Other logistics APIs
```

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    tracehub-network (Bridge)                     │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  frontend    │───▶│   backend    │───▶│      db      │     │
│  │  (nginx)     │    │  (fastapi)   │    │ (postgres)   │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│       │ :80                                                     │
└───────┼─────────────────────────────────────────────────────────┘
        │
    ┌───▼────┐
    │  Host  │
    │ System │
    └────────┘
```

## Volume Mounts

```
Host System                      Container
─────────────────────────────────────────────────────
./uploads              →         /app/uploads (backend)
./logs                 →         /app/logs (backend)
./logs/nginx           →         /var/log/nginx (frontend)
tracehub_postgres_data →         /var/lib/postgresql/data (db)
./backups              →         /backups (db) [optional]
/etc/letsencrypt       →         /etc/nginx/ssl (frontend) [production]
```

## Environment Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                      Environment Variables                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  .env (Root)                                                    │
│  ├── DB_USER, DB_PASSWORD, DB_NAME                             │
│  ├── JWT_SECRET                                                 │
│  ├── JSONCARGO_API_KEY                                          │
│  └── CORS_ORIGINS                                               │
│                                                                  │
│  frontend/.env.production                                       │
│  ├── VITE_API_URL=/api                                          │
│  ├── VITE_APP_NAME                                              │
│  └── VITE_ENABLE_*                                              │
│                                                                  │
│  backend/.env (Generated from root .env)                        │
│  └── DATABASE_URL=postgresql://...                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Network Isolation                                       │
│ - Bridge network isolates containers                             │
│ - Database not exposed to host in production                     │
│ - Backend not exposed to host in production                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: Nginx Security                                          │
│ - HTTPS/TLS encryption                                           │
│ - Security headers (X-Frame-Options, CSP, etc.)                  │
│ - Request size limits                                            │
│ - Rate limiting (configurable)                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: Application Security                                    │
│ - JWT authentication                                             │
│ - CORS restrictions                                              │
│ - Input validation                                               │
│ - File upload restrictions                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: Data Security                                           │
│ - Environment variable secrets                                   │
│ - Database encryption at rest                                    │
│ - Backup encryption (configurable)                               │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Configurations

### Development Mode
```yaml
docker-compose.yml:
  - All ports exposed for debugging
  - Hot-reload enabled
  - Debug mode on
  - Volume mounts for live code editing
  - Database exposed on 5432
```

### Production Mode
```yaml
docker-compose.prod.yml:
  - Only frontend exposed (80, 443)
  - No hot-reload
  - Debug mode off
  - No volume mounts for code
  - Database internal only
  - Restart policies enabled
  - Resource limits configured
```

## High Availability Architecture (Future)

```
┌─────────────────────────────────────────────────────────────────┐
│                       Load Balancer                              │
│                    (Nginx / HAProxy)                             │
└──────────────┬──────────────────────────────┬───────────────────┘
               │                              │
    ┌──────────▼─────────┐        ┌──────────▼─────────┐
    │  Frontend Instance │        │  Frontend Instance │
    │        #1          │        │        #2          │
    └──────────┬─────────┘        └──────────┬─────────┘
               │                              │
    ┌──────────▼──────────────────────────────▼─────────┐
    │              Backend Cluster                       │
    │         (Multiple FastAPI Instances)               │
    └──────────┬──────────────────────────────┬─────────┘
               │                              │
    ┌──────────▼─────────┐        ┌──────────▼─────────┐
    │  Database Primary  │───────▶│  Database Replica  │
    │   (Write/Read)     │        │    (Read Only)     │
    └────────────────────┘        └────────────────────┘
```

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Health Check System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Docker Health Checks                                           │
│  ├── Database: pg_isready (every 5s)                            │
│  ├── Backend: /health endpoint (every 30s)                      │
│  └── Frontend: /health endpoint (every 30s)                     │
│                                                                  │
│  External Monitoring (Future)                                   │
│  ├── Prometheus: Metrics collection                             │
│  ├── Grafana: Visualization                                     │
│  └── Alert Manager: Notifications                               │
│                                                                  │
│  Logging                                                        │
│  ├── Application logs: /app/logs                                │
│  ├── Nginx logs: /var/log/nginx                                 │
│  └── Database logs: Container logs                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Backup Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      Backup Flow                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Daily Automated Backup (2 AM)                                  │
│  ├── Database dump (pg_dump)                                    │
│  ├── Uploads archive (tar.gz)                                   │
│  └── Metadata file                                              │
│                                                                  │
│  Backup Storage                                                 │
│  ├── Local: ./backups/                                          │
│  └── Remote: [S3/GCS] (Future)                                  │
│                                                                  │
│  Retention Policy                                               │
│  ├── Daily backups: 30 days                                     │
│  ├── Weekly backups: 3 months                                   │
│  └── Monthly backups: 1 year                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                   Deployment Process                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Pre-Deployment                                              │
│     ├── Validate environment variables                          │
│     ├── Create database backup                                  │
│     └── Pull latest code (optional)                             │
│                                                                  │
│  2. Build Phase                                                 │
│     ├── Build backend image                                     │
│     ├── Build frontend image                                    │
│     └── Tag images                                              │
│                                                                  │
│  3. Deploy Phase                                                │
│     ├── Stop existing containers                                │
│     ├── Start new containers                                    │
│     └── Wait for health checks                                  │
│                                                                  │
│  4. Migration Phase                                             │
│     ├── Run database migrations                                 │
│     └── Verify schema                                           │
│                                                                  │
│  5. Verification Phase                                          │
│     ├── Health check all services                               │
│     ├── Test API endpoints                                      │
│     └── Verify frontend accessibility                           │
│                                                                  │
│  6. Post-Deployment                                             │
│     ├── Clean old Docker images                                 │
│     ├── Update documentation                                    │
│     └── Notify team                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     Technology Stack                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Frontend                                                       │
│  ├── React 18                                                   │
│  ├── TypeScript                                                 │
│  ├── Vite (build tool)                                          │
│  ├── TailwindCSS                                                │
│  ├── Nginx (production server)                                  │
│  └── Alpine Linux                                               │
│                                                                  │
│  Backend                                                        │
│  ├── Python 3.11                                                │
│  ├── FastAPI                                                    │
│  ├── SQLAlchemy (ORM)                                           │
│  ├── Alembic (migrations)                                       │
│  ├── Uvicorn (ASGI server)                                      │
│  └── Debian Slim                                                │
│                                                                  │
│  Database                                                       │
│  ├── PostgreSQL 15                                              │
│  └── Debian-based official image                                │
│                                                                  │
│  Infrastructure                                                 │
│  ├── Docker                                                     │
│  ├── Docker Compose                                             │
│  ├── Bash scripts                                               │
│  └── Make                                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Resource Requirements

### Minimum (Development)
```
CPU:    2 cores
RAM:    4 GB
Disk:   20 GB
```

### Recommended (Production)
```
CPU:    4 cores
RAM:    8 GB
Disk:   50 GB SSD
Network: 100 Mbps
```

### Container Resources
```
Frontend:  512 MB RAM, 0.5 CPU
Backend:   1 GB RAM, 1 CPU
Database:  2 GB RAM, 1 CPU
```

## Scaling Strategy

### Vertical Scaling
```
1. Increase container resource limits
2. Upgrade host machine specs
3. Optimize database configuration
```

### Horizontal Scaling
```
1. Add load balancer
2. Run multiple frontend instances
3. Run multiple backend instances
4. Setup database replication
5. Use external file storage (S3)
```

## Summary

This architecture provides:
- Containerized microservices
- Secure network isolation
- Production-ready Nginx configuration
- Automated deployment and backups
- Health monitoring
- Scalability path
- Comprehensive documentation

All components are production-ready and can be deployed immediately using the provided scripts and configurations.
