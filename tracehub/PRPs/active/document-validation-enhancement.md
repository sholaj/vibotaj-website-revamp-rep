# PRP: Document Validation & Compliance Enhancement

**Status:** Draft
**Priority:** P0 (Critical)
**Sprint:** 13-15 (Multi-sprint)
**Author:** TraceHub Engineering
**Created:** 2026-01-18
**Last Updated:** 2026-01-18

---

## 1. Overview

**Feature Name:** Document Validation & Compliance Enhancement
**Product:** TraceHub Compliance Platform
**Goal:** Strengthen the robustness and reliability of document validation across the TraceHub platform.

### Business Value

The existing system has several reliability gaps:
- Documents are sometimes ignored or misclassified with 0% AI confidence
- Documents marked as "missing" even when drafts exist
- Duplicate documents treated as errors without resolution workflow
- Critical metadata extraction failures (vet cert dates, signatories)
- No cross-document validation for consistency

This PRP delivers a comprehensive, scalable, and test-driven approach to document validation that:
- Ensures every required document is ingested, recognized, and validated
- Detects duplicates and provides version management
- Checks content completeness and consistency
- Supports cross-document validation (BoL vs packing list vs certificates)
- Maintains audit trail with override workflow
- Applies to both new uploads AND historic shipments

---

## 2. Problems Addressed

| ID | Problem | Impact | Evidence |
|----|---------|--------|----------|
| P1 | Ignored/Unrecognized Documents | Documents flagged as "unrelated" with 0% confidence silently dropped | Validation reports show missing docs that were uploaded |
| P2 | Missing Document Detection | Drafts counted as "missing" | EU TRACES flagged missing when draft present |
| P3 | Duplicate Handling | Two CoOs flagged as error, no resolution path | No version selection mechanism |
| P4 | Incomplete Metadata Extraction | Vet cert issue date and signer not extracted | Cannot enforce date rules |
| P5 | Weak Content Validation | No weight/HS code comparison across docs | Mismatches go undetected |
| P6 | No Cross-Document Validation | Container numbers not verified across BoL/packing list | Inconsistencies slip through |
| P7 | Limited Override Workflow | Override doesn't trigger re-validation | Stale issues persist |

---

## 3. Scope

### In-Scope

- **Document Ingestion & Classification**: Every upload classified or flagged for manual review
- **Presence & Completeness Checks**: Required docs based on HS codes, destination, product type
- **Document Versioning**: Duplicate detection with version selection (not just errors)
- **Content Relevance Scoring**: Low confidence routes to manual review, not silent rejection
- **Metadata Extraction & Validation**:
  - Vet cert issue date <= vessel ETD
  - Authorized signer presence (warning if missing)
  - B/L and container number consistency
  - Weight/volume tolerance (±5%)
- **Cross-Document Validation**: Compare fields across BoL, packing list, certificates, invoices
- **Override & Audit Workflow**: Structured override with re-validation capability
- **Historic Shipment Revalidation**: Backfill existing documents to new schema
- **TDD Implementation**: Write failing tests first at all layers

### Out-of-Scope

- OCR/LLM parsing improvements (separate BoL Parsing PRP)
- Container tracking enhancements (separate Container Tracking PRP)
- Full cross-document validation for ALL document types (focus on key 8 types)
- Full UI redesign (minimal changes for new validation states)

---

## 4. Technical Approach

### 4.1 Canonical Document Schema

Extend the existing `Document` model to support canonical extracted data for all document types:

```python
class CanonicalDocumentData(BaseModel):
    """Canonical extracted data for any document type."""
    document_type: DocumentType
    file_id: UUID
    upload_timestamp: datetime
    parsed_at: Optional[datetime]
    parser_version: str = "1.0.0"

    # Extracted fields (document-type specific)
    fields: Dict[str, Any] = {}

    # Confidence and raw data
    raw_text: Optional[str] = None
    confidence_scores: Dict[str, float] = {}

    # Validation state
    status: DocumentValidationStatus  # draft, validated, invalid, overridden
    issues: List[DocumentIssue] = []

    # Versioning
    version: int = 1
    is_primary: bool = True
    supersedes_id: Optional[UUID] = None
```

### 4.2 Document Types and Required Fields

