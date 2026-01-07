# TraceHub E2E Test Plan - Actor-Based User Journeys

**Date:** 7 January 2026  
**Framework:** Playwright + Node.js  
**Test Scope:** All 6 user roles across their distinct workflows  
**Database:** PostgreSQL (seeded with sample data)  

---

## Actor Analysis & User Journeys

### 1. **ADMIN** (`admin@vibotaj.com` / `tracehub2026`)
**Role:** Full system access, user/org management  
**Permissions:** All operations  

#### Journey: System Setup & User Management
```
Login → Create Organization → Invite Users → Manage Permissions → View Dashboard
        ↓
    Assign Roles: compliance, logistics_agent, buyer, supplier, viewer
```

**E2E Steps:**
1. Login with admin credentials
2. Navigate to Users/Organizations section
3. Create new organization or view existing ones
4. Invite users with specific roles
5. Verify role-based menu visibility
6. Check dashboard shows all organizations' data
7. Verify audit/activity log access

**Success Criteria:**
- Can invite users with all 5 role types
- Roles update permission menu immediately
- Dashboard shows cross-org data
- Activity log displays admin actions

---

### 2. **COMPLIANCE OFFICER** (`compliance@vibotaj.com` / `tracehub2026`)
**Role:** Document validation, approval authority  
**Permissions:** Validate & approve docs, reject with comments, view all shipments, recommend compliance status  

#### Journey: Document Review & Shipment Approval
```
Login → Dashboard (Pending Docs) → Open Shipment → Review Documents 
        ↓
    View Compliance Issues → Validate/Approve → Update Shipment Status
        ↓
    (Optional) Reject with Comments → Back to Logistics for correction
```

**E2E Steps:**
1. Login as compliance officer
2. View dashboard—see "Pending Documents" count
3. Click on shipment with pending docs (VIBO-2026-001)
4. Review document list (B/L, Invoice, etc.)
5. Check EUDR/Horn&Hoof compliance flags
6. Approve compliant documents
7. Check shipment moves to `docs_complete` status
8. View compliance summary updates
9. Download audit pack (if available)

**Success Criteria:**
- Can only validate/approve (not upload new docs)
- Document status changes from `UPLOADED` → `VALIDATED`
- Shipment status updates when all docs validated
- Comments saved if rejecting document
- Compliance status card shows green ✓

---

### 3. **LOGISTICS AGENT** (`31stcenturyglobalventures@gmail.com` / `Adeshola123!`)
**Role:** Shipment creation, all document uploads, tracking  
**Permissions:** Create shipments, upload any document type, manage shipments  

#### Journey: Create Shipment → Upload All Documents → Track Status
```
Login → Create Shipment → Add Product Details → Upload Documents
        ↓
    Assign Origin (Geolocation) → Submit for Compliance → Track Status
        ↓
    Monitor Container Tracking → Update Status as needed
```

**E2E Steps:**
1. Login as logistics agent
2. Navigate to "Create Shipment"
3. Fill shipment form:
   - Container number, B/L, vessel, voyage
   - Port of origin/destination
   - ETD/ETA dates
4. Add product details (name, HS code, quantity)
5. Add origin (geolocation, farm name, deforestation status)
6. Upload required documents:
   - Bill of Lading
   - Commercial Invoice
   - Packing List
   - Certificate of Origin
   - Origin Verification (if Horn&Hoof: EU TRACES + Veterinary)
7. Submit for compliance review
8. Monitor shipment status progression
9. View container tracking updates

**Success Criteria:**
- Can create shipment with all fields
- Can upload multiple document types
- Documents appear in "Pending Review" state
- Shipment moves to `docs_pending` → `docs_complete` → `in_transit`
- Cannot approve own documents (compliance only)

---

### 4. **BUYER** (`buyer@vibotaj.com` / `tracehub2026`)
**Role:** Read-only access to assigned shipments  
**Permissions:** View shipments, documents, compliance status; no edits  

#### Journey: Monitor Assigned Shipments & Compliance
```
Login → Dashboard (My Shipments) → Open Shipment → Review Status & Documents
        ↓
    Track Container Movement → View Compliance Summary → Check Metrics
```

**E2E Steps:**
1. Login as buyer
2. View dashboard—should only show assigned shipments
3. See shipment VIBO-2026-001 in list
4. Click to open shipment detail
5. View (but not edit):
   - Product details
   - Document list with statuses
   - Compliance status card
   - Container tracking timeline
6. View analytics for assigned shipments only
7. Cannot access Users, Organizations, or other buyers' shipments

**Success Criteria:**
- Dashboard only shows 1 shipment (the assigned one)
- All buttons are read-only (no Create, Upload, Approve)
- Can view all documents but cannot edit
- Compliance status visible
- Container tracking updates visible

---

### 5. **SUPPLIER** (`supplier@vibotaj.com` / `tracehub2026`)
**Role:** Upload origin certificates, provide geolocation  
**Permissions:** Upload origin documents, provide coordinates/photos  

#### Journey: Verify Origin & Upload Origin Certificate
```
Login → View Assigned Shipment → Upload Origin Certificate
        ↓
    Provide Geolocation (photos/coords) → Submit
        ↓
    Monitor Compliance Review
```

