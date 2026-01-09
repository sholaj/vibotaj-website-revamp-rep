# TraceHub AI Agent Instructions

> Container tracking & compliance platform for VIBOTAJ agro-exports  
> **Stack:** FastAPI (Python 3.11) + React 18 (TypeScript) + PostgreSQL

## Critical Business Rules

### EUDR Compliance - READ FIRST

**Horn & Hoof (HS 0506/0507) = NOT covered by EUDR**

NEVER add geolocation, deforestation statements, or EUDR risk scores to horn/hoof products. Check [docs/COMPLIANCE_MATRIX.md](../docs/COMPLIANCE_MATRIX.md) before any compliance work. Function reference: `is_eudr_required(hs_code: str)` validates this.

## Project Structure

### Backend (tracehub/backend/)

- FastAPI application with PostgreSQL database
- Key modules:
  - `auth/`: JWT authentication, user roles
  - `routers/`: API endpoints (auth, shipments, documents, tracking, etc.)
  - `models/`: SQLAlchemy ORM models (User, Shipment, Document, Organization, etc.)
  - `services/`: Business logic (permissions, org_permissions, document_classifier)
  - `schemas/`: Pydantic request/response validation
  - `middleware/`: Request tracking, rate limiting, error handling
  - `compliance/`: EUDR validation, HS code checks
  - `notifications/`: Email alerts (planned - not yet implemented)
- Alembic for database migrations ([tracehub/backend/alembic/](../tracehub/backend/alembic/))

### Frontend (tracehub/frontend/)

- React 18 with TypeScript + TailwindCSS
- Key components:
  - `AuthContext`: Manages JWT tokens and user sessions
  - `Dashboard`: Overview of shipments and compliance status
  - `ShipmentDetails`: Document upload and tracking info
  - `ComplianceWizard`: Guides users through document requirements
- **Server State Management:** React Query for server state caching and synchronization
- **Client State:** AuthContext (JWT tokens, user info); minimal additional global state

## Development Workflow

1. **Setup Environment:** Follow [tracehub/README.md](../tracehub/README.md) for local Docker setup
2. **Branching:** Use feature branches named `feature/xyz` or `bugfix/abc`
3. **Database Migrations:** See [Alembic Migration Patterns](#alembic-migration-patterns) below
4. **Testing:** Write tests in `tests/` directories; run with `pytest` (backend) and `vitest` (frontend)
5. **Code Style:** Follow PEP 8 (Python) and Airbnb style guide (TypeScript)
6. **Pull Requests:** Create PRs with clear descriptions; link to relevant issues
7. **Pre-commit Hooks:** Run `make test && make lint` before committing; never commit secrets

## Alembic Migration Patterns

### Creating Migrations

```bash
# After model changes, auto-generate migration
cd tracehub/backend
alembic revision --autogenerate -m "descriptive message"

# Always review generated migration in alembic/versions/
# Edit if needed - autogenerate can miss relationships, constraints, etc.
```

### Running Migrations

```bash
# Apply all pending migrations
make db-migrate

# Rollback last migration
make db-rollback

# Inspect current database schema
make db-shell
```

### Common Patterns

- **Adding column:** Include `nullable=True` initially, then create separate migration to make non-nullable
- **Foreign keys:** Use `ForeignKey("table.column", ondelete="CASCADE")` to handle cascading deletes
- **Enums:** PostgreSQL enums are type-safe but migrations need special handling (see existing patterns in [alembic/versions/](../tracehub/backend/alembic/versions/))
- **Indexes:** Add indexes for frequently queried fields (email, organization_id, shipment_id)
- **Always test locally:** Run `make test` before committing to catch migration issues

### Pitfalls to Avoid

- Don't modify models without generating corresponding migrations
- Don't skip data migrations for non-nullable column additions
- Migrations must be idempotent (safe to run multiple times)
- Test rollbacks locally: `make db-rollback` then re-apply

## Authentication & Permissions

### Role Hierarchy

1. **admin**: Full system access
2. **compliance**: Validate/approve documents, view all shipments
3. **logistics_agent**: Create shipments, upload all documents
4. **buyer**: Read-only access to assigned shipments
5. **supplier**: Upload origin certificates only
6. **viewer**: Read-only access to all data

### Multi-Tenancy

- Organization-scoped permissions via `OrganizationMembership` model
- Check [tracehub/backend/app/services/org_permissions.py](../tracehub/backend/app/services/org_permissions.py) for org-level RBAC
- Users belong to primary organization; can have memberships in multiple orgs

## External Integrations

- **Container Tracking API:** JSCargo (not ShipsGo/Vizion) - webhook-based events for live tracking
- **Document Classification:** Anthropic Claude API for intelligent document type detection
- **Notifications:** Email/SMS features planned but not yet implemented

## Key Workflows & Commands

### Essential Makefile Commands (run from tracehub/)

```bash
make dev              # Start local environment
make test             # Run backend tests (isolated Docker)
make test-frontend    # Run frontend tests (Vitest)
make db-migrate       # Apply Alembic migrations
make db-backup        # Create database backup
make prod-up          # Start production stack
```

### GitOps Deployment Pipeline

```
feature/* → develop (staging auto-deploys) → main (production auto-deploys)
```

Never push directly to `main`; always verify on staging first.

## Key Documentation

- [CLAUDE.md](../CLAUDE.md) - Project context & business rules
- [docs/COMPLIANCE_MATRIX.md](../docs/COMPLIANCE_MATRIX.md) - HS codes & required documents
- [docs/architecture/tracehub-architecture.md](../docs/architecture/tracehub-architecture.md) - Full system design
- [tracehub/README.md](../tracehub/README.md) - Quick start guide
- [tracehub/TESTING.md](../tracehub/TESTING.md) - Testing strategy & CI/CD
- [tracehub/DEPLOYMENT.md](../tracehub/DEPLOYMENT.md) - Hostinger VPS setup & SSL

## Notes

- Container tracking uses **JSCargo APIs** for live container events
- Document classification leverages **Anthropic Claude AI**
- Email/SMS notification features are planned but **not yet implemented**
- 163 backend tests with 100% pass rate (see [tracehub/TESTING.md](../tracehub/TESTING.md))
- CI/CD: GitHub Actions auto-deploys from develop (staging) and main (production)