| Document Type | Required Fields | Cross-Check Fields |
|---------------|-----------------|-------------------|
| `bill_of_lading` | bol_number, shipper, consignee, containers, cargo | container_numbers, weights, hs_codes |
| `packing_list` | item_count, gross_weight, net_weight, container_refs | weights, hs_codes, container_numbers |
| `certificate_of_origin` | origin_country, exporter, certificate_number | product_description, hs_codes |
| `vet_health_certificate` | issue_date, signer_name, authority, certificate_number | product_batch, issue_date vs ETD |
| `fumigation_certificate` | treatment_date, certificate_number, container_refs | container_numbers |
| `commercial_invoice` | invoice_number, total_value, line_items | quantities, weights, values |
| `export_declaration` | declaration_number, customs_office, export_date | hs_codes, weights |
| `eu_traces_certificate` | traces_reference, issue_date, validity | product_batch |

### 4.3 Validation Rules Engine Extension

Extend existing `bol_rules/engine.py` to support document-level and cross-document rules:

```python
class DocumentValidationRule(BaseModel):
    """Rule for validating individual documents."""
    id: str
    name: str
    document_type: DocumentType
    field: str
    condition: ConditionType
    value: Optional[Any] = None
    severity: Severity  # ERROR, WARNING, INFO
    message: str


class CrossDocumentRule(BaseModel):
    """Rule for validating consistency across documents."""
    id: str
    name: str
    source_doc: DocumentType
    source_field: str
    target_doc: DocumentType
    target_field: str
    comparison: ComparisonType  # EQUALS, WITHIN_TOLERANCE, CONTAINS
    tolerance: Optional[float] = None  # For numeric comparisons
    severity: Severity
    message: str
```

### 4.4 Document Validation Service

```python
class DocumentValidationService:
    """Stateless service for document validation."""

    async def classify_document(
        self,
        file_content: bytes,
        file_name: str,
        type_hint: Optional[DocumentType] = None
    ) -> ClassificationResult:
        """Classify document type with confidence score."""

    async def extract_and_map(
        self,
        document_id: UUID,
        document_type: DocumentType
    ) -> CanonicalDocumentData:
        """Extract fields and map to canonical schema."""

    async def validate_document(
        self,
        canonical_data: CanonicalDocumentData,
        shipment: Shipment
    ) -> List[DocumentIssue]:
        """Run document-level validation rules."""

    async def validate_cross_document(
        self,
        documents: List[CanonicalDocumentData],
        shipment: Shipment
    ) -> List[DocumentIssue]:
        """Run cross-document consistency checks."""

    async def handle_duplicate(
        self,
        existing_doc: Document,
        new_doc: Document,
        user_selection: Optional[UUID] = None
    ) -> Document:
        """Manage duplicate versions, return primary."""

    async def revalidate_shipment(
        self,
        shipment_id: UUID,
        force: bool = False
    ) -> ValidationSummary:
        """Revalidate all documents for a shipment."""
```

### 4.5 Presence & Uniqueness Engine

```python
def get_required_documents(shipment: Shipment) -> List[RequiredDocument]:
    """Determine required document types based on shipment context."""
    hs_codes = shipment.get_hs_codes()
    required = [
        RequiredDocument(DocumentType.BILL_OF_LADING, mandatory=True),
        RequiredDocument(DocumentType.COMMERCIAL_INVOICE, mandatory=True),
        RequiredDocument(DocumentType.CERTIFICATE_OF_ORIGIN, mandatory=True),
        RequiredDocument(DocumentType.PACKING_LIST, mandatory=True),
    ]

    # Horn & Hoof (HS 0506/0507) - NO EUDR
    if any(code.startswith(('0506', '0507')) for code in hs_codes):
        required.extend([
            RequiredDocument(DocumentType.EU_TRACES_CERTIFICATE, mandatory=True),
            RequiredDocument(DocumentType.VETERINARY_HEALTH_CERTIFICATE, mandatory=True),
            RequiredDocument(DocumentType.FUMIGATION_CERTIFICATE, mandatory=True),
        ])

    # Plant products
    if any(code.startswith(('0714', '0902', '0910')) for code in hs_codes):
        required.append(
            RequiredDocument(DocumentType.PHYTOSANITARY_CERTIFICATE, mandatory=True)
        )

    return required


def check_presence(
    shipment: Shipment,
    documents: List[Document]
) -> List[PresenceCheckResult]:
    """Check which required documents are present/missing/draft."""
    required = get_required_documents(shipment)
    results = []

    for req in required:
        matching = [d for d in documents if d.document_type == req.document_type]
        if not matching:
            status = "missing"
        elif all(d.status == DocumentStatus.DRAFT for d in matching):
            status = "draft"  # Not missing - just not validated yet
        elif any(d.status == DocumentStatus.VALIDATED for d in matching):
            status = "validated"
        else:
            status = "uploaded"

        results.append(PresenceCheckResult(
            document_type=req.document_type,
            status=status,
            mandatory=req.mandatory,
            count=len(matching),
            has_duplicates=len(matching) > 1
        ))

    return results
```

