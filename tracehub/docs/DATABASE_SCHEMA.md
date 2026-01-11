# TraceHub Database Schema Reference

> Last updated: January 2026 | Schema version: 20260109_0003

## Overview

TraceHub uses PostgreSQL with SQLAlchemy ORM. The schema supports multi-tenancy through `organization_id` foreign keys on all major tables.

**Total Tables:** 12
**Enums:** 14

---

## Entity Relationship Diagram

```
Organizations (Multi-Tenancy Root)
├── Users (many-to-one)
├── OrganizationMemberships (one-to-many)
├── Shipments (one-to-many via organization_id)
├── Shipments (one-to-many via buyer_organization_id)
├── Products (one-to-many)
├── Origins (one-to-many)
├── ContainerEvents (one-to-many)
└── AuditLogs (one-to-many)

Shipments
├── Documents (one-to-many, CASCADE)
├── Products (one-to-many, CASCADE)
├── Origins (one-to-many)
├── ContainerEvents (one-to-many, CASCADE)
└── ReferenceRegistry (one-to-many, CASCADE)

Documents
└── DocumentContents (one-to-many, CASCADE)
```

---

## Tables

### 1. organizations

Multi-tenancy foundation table. All data is scoped to organizations.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `name` | VARCHAR(255) | NO | | Organization name |
| `slug` | VARCHAR(50) | NO | | URL-friendly identifier (unique, indexed) |
| `type` | OrganizationType | NO | | VIBOTAJ, BUYER, SUPPLIER, LOGISTICS_AGENT |
| `status` | OrganizationStatus | NO | ACTIVE | ACTIVE, SUSPENDED, PENDING_SETUP |
| `contact_email` | VARCHAR(255) | NO | | Primary contact email |
| `contact_phone` | VARCHAR(50) | YES | | Phone number |
| `address` | JSONB | NO | {} | Flexible address data |
| `tax_id` | VARCHAR(100) | YES | | Tax identification number |
| `registration_number` | VARCHAR(100) | YES | | Business registration number |
| `logo_url` | VARCHAR(500) | YES | | Logo URL |
| `settings` | JSONB | NO | {} | Organization settings |
| `created_at` | TIMESTAMP | NO | now() | |
| `updated_at` | TIMESTAMP | NO | now() | |
| `created_by` | UUID | YES | | FK → users.id |

**Indexes:**
- `ix_organizations_type_status` (type, status)
- `ix_organizations_name` (name)
- UNIQUE on `slug`

---

### 2. users

System users with global roles.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `email` | VARCHAR(255) | NO | | Unique, indexed |
| `hashed_password` | VARCHAR(255) | NO | | Bcrypt hash |
| `full_name` | VARCHAR(100) | NO | | |
| `role` | UserRole | NO | VIEWER | System-wide role |
| `is_active` | BOOLEAN | NO | true | Account status |
| `organization_id` | UUID | NO | | FK → organizations.id |
| `created_at` | TIMESTAMP | NO | now() | |
| `updated_at` | TIMESTAMP | NO | now() | |
| `last_login` | TIMESTAMP | YES | | |

**Indexes:**
- UNIQUE on `email`

---

### 3. organization_memberships

Links users to organizations with org-specific roles.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `user_id` | UUID | NO | | FK → users.id |
| `organization_id` | UUID | NO | | FK → organizations.id |
| `org_role` | OrgRole | NO | MEMBER | ADMIN, MANAGER, MEMBER, VIEWER |
| `status` | MembershipStatus | NO | ACTIVE | ACTIVE, SUSPENDED, PENDING |
| `is_primary` | BOOLEAN | NO | false | Primary organization flag |
| `joined_at` | TIMESTAMP | NO | now() | |
| `last_active_at` | TIMESTAMP | NO | now() | |
| `invited_by` | UUID | YES | | FK → users.id |
| `invitation_id` | UUID | YES | | FK → invitations.id |

**Constraints:**
- UNIQUE on (user_id, organization_id)

**Indexes:**
- `ix_membership_user_org` (user_id, organization_id)
- `ix_membership_org_role` (organization_id, org_role)
- `ix_membership_user_primary` (user_id, is_primary)

---

### 4. invitations

