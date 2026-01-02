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

### 5. Login Credentials (POC)

- **Username**: `demo`
- **Password**: `tracehub2026`

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

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/shipments/{id}` | Shipment details |
| GET | `/api/shipments/{id}/documents` | List documents |
| POST | `/api/documents/upload` | Upload document |
| GET | `/api/shipments/{id}/events` | Container events |
| GET | `/api/shipments/{id}/audit-pack` | Download ZIP |
| POST | `/api/tracking/subscribe/{id}` | Subscribe to Vizion |
| POST | `/api/webhooks/vizion` | Tracking webhook |

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
| `VIZION_API_KEY` | Vizion API key for tracking | (empty - mock mode) |
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

## Sprint Progress

- [x] **Sprint 1**: Backend foundation, models, Docker setup
- [ ] **Sprint 2**: Vizion API integration
- [ ] **Sprint 3**: React frontend
- [ ] **Sprint 4**: Audit pack, polish

## License

Proprietary - VIBOTAJ Global Nigeria Ltd
