# VIBOTAJ TraceHub POC Implementation Plan

## Single-Shipment TraceHub Slice

**Version:** 1.0
**Date:** January 2026
**Duration:** 2-3 Weeks (4 Sprints)
**Status:** Planning

---

## Executive Summary

This POC demonstrates the TraceHub concept using ONE real shipment (hooves or pellets to Germany) to validate the platform's core value proposition: unified container tracking and compliance documentation visibility.

### Primary Objective

Prove that VIBOTAJ can deliver a single-screen experience where:
- All core documents and container events are visible together
- An audit-ready bundle is exportable with one click
- A non-technical user can answer key questions within 30 seconds:
  - "Where is my container now and when will it arrive?"
  - "Do you have all required documents and are there any compliance gaps?"

---

## POC Scope Definition

### In Scope

| Component | Description |
|-----------|-------------|
| Single shipment | One real hooves or pellets shipment to Germany |
| Container tracking | Read-only API integration with one provider |
| Document management | Upload, storage, and status tracking |
| Compliance model | EUDR and standard export document requirements |
| Web interface | Authenticated view for buyers/internal users |
| Audit export | ZIP bundle with PDF index and all documents |

### Out of Scope (Deferred to Phase 2+)

- Multiple shipments/batch views
- Supplier-side upload portal
- AI-powered validation (hooks only, no implementation)
- Multi-tenant architecture (design only, no implementation)
- WordPress integration (standalone POC UI)
- Mobile-responsive design
- Email/notification system
- User management/roles

---

## POC Deliverables

### 1. Data Model and Database Setup

**Objective:** Capture all metadata for one real shipment in a structured, documented schema.

#### Shipment Entity
```
shipment
├── id (UUID)
├── reference_number (VIBO-2026-XXX)
├── container_number
├── bl_number (Bill of Lading)
├── booking_reference
├── vessel_name
├── voyage_number
├── etd (Estimated Time of Departure)
├── eta (Estimated Time of Arrival)
├── pol (Port of Loading)
├── pod (Port of Discharge)
├── final_destination
├── incoterms (FOB/CIF/etc.)
├── status (enum: created, docs_pending, docs_complete, in_transit, arrived, delivered)
├── created_at
├── updated_at
```

#### Product Entity
```
product
├── id (UUID)
├── shipment_id (FK)
├── hs_code
├── description
├── quantity_net_kg
├── quantity_gross_kg
├── packaging_type
├── packaging_count
├── batch_lot_number
├── quality_grade
├── moisture_percentage (nullable)
├── production_date
```

#### Origin Entity (EUDR Compliance)
```
origin
├── id (UUID)
├── product_id (FK)
├── farm_plot_identifier
├── geolocation_lat
├── geolocation_lng
├── geolocation_polygon (GeoJSON, nullable)
├── country
├── region
├── production_start_date
├── production_end_date
├── supplier_id (FK)
├── deforestation_cutoff_compliant (boolean)
├── due_diligence_statement_ref
```

#### Party Entity
```
party
├── id (UUID)
├── type (enum: supplier, buyer, shipper, consignee, notify_party)
├── company_name
├── contact_name
├── email
├── phone
├── address
├── country
├── registration_number
├── tax_id
```

#### Document Entity
```
document
├── id (UUID)
├── shipment_id (FK)
├── document_type (enum: see below)
├── file_name
├── file_path
├── file_size_bytes
├── mime_type
├── status (enum: draft, uploaded, validated, compliance_checked, linked, archived)
├── required (boolean)
├── expiry_date (nullable)
├── issue_date
├── issuing_authority
├── reference_number
├── validation_notes
├── uploaded_by
├── uploaded_at
├── validated_at
├── validated_by
```

**Document Types:**
- `bill_of_lading`
- `commercial_invoice`
- `packing_list`
- `certificate_of_origin`
- `phytosanitary_certificate`
- `fumigation_certificate`
- `sanitary_certificate`
- `insurance_certificate`
- `customs_declaration`
- `contract`
- `eudr_due_diligence_statement`
- `quality_certificate`
- `other`