Organization membership invitations.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `organization_id` | UUID | NO | | FK → organizations.id |
| `email` | VARCHAR(255) | NO | | Invited email |
| `org_role` | OrgRole | NO | | Role to assign |
| `token_hash` | VARCHAR(64) | NO | | Secure token hash (unique) |
| `status` | InvitationStatus | NO | PENDING | PENDING, ACCEPTED, EXPIRED, REVOKED |
| `expires_at` | TIMESTAMP | NO | | Expiration time |
| `created_at` | TIMESTAMP | NO | now() | |
| `created_by` | UUID | NO | | FK → users.id |
| `accepted_at` | TIMESTAMP | YES | | |
| `accepted_by` | UUID | YES | | FK → users.id |
| `invitation_metadata` | JSONB | NO | {} | |

**Indexes:**
- `ix_invitation_org_email` (organization_id, email)
- `ix_invitation_status` (status)
- `ix_invitation_expires` (expires_at)
- UNIQUE on `token_hash`

---

### 5. shipments

Core business entity for container shipments.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `reference` | VARCHAR(50) | NO | | Unique reference (e.g., VIBO-2026-001) |
| `container_number` | VARCHAR(20) | NO | | ISO 6346 format |
| `bl_number` | VARCHAR(50) | YES | | Bill of Lading |
| `booking_ref` | VARCHAR(50) | YES | | Booking reference |
| `vessel_name` | VARCHAR(100) | YES | | |
| `voyage_number` | VARCHAR(50) | YES | | |
| `carrier_code` | VARCHAR(10) | YES | | e.g., MAEU, MSCU |
| `carrier_name` | VARCHAR(100) | YES | | e.g., Maersk |
| `etd` | TIMESTAMP | YES | | Estimated departure |
| `eta` | TIMESTAMP | YES | | Estimated arrival |
| `atd` | TIMESTAMP | YES | | Actual departure |
| `ata` | TIMESTAMP | YES | | Actual arrival |
| `pol_code` | VARCHAR(5) | YES | | Port of Loading UN/LOCODE |
| `pol_name` | VARCHAR(100) | YES | | |
| `pod_code` | VARCHAR(5) | YES | | Port of Discharge UN/LOCODE |
| `pod_name` | VARCHAR(100) | YES | | |
| `incoterms` | VARCHAR(10) | YES | | FOB, CIF, etc. |
| `status` | ShipmentStatus | NO | DRAFT | |
| `product_type` | ProductType | YES | | Determines doc requirements |
| `exporter_name` | VARCHAR(255) | YES | | |
| `importer_name` | VARCHAR(255) | YES | | |
| `eudr_compliant` | BOOLEAN | NO | false | |
| `eudr_statement_id` | VARCHAR(100) | YES | | DDS reference |
| `organization_id` | UUID | NO | | FK → organizations.id |
| `buyer_organization_id` | UUID | YES | | FK → organizations.id |
| `created_at` | TIMESTAMP | NO | now() | |
| `updated_at` | TIMESTAMP | NO | now() | |

**Indexes:**
- `ix_shipments_organization_id` (organization_id)
- `ix_shipments_buyer_organization_id` (buyer_organization_id)
- `ix_shipments_product_type` (product_type)
- UNIQUE on `reference`

---

### 6. documents

Uploaded documents attached to shipments.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `shipment_id` | UUID | NO | | FK → shipments.id (CASCADE) |
| `name` | VARCHAR(255) | NO | | Display name |
| `document_type` | DocumentType | NO | | Classification |
| `status` | DocumentStatus | NO | UPLOADED | Workflow status |
| `file_name` | VARCHAR(255) | YES | | Original filename |
| `file_path` | VARCHAR(500) | YES | | Storage path |
| `file_size` | INTEGER | YES | | Bytes |
| `mime_type` | VARCHAR(100) | YES | | |
| `document_date` | TIMESTAMP(tz) | YES | | Issue date |
| `expiry_date` | TIMESTAMP(tz) | YES | | Expiration |
| `issuer` | VARCHAR(255) | YES | | Issuing authority |
| `reference_number` | VARCHAR(100) | YES | | Document reference |
| `validation_notes` | TEXT | YES | | |
| `validated_by` | UUID | YES | | FK → users.id |
| `validated_at` | TIMESTAMP(tz) | YES | | |
| `uploaded_by` | UUID | YES | | FK → users.id |
| `organization_id` | UUID | YES | | FK → organizations.id |
| `created_at` | TIMESTAMP(tz) | NO | now() | |
| `updated_at` | TIMESTAMP(tz) | NO | now() | |

---

### 7. document_contents