### 4.6 Cross-Document Validation Rules

```python
CROSS_DOCUMENT_RULES = [
    # B/L vs Packing List
    CrossDocumentRule(
        id="XD-001",
        name="Container Number Consistency",
        source_doc=DocumentType.BILL_OF_LADING,
        source_field="containers[*].number",
        target_doc=DocumentType.PACKING_LIST,
        target_field="container_refs",
        comparison=ComparisonType.SET_EQUALS,
        severity="ERROR",
        message="Container numbers in B/L do not match packing list"
    ),

    CrossDocumentRule(
        id="XD-002",
        name="Gross Weight Tolerance",
        source_doc=DocumentType.BILL_OF_LADING,
        source_field="cargo[*].gross_weight_kg",
        target_doc=DocumentType.PACKING_LIST,
        target_field="gross_weight_kg",
        comparison=ComparisonType.WITHIN_TOLERANCE,
        tolerance=0.05,  # 5% tolerance
        severity="WARNING",
        message="B/L weight differs from packing list by more than 5%"
    ),

    CrossDocumentRule(
        id="XD-003",
        name="HS Code Consistency",
        source_doc=DocumentType.BILL_OF_LADING,
        source_field="cargo[*].hs_code",
        target_doc=DocumentType.CERTIFICATE_OF_ORIGIN,
        target_field="hs_codes",
        comparison=ComparisonType.SET_CONTAINS,
        severity="ERROR",
        message="HS codes on CoO do not match B/L cargo"
    ),

    # Packing List vs Invoice
    CrossDocumentRule(
        id="XD-004",
        name="Invoice Weight Match",
        source_doc=DocumentType.PACKING_LIST,
        source_field="net_weight_kg",
        target_doc=DocumentType.COMMERCIAL_INVOICE,
        target_field="total_net_weight_kg",
        comparison=ComparisonType.WITHIN_TOLERANCE,
        tolerance=0.02,  # 2% tolerance
        severity="WARNING",
        message="Packing list weight differs from invoice"
    ),

    # Vet Cert vs Shipment
    CrossDocumentRule(
        id="XD-005",
        name="Vet Cert Before ETD",
        source_doc=DocumentType.VETERINARY_HEALTH_CERTIFICATE,
        source_field="issue_date",
        target_doc=None,  # Compare to shipment metadata
        target_field="shipment.etd",
        comparison=ComparisonType.DATE_BEFORE_OR_EQUAL,
        severity="ERROR",
        message="Vet certificate must be issued before vessel departure"
    ),

    # Container Numbers Across All Docs
    CrossDocumentRule(
        id="XD-006",
        name="Fumigation Certificate Container Match",
        source_doc=DocumentType.FUMIGATION_CERTIFICATE,
        source_field="container_refs",
        target_doc=DocumentType.BILL_OF_LADING,
        target_field="containers[*].number",
        comparison=ComparisonType.SET_SUBSET,
        severity="ERROR",
        message="Fumigation certificate references unknown containers"
    ),
]
```

### 4.7 Database Migrations (Idempotent)

```python
# alembic/versions/20260120_add_document_validation_fields.py

def column_exists(table, column):
    """Check if column exists (for idempotency)."""
    ...

def upgrade():
    # Add canonical_data JSONB column if not exists
    if not column_exists('documents', 'canonical_data'):
        op.add_column('documents', sa.Column('canonical_data', JSONB, nullable=True))

    # Add versioning fields
    if not column_exists('documents', 'version'):
        op.add_column('documents', sa.Column('version', sa.Integer, default=1))
    if not column_exists('documents', 'is_primary'):
        op.add_column('documents', sa.Column('is_primary', sa.Boolean, default=True))
    if not column_exists('documents', 'supersedes_id'):
        op.add_column('documents', sa.Column(
            'supersedes_id',
            UUID(as_uuid=True),
            ForeignKey('documents.id'),
            nullable=True
        ))

    # Add classification confidence
    if not column_exists('documents', 'classification_confidence'):
        op.add_column('documents', sa.Column('classification_confidence', sa.Float, nullable=True))

    # Create document_issues table if not exists
    if not table_exists('document_issues'):
        op.create_table(
            'document_issues',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE')),
            sa.Column('rule_id', sa.String(50)),
            sa.Column('severity', sa.String(20)),
            sa.Column('message', sa.Text),
            sa.Column('field', sa.String(100)),
            sa.Column('expected_value', sa.Text),
            sa.Column('actual_value', sa.Text),
            sa.Column('is_overridden', sa.Boolean, default=False),
            sa.Column('overridden_by', UUID(as_uuid=True), ForeignKey('users.id')),
            sa.Column('overridden_at', sa.DateTime(timezone=True)),
            sa.Column('override_reason', sa.Text),
            sa.Column('created_at', sa.DateTime(timezone=True), default=func.now()),
        )


def downgrade():
    # Safe downgrade - keep data, remove new columns
    op.drop_table('document_issues')
    op.drop_column('documents', 'supersedes_id')
    op.drop_column('documents', 'is_primary')
    op.drop_column('documents', 'version')
    op.drop_column('documents', 'classification_confidence')
    op.drop_column('documents', 'canonical_data')
```