#### Container Event Entity
```
container_event
├── id (UUID)
├── shipment_id (FK)
├── event_type (enum: loaded, departed, transshipment, arrived, discharged, delivered)
├── event_timestamp
├── location_name
├── location_code (UN/LOCODE)
├── location_lat
├── location_lng
├── vessel_name
├── voyage_number
├── delay_hours (nullable)
├── source (api_provider_name)
├── raw_payload (JSONB)
├── created_at
```

#### Required Documents Matrix

| Document Type | Hooves to Germany | Pellets to Germany |
|--------------|-------------------|-------------------|
| Bill of Lading | Required | Required |
| Commercial Invoice | Required | Required |
| Packing List | Required | Required |
| Certificate of Origin | Required | Required |
| Phytosanitary Certificate | Required | Required |
| Fumigation Certificate | Conditional | Conditional |
| Sanitary Certificate | Required | Not Required |
| Insurance Certificate | Required | Required |
| EUDR Due Diligence Statement | Required (from Dec 2026) | Required (from Dec 2026) |
| Quality Certificate | Recommended | Recommended |

---

### 2. Container Tracking API Integration

**Objective:** Integrate with ONE tracking API in read-only mode to pull container status and events.

#### Recommended Provider: Vizion API

**Rationale:**
- Developer tier includes 15 containers/month free
- REST API with JSON responses
- Webhook support for real-time updates
- 99% global ocean freight coverage
- Auto carrier identification feature

**Alternative Provider:** ShipsGo
- 3 free trial credits
- $1.82/container after trial
- Unlimited API calls included
- Good documentation

#### Integration Specification

**Endpoints to Implement:**

1. **Subscribe Container**
   - Input: Container number, carrier code (optional with auto-ID)
   - Output: Subscription confirmation, initial status

2. **Get Container Status**
   - Input: Container number or subscription ID
   - Output: Current status, location, ETA, vessel info

3. **Webhook Receiver**
   - Events: Container milestone updates
   - Action: Persist to container_event table, update shipment ETA

**Data Mapping:**

| API Field | Database Field |
|-----------|---------------|
| container_id | shipment.container_number |
| status | container_event.event_type |
| timestamp | container_event.event_timestamp |
| location.name | container_event.location_name |
| location.coordinates | container_event.location_lat/lng |
| vessel.name | container_event.vessel_name |
| eta | shipment.eta |
| delays | container_event.delay_hours |

**Error Handling:**
- API unavailable: Show last known status with timestamp
- Container not found: Display "Tracking pending" status
- Rate limits: Queue requests, implement exponential backoff

---

### 3. Document Lifecycle Implementation

**Objective:** Implement state machine for documents and shipments with visual indicators.

#### Document State Machine

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                                                         │
                    v                                                         │
┌──────────┐    ┌──────────┐    ┌────────────┐    ┌────────────────┐    ┌─────────┐
│  DRAFT   │───>│ UPLOADED │───>│ VALIDATED  │───>│ COMPLIANCE_OK  │───>│ LINKED  │
└──────────┘    └──────────┘    └────────────┘    └────────────────┘    └─────────┘
                    │                │                    │                   │
                    │                │                    │                   │
                    v                v                    v                   v
              ┌──────────┐    ┌────────────┐    ┌────────────────┐    ┌─────────┐
              │ REJECTED │    │ VALIDATION │    │ COMPLIANCE     │    │ARCHIVED │
              │          │    │ FAILED     │    │ FAILED         │    │         │
              └──────────┘    └────────────┘    └────────────────┘    └─────────┘
