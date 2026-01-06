# TraceHub Architecture

> High-level architecture overview and design principles

## Quick Links

- **Full Architecture Document:** [docs/architecture/tracehub-architecture.md](architecture/tracehub-architecture.md)
- **Multi-Tenancy ADR:** [tracehub/docs/architecture/ADR-008-multi-tenancy-architecture.md](../tracehub/docs/architecture/ADR-008-multi-tenancy-architecture.md)
- **Architecture Decisions:** [docs/decisions/](decisions/)

## Overview

TraceHub is a **decoupled, API-first platform** for container tracking and documentation compliance in agro-export operations.

## Three Core Pillars

1. **Real-Time Container Tracking**
   - Carrier-agnostic API integration
   - Live status and ETD/ETA updates
   - Port event tracking

2. **Document Lifecycle & Compliance**
   - State machine for document workflow
   - EUDR compliance validation
   - Audit-ready bundle generation

3. **Buyer & Supplier Experience**
   - Role-based dashboards
   - Document upload and validation
   - Real-time shipment visibility

## Architecture Principles

### 1. Decoupled Design
- **Frontend:** React 18 (TypeScript) - Independent UI
- **Backend:** FastAPI (Python 3.11) - Core business logic
- **Database:** PostgreSQL 15 - Persistent storage

### 2. API-First
- All functionality exposed via REST APIs
- JWT-based authentication
- OpenAPI documentation auto-generated

### 3. Compliance by Design
- EUDR rules embedded in data model
- Document requirements driven by HS codes
- Refer to [`COMPLIANCE_MATRIX.md`](COMPLIANCE_MATRIX.md) as single source of truth

### 4. Multi-Tenant Ready
- Organization-based data isolation
- Role-based access control (RBAC)
- Scalable to multiple exporters

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TraceHub Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (React + TypeScript)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Buyer      │  │   Supplier   │  │     Admin       │  │
│  │  Dashboard   │  │    Portal    │  │   Dashboard     │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                      REST API (JWT)                         │
│                            │                                │
│  ┌────────────────────────┴──────────────────────────────┐ │
│  │        Backend (FastAPI + Python 3.11)                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │ │
│  │  │  Shipments   │  │  Documents   │  │ Compliance │  │ │
│  │  │   Service    │  │   Service    │  │  Service   │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │ │
│  │  │   Tracking   │  │     Auth     │  │ Analytics  │  │ │
│  │  │   Service    │  │   Service    │  │  Service   │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │ │
│  └────────────────────────┬──────────────────────────────┘ │
│                           │                                │
│  ┌────────────────────────┴──────────────────────────────┐ │
│  │          PostgreSQL Database (Multi-Tenant)           │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │ │
│  │  │  Orgs    │ │ Shipments│ │Documents │ │ Users   │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                              │
         v                              v
┌──────────────────┐          ┌──────────────────────┐
│ Container        │          │ Document Storage     │
│ Tracking API     │          │ (S3 / Local)         │
│ (ShipsGo/Vizion) │          └──────────────────────┘
└──────────────────┘
```

## Core Data Entities

| Entity | Purpose | Key Fields |
|--------|---------|------------|
| **Organization** | Multi-tenant separation | name, settings, active |
| **Shipment** | Container tracking | container_no, bl_number, status |
| **Product** | Goods being shipped | hs_code, quantity, eudr_applicable |
| **Document** | Compliance documentation | type, status, file_path |
| **User** | System access | email, role, organization_id |
| **ContainerEvent** | Tracking events | event_type, location, timestamp |

## Document Lifecycle States

```
Draft → Uploaded → Validated → Compliance_Check → Linked → Archived
```

## Shipment Lifecycle States

```
Created → Docs_Pending → Docs_Complete → In_Transit → 
Arrived → Delivered → Closed
```

## Technology Stack

### Backend
- **Framework:** FastAPI 0.109+
- **Language:** Python 3.11+
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL 15
- **Auth:** JWT (python-jose)

### Frontend
- **Framework:** React 18
- **Language:** TypeScript
- **Build:** Vite
- **Routing:** React Router
- **State:** Context API

### Infrastructure
- **Deployment:** Docker + Docker Compose
- **Web Server:** Nginx (production)
- **Database:** PostgreSQL 15
- **File Storage:** S3 (production) / Local (dev)

## Security

- **Authentication:** JWT tokens with refresh
- **Authorization:** Role-based access control (RBAC)
- **Data Isolation:** Organization-level row-level security
- **Secrets:** Environment variables only (`.env` files)
- **API Security:** Rate limiting, CORS, input validation

## Scalability Considerations

### Current (POC)
- Single Docker host
- Basic horizontal scaling (multiple containers)

### Future (Production)
- Load balancer (Nginx/HAProxy)
- Multiple API instances
- Database read replicas
- Redis for caching and sessions
- CDN for static assets

## Development Workflow

See [`CLAUDE.md`](../CLAUDE.md) for:
- Coding standards
- Commit conventions
- Testing requirements
- Security checklist

## Related Documentation

- **Compliance Rules:** [`docs/COMPLIANCE_MATRIX.md`](COMPLIANCE_MATRIX.md)
- **API Docs:** [`docs/API.md`](API.md)
- **Deployment:** [`docs/DEPLOYMENT.md`](DEPLOYMENT.md)
- **Full Architecture:** [`docs/architecture/tracehub-architecture.md`](architecture/tracehub-architecture.md)

---

**Version:** 1.0  
**Last Updated:** 2026-01-06  
**Status:** Active
