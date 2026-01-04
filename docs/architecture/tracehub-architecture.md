# VIBOTAJ TraceHub - Architecture Document

**Version:** 1.0
**Date:** January 2026
**Status:** POC Design Phase

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Logical Architecture](#2-logical-architecture)
3. [Data Model](#3-data-model)
4. [Document & Shipment Lifecycle](#4-document--shipment-lifecycle)
5. [API Design](#5-api-design)
6. [AI Agent Integration Points](#6-ai-agent-integration-points)
7. [Multi-Tenant SaaS Considerations](#7-multi-tenant-saas-considerations)
8. [Technology Stack Recommendations](#8-technology-stack-recommendations)

---

## 1. Executive Summary

### Platform Vision

VIBOTAJ TraceHub is a container tracking and documentation compliance platform designed for agro-export operations. The platform addresses three critical pain points identified by German buyers and African suppliers:

- **Documentation gaps**: Missing or incomplete export documentation
- **Inconsistent shipment visibility**: Lack of real-time container tracking
- **Audit-readiness**: No consolidated, compliant record bundles for regulatory review

### Three Pillars

```
+------------------------------------------------------------------+
|                      VIBOTAJ TraceHub                             |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------------+  +-------------------+  +------------------+ |
|  |   REAL-TIME     |  |    DOCUMENT       |  |  BUYER/SUPPLIER  | |
|  |   CONTAINER     |  |    LIFECYCLE &    |  |  EXPERIENCE      | |
|  |   TRACKING      |  |    COMPLIANCE     |  |                  | |
|  +-----------------+  +-------------------+  +------------------+ |
|  | - Carrier API   |  | - State machine   |  | - Role-based     | |
|  |   integration   |  | - EUDR compliance |  |   dashboards     | |
|  | - Event ingest  |  | - Metadata model  |  | - Upload portal  | |
|  | - ETD/ETA       |  | - Audit bundles   |  | - Doc status     | |
|  | - Port events   |  | - Validation      |  | - Tracking view  | |
|  +-----------------+  +-------------------+  +------------------+ |
|                                                                   |
+------------------------------------------------------------------+
```

### Business Goals

1. **Immediate (POC)**: Single-shipment end-to-end visibility with audit-ready bundle export
2. **Short-term**: Full VIBOTAJ operations on TraceHub (all shipments, all products)
3. **Long-term**: Multi-tenant SaaS for other agro-exporters, generating recurring revenue

---

## 2. Logical Architecture

### Architecture Principles

- **Decoupled Design**: WordPress serves as UI shell only; core logic resides in independent backend
- **API-First**: All functionality exposed via REST APIs for flexibility and future UI changes
- **Compliance by Design**: EUDR and export compliance are first-class data model concepts
- **Event-Driven**: Container tracking events flow through webhooks for real-time updates

### High-Level Architecture

```
+-------------------------------------------------------------------------+
|                           VIBOTAJ TraceHub                               |
+-------------------------------------------------------------------------+
|                                                                          |
|  PRESENTATION LAYER                                                      |
|  +--------------------------------------------------------------------+  |
|  |                     WordPress Portal (UI Shell)                    |  |
|  |  +---------------+  +---------------+  +------------------------+  |  |
|  |  | Buyer Portal  |  | Supplier      |  | Admin Dashboard        |  |  |
|  |  | - Tracking    |  | Portal        |  | - Shipment management  |  |  |
|  |  | - Documents   |  | - Doc upload  |  | - Compliance review    |  |  |
|  |  | - Audit packs |  | - Status view |  | - User management      |  |  |
|  |  +---------------+  +---------------+  +------------------------+  |  |
|  +--------------------------------------------------------------------+  |
|         |                      |                      |                  |
|         |                REST API (JWT Auth)          |                  |
|         v                      v                      v                  |
|  +--------------------------------------------------------------------+  |
|  |                    TraceHub Core Service                           |  |
|  |                      (Node.js / Python)                            |  |
|  |  +----------------+  +----------------+  +---------------------+   |  |
|  |  | Shipment       |  | Document       |  | Compliance          |   |  |
|  |  | Service        |  | Service        |  | Service             |   |  |
|  |  +----------------+  +----------------+  +---------------------+   |  |
|  |  +----------------+  +----------------+  +---------------------+   |  |
|  |  | Tracking       |  | Party          |  | AI Agent            |   |  |
|  |  | Service        |  | Service        |  | Service             |   |  |
|  |  +----------------+  +----------------+  +---------------------+   |  |
|  +--------------------------------------------------------------------+  |
|         |                      |                      |                  |
|         v                      v                      v                  |
|  +--------------------------------------------------------------------+  |
|  |                        Data Layer                                  |  |
|  |  +-----------------------+    +-----------------------------+      |  |
|  |  |  PostgreSQL           |    |  File Storage               |      |  |
|  |  |  - Shipments          |    |  - Documents (S3/local)     |      |  |
|  |  |  - Products           |    |  - Audit bundles            |      |  |
|  |  |  - Documents metadata |    |  - Generated reports        |      |  |
|  |  |  - Container events   |    +-----------------------------+      |  |
|  |  |  - Compliance checks  |                                         |  |
|  |  +-----------------------+                                         |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
|  INTEGRATION LAYER                                                       |
|  +--------------------------------------------------------------------+  |
|  |  +------------------+  +------------------+  +------------------+  |  |
|  |  | Container        |  | Email/SMS        |  | Future           |  |  |
|  |  | Tracking APIs    |  | Notifications    |  | Integrations     |  |  |
|  |  | - ShipsGo        |  | - Transactional  |  | - Customs APIs   |  |  |
|  |  | - Vizion         |  | - Alerts         |  | - Payment        |  |  |
|  |  +------------------+  +------------------+  +------------------+  |  |
|  +--------------------------------------------------------------------+  |
|                                                                          |
+-------------------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| WordPress Portal | User authentication, UI rendering, session management | WordPress 6.x + Custom Theme |
| TraceHub Core | Business logic, API endpoints, data orchestration | Node.js (Express) or Python (FastAPI) |
| PostgreSQL | Structured data persistence, transactions, queries | PostgreSQL 15+ |
| File Storage | Document storage, audit bundle generation | Local FS (POC) / S3 (Production) |
| Container Tracking | External API integration for vessel/container events | ShipsGo or Vizion API |

### Communication Patterns

```
+------------------+        +------------------+        +------------------+
|   WordPress      |  REST  |   TraceHub       |  SQL   |   PostgreSQL     |
|   Portal         | -----> |   Core API       | -----> |   Database       |
|                  | <----- |                  | <----- |                  |
+------------------+  JSON  +------------------+        +------------------+
                                   |
                                   | Webhook (inbound)
                                   v
                          +------------------+
                          |  Container       |
                          |  Tracking API    |
                          |  (ShipsGo/Vizion)|
                          +------------------+
```

---

## 3. Data Model

### Entity Relationship Diagram

```
+------------------+       +------------------+       +------------------+
|     TENANT       |       |     PARTY        |       |     USER         |
+------------------+       +------------------+       +------------------+
| id (PK)          |       | id (PK)          |       | id (PK)          |
| name             |<---+  | tenant_id (FK)   |       | tenant_id (FK)   |
| domain           |    |  | type             |       | party_id (FK)    |
| settings (JSON)  |    |  | name             |       | email            |
| created_at       |    |  | country          |       | role             |
| updated_at       |    |  | address          |       | wp_user_id       |
+------------------+    |  | contact_email    |       | created_at       |
         |              |  | contact_phone    |       +------------------+
         |              |  | created_at       |
         |              |  +------------------+
         |              |          |
         |              |          | buyer_id / supplier_id
         v              |          v
+------------------+    |  +------------------+       +------------------+
|    SHIPMENT      |----+  |    PRODUCT       |       | CONTAINER_EVENT  |
+------------------+       +------------------+       +------------------+
| id (PK)          |       | id (PK)          |       | id (PK)          |
| tenant_id (FK)   |       | shipment_id (FK) |       | shipment_id (FK) |
| reference        |       | hs_code          |       | event_type       |
| container_number |       | description      |       | timestamp        |
| bl_number        |       | quantity_net     |       | location         |
| booking_ref      |       | quantity_gross   |       | vessel           |
| vessel           |       | packaging        |       | voyage           |
| voyage           |       | batch_lot        |       | port_code        |
| etd              |       | moisture         |       | port_name        |
| eta              |       | quality_grade    |       | source_api       |
| pol_code         |       | unit_of_measure  |       | raw_data (JSON)  |
| pol_name         |       | created_at       |       | created_at       |
| pod_code         |       +------------------+       +------------------+
| pod_name         |                |
| incoterms        |                |
| status           |                v
| buyer_id (FK)    |       +------------------+
| supplier_id (FK) |       |     ORIGIN       |
| created_at       |       |    (EUDR)        |
| updated_at       |       +------------------+
+------------------+       | id (PK)          |
         |                 | product_id (FK)  |
         |                 | farm_plot_id     |
         |                 | geolocation_lat  |
         |                 | geolocation_lng  |
         |                 | geolocation_poly |
         |                 | country          |
         |                 | region           |
         |                 | production_date  |
         |                 | supplier_id (FK) |
         v                 | deforestation_   |
+------------------+       |   free_statement |
|    DOCUMENT      |       | verified_at      |
+------------------+       | verified_by      |
| id (PK)          |       | created_at       |
| shipment_id (FK) |       +------------------+
| type             |
| name             |       +------------------+
| file_url         |       | COMPLIANCE_CHECK |
| file_size        |       +------------------+
| mime_type        |       | id (PK)          |
| state            |       | shipment_id (FK) |
| uploaded_by (FK) |       | rule_type        |
| validated_at     |       | rule_version     |
| validated_by(FK) |       | passed           |
| compliance_notes |       | details (JSON)   |
| metadata (JSON)  |       | checked_at       |
| created_at       |       | checked_by       |
| updated_at       |       | created_at       |
+------------------+       +------------------+
```

### Core Entity Definitions

#### Tenant (Multi-Tenant Support)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(255) | Company name (e.g., "VIBOTAJ") |
| domain | VARCHAR(255) | Custom domain for white-label |
| settings | JSONB | Tenant-specific configuration |
| created_at | TIMESTAMP | Record creation time |

#### Shipment

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID (FK) | Multi-tenant isolation |
| reference | VARCHAR(50) | Internal reference (e.g., VIBO-2026-001) |
| container_number | VARCHAR(20) | Container ID (e.g., MSCU1234567) |
| bl_number | VARCHAR(50) | Bill of Lading number |
| booking_ref | VARCHAR(50) | Carrier booking reference |
| vessel | VARCHAR(100) | Vessel name |
| voyage | VARCHAR(50) | Voyage number |
| etd | TIMESTAMP | Estimated time of departure |
| eta | TIMESTAMP | Estimated time of arrival |
| pol_code | VARCHAR(5) | Port of Loading UN/LOCODE |
| pol_name | VARCHAR(100) | Port of Loading name |
| pod_code | VARCHAR(5) | Port of Discharge UN/LOCODE |
| pod_name | VARCHAR(100) | Port of Discharge name |
| incoterms | VARCHAR(10) | Trade terms (FOB, CIF, etc.) |
| status | ENUM | Shipment lifecycle state |
| buyer_id | UUID (FK) | Reference to Party |
| supplier_id | UUID (FK) | Reference to Party |

#### Product

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| shipment_id | UUID (FK) | Parent shipment |
| hs_code | VARCHAR(12) | Harmonized System code |
| description | TEXT | Product description |
| quantity_net | DECIMAL(12,3) | Net weight/quantity |
| quantity_gross | DECIMAL(12,3) | Gross weight/quantity |
| packaging | VARCHAR(100) | Packaging type (bags, containers) |
| batch_lot | VARCHAR(50) | Batch or lot number |
| moisture | DECIMAL(5,2) | Moisture percentage |
| quality_grade | VARCHAR(20) | Quality classification |
| unit_of_measure | VARCHAR(10) | UoM (kg, MT, pcs) |

#### Origin (EUDR Compliance)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| product_id | UUID (FK) | Associated product |
| farm_plot_id | VARCHAR(100) | Unique farm/plot identifier |
| geolocation_lat | DECIMAL(10,7) | Latitude coordinate |
| geolocation_lng | DECIMAL(10,7) | Longitude coordinate |
| geolocation_poly | GEOMETRY | Polygon for plot boundaries |
| country | VARCHAR(2) | ISO country code |
| region | VARCHAR(100) | Administrative region |
| production_date | DATE | Date of production/harvest |
| supplier_id | UUID (FK) | Originating supplier |
| deforestation_free_statement | TEXT | EUDR compliance statement |
| verified_at | TIMESTAMP | Verification timestamp |
| verified_by | UUID (FK) | Verifying user |

#### Document

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| shipment_id | UUID (FK) | Parent shipment |
| type | ENUM | Document type (see below) |
| name | VARCHAR(255) | File name |
| file_url | TEXT | Storage URL/path |
| state | ENUM | Document lifecycle state |
| uploaded_by | UUID (FK) | Uploading user |
| validated_at | TIMESTAMP | Validation timestamp |
| validated_by | UUID (FK) | Validating user |
| compliance_notes | TEXT | Notes from compliance review |
| metadata | JSONB | Type-specific metadata |

**Document Types:**
- `BILL_OF_LADING` - Transport document
- `COMMERCIAL_INVOICE` - Invoice for goods
- `PACKING_LIST` - Itemized packing details
- `PHYTOSANITARY_CERT` - Plant health certificate
- `CERTIFICATE_OF_ORIGIN` - Origin certification
- `FUMIGATION_CERT` - Fumigation certificate
- `SANITARY_CERT` - Sanitary/health certificate
- `INSURANCE_CERT` - Cargo insurance
- `CUSTOMS_DECLARATION` - Customs documents
- `CONTRACT` - Sale/purchase contract
- `QUALITY_CERT` - Quality inspection
- `EUDR_STATEMENT` - Deforestation-free declaration
- `OTHER` - Miscellaneous documents

#### ContainerEvent

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| shipment_id | UUID (FK) | Associated shipment |
| event_type | ENUM | Event classification |
| timestamp | TIMESTAMP | Event occurrence time |
| location | VARCHAR(255) | Location description |
| vessel | VARCHAR(100) | Vessel name at event |
| voyage | VARCHAR(50) | Voyage at event |
| port_code | VARCHAR(5) | UN/LOCODE |
| port_name | VARCHAR(100) | Port name |
| source_api | VARCHAR(50) | Source (shipsgo/vizion) |
| raw_data | JSONB | Original API response |

**Event Types:**
- `BOOKING_CONFIRMED` - Booking accepted
- `GATE_IN` - Container at origin terminal
- `LOADED` - Loaded on vessel
- `DEPARTED` - Vessel departed
- `TRANSSHIPMENT` - Transfer at intermediate port
- `ARRIVED` - Vessel arrived at POD
- `DISCHARGED` - Unloaded from vessel
- `GATE_OUT` - Released from terminal
- `DELIVERED` - Final delivery confirmed

#### ComplianceCheck

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| shipment_id | UUID (FK) | Checked shipment |
| rule_type | VARCHAR(50) | Rule category |
| rule_version | VARCHAR(20) | Version of rule applied |
| passed | BOOLEAN | Check result |
| details | JSONB | Detailed findings |
| checked_at | TIMESTAMP | Check execution time |
| checked_by | VARCHAR(50) | user/ai_agent identifier |

---

## 4. Document & Shipment Lifecycle

### Document Lifecycle State Machine

```
                              +----------+
                              |  DRAFT   |
                              +----+-----+
                                   |
                                   | Supplier uploads file
                                   v
                              +---------+
                              |UPLOADED |
                              +----+----+
                                   |
                                   | Metadata validated
                                   | (format, required fields)
                                   v
                             +----------+
                             |VALIDATED |
                             +----+-----+
                                  |
                                  | Compliance rules checked
                                  v
                          +----------------+
                          |COMPLIANCE_OK   |
                          |     or         |
                          |COMPLIANCE_FAIL |
                          +-------+--------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
            +---------------+           +---------------+
            | LINKED        |           | NEEDS_ACTION  |
            | (to shipment) |           | (review req)  |
            +-------+-------+           +-------+-------+
                    |                           |
                    |                           | Corrected and
                    |                           | re-uploaded
                    |                           |
                    +<--------------------------+
                    |
                    | Shipment delivered
                    v
              +-----------+
              | DELIVERED |
              +-----+-----+
                    |
                    | Retention period
                    v
              +-----------+
              | ARCHIVED  |
              +-----------+
```

### Document State Definitions

| State | Description | Allowed Actions |
|-------|-------------|-----------------|
| DRAFT | Placeholder created, no file | Upload, Delete |
| UPLOADED | File uploaded, pending validation | Validate, Replace, Delete |
| VALIDATED | Format and metadata verified | Run Compliance, Replace |
| COMPLIANCE_OK | Passed compliance rules | Link to Shipment |
| COMPLIANCE_FAIL | Failed compliance check | Review, Replace, Override |
| NEEDS_ACTION | Manual review required | Update, Resolve |
| LINKED | Associated with shipment | View, Download |
| DELIVERED | Shipment complete | View, Download |
| ARCHIVED | Long-term storage | View, Download, Restore |

### Shipment Lifecycle State Machine

```
                        +----------+
                        | CREATED  |
                        +----+-----+
                             |
                             | Booking confirmed
                             v
                    +-----------------+
                    | DOCS_PENDING    |<--------------+
                    +--------+--------+               |
                             |                        |
                             | All required docs      | Missing docs
                             | uploaded & validated   | detected
                             v                        |
                    +-----------------+               |
                    | DOCS_COMPLETE   |---------------+
                    +--------+--------+
                             |
                             | Container gate-in or
                             | vessel departed event
                             v
                    +-----------------+
                    | IN_TRANSIT      |
                    +--------+--------+
                             |
                             | Vessel arrived at POD
                             v
                    +-----------------+
                    | ARRIVED         |
                    +--------+--------+
                             |
                             | Container delivered /
                             | gate-out confirmed
                             v
                    +-----------------+
                    | DELIVERED       |
                    +--------+--------+
                             |
                             | All records finalized
                             | Audit pack generated
                             v
                    +-----------------+
                    | CLOSED          |
                    +-----------------+
```

### Shipment State Definitions

| State | Description | Triggers |
|-------|-------------|----------|
| CREATED | Shipment record created | Manual creation or booking import |
| DOCS_PENDING | Awaiting required documents | Default after creation |
| DOCS_COMPLETE | All required docs validated | Document completeness check |
| IN_TRANSIT | Container moving | Gate-in or departure event |
| ARRIVED | At destination port | Arrival event from tracking API |
| DELIVERED | Goods received by buyer | Delivery confirmation or gate-out |
| CLOSED | Fully archived | Manual closure after audit |

### Required Documents by Product/Destination

```
+------------------+------------------+----------------------------------+
| Product Category | Destination      | Required Documents               |
+------------------+------------------+----------------------------------+
| Hooves (raw)     | Germany (EU)     | BL, Invoice, Packing List,       |
|                  |                  | Phyto, Origin Cert, Fumigation,  |
|                  |                  | EUDR Statement                   |
+------------------+------------------+----------------------------------+
| Pellets          | Germany (EU)     | BL, Invoice, Packing List,       |
|                  |                  | Quality Cert, Origin Cert,       |
|                  |                  | EUDR Statement                   |
+------------------+------------------+----------------------------------+
| General agro     | Non-EU           | BL, Invoice, Packing List,       |
|                  |                  | Origin Cert (varies by product)  |
+------------------+------------------+----------------------------------+
```

---

## 5. API Design

### API Overview

All APIs follow REST conventions with JSON payloads. Authentication uses JWT tokens issued by the TraceHub Core service, with WordPress handling initial user authentication.

### Base URL Structure

```
Production: https://api.tracehub.vibotaj.com/v1
POC:        https://tracehub-api.vibotaj.com/v1
```

### Authentication Flow

```
+------------+       +------------+       +------------+
|  WordPress |       |  TraceHub  |       |  Protected |
|   Login    | ----> |  Auth API  | ----> |  Resources |
+------------+       +------------+       +------------+
     |                     |
     | 1. User login       | 2. Exchange WP session
     |    (WP native)      |    for JWT token
     |                     |
     v                     v
+------------+       +------------+
| WP Session |       | JWT Token  |
| Cookie     |       | (1h expiry)|
+------------+       +------------+
```

### Core Endpoints

#### Shipments

```
GET    /shipments                    List shipments (filtered, paginated)
GET    /shipments/{id}               Get shipment details
POST   /shipments                    Create new shipment
PUT    /shipments/{id}               Update shipment
DELETE /shipments/{id}               Delete shipment (soft delete)
GET    /shipments/{id}/documents     List shipment documents
GET    /shipments/{id}/events        List container events
GET    /shipments/{id}/compliance    Get compliance status
GET    /shipments/{id}/audit-pack    Download audit bundle (ZIP)
POST   /shipments/{id}/refresh       Trigger tracking refresh
```

#### Documents

```
GET    /documents                    List documents (filtered)
GET    /documents/{id}               Get document metadata
POST   /documents                    Create document record
PUT    /documents/{id}               Update document metadata
DELETE /documents/{id}               Delete document
POST   /documents/{id}/upload        Upload file (multipart)
GET    /documents/{id}/download      Download file
POST   /documents/{id}/validate      Trigger validation
POST   /documents/{id}/link          Link to shipment
```

#### Container Tracking

```
GET    /tracking/{container_number}  Get current container status
GET    /tracking/{container_number}/events   Get all events
POST   /tracking/subscribe           Subscribe to container updates

# Webhook endpoint (inbound from tracking APIs)
POST   /webhooks/tracking            Receive tracking updates
```

#### Compliance

```
GET    /compliance/rules             List active compliance rules
GET    /compliance/check/{shipment_id}   Run compliance check
GET    /compliance/history/{shipment_id} Get compliance history
POST   /compliance/override          Manual override (with reason)
```

#### Parties

```
GET    /parties                      List parties (buyers, suppliers)
GET    /parties/{id}                 Get party details
POST   /parties                      Create party
PUT    /parties/{id}                 Update party
```

### Sample API Responses

#### GET /shipments/{id}

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "reference": "VIBO-2026-001",
  "container_number": "MSCU1234567",
  "bl_number": "MSCU789456123",
  "status": "IN_TRANSIT",
  "vessel": "MSC ANNA",
  "voyage": "FA605R",
  "etd": "2026-01-15T08:00:00Z",
  "eta": "2026-02-12T14:00:00Z",
  "pol": {
    "code": "NGAPP",
    "name": "Apapa, Lagos"
  },
  "pod": {
    "code": "DEHAM",
    "name": "Hamburg"
  },
  "incoterms": "FOB",
  "buyer": {
    "id": "...",
    "name": "German Buyer GmbH",
    "country": "DE"
  },
  "supplier": {
    "id": "...",
    "name": "Nigerian Supplier Ltd",
    "country": "NG"
  },
  "products": [...],
  "documents_summary": {
    "total": 8,
    "complete": 6,
    "pending": 2,
    "missing": ["FUMIGATION_CERT", "EUDR_STATEMENT"]
  },
  "last_event": {
    "type": "DEPARTED",
    "timestamp": "2026-01-16T03:45:00Z",
    "location": "Apapa, Lagos"
  },
  "compliance_status": "PENDING",
  "created_at": "2026-01-10T09:30:00Z",
  "updated_at": "2026-01-16T04:00:00Z"
}
```

### Webhook Handler

Inbound webhooks from container tracking APIs (ShipsGo/Vizion):

```
POST /webhooks/tracking
Headers:
  X-Webhook-Signature: sha256=...
  Content-Type: application/json

Body:
{
  "container_number": "MSCU1234567",
  "event_type": "DEPARTED",
  "timestamp": "2026-01-16T03:45:00Z",
  "location": "Apapa, Lagos",
  "vessel": "MSC ANNA",
  "voyage": "FA605R",
  "next_port": "Hamburg",
  "eta": "2026-02-12T14:00:00Z"
}
```

---

## 6. AI Agent Integration Points

### Architecture for AI Integration

The system is designed with explicit hooks for AI agents, enabling progressive automation from manual rules to full AI-driven workflows.

```
+------------------------------------------------------------------+
|                    AI Agent Integration Layer                     |
+------------------------------------------------------------------+
|                                                                   |
|  +-------------------+  +-------------------+  +-----------------+|
|  | Document          |  | Discrepancy       |  | Summary         ||
|  | Completeness      |  | Detection         |  | Generation      ||
|  | Agent             |  | Agent             |  | Agent           ||
|  +--------+----------+  +--------+----------+  +--------+--------+|
|           |                      |                      |         |
|           v                      v                      v         |
|  +-------------------+  +-------------------+  +-----------------+|
|  | Rule Engine       |  | Comparison Engine |  | NLP Generator   ||
|  | (Manual -> AI)    |  | (Manual -> AI)    |  | (Template->LLM) ||
|  +-------------------+  +-------------------+  +-----------------+|
|                                                                   |
+------------------------------------------------------------------+
         |                         |                      |
         v                         v                      v
+------------------------------------------------------------------+
|                     TraceHub Core Services                        |
+------------------------------------------------------------------+
```

### Integration Point 1: Document Completeness Validation

**Purpose**: Validate that all required documents are present for a shipment based on product type, destination, and compliance requirements.

**Current (POC)**: Rule-based validation

```python
# Pseudo-code for document completeness check
def check_document_completeness(shipment):
    required_docs = get_required_documents(
        product_hs_code=shipment.products[0].hs_code,
        destination_country=shipment.pod_country,
        incoterms=shipment.incoterms
    )

    uploaded_docs = [d.type for d in shipment.documents if d.state in ['VALIDATED', 'COMPLIANCE_OK', 'LINKED']]

    missing = [doc for doc in required_docs if doc not in uploaded_docs]

    return {
        "complete": len(missing) == 0,
        "missing_documents": missing,
        "uploaded_count": len(uploaded_docs),
        "required_count": len(required_docs)
    }
```

**Future (AI-Enhanced)**:
- Natural language queries: "For hooves to Germany under HS 0506, what documents are missing?"
- Context-aware suggestions based on historical shipments
- Automatic classification of uploaded documents

### Integration Point 2: Discrepancy Detection

**Purpose**: Identify mismatches between documents, contracts, and shipment data.

**Discrepancy Types**:
- Quantity mismatches (invoice vs. BL vs. packing list)
- HS code inconsistencies
- Origin data conflicts
- Date/validity issues
- Party name variations

**Current (POC)**: Field-by-field comparison

```json
{
  "shipment_id": "...",
  "discrepancies": [
    {
      "type": "QUANTITY_MISMATCH",
      "field": "net_weight",
      "sources": [
        {"document": "COMMERCIAL_INVOICE", "value": "25000 kg"},
        {"document": "BILL_OF_LADING", "value": "24800 kg"}
      ],
      "severity": "WARNING",
      "suggested_action": "Verify with supplier; minor variance may be acceptable"
    }
  ]
}
```

**Future (AI-Enhanced)**:
- OCR and document parsing for automatic extraction
- Semantic matching for party names and addresses
- Anomaly detection based on historical patterns

### Integration Point 3: Summary Generation

**Purpose**: Generate human-readable status summaries for buyers and internal stakeholders.

**Current (POC)**: Template-based generation

```
Template:
"Shipment {reference}: {status_text}. ETA {destination} {eta_date}.
Documents: {docs_complete}/{docs_total} complete.
{compliance_text}"

Output:
"Shipment VIBO-2026-001: In transit, vessel departed Lagos.
ETA Hamburg 12 Feb 2026. Documents: 6/8 complete.
Missing: Fumigation Certificate, EUDR Statement."
```

**Future (AI-Enhanced)**:
- LLM-generated natural language summaries
- Personalized detail level by user role
- Proactive notifications for significant changes

### AI Service Interface

```typescript
interface AIAgentService {
  // Document completeness
  checkCompleteness(shipmentId: string): Promise<CompletenessResult>;
  suggestMissingDocuments(shipmentId: string): Promise<Suggestion[]>;

  // Discrepancy detection
  detectDiscrepancies(shipmentId: string): Promise<Discrepancy[]>;
  resolveDiscrepancy(discrepancyId: string, resolution: Resolution): Promise<void>;

  // Summary generation
  generateSummary(shipmentId: string, format: 'brief' | 'detailed'): Promise<string>;
  generateBuyerNotification(shipmentId: string, eventType: string): Promise<Notification>;

  // Future capabilities
  classifyDocument(fileBuffer: Buffer): Promise<DocumentClassification>;
  extractMetadata(documentId: string): Promise<ExtractedMetadata>;
  predictDelays(shipmentId: string): Promise<DelayPrediction>;
}
```

---

## 7. Multi-Tenant SaaS Considerations

### Tenant Isolation Strategy

```
+------------------------------------------------------------------+
|                        SHARED INFRASTRUCTURE                      |
+------------------------------------------------------------------+
|  +--------------------+  +--------------------+  +---------------+|
|  |  TraceHub API      |  |  PostgreSQL        |  |  File Storage ||
|  |  (Single Deploy)   |  |  (Row-Level Sec)   |  |  (Prefixed)   ||
|  +--------------------+  +--------------------+  +---------------+|
+------------------------------------------------------------------+
         |                         |                      |
         v                         v                      v
+------------------------------------------------------------------+
|                        TENANT DATA ISOLATION                      |
+------------------------------------------------------------------+
|  +------------------+    +------------------+   +----------------+|
|  | Tenant: VIBOTAJ  |    | Tenant: ExportCo |   | Tenant: ...    ||
|  | tenant_id: abc   |    | tenant_id: xyz   |   | tenant_id: ... ||
|  +------------------+    +------------------+   +----------------+|
|  | Shipments        |    | Shipments        |   | Shipments      ||
|  | Documents        |    | Documents        |   | Documents      ||
|  | Parties          |    | Parties          |   | Parties        ||
|  | Users            |    | Users            |   | Users          ||
|  +------------------+    +------------------+   +----------------+|
+------------------------------------------------------------------+
```

### Database Isolation

**Approach**: Row-Level Security (RLS) with tenant_id column

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their tenant's data
CREATE POLICY tenant_isolation_policy ON shipments
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Set tenant context on each request
SET app.current_tenant = 'tenant-uuid-here';
```

### File Storage Isolation

```
s3://tracehub-documents/
  |-- tenants/
      |-- vibotaj/
      |   |-- shipments/
      |   |   |-- VIBO-2026-001/
      |   |   |   |-- bill_of_lading.pdf
      |   |   |   |-- invoice.pdf
      |   |-- audit-packs/
      |       |-- VIBO-2026-001-audit.zip
      |-- exportco/
          |-- shipments/
          |-- audit-packs/
```

### Tenant Configuration

```json
{
  "tenant_id": "abc-123",
  "name": "VIBOTAJ",
  "settings": {
    "branding": {
      "logo_url": "https://...",
      "primary_color": "#1a365d"
    },
    "compliance": {
      "default_destination": "EU",
      "eudr_required": true,
      "custom_document_types": []
    },
    "notifications": {
      "email_enabled": true,
      "sms_enabled": false,
      "webhook_url": null
    },
    "integrations": {
      "tracking_api": "shipsgo",
      "tracking_api_key": "encrypted:..."
    }
  },
  "subscription": {
    "plan": "professional",
    "shipments_per_month": 50,
    "users_limit": 10,
    "storage_gb": 10
  }
}
```

### Future Billing Model

```
+------------------------------------------------------------------+
|                     SUBSCRIPTION TIERS                            |
+------------------------------------------------------------------+
| Tier        | Shipments/mo | Users | Storage | Price/mo          |
+------------------------------------------------------------------+
| Starter     | 10           | 3     | 2 GB    | $99               |
| Professional| 50           | 10    | 10 GB   | $299              |
| Enterprise  | Unlimited    | 50    | 100 GB  | $999              |
| Custom      | Negotiated   | -     | -       | Contact sales     |
+------------------------------------------------------------------+

Usage-based add-ons:
- Additional API calls: $0.01/call beyond tier limit
- Additional storage: $0.10/GB/month
- Premium tracking APIs: $2/container/month
```

---

## 8. Technology Stack Recommendations

### POC Stack (Immediate) - IMPLEMENTED

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React 18 + Vite + TailwindCSS | Modern SPA, fast development |
| **Backend API** | Python 3.11 (FastAPI) | Rapid development, good ecosystem |
| **Database** | PostgreSQL 15 | JSONB support, robust, free |
| **File Storage** | Local filesystem (Docker volumes) | Simple for POC, migrate later |
| **Container Tracking** | JSONCargo API | Cost-effective container tracking |
| **Authentication** | JWT (PyJWT) | Stateless, role-based access |
| **Hosting** | Hostinger VPS (Docker Compose) | Full control, SSL via Let's Encrypt |
| **Reverse Proxy** | Nginx (in Docker) | SSL termination, API proxy |

### Production Stack (Future)

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend Portal** | React 18 + Next.js | Better UX, SEO, performance |
| **Backend API** | Node.js or Python (containerized) | Same as POC, production-hardened |
| **Database** | PostgreSQL 15 (managed: Supabase/RDS) | Managed backups, scaling |
| **File Storage** | AWS S3 or Cloudflare R2 | Scalable, CDN integration |
| **Container Tracking** | Vizion or multi-provider | Better coverage, reliability |
| **Cache** | Redis | Session storage, API caching |
| **Search** | Elasticsearch or Meilisearch | Full-text search across documents |
| **Orchestration** | Docker + Kubernetes | Scalable, portable deployment |
| **CI/CD** | GitHub Actions | Automated testing and deployment |
| **Monitoring** | Datadog or Grafana Cloud | Observability, alerting |

### Deployment Architecture (Production)

```
+------------------------------------------------------------------+
|                        PRODUCTION DEPLOYMENT                      |
+------------------------------------------------------------------+
|                                                                   |
|  +------------------+     +------------------+                    |
|  | Cloudflare CDN   |     | Load Balancer    |                    |
|  | (SSL, DDoS)      |---->| (nginx/ALB)      |                    |
|  +------------------+     +--------+---------+                    |
|                                    |                              |
|           +------------------------+------------------------+     |
|           |                        |                        |     |
|           v                        v                        v     |
|  +------------------+     +------------------+     +-------------+|
|  | TraceHub API     |     | TraceHub API     |     | WordPress   ||
|  | (Container 1)    |     | (Container 2)    |     | (Static)    ||
|  +--------+---------+     +--------+---------+     +-------------+|
|           |                        |                              |
|           +------------------------+                              |
|                        |                                          |
|           +------------+------------+                             |
|           |                         |                             |
|           v                         v                             |
|  +------------------+      +------------------+                   |
|  | PostgreSQL       |      | Redis            |                   |
|  | (Primary/Replica)|      | (Cache/Sessions) |                   |
|  +------------------+      +------------------+                   |
|                                                                   |
|  +------------------+      +------------------+                   |
|  | S3 / R2          |      | Elasticsearch    |                   |
|  | (Documents)      |      | (Search Index)   |                   |
|  +------------------+      +------------------+                   |
|                                                                   |
+------------------------------------------------------------------+
```

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/vibotaj/tracehub.git
cd tracehub

# Backend setup (Node.js example)
cd backend
npm install
cp .env.example .env
# Edit .env with database credentials and API keys
npm run db:migrate
npm run dev

# Frontend (WordPress)
# Configure wp-config.php with TraceHub API URL
# Install TraceHub connector plugin

# Database
docker run -d --name tracehub-db \
  -e POSTGRES_DB=tracehub \
  -e POSTGRES_USER=tracehub \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  postgres:15
```

---

## Appendix A: POC Checklist - COMPLETED

### Week 1: Data Model & Backend ✅
- [x] Set up PostgreSQL database with schema
- [x] Create backend project (Python FastAPI)
- [x] Implement core entities (Shipment, Document, Product, Origin)
- [x] Build basic CRUD APIs for shipments and documents
- [x] Integrate JSONCargo API (container tracking)

### Week 2: Lifecycle & Integration ✅
- [x] Implement document lifecycle state machine
- [x] Implement shipment lifecycle state machine
- [x] Create webhook handler for tracking events
- [x] Build document upload/download functionality
- [x] Create compliance check rules for hooves to Germany
- [x] Implement EUDR compliance tracking

### Week 3: UI & Delivery ✅
- [x] Build React SPA frontend (standalone, not WordPress)
- [x] Create buyer dashboard view (tracking + documents)
- [x] Implement "Download Audit Pack" functionality
- [x] Test with real shipment data
- [x] Document API and deployment process
- [x] Deploy to production (tracehub.vibotaj.com)

### Additional Features Implemented
- [x] Role-based access control (6 roles)
- [x] User management (admin)
- [x] Multi-document PDF detection with AI classification
- [x] Per-document-type validation
- [x] Duplicate detection by reference numbers
- [x] Analytics dashboard
- [x] Audit logging
- [x] Notification system

### Success Criteria ✅
- [x] Single shipment visible with all metadata
- [x] Container events displayed in real-time
- [x] Documents listed with complete/missing status
- [x] Audit pack downloadable as ZIP
- [x] User can answer: "Where is my container?" in 30 seconds
- [x] User can answer: "Are documents complete?" in 30 seconds

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| BL | Bill of Lading - transport document |
| EUDR | EU Deforestation Regulation |
| ETD | Estimated Time of Departure |
| ETA | Estimated Time of Arrival |
| HS Code | Harmonized System code for product classification |
| Incoterms | International Commercial Terms (FOB, CIF, etc.) |
| POD | Port of Discharge (destination) |
| POL | Port of Loading (origin) |
| Phyto | Phytosanitary Certificate |
| UN/LOCODE | United Nations Location Code for ports |

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Author: Development Architecture Team*