```

**State Transitions:**

| From | To | Trigger | Conditions |
|------|-----|---------|------------|
| draft | uploaded | File attached | File present, valid format |
| uploaded | validated | Manual validation | All required fields present |
| uploaded | rejected | Manual rejection | Invalid document |
| validated | compliance_checked | Compliance review | Meets regulatory requirements |
| validated | validation_failed | Re-review | Missing fields discovered |
| compliance_checked | linked | Link to shipment | Shipment exists, doc complete |
| linked | archived | Shipment delivered | Shipment status = delivered |

#### Shipment State Machine

```
┌─────────┐    ┌─────────────┐    ┌──────────────┐    ┌────────────┐    ┌─────────┐    ┌───────────┐
│ CREATED │───>│ DOCS_PENDING│───>│ DOCS_COMPLETE│───>│ IN_TRANSIT │───>│ ARRIVED │───>│ DELIVERED │
└─────────┘    └─────────────┘    └──────────────┘    └────────────┘    └─────────┘    └───────────┘
```

**State Transitions:**

| From | To | Trigger |
|------|-----|---------|
| created | docs_pending | First document uploaded |
| docs_pending | docs_complete | All required documents linked |
| docs_complete | in_transit | Container departed event received |
| in_transit | arrived | Container arrived at POD |
| arrived | delivered | Container discharged/delivered |

#### Compliance Checklist

For each shipment, display:

```
DOCUMENT COMPLIANCE STATUS
==========================
[X] Bill of Lading - Validated
[X] Commercial Invoice - Validated
[X] Packing List - Validated
[X] Certificate of Origin - Validated
[X] Phytosanitary Certificate - Validated
[ ] Fumigation Certificate - MISSING (Required)
[X] Sanitary Certificate - Validated
[X] Insurance Certificate - Uploaded (Pending Validation)
[ ] EUDR Due Diligence - MISSING (Required from Dec 2026)