Individual documents within combined PDFs.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `document_id` | UUID | NO | | FK → documents.id (CASCADE) |
| `document_type` | DocumentType | NO | | Detected type |
| `status` | DocumentStatus | NO | UPLOADED | |
| `page_start` | INTEGER | NO | | Starting page |
| `page_end` | INTEGER | NO | | Ending page |
| `reference_number` | VARCHAR(100) | YES | | Extracted reference |
| `detected_fields` | JSONB | NO | {} | Extracted metadata |
| `confidence_score` | FLOAT | NO | 0.0 | 0.0-1.0 |
| `detection_method` | VARCHAR(50) | NO | | "ai", "keyword", "manual" |
| `validation_notes` | VARCHAR(1000) | YES | | |
| `validated_at` | TIMESTAMP | YES | | |
| `validated_by` | VARCHAR(100) | YES | | Validator name (not FK) |
| `created_at` | TIMESTAMP | NO | now() | |
| `updated_at` | TIMESTAMP | NO | now() | |

---

### 8. reference_registry

Tracks document references for duplicate detection.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `shipment_id` | UUID | NO | | FK → shipments.id (CASCADE) |
| `reference_number` | VARCHAR(100) | NO | | Document reference |
| `document_type` | DocumentType | NO | | |
| `document_content_id` | UUID | YES | | FK → document_contents.id (SET NULL) |
| `document_id` | UUID | YES | | FK → documents.id (SET NULL) |
| `first_seen_at` | TIMESTAMP | NO | now() | |

**Constraints:**
- UNIQUE on (shipment_id, reference_number, document_type)

---

### 9. products

Goods/commodities in shipments.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `shipment_id` | UUID | NO | | FK → shipments.id (CASCADE) |
| `organization_id` | UUID | NO | | FK → organizations.id |
| `name` | VARCHAR(255) | NO | | |
| `description` | TEXT | YES | | |
| `hs_code` | VARCHAR(20) | YES | | Harmonized System code |
| `quantity_net_kg` | FLOAT | YES | | |
| `quantity_gross_kg` | FLOAT | YES | | |
| `quantity_units` | INTEGER | YES | | |
| `packaging` | VARCHAR(100) | YES | | |
| `batch_number` | VARCHAR(100) | YES | | |
| `lot_number` | VARCHAR(100) | YES | | |
| `moisture_content` | FLOAT | YES | | Percentage |
| `quality_grade` | VARCHAR(50) | YES | | |
| `created_at` | TIMESTAMP(tz) | NO | now() | |
| `updated_at` | TIMESTAMP(tz) | NO | now() | |

**Indexes:**
- `ix_products_shipment_id` (shipment_id)
- `ix_products_organization_id` (organization_id)

---

### 10. origins

EUDR compliance origin data.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `shipment_id` | UUID | NO | | FK → shipments.id |
| `organization_id` | UUID | NO | | FK → organizations.id |
| `farm_name` | VARCHAR(255) | YES | | |
| `plot_identifier` | VARCHAR(100) | YES | | |
| `latitude` | FLOAT | YES | | GPS coordinate |
| `longitude` | FLOAT | YES | | GPS coordinate |
| `country` | VARCHAR(100) | NO | | |
| `region` | VARCHAR(255) | YES | | |
| `address` | TEXT | YES | | |
| `production_date` | TIMESTAMP(tz) | YES | | |
| `harvest_date` | TIMESTAMP(tz) | YES | | |
| `supplier_name` | VARCHAR(255) | YES | | |
| `supplier_id` | VARCHAR(100) | YES | | |
| `deforestation_free` | BOOLEAN | YES | | |
| `eudr_cutoff_compliant` | BOOLEAN | YES | | |
| `risk_level` | RiskLevel | YES | | LOW, MEDIUM, HIGH, CRITICAL |
| `verified` | BOOLEAN | NO | false | |
| `verified_by` | UUID | YES | | Not a FK (should be) |
| `verified_at` | TIMESTAMP(tz) | YES | | |
| `verification_notes` | TEXT | YES | | |
| `created_at` | TIMESTAMP(tz) | NO | now() | |
| `updated_at` | TIMESTAMP(tz) | NO | now() | |

**Note:** Horn & Hoof products (HS 0506/0507) should NOT have latitude/longitude or risk_level per COMPLIANCE_MATRIX.md.

---

### 11. container_events

Tracking milestones from JSONCargo API.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `shipment_id` | UUID | NO | | FK → shipments.id (CASCADE) |
| `organization_id` | UUID | NO | | FK → organizations.id |
| `event_status` | EventStatus | NO | | Event type |
| `event_time` | TIMESTAMP(tz) | NO | | When event occurred |
| `location_code` | VARCHAR(20) | YES | | UN/LOCODE |
| `location_name` | VARCHAR(255) | YES | | |
| `vessel_name` | VARCHAR(100) | YES | | |
| `voyage_number` | VARCHAR(50) | YES | | |
| `description` | TEXT | YES | | |
| `source` | VARCHAR(50) | YES | | API source |
| `raw_data` | JSONB | YES | | Original API response |
| `created_at` | TIMESTAMP(tz) | NO | now() | |

