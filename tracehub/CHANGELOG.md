# TraceHub Changelog

All notable changes to the TraceHub platform are documented in this file.

## [Unreleased]
- Sprint 7: OCR & AI Document Detection
- Sprint 8: Buyer Portal & Notifications
- Sprint 9: AI-Powered Compliance
- Sprint 10: Multi-Tenant & SaaS Foundation

---

## [1.1.0] - 2026-01-04

### Sprint 6: DevOps & GitOps Implementation

**CI/CD Pipeline:**
- GitHub Actions CI workflows for backend and frontend
- Automated linting (flake8, black, ESLint)
- Automated type checking (mypy, TypeScript)
- Unit tests with coverage reporting (pytest, Vitest)
- Security scanning (bandit, safety, npm audit)
- Docker image building and pushing to GHCR

**Deployment Automation:**
- Staging deployment workflow (auto-deploy on develop branch)
- Production deployment workflow (manual trigger with approval)
- Zero-downtime deployment with health checks
- Automatic database backups before deployment
- Deployment failure notifications

**Database Migrations:**
- Alembic migrations fully configured
- Initial schema migration created
- Migrations run automatically during deployment

**Rollback & Recovery:**
- `rollback.sh` script for deployment and database rollback
- Blue-green deployment support
- Pre-rollback backup creation
- Health check verification after rollback

**Documentation:**
- GitHub secrets documentation (`GITHUB_SECRETS.md`)
- DevOps/GitOps implementation plan (`DEVOPS_GITOPS_PLAN.md`)

**Workflow Files:**
- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/build-and-push.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-production.yml`
- `.github/workflows/database-migrations.yml`

**Technical:**
- Zero infrastructure cost (using GitHub Actions, free tiers)
- Deployment frequency: automated on every push
- Mean time to recovery: < 15 minutes with rollback script

---

## [1.0.0] - 2026-01-03

### Sprint 5: Historical Data & Logistics Agent Workflow

**Features:**
- Shipment creation endpoint for historical/completed trades
- Logistics agent role with full document upload permissions
- Support for uploading documentation for past shipments
- Historical shipment status tracking (delivered, completed)

**API Endpoints:**
- `POST /api/shipments` - Create new shipments (admin, logistics_agent)

**Technical:**
- Added `ShipmentCreate` schema with `is_historical` flag
- Logistics agent can create shipments with any status including "delivered"

---

## [0.5.0] - 2025-12-30

### Sprint 4: EUDR Compliance & Analytics

**Features:**
- EUDR status tracking per shipment
- Analytics dashboard with compliance metrics
- Multi-type document support (single PDF containing multiple document types)
- EUDR compliance status indicators (pending, compliant, non_compliant, review_required)

**Components:**
- `EUDRStatusCard` - Visual EUDR compliance status
- `Analytics` page - Dashboard with charts and metrics

**API Endpoints:**
- `GET /api/analytics/summary` - Compliance and shipment statistics
- `GET /api/eudr/status/{shipment_id}` - EUDR compliance status

**Data Model:**
- Added `document_types` JSONB array for combined document PDFs
- EUDR compliance fields on shipment model

---

## [0.4.0] - 2025-12-27

### Sprint 3: Document Validation & Workflow Engine

**Features:**
- Document lifecycle states (draft -> uploaded -> validated -> approved -> rejected)
- Validation service with field requirements per document type
- Transition permissions based on user role
- In-app notifications on document events
- Document approval/rejection workflow for compliance officers

**API Endpoints:**
- `POST /api/documents/{id}/validate` - Validate document (compliance)
- `POST /api/documents/{id}/approve` - Approve document (compliance)
- `POST /api/documents/{id}/reject` - Reject document with reason (compliance)
- `GET /api/notifications` - User notifications
- `POST /api/notifications/{id}/read` - Mark notification as read

**Components:**
- `NotificationBell` - Real-time notification indicator
- Document workflow actions in shipment detail view

**Technical:**
- `DocumentStatus` enum with state machine transitions
- `Notification` model for user alerts
- Role-based document state transitions

---

## [0.3.0] - 2025-12-24

### Sprint 2: Role-Based Access Control & Multi-User Support

**Features:**
- Six user roles with hierarchical permissions:
  - **Admin** (level 5): Full system access
  - **Compliance** (level 4): Document validation & approval
  - **Logistics Agent** (level 3): Create shipments, upload documents
  - **Buyer** (level 2): View assigned shipments
  - **Supplier** (level 2): Upload origin certificates
  - **Viewer** (level 1): Read-only access
- User management page (admin only)
- Permission-based UI components
- JWT tokens include role information

**API Endpoints:**
- `GET /api/users` - List users (admin)
- `POST /api/users` - Create user (admin)
- `GET /api/users/{id}` - Get user details (admin)
- `PATCH /api/users/{id}` - Update user (admin)
- `DELETE /api/users/{id}` - Deactivate user (admin)
- `POST /api/users/{id}/activate` - Reactivate user (admin)
- `GET /api/users/roles` - Get available roles
- `GET /api/auth/me/full` - Current user with permissions
- `GET /api/auth/permissions` - Current user's permissions

**Components:**
- `PermissionGuard` - Conditional rendering based on permissions
- `AuthContext` with permission checking
- `Users` page - User management interface

**Technical:**
- `User` model with role enum
- Permission system with granular access control
- `has_permission()` utility function

---

## [0.2.0] - 2025-12-21

### Sprint 1.5: JSONCargo API Integration

**Features:**
- Live container tracking via JSONCargo API
- Webhook support for tracking event updates
- Container event history storage
- Real-time ETD/ETA updates

**API Endpoints:**
- `POST /api/tracking/subscribe/{shipment_id}` - Subscribe to container tracking
- `POST /api/webhooks/jsoncargo` - Tracking webhook callback

**Technical:**
- JSONCargo API client service
- `ContainerEvent` model for tracking history
- Webhook signature verification

---

## [0.1.0] - 2025-12-18

### Sprint 1: Backend Foundation

**Features:**
- Core data models for shipments and documents
- Document upload with file storage
- Basic authentication with JWT
- Docker containerization
- PostgreSQL database setup
- Health check endpoints
- Seed data script with real shipment example

**API Endpoints:**
- `POST /api/auth/login` - Get JWT token
- `GET /api/auth/me` - Current user info
- `GET /api/shipments` - List shipments
- `GET /api/shipments/{id}` - Shipment details
- `GET /api/shipments/{id}/documents` - List documents
- `GET /api/shipments/{id}/events` - Container events
- `GET /api/shipments/{id}/audit-pack` - Download ZIP audit pack
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/{id}` - Get document details
- `PATCH /api/documents/{id}` - Update document metadata