Status: 7/9 Documents Complete
Compliance: NOT READY (2 documents missing)
```

---

### 4. Simple Authenticated Web View

**Objective:** Provide a single-screen view for shipment status and document completeness.

#### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend API | Node.js + Express OR Python + FastAPI | Fast development, good ecosystem |
| Database | PostgreSQL | Robust, supports JSONB, production-ready |
| Frontend | React SPA (Vite) | Simple, fast build, easy deployment |
| Authentication | JWT + simple email/password | POC-appropriate security |
| File Storage | Local filesystem (POC) | Simplest option for POC |
| Deployment | Docker Compose | Easy local development and deployment |

#### UI Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  VIBOTAJ TraceHub                                    [User] [Logout]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SHIPMENT: VIBO-2026-001                                               │
│  ═══════════════════════════════════════════════════════════════════   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  CONTAINER STATUS                                               │   │
│  │  ─────────────────                                              │   │
│  │  Container: MSCU1234567                                         │   │
│  │  Status: IN TRANSIT                                             │   │
│  │  Last Event: Departed Port Said (Jan 5, 2026 14:30 UTC)        │   │
│  │  Current Location: Mediterranean Sea                            │   │
│  │  ETA Hamburg: January 15, 2026                                  │   │
│  │  Vessel: MSC OSCAR, Voyage 2601E                                │   │
│  │  Delays: None                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  SHIPMENT DETAILS                                               │   │
│  │  ────────────────                                               │   │
│  │  Product: Dried Cattle Hooves (HS 0506.90)                      │   │
│  │  Quantity: 18,000 kg net (20,000 kg gross)                      │   │
│  │  Origin: Nigeria, Kano State                                    │   │
│  │  Buyer: [German Company Name]                                   │   │
│  │  Incoterms: FOB Lagos                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  DOCUMENTS (7/9 Complete)                              [Upload] │   │
│  │  ─────────────────────────                                      │   │
│  │  [X] Bill of Lading            BL-2026-001       [View] [Down]  │   │
│  │  [X] Commercial Invoice        INV-2026-001      [View] [Down]  │   │
│  │  [X] Packing List              PL-2026-001       [View] [Down]  │   │
│  │  [X] Certificate of Origin     COO-2026-001      [View] [Down]  │   │
│  │  [X] Phytosanitary Cert        PHY-2026-001      [View] [Down]  │   │
│  │  [ ] Fumigation Cert           MISSING           [Upload]       │   │
│  │  [X] Sanitary Certificate      SAN-2026-001      [View] [Down]  │   │
│  │  [X] Insurance Certificate     INS-2026-001      [View] [Down]  │   │
│  │  [ ] EUDR Due Diligence        MISSING           [Upload]       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  COMPLIANCE STATUS                                              │   │
│  │  ─────────────────                                              │   │
│  │  [!] WARNING: 2 required documents missing                      │   │
│  │      - Fumigation Certificate (required for animal products)    │   │
│  │      - EUDR Due Diligence Statement (required from Dec 2026)    │   │
│  │                                                                 │   │
│  │  EUDR Status: Post-cutoff compliant (Production: March 2025)   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  CONTAINER TIMELINE                                             │   │
│  │  ──────────────────                                             │   │
│  │  [X] Jan 02 - Loaded at Lagos Terminal                          │   │
│  │  [X] Jan 03 - Departed Lagos                                    │   │
│  │  [X] Jan 05 - Departed Port Said (Transshipment)                │   │
│  │  [ ] Jan 15 - ETA Hamburg (Expected)                            │   │
│  │  [ ] Jan 16 - Discharge Hamburg (Expected)                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │          [ DOWNLOAD AUDIT PACK ]                                │   │
│  │          (ZIP with all documents + shipment summary PDF)        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Audit Pack Contents

The "Download Audit Pack" button generates a ZIP file containing:

```
VIBO-2026-001-audit-pack.zip
├── 00-SHIPMENT-INDEX.pdf          # Generated summary document
├── 01-bill-of-lading.pdf
├── 02-commercial-invoice.pdf
├── 03-packing-list.pdf
├── 04-certificate-of-origin.pdf
├── 05-phytosanitary-certificate.pdf
├── 06-sanitary-certificate.pdf
├── 07-insurance-certificate.pdf
├── container-tracking-log.json    # All container events
└── metadata.json                  # Machine-readable shipment data
```

**SHIPMENT-INDEX.pdf Contents:**
- Shipment reference and summary
- Container tracking history
- Document checklist with status
- EUDR compliance statement
- Key parties (supplier, buyer, shipper)
- Product details and origin information

---

## Technical Approach

### Backend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│                   http://localhost:3000                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ REST API
                              v
┌─────────────────────────────────────────────────────────────┐
│                      Backend (Node/Python)                   │
│                   http://localhost:8000                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Auth Module  │  │ Shipment API │  │ Document API     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Tracking     │  │ Audit Export │  │ Webhook Handler  │  │
│  │ Service      │  │ Service      │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              v               v               v
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│   PostgreSQL     │  │ File Storage │  │ Vizion API   │
│   Database       │  │ (Local/S3)   │  │ (External)   │
└──────────────────┘  └──────────────┘  └──────────────┘
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | User authentication |
| GET | /api/auth/me | Get current user |
| GET | /api/shipments/:id | Get shipment details |
| GET | /api/shipments/:id/documents | List shipment documents |
| POST | /api/shipments/:id/documents | Upload document |
| GET | /api/shipments/:id/tracking | Get container tracking status |
| GET | /api/shipments/:id/events | Get container event history |
| GET | /api/shipments/:id/audit-pack | Download audit pack ZIP |
| POST | /api/webhooks/tracking | Receive tracking webhooks |

### Database Schema (PostgreSQL)

```sql
-- Core tables as defined in data model section
-- See detailed entity definitions above