**Indexes:**
- `ix_container_events_shipment_id` (shipment_id)
- `ix_container_events_event_time` (event_time)
- `ix_container_events_organization_id` (organization_id)

---

### 12. notifications

User notification queue.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `user_id` | VARCHAR(100) | NO | | User identifier (not FK) |
| `type` | VARCHAR(50) | NO | | Notification type |
| `title` | VARCHAR(255) | NO | | |
| `message` | TEXT | NO | | |
| `data` | JSONB | NO | {} | Related entity data |
| `read` | BOOLEAN | NO | false | |
| `read_at` | TIMESTAMP | YES | | |
| `created_at` | TIMESTAMP | NO | now() | |

**Indexes:**
- `ix_notifications_user_read` (user_id, read)
- `ix_notifications_user_created` (user_id, created_at)

**Note:** `user_id` is String, not UUID FK. This is a known limitation.

---

### 13. audit_logs

Compliance audit trail.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NO | uuid4() | Primary Key |
| `organization_id` | UUID | YES | | FK → organizations.id (nullable for system actions) |
| `user_id` | VARCHAR(100) | YES | | |
| `username` | VARCHAR(100) | YES | | |
| `ip_address` | VARCHAR(45) | YES | | IPv4/IPv6 |
| `user_agent` | VARCHAR(500) | YES | | |
| `action` | VARCHAR(100) | NO | | e.g., "shipment.view" |
| `resource_type` | VARCHAR(50) | YES | | "shipment", "document", etc. |
| `resource_id` | VARCHAR(100) | YES | | |
| `request_id` | VARCHAR(100) | YES | | Correlation ID |
| `method` | VARCHAR(10) | YES | | HTTP method |
| `path` | VARCHAR(500) | YES | | |
| `status_code` | VARCHAR(10) | YES | | |
| `success` | VARCHAR(10) | NO | | "true" or "false" |
| `details` | JSONB | NO | {} | |
| `error_message` | TEXT | YES | | |
| `duration_ms` | VARCHAR(20) | YES | | |
| `timestamp` | TIMESTAMP | NO | now() | |

**Indexes:**
- `ix_audit_logs_user_timestamp` (username, timestamp)
- `ix_audit_logs_action_timestamp` (action, timestamp)
- `ix_audit_logs_resource` (resource_type, resource_id)
- `ix_audit_logs_organization_id` (organization_id)

---

### 14. parties (Legacy - Unused)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary Key |
| `type` | PartyType | NO | SUPPLIER, BUYER, SHIPPER, CONSIGNEE, NOTIFY_PARTY |
| `company_name` | VARCHAR(255) | NO | |
| `contact_name` | VARCHAR(255) | YES | |
| `email` | VARCHAR(255) | YES | |
| `phone` | VARCHAR(50) | YES | |
| `address` | VARCHAR(500) | YES | |
| `city` | VARCHAR(100) | YES | |
| `country` | VARCHAR(2) | YES | ISO code |
| `registration_number` | VARCHAR(100) | YES | |
| `tax_id` | VARCHAR(100) | YES | |
| `created_at` | TIMESTAMP | NO | |
| `updated_at` | TIMESTAMP | NO | |

**Status:** DEPRECATED. Shipments now use `exporter_name`/`importer_name` strings.

---

## Enums

### OrganizationType
```python
VIBOTAJ = "vibotaj"         # Platform owner
BUYER = "buyer"             # HAGES, Witatrade, etc.
SUPPLIER = "supplier"       # Suppliers
LOGISTICS_AGENT = "logistics_agent"
```

### OrganizationStatus
```python
ACTIVE = "active"
SUSPENDED = "suspended"
PENDING_SETUP = "pending_setup"
```

### UserRole (System-wide)
```python
ADMIN = "admin"             # Level 6 - Full access
COMPLIANCE = "compliance"   # Level 5 - Validate documents
LOGISTICS_AGENT = "logistics_agent"  # Level 4 - Manage shipments
BUYER = "buyer"             # Level 3 - Read-only shipments
SUPPLIER = "supplier"       # Level 2 - Upload certs
VIEWER = "viewer"           # Level 1 - Read-only
```

