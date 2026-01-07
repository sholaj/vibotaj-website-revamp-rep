# TraceHub Local Build & Login Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend dev if not using Docker)
- Git

### 1. Start All Services

```bash
cd /path/to/tracehub

# Spin up DB, Backend, Frontend
docker-compose up -d

# Wait 10-15 seconds for services to be ready
sleep 15

# Seed database with test data
docker-compose exec backend python -m seed_data

# Verify services are running
docker-compose ps
```

**Expected Output:**
```
NAME                   STATUS           PORTS
tracehub-backend-1     Up (healthy)     0.0.0.0:8000->8000/tcp
tracehub-frontend-1    Up               0.0.0.0:80->80/tcp
tracehub-db-1          Up (healthy)     0.0.0.0:5433->5432/tcp
```

---

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:80 | Login & app UI |
| **API Docs** | http://localhost:8000/docs | Swagger docs (helpful for debugging) |
| **Database** | localhost:5433 | Direct DB access (if needed) |

---

## Test User Credentials

Use these accounts to test different role journeys:

| Role | Email | Password | Expected Access |
|------|-------|----------|-----------------|
| **ADMIN** | admin@vibotaj.com | tracehub2026 | Full system (users, orgs, all data) |
| **COMPLIANCE OFFICER** | compliance@vibotaj.com | tracehub2026 | Document validation, approval, all shipments |
| **LOGISTICS AGENT** | 31stcenturyglobalventures@gmail.com | Adeshola123! | Create shipments, upload docs, manage tracking |
| **BUYER** | buyer@vibotaj.com | tracehub2026 | Read-only on assigned shipments |
| **SUPPLIER** | supplier@vibotaj.com | tracehub2026 | Upload origin certificates, geolocation |
| **VIEWER** | (create in UI) | - | Read-only audit & analytics |

---

## Test Shipment Data

**Shipment ID:** `VIBO-2026-001`  
**Product:** Crushed Cow Hooves & Horns  
**HS Code:** 0506.90.00  
**Route:** Lagos (Apapa) → Hamburg  
**Status:** IN_TRANSIT  
**Container:** MRSU3452572  
**Vessel:** MSC Gulsun  

**Documents Included:**
- Bill of Lading #262495038
- Commercial Invoice REF-1416
- Packing List
- Certificate of Origin

---

## User Journey Examples

### Example 1: Login as Logistics Agent → Create & Track Shipment
1. Open http://localhost:80
2. Click "Login"
3. Enter: `31stcenturyglobalventures@gmail.com` / `Adeshola123!`
4. Navigate to **Create Shipment**
5. Fill form with B/L, Container #, Ports, Product details
6. Upload Bill of Lading & Invoice
7. Submit for compliance review
8. Watch status transition to "Pending Documents"

### Example 2: Login as Compliance → Review & Approve Documents
1. Open http://localhost:80
2. Click "Login"
3. Enter: `compliance@vibotaj.com` / `tracehub2026`
4. View dashboard—see "Pending Documents" count
5. Click on shipment
6. Review each document (check for EUDR/compliance flags)
7. Click "Approve" on each document
8. Shipment moves to "Documents Complete"

### Example 3: Login as Buyer → View Assigned Shipment (Read-Only)
1. Open http://localhost:80
2. Login: `buyer@vibotaj.com` / `tracehub2026`
3. Dashboard shows only assigned shipment(s)
4. Click shipment to view details
5. View documents, compliance status, tracking
6. **No edit/upload buttons visible**

---

## Debugging & Troubleshooting

### Backend Logs
```bash
docker-compose logs -f backend
```

### Frontend Logs
```bash
docker-compose logs -f frontend
```

### Database Connection Issues
```bash
# Check if DB is running
docker-compose ps db

# Access DB directly (if needed)
docker-compose exec db psql -U tracehub -d tracehub
```

### Reset Database
```bash
# Stop and remove volumes
docker-compose down -v

# Restart with fresh data
docker-compose up -d
sleep 15
docker-compose exec backend python -m seed_data
```

### Clear Cache & Rebuild
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
sleep 15
docker-compose exec backend python -m seed_data
```

---

## Performance Tips

- **First load slow?** Browser may be downloading ~3MB of frontend bundle. Subsequent loads cached.
- **API calls timeout?** Check if backend is still starting: `docker-compose logs backend | grep "Application startup complete"`
- **Database locked?** Another test may still be writing. Wait 5s and retry.

---

## CI/CD Integration

Once tests are written (Playwright in `e2e/`), the full stack is validated in GitHub Actions:

```yaml
# .github/workflows/integration-tests.yml
- Run: docker-compose up -d
- Run: seed database
- Run: playwright test
```

Tests must pass on all PRs to feature/* branches before merge to `develop`.

---

## Next: Run E2E Tests

See `E2E_TEST_PLAN.md` for comprehensive actor-based test design.

Once you're comfortable with the UI, run:

```bash
# Install Playwright (one time)
cd tracehub/frontend
npm install -D @playwright/test

# Run tests locally
npx playwright test --headed  # see browser
npx playwright test --ui      # interactive UI mode
```