-- Key indexes for performance
CREATE INDEX idx_shipment_status ON shipment(status);
CREATE INDEX idx_document_shipment ON document(shipment_id);
CREATE INDEX idx_document_status ON document(status);
CREATE INDEX idx_container_event_shipment ON container_event(shipment_id);
CREATE INDEX idx_container_event_timestamp ON container_event(event_timestamp);
```

---

## Success Criteria

### Functional Criteria

| Criteria | Metric | Target |
|----------|--------|--------|
| Single shipment visibility | All documents + events on one screen | 100% |
| Container tracking | Live status displayed | Working |
| Document completeness | Missing docs identified | Accurate |
| Audit pack export | ZIP downloadable | Functional |
| User response time | Time to answer key questions | < 30 seconds |

### Non-Functional Criteria

| Criteria | Target |
|----------|--------|
| Page load time | < 3 seconds |
| API response time | < 500ms |
| Availability (POC) | 95% during demo |

### User Acceptance Test Scenarios

**Scenario 1: "Where is my container?"**
1. User logs in
2. User views shipment page
3. User sees: Container status, location, ETA
4. Time: < 30 seconds

**Scenario 2: "Are all documents complete?"**
1. User logs in
2. User views shipment page
3. User sees: Document checklist with complete/missing indicators
4. User identifies: Which documents are missing
5. Time: < 30 seconds

**Scenario 3: "Generate audit pack"**
1. User clicks "Download Audit Pack"
2. ZIP file downloads
3. ZIP contains: All documents + summary PDF + metadata
4. Time: < 60 seconds

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| API access delayed | Medium | High | Have ShipsGo as backup; mock data for development |
| Container data unavailable | Low | Medium | Use historical shipment with known data |
| File storage issues | Low | Low | Use local storage for POC, S3 in production |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| No suitable real shipment | Medium | High | Identify 2-3 candidate shipments in advance |
| Stakeholder availability | Medium | Medium | Schedule demo early, have async review option |
| Requirements change | Low | Medium | Time-box POC scope strictly |

### Contingency Plans

1. **If Vizion API unavailable:** Use ShipsGo free tier (3 credits)
2. **If no active shipment:** Use recent completed shipment with mock "live" status
3. **If timeline slips:** Deliver core view without audit pack export

---

## Sprint Breakdown

### Sprint 1 (Days 1-4): Data Model and Database

**Goal:** Complete data model implementation and seed with real shipment data.

**Tasks:**
- [ ] Finalize database schema
- [ ] Set up PostgreSQL instance
- [ ] Create migration scripts
- [ ] Identify real shipment for POC
- [ ] Collect and prepare real shipment data
- [ ] Seed database with shipment, product, party data
- [ ] Document all metadata captured

**Deliverables:**
- Working database with schema
- One real shipment seeded
- Data dictionary document

### Sprint 2 (Days 5-8): Container Tracking Integration

**Goal:** Live container tracking data flowing into system.

**Tasks:**
- [ ] Register for Vizion/ShipsGo developer account
- [ ] Implement API client service
- [ ] Subscribe test container to tracking
- [ ] Implement webhook receiver
- [ ] Persist tracking events to database
- [ ] Link events to shipment record
- [ ] Test with real container number

**Deliverables:**
- Working tracking integration
- Container events in database
- Webhook endpoint live

### Sprint 3 (Days 9-14): UI and Document Management

**Goal:** Complete user interface with document status display.

**Tasks:**
- [ ] Set up React frontend project
- [ ] Implement authentication flow
- [ ] Build shipment detail page
- [ ] Build document list component
- [ ] Implement document upload
- [ ] Build container status display
- [ ] Build timeline component
- [ ] Implement compliance status logic

**Deliverables:**
- Working authenticated UI
- Shipment view complete
- Document upload functional

### Sprint 4 (Days 15-18): Audit Pack and Polish

**Goal:** Export functionality and refinement.

**Tasks:**
- [ ] Implement audit pack ZIP generation
- [ ] Generate PDF summary document
- [ ] Include tracking log export
- [ ] UI polish and error handling
- [ ] End-to-end testing
- [ ] User acceptance testing
- [ ] Bug fixes
- [ ] Demo preparation

**Deliverables:**
- Working audit pack export
- Polished UI
- Ready for demo

---

## Resource Requirements

### Team

| Role | Time Required | Notes |
|------|--------------|-------|
| Full-stack Developer | 80-100 hours | Primary POC builder |
| Product/Business Lead | 10-15 hours | Requirements, testing, feedback |
| Data Entry | 5-10 hours | Seed real shipment data |

### Infrastructure

| Resource | Cost (POC) | Notes |
|----------|-----------|-------|
| Vizion API | Free | Developer tier (15 containers/month) |
| PostgreSQL | Free | Local or free tier cloud |
| Hosting | Free | Local development or free tier |
| Domain | N/A | Not required for POC |

### External Dependencies

- [ ] Access to real shipment documentation (BL, invoices, certificates)
- [ ] Container number for active/recent shipment
- [ ] Vizion or ShipsGo API credentials
- [ ] Sample German buyer for testing feedback

---

## Design Considerations for Future Phases

### AI Agent Integration Hooks

The POC architecture should include:

```python
# Document validation hook (stub for POC)
async def validate_document_completeness(shipment_id: str) -> ValidationResult:
    """
    Future: AI agent validates document completeness
    POC: Rule-based checklist comparison
    """
    pass