**E2E Steps:**
1. Login as supplier
2. See "My Shipments" (likely different list than buyer)
3. Click shipment assigned to supplier
4. Navigate to "Origin Verification" section
5. Upload origin certificate
6. Add geolocation data (coordinates, photos)
7. Submit for compliance review
8. View status change (maybe show "Pending Supplier Documents" on dashboard)

**Success Criteria:**
- Can upload origin-specific documents only
- Cannot upload B/L, invoices, etc.
- Geolocation data saved with images
- Compliance officer sees updated origin status

---

### 6. **VIEWER** (Read-only all data)
**Role:** Audit, reporting, analytics  
**Permissions:** View all shipments, documents, analytics; no actions  

#### Journey: Audit Trail & Reporting
```
Login → Dashboard (All Shipments) → Drill Down → View Compliance Reports
        ↓
    Generate/Download Reports → View Activity Log
```

**E2E Steps:**
1. Login as viewer
2. See all shipments in dashboard (unrestricted)
3. View analytics and metrics
4. Open any shipment and view details
5. View activity log / audit trail
6. All action buttons disabled (Create, Upload, Approve, etc.)
7. Generate compliance report
8. Download shipment export

**Success Criteria:**
- Can view all data but cannot perform any actions
- Analytics show all organizations' data
- Download/export available
- No edit/create buttons visible

---

## Test Data Setup

**Seed Data:** `tracehub/backend/seed_data.py`

### Shipment 1: VIBO-2026-001
- **Product:** Crushed Cow Hooves & Horns (HS 0506.90.00)
- **Route:** Lagos → Hamburg
- **Status:** `IN_TRANSIT`
- **Documents:** B/L, Invoice (already validated by compliance)
- **Origin:** TEMIRA Lagos Hub (geolocation: 6.4541°N, 3.3947°E)

### Test Users Pre-Seeded
| Role | Email | Password | Org |
|------|-------|----------|-----|
| Admin | admin@vibotaj.com | tracehub2026 | VIBOTAJ |
| Compliance | compliance@vibotaj.com | tracehub2026 | VIBOTAJ |
| Logistics Agent | 31stcenturyglobalventures@gmail.com | Adeshola123! | VIBOTAJ |
| Buyer | buyer@vibotaj.com | tracehub2026 | VIBOTAJ |
| Supplier | supplier@vibotaj.com | tracehub2026 | VIBOTAJ |
| Viewer | (to be created) | - | - |

---

## Test Execution Environment

### Local Setup
```bash
# Start Docker Compose stack
cd tracehub
docker-compose up -d

# Wait for services
sleep 10 && docker-compose exec backend python -m seed_data

# Access
Frontend: http://localhost:80 (or http://localhost:3000 if dev)
API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

### Playwright Configuration
- **Browser:** Chromium (headless or headed for debugging)
- **Base URL:** http://localhost:80
- **Timeout:** 30s per action
- **Screenshots:** On failure
- **Video:** Optional (can enable for debugging)

---

## Test Coverage Matrix

| Actor | Login | Dashboard | View Shipment | Upload Doc | Approve Doc | Edit Shipment | View Analytics | Create Shipment | Create Org | Manage Users |
|-------|:-----:|:---------:|:-------------:|:----------:|:-----------:|:-------------:|:--------------:|:---------------:|:----------:|:------------:|
| **Admin** | ✅ | ✅ (all) | ✅ | ❌ | ❌ | ❌ | ✅ (all) | ❌ | ✅ | ✅ |
| **Compliance** | ✅ | ✅ (all) | ✅ | ❌ | ✅ | ❌ | ✅ (all) | ❌ | ❌ | ❌ |
| **Logistics** | ✅ | ✅ (assigned) | ✅ | ✅ | ❌ | ✅ | ✅ (assigned) | ✅ | ❌ | ❌ |
| **Buyer** | ✅ | ✅ (assigned) | ✅ | ❌ | ❌ | ❌ | ✅ (assigned) | ❌ | ❌ | ❌ |
| **Supplier** | ✅ | ✅ (assigned) | ✅ | ✅ (origin only) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Viewer** | ✅ | ✅ (all) | ✅ | ❌ | ❌ | ❌ | ✅ (all) | ❌ | ❌ | ❌ |

---

## Success Criteria

### Per Test
- ✅ No JavaScript console errors
- ✅ All expected elements render
- ✅ Permission checks enforce (e.g., buttons hidden/disabled)
- ✅ Data persists (DB verified via API)
- ✅ Status transitions correct
- ✅ UI updates reflect backend state

### Overall
- ✅ All 6 actor journeys executable without failure
- ✅ No permission bypass vulnerabilities
- ✅ Role-based menu visibility correct
- ✅ Cross-org data isolation maintained
- ✅ Performance: <3s page load, <10s upload

---

## Next Steps

1. **Set up Playwright project** in `tracehub/frontend/e2e/` directory
2. **Implement test cases** for each actor (6 main tests)
3. **Add helper functions** for login, navigation, data verification
4. **Run locally** with Docker Compose
5. **Integrate into CI/CD** (integration-tests.yml)
6. **Run nightly** on staging