**Data Model:**
- `Shipment` - Container shipment with routing info
- `Document` - Attached compliance documents
- `ContainerEvent` - Tracking events
- `Product` - Cargo details
- `Party` - Shipper/consignee info
- `Origin` - Product origin for EUDR

**Technical:**
- FastAPI application structure
- SQLAlchemy ORM with PostgreSQL
- Pydantic schemas for validation
- Docker Compose deployment
- Nginx reverse proxy
- File upload handling

---

## Production Deployment

- **URL**: https://tracehub.vibotaj.com
- **Server**: Hostinger VPS (82.198.225.150)
- **Stack**: Docker Compose (Nginx + FastAPI + PostgreSQL)
- **CI/CD**: GitHub Actions with SSH deployment

---

## Document Types Supported

| Type | Description | Required For |
|------|-------------|--------------|
| `bill_of_lading` | Ocean B/L | All shipments |
| `commercial_invoice` | Commercial invoice | All shipments |
| `packing_list` | Packing list | All shipments |
| `certificate_of_origin` | Origin certificate | EUDR compliance |
| `phytosanitary_certificate` | Phyto cert | Agricultural products |
| `fumigation_certificate` | Fumigation cert | Some products |
| `quality_certificate` | Quality/inspection | Optional |
| `insurance_certificate` | Cargo insurance | Optional |
| `customs_declaration` | Export/import customs | All shipments |
| `contract` | Sales contract | EUDR compliance |
| `due_diligence_statement` | EUDR statement | EU imports |

---

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL 15
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Tracking API**: JSONCargo