### OrgRole (Organization-specific)
```python
ADMIN = "admin"     # Level 4
MANAGER = "manager" # Level 3
MEMBER = "member"   # Level 2
VIEWER = "viewer"   # Level 1
```

### MembershipStatus
```python
ACTIVE = "active"
SUSPENDED = "suspended"
PENDING = "pending"
```

### InvitationStatus
```python
PENDING = "pending"
ACCEPTED = "accepted"
EXPIRED = "expired"
REVOKED = "revoked"
```

### ShipmentStatus
```python
DRAFT = "draft"
DOCS_PENDING = "docs_pending"
DOCS_COMPLETE = "docs_complete"
IN_TRANSIT = "in_transit"
ARRIVED = "arrived"
CUSTOMS = "customs"
DELIVERED = "delivered"
ARCHIVED = "archived"
```

### ProductType
```python
HORN_HOOF = "horn_hoof"       # HS 0506/0507 - NO EUDR
SWEET_POTATO = "sweet_potato" # HS 0714 - NO EUDR
HIBISCUS = "hibiscus"         # HS 0902 - NO EUDR
GINGER = "ginger"             # HS 0910 - NO EUDR
COCOA = "cocoa"               # HS 1801 - EUDR REQUIRED
OTHER = "other"
```

### DocumentType
```python
BILL_OF_LADING = "bill_of_lading"
COMMERCIAL_INVOICE = "commercial_invoice"
PACKING_LIST = "packing_list"
CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
PHYTOSANITARY_CERTIFICATE = "phytosanitary_certificate"
FUMIGATION_CERTIFICATE = "fumigation_certificate"
SANITARY_CERTIFICATE = "sanitary_certificate"
INSURANCE_CERTIFICATE = "insurance_certificate"
CUSTOMS_DECLARATION = "customs_declaration"
CONTRACT = "contract"
EUDR_DUE_DILIGENCE = "eudr_due_diligence"
QUALITY_CERTIFICATE = "quality_certificate"
EU_TRACES_CERTIFICATE = "eu_traces_certificate"      # Horn & Hoof
VETERINARY_HEALTH_CERTIFICATE = "veterinary_health_certificate"  # Horn & Hoof
EXPORT_DECLARATION = "export_declaration"
OTHER = "other"
```

### DocumentStatus
```python
# Current values
UPLOADED = "uploaded"
PENDING_VALIDATION = "pending_validation"
VALIDATED = "validated"
REJECTED = "rejected"
EXPIRED = "expired"

# Legacy values (backward compatibility)
DRAFT = "draft"
COMPLIANCE_OK = "compliance_ok"
COMPLIANCE_FAILED = "compliance_failed"
LINKED = "linked"
ARCHIVED = "archived"
```

### EventStatus
```python
BOOKED = "booked"
GATE_IN = "gate_in"
LOADED = "loaded"
DEPARTED = "departed"
IN_TRANSIT = "in_transit"
TRANSSHIPMENT = "transshipment"
ARRIVED = "arrived"
DISCHARGED = "discharged"
GATE_OUT = "gate_out"
DELIVERED = "delivered"
OTHER = "other"
```

### RiskLevel
```python
LOW = "low"
MEDIUM = "medium"
HIGH = "high"
CRITICAL = "critical"
```

### NotificationType
```python
DOCUMENT_UPLOADED = "document_uploaded"
DOCUMENT_VALIDATED = "document_validated"
DOCUMENT_REJECTED = "document_rejected"
ETA_CHANGED = "eta_changed"
SHIPMENT_ARRIVED = "shipment_arrived"
SHIPMENT_DEPARTED = "shipment_departed"
SHIPMENT_DELIVERED = "shipment_delivered"
COMPLIANCE_ALERT = "compliance_alert"
EXPIRY_WARNING = "expiry_warning"
SYSTEM_ALERT = "system_alert"
```

---

## Migration History

| Version | Date | Description |
|---------|------|-------------|
| 20260109_0001 | 2026-01-09 | Baseline reset - creates all tables from models |
| 20260109_0002 | 2026-01-09 | Add buyer_organization_id to shipments |
| 20260109_0003 | 2026-01-09 | Add product_type to shipments |

---

## Known Schema Issues

See [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) for detailed tracking of schema inconsistencies and planned fixes.

1. **notifications.user_id** - String instead of UUID FK
2. **document_contents.validated_by** - String instead of UUID FK
3. **origins.verified_by** - UUID but not a FK constraint
4. **DateTime columns** - Inconsistent timezone handling
5. **parties table** - Deprecated, unused
6. **DocumentStatus enum** - Mixed current/legacy values