# Discrepancy detection hook (stub for POC)
async def detect_discrepancies(shipment_id: str) -> List[Discrepancy]:
    """
    Future: AI agent compares quantities, HS codes, etc.
    POC: Manual review
    """
    pass

# Summary generation hook (stub for POC)
async def generate_buyer_summary(shipment_id: str) -> str:
    """
    Future: AI generates natural language summary
    POC: Template-based summary
    """
    pass
```

### Multi-Tenant Design Principles

Even in POC, structure code to support:

- Tenant ID field in all core tables (nullable for POC)
- API authorization middleware with tenant context
- Data isolation patterns in queries
- Configuration per tenant (document requirements, etc.)

### WordPress Integration Path

POC is standalone, but document how to:

- Embed React app in WordPress page
- Share authentication with WordPress users
- Use WordPress as login portal
- API access from WordPress plugins

---

## Appendix A: EUDR Compliance Context

### Timeline (Updated December 2025)

- **December 30, 2026:** Large operators and traders must comply
- **June 30, 2027:** Small operators must comply
- **First annual report:** After December 30, 2026 (covering 2026)

### Key Requirements for Animal Products (Hooves)

1. **Geolocation:** Farm/plot coordinates where cattle were raised
2. **Production dates:** Evidence of post-cutoff production (after Dec 31, 2020)
3. **Supplier identity:** Full traceability to source
4. **Due diligence statement:** Electronic submission to EU authorities
5. **Deforestation-free declaration:** Confirmation no deforestation involved

### Country Risk Classification

Nigeria is currently classified as **Standard Risk**, requiring:
- Full due diligence process
- Risk assessment and mitigation
- 3% of imports subject to annual checks

---

## Appendix B: Container Tracking API Comparison

| Feature | Vizion | ShipsGo |
|---------|--------|---------|
| Free Tier | 15 containers/month | 3 credits (trial) |
| Price per container | $5 (after free) | $1.82 |
| Coverage | 99% ocean freight | 100+ carriers |
| Webhooks | Yes | Yes |
| Auto carrier ID | Yes | Limited |
| Documentation | Good | Good |
| REST API | Yes | Yes |

**Recommendation:** Start with Vizion for better developer experience and free tier. Fall back to ShipsGo if needed.

---

## Appendix C: Document Type Specifications

### Bill of Lading (B/L)
- **Purpose:** Receipt of cargo, contract of carriage, document of title
- **Required fields:** Container number, shipper, consignee, notify party, description of goods, weight, seal number
- **Validation:** Match container number to shipment, verify parties

### Phytosanitary Certificate
- **Purpose:** Confirms goods free from plant pests/diseases
- **Issuing authority:** National Plant Protection Organization (NPPO)
- **Required for:** All plant and animal products to EU
- **Validity:** Typically 14-21 days

### Certificate of Origin
- **Purpose:** Confirms country of origin for customs and trade agreements
- **Issuing authority:** Chamber of Commerce or equivalent
- **Required fields:** Exporter, importer, goods description, HS code, origin declaration

### EUDR Due Diligence Statement
- **Purpose:** Electronic declaration of EUDR compliance
- **Submission:** To EU Information System (when operational)
- **Required data:** Geolocation, production dates, deforestation-free declaration
- **Timeline:** Required from December 30, 2026

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 2026 | Development Architect | Initial POC plan |

---

## References

- [ShipsGo Container Tracking API](https://shipsgo.com/ocean/container-tracking-api)
- [Vizion Container Tracking API](https://www.vizionapi.com/)
- [EU Deforestation Regulation Implementation](https://green-forum.ec.europa.eu/nature-and-biodiversity/deforestation-regulation-implementation_en)
- [EUDR 2026 Updates - QIMA](https://blog.qima.com/esg/eu-deforestation-update-2026)
- [Vizion Pricing](https://www.vizionapi.com/container-tracking/pricing)
- [ShipsGo Pricing - G2](https://www.g2.com/products/shipsgo-container-tracking/pricing)