---

## 5. Files to Modify

### Backend - New Files

| File | Description |
|------|-------------|
| `app/schemas/document_validation.py` | Canonical document schemas, issue types |
| `app/services/document_validation.py` | DocumentValidationService implementation |
| `app/services/document_rules/` | Document-level and cross-document rules |
| `app/services/document_presence.py` | Presence and uniqueness checking |
| `app/services/document_revalidation.py` | Background revalidation job |
| `alembic/versions/20260120_*.py` | Database migrations |

### Backend - Modify

| File | Changes |
|------|---------|
| `app/models/document.py` | Add versioning fields, canonical_data JSONB |
| `app/routers/documents.py` | Add revalidation endpoint, version selection |
| `app/services/bol_rules/engine.py` | Extend for document-level rules |
| `app/services/bol_parser.py` | Extract additional metadata fields |

### Frontend - Modify

| File | Changes |
|------|---------|
| `components/DocumentReviewPanel.tsx` | Show issues, version selector, override UI |
| `components/DocumentUploadModal.tsx` | Real-time validation feedback |
| `types/index.ts` | Add document validation types |
| `api/client.ts` | Add revalidation API calls |

---

## 6. Test Requirements

### Unit Tests (Write First - TDD)

```python
# tests/test_document_validation_rules.py
class TestDocumentValidationRules:
    def test_vet_cert_issue_date_required(self):
        """Vet cert without issue date raises ERROR."""

    def test_vet_cert_date_before_etd(self):
        """Vet cert date after ETD raises ERROR."""

    def test_signer_missing_raises_warning(self):
        """Missing authorized signer raises WARNING."""

    def test_weight_tolerance_5_percent(self):
        """Weight difference > 5% raises WARNING."""


# tests/test_cross_document_validation.py
class TestCrossDocumentValidation:
    def test_bol_packing_list_container_mismatch(self):
        """Different containers in BoL vs packing list raises ERROR."""

    def test_bol_coo_hs_code_mismatch(self):
        """HS codes not matching raises ERROR."""

    def test_weight_tolerance_across_docs(self):
        """Weight within 5% tolerance passes."""


# tests/test_document_presence.py
class TestDocumentPresence:
    def test_draft_not_counted_as_missing(self):
        """Documents in draft status are not 'missing'."""

    def test_duplicate_detection(self):
        """Multiple docs of same type detected as duplicates."""

    def test_horn_hoof_requires_traces(self):
        """HS 0506/0507 requires EU TRACES certificate."""


# tests/test_document_versioning.py
class TestDocumentVersioning:
    def test_version_increment_on_duplicate(self):
        """New duplicate gets version number + 1."""

    def test_select_primary_version(self):
        """User can select which version is primary."""

    def test_non_primary_excluded_from_validation(self):
        """Only primary versions are validated."""
```

### Integration Tests

```python
# tests/test_document_validation_integration.py
class TestDocumentValidationIntegration:
    async def test_upload_classification_flow(self):
        """Upload -> OCR -> classify -> map to schema."""

    async def test_revalidation_after_new_upload(self):
        """Uploading new doc triggers shipment revalidation."""

    async def test_override_clears_issue(self):
        """Override marks issue as resolved."""

    async def test_historic_shipment_revalidation(self):
        """Background job revalidates old shipments."""
```

### Migration Tests

```python
# tests/test_document_validation_migration.py
class TestMigrationIdempotency:
    def test_migration_runs_twice_safely(self):
        """Running migration twice has no effect."""

    def test_existing_documents_preserved(self):
        """Migration doesn't corrupt existing data."""

    def test_backfill_populates_canonical_data(self):
        """Backfill script populates canonical_data for existing docs."""
```

