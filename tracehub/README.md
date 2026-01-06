# TraceHub POC

Container tracking and documentation compliance platform for VIBOTAJ agro-exports.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend, coming in Sprint 3)

### 1. Start the Database

```bash
# Start PostgreSQL
docker-compose up -d db

# Wait for it to be healthy
docker-compose ps
```

### 2. Run the Backend

**Option A: Using Docker (recommended)**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

**Option B: Local development**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 3. Seed Sample Data

```bash
# With Docker
docker-compose exec backend python -m seed_data

# Or locally
cd backend
python -m seed_data
```

### 4. Access the API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 5. Login Credentials

**Production URL**: https://tracehub.vibotaj.com

**Users with role-based access:**

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| Admin | admin@vibotaj.com | tracehub2026 | Full system access |
| Compliance | compliance@vibotaj.com | tracehub2026 | Document validation & approval |
| Logistics Agent | 31stcenturyglobalventures@gmail.com | Adeshola123! | Create shipments, upload all documents |
| Buyer | buyer@vibotaj.com | tracehub2026 | Read-only access to assigned shipments |
| Supplier | supplier@vibotaj.com | tracehub2026 | Upload origin certificates |
| Viewer | (none seeded) | - | Read-only access to all data |

### 6. Real Shipment Data (POC)

The seed script creates data from an actual shipment:
- **Container**: MRSU3452572
- **B/L**: 262495038 (Maersk)
- **Vessel**: RHINE MAERSK / Voyage 550N
- **Route**: Apapa, Lagos → Hamburg
- **Cargo**: 25,000 KGS Crushed Cow Hooves & Horns
- **Shipper**: TEMIRA INDUSTRIES NIGERIA LTD
- **Consignee**: WITATRADE GMBH (Germany)

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/auth/me/full` | Current user with permissions |
| GET | `/api/auth/permissions` | Current user's permissions |

### Shipments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shipments` | List all shipments |
| POST | `/api/shipments` | Create shipment (admin, logistics_agent) |
| GET | `/api/shipments/{id}` | Shipment details |
| GET | `/api/shipments/{id}/documents` | List documents |
| GET | `/api/shipments/{id}/events` | Container events |
| GET | `/api/shipments/{id}/audit-pack` | Download ZIP audit pack |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload document |
| GET | `/api/documents/{id}` | Get document details |
| PATCH | `/api/documents/{id}` | Update document metadata |
| POST | `/api/documents/{id}/validate` | Validate document (compliance) |
| POST | `/api/documents/{id}/approve` | Approve document (compliance) |
| POST | `/api/documents/{id}/reject` | Reject document (compliance) |

### Users (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List users |
| POST | `/api/users` | Create user |
| GET | `/api/users/{id}` | Get user details |
| PATCH | `/api/users/{id}` | Update user |
| DELETE | `/api/users/{id}` | Deactivate user |
| POST | `/api/users/{id}/activate` | Reactivate user |
| GET | `/api/users/roles` | Get available roles |

### Tracking (JSONCargo Integration)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tracking/subscribe/{id}` | Subscribe to container tracking |
| POST | `/api/webhooks/jsoncargo` | Tracking webhook callback |

## Project Structure

```
tracehub/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Settings
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # API endpoints
│   │   └── services/         # Business logic
│   ├── seed_data.py          # Sample data script
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # React app (Sprint 3)
├── docker-compose.yml
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://tracehub:tracehub@localhost:5432/tracehub` |
| `JSONCARGO_API_KEY` | JSONCargo API key for container tracking | (empty - mock mode) |
| `JWT_SECRET` | Secret for JWT tokens | Change in production! |
| `DEBUG` | Enable debug mode | `true` |

## Development

### Running Tests

```bash
cd backend
pytest
```

### Database Migrations (when schema changes)

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## User Roles & Permissions

TraceHub implements role-based access control (RBAC) with six roles:

| Role | Level | Description | Key Permissions |
|------|-------|-------------|-----------------|
| **Admin** | 5 | Full system access | All permissions including user management |
| **Compliance** | 4 | Document validation | Validate, approve, reject documents; view all |
| **Logistics Agent** | 3 | Shipment operations | Create shipments, upload all documents |
| **Buyer** | 2 | Customer access | View assigned shipments and documents |
| **Supplier** | 2 | Origin data provider | Upload origin certificates, geolocation |
| **Viewer** | 1 | Read-only access | View shipments and documents |

## Data Model

### Key Entities

```
Shipment
├── reference (unique identifier)
├── container_number
├── bl_number (Bill of Lading)
├── vessel_name, voyage_number
├── pol_name, pod_name (Port of Loading/Discharge)
├── etd, eta, atd, ata (dates)
├── status (in_transit, at_port, delivered, etc.)
└── Documents[]

Document
├── document_type (bill_of_lading, commercial_invoice, etc.)
├── document_types[] (JSONB - for combined PDFs with multiple docs)
├── status (draft, uploaded, validated, approved, etc.)
├── file_path, file_name, mime_type
├── reference_number, issue_date, expiry_date
├── uploaded_by, validated_by
└── Shipment (FK)

User
├── email (unique)
├── role (admin, compliance, logistics_agent, buyer, supplier, viewer)
├── full_name
├── is_active
└── hashed_password
```

## Sprint Progress

- [x] **Sprint 1**: Backend foundation, models, Docker setup
- [x] **Sprint 1.5**: JSONCargo API integration (live container tracking)
- [x] **Sprint 2**: Role-based access control & multi-user support
  - User model with 6 roles (admin, compliance, logistics_agent, buyer, supplier, viewer)
  - Permission system with granular access control
  - User CRUD endpoints (admin only)
  - JWT tokens include role information
  - Frontend AuthContext with permission checking
  - PermissionGuard component for UI access control
  - User management page
- [x] **Sprint 3**: Document workflow engine
  - Document lifecycle states (draft → uploaded → validated → approved)
  - Validation service with field requirements
  - Transition permissions per role
  - Notifications on document events
- [x] **Sprint 4**: EUDR compliance & analytics
  - EUDR status tracking per shipment
  - Analytics dashboard with charts
  - Multi-type document support (single PDF with multiple document types)
- [x] **Sprint 5**: Historical data & logistics agent workflow
  - Shipment creation endpoint for historical trades
  - Logistics agent role with full document upload permissions

## Production Deployment

- **URL**: https://tracehub.vibotaj.com
- **Server**: Hostinger VPS (82.198.225.150)
- **Stack**: Docker Compose (Nginx + FastAPI + PostgreSQL)
- **CI/CD**: GitHub Actions with SSH deployment

For detailed deployment instructions, see [docs/deployment/](docs/deployment/).

## Documentation

Complete documentation is organized in the `docs/` directory:

- **[Documentation Index](docs/INDEX.md)** - Complete navigation guide
- **[Deployment](docs/deployment/)** - Infrastructure and deployment guides
- **[DevOps](docs/devops/)** - CI/CD, automation, and GitOps
- **[Frontend](docs/frontend/)** - UI/UX specifications and components
- **[Architecture](docs/architecture/)** - System architecture and ADRs
- **[Strategy](docs/strategy/)** - Product roadmap and planning
- **[API Specs](docs/api/)** - API specifications
- **[Sprint Archives](docs/sprints/)** - Historical sprint documentation

### Quick Links

- **Getting Started:** [QUICKSTART.md](QUICKSTART.md)
- **Deployment:** [docs/deployment/DEPLOYMENT_QUICK_REFERENCE.md](docs/deployment/DEPLOYMENT_QUICK_REFERENCE.md)
- **Architecture:** [docs/architecture/tracehub-detailed-architecture.md](docs/architecture/tracehub-detailed-architecture.md)
- **Version History:** [CHANGELOG.md](CHANGELOG.md)

## License

Proprietary - VIBOTAJ Global Nigeria Ltd