---

## 7. Compliance Check

**Product HS Codes Affected:**
- 0506, 0507 (Horn & Hoof) - NO EUDR
- 0714.20 (Sweet Potato Pellets) - NO EUDR
- 0902.10 (Hibiscus) - NO EUDR
- 0910.11 (Ginger) - NO EUDR

**EUDR Applicable:** NO for current products

**Required Documents by Product:**

| Product | Required Documents |
|---------|-------------------|
| Horn & Hoof | BoL, Invoice, CoO, Packing List, EU TRACES, Vet Health Cert, Fumigation Cert |
| Agricultural | BoL, Invoice, CoO, Packing List, Phytosanitary Cert |

**CRITICAL:** This PRP does NOT add any EUDR fields to Horn & Hoof documents.

---

## 8. Acceptance Criteria

### Functional

- [ ] Every uploaded document is classified or flagged for manual review (no silent drops)
- [ ] Documents in DRAFT status are NOT counted as "missing"
- [ ] Duplicate uploads create versions, not errors
- [ ] User can select which version is the "primary" for validation
- [ ] Vet cert issue date extraction works and is validated against ETD
- [ ] Authorized signer extraction works (warning if missing)
- [ ] Cross-document weight validation with 5% tolerance
- [ ] Cross-document container number validation
- [ ] Cross-document HS code validation
- [ ] Override workflow records reason and timestamp
- [ ] Re-validation clears resolved overrides
- [ ] Historic shipments can be revalidated via background job

### Technical

- [ ] All 160+ existing tests continue to pass
- [ ] New unit tests cover all validation rules
- [ ] Integration tests cover upload-to-validation flow
- [ ] Migration is idempotent (can run multiple times safely)
- [ ] No breaking changes to existing API contracts
- [ ] Performance: Validation completes in < 5 seconds per document

### Documentation

- [ ] API documentation updated for new endpoints
- [ ] Document validation rules documented in COMPLIANCE_MATRIX.md
- [ ] Override workflow documented for users

---

## 9. Security Considerations

- **Access Control**: Document validation respects organization_id multi-tenancy
- **Audit Trail**: All overrides logged with user, timestamp, reason
- **Data Privacy**: Raw document text stored securely, not exposed in logs
- **Input Validation**: File uploads validated for type and size before processing

---

## 10. Rollout Plan

### Phase 1: Foundation (Sprint 13)
1. Database migrations (idempotent)
2. Canonical document schema
3. Document-level validation rules
4. Unit tests

### Phase 2: Cross-Document Validation (Sprint 14)
1. Cross-document rules engine
2. Presence and uniqueness checks
3. Integration tests
4. Frontend: Issue display

### Phase 3: Revalidation & Polish (Sprint 15)
1. Historic shipment revalidation job
2. Override workflow improvements
3. Version selection UI
4. End-to-end testing

---

## 11. Dependencies

- Existing BoL Parsing PRP (for extraction logic)
- Existing Container Tracking PRP (for container number validation)
- Claude API access (for classification fallback)
- PostgreSQL JSONB support (for canonical_data storage)

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Historic revalidation overloads system | High | Batch processing with rate limiting |
| AI classification accuracy too low | Medium | Manual review workflow + confidence thresholds |
| Cross-document validation false positives | Medium | Configurable tolerances, override workflow |
| Breaking existing workflows | High | TDD, comprehensive regression tests |

---

## 13. Worked Example

**Shipment VIBO-2026-002 - Current State:**
- EU TRACES flagged as "missing" (draft exists)
- Two Bills of Lading uploaded (flagged as duplicate error)
- Vet cert missing issue date
- Documents marked "unrelated" with 0% confidence

**After Implementation:**
1. EU TRACES shows status "draft" (not missing)
2. Two BoLs become versions 1 and 2; user selects primary
3. Vet cert extraction issue logged: "Missing issue date - ERROR"
4. Low-confidence documents flagged for manual review with reclassification UI
5. Cross-document check: Container MSCU1234567 matches across BoL and packing list
6. Weight check: BoL shows 20,000 kg, packing list shows 19,800 kg (-1%) - PASS

---

## 14. Future Extensions (Backlog)

- Advanced AI classifier (domain-fine-tuned BERT)
- Full cross-document validation for all document types
- Automated remediation suggestions
- Integration with TRACES network for certificate verification
- Improved OCR preprocessing (deskew, noise removal)

---

**Prepared By:** TraceHub Engineering
**Review Frequency:** Before each sprint
**Next Review:** Sprint 13 Planning
