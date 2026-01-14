# PRP: Document Validation Rules Engine

**Status:** Draft
**Priority:** P1
**Sprint:** 14
**Created:** 2026-01-14
**Updated:** 2026-01-14
**Author:** AI-Assisted

## Overview

Implement a modular, extensible document validation rules engine for TraceHub shipments. The system will validate that all required documents for horns and hooves compliance are present, unique, meet business rules, and **reject unrelated documents using AI classification**. The architecture must support easy addition of new validation rules as regulatory requirements evolve.

### Business Value
- **Compliance Assurance:** Ensure every shipment has all required documents before export
- **Error Prevention:** Catch missing or duplicate documents before they cause delays
- **AI-Powered Rejection:** Automatically detect and reject unrelated/incorrect documents
- **Audit Trail:** Maintain comprehensive logs of all validations for regulatory compliance
- **Extensibility:** Allow business users to add new rules without code changes (future)

---

## TDD Implementation Workflow

This feature will be implemented using **Test-Driven Development (TDD)**. All tests must be written BEFORE implementation code.

### TDD Principles

1. **Red-Green-Refactor Cycle:**
   - RED: Write a failing test first
   - GREEN: Write minimum code to make test pass
   - REFACTOR: Clean up code while keeping tests green

2. **Test-First Sequence:**
   - Each commit follows pattern: `test: add X` followed by `feat: implement X`
   - No implementation code without a failing test

3. **Coverage Requirements:**
   - Minimum 90% line coverage for new code
   - 100% branch coverage for rule logic
   - All edge cases documented and tested

### TDD Implementation Phases

#### Phase 1: Write Failing Tests First (RED)

Create `tracehub/backend/tests/test_document_validation_rules.py`:

```python
# Tests to write BEFORE any implementation

class TestRequiredDocumentsPresentRule:
    """Test PRESENCE_001 rule."""

    def test_fails_with_missing_required_documents(self):
        """GIVEN a shipment with missing documents
        WHEN validation runs
        THEN it should fail with list of missing document types."""
        pass  # Write test first, then implement

    def test_passes_with_all_required_documents(self):
        """GIVEN a shipment with all required documents
        WHEN validation runs
        THEN it should pass."""
        pass

    def test_uses_correct_requirements_for_horn_hoof(self):
        """GIVEN a Horn & Hoof shipment
        WHEN validation runs
        THEN it should require EU TRACES, Vet Cert, CoO, BOL, Invoice, Packing, Export Dec."""
        pass


class TestNoDuplicateDocumentsRule:
    """Test UNIQUE_001 rule."""

    def test_detects_duplicate_document_types(self):
        """GIVEN a shipment with 2 Bills of Lading
        WHEN validation runs
        THEN it should fail with duplicate error."""
        pass

    def test_passes_with_unique_document_types(self):
        """GIVEN a shipment with one of each document type
        WHEN validation runs
        THEN it should pass."""
        pass


class TestDocumentRelevanceRule:
    """Test RELEVANCE_001 rule - AI-based document rejection."""

    def test_rejects_unrelated_document_low_confidence(self):
        """GIVEN a document with AI confidence < 0.3
        WHEN validation runs
        THEN it should REJECT the document as unrelated."""
        pass

    def test_flags_uncertain_document_medium_confidence(self):
        """GIVEN a document with AI confidence 0.3-0.5
        WHEN validation runs
        THEN it should FLAG for manual review (WARNING)."""
        pass

    def test_accepts_matching_document_high_confidence(self):
        """GIVEN a document where AI type matches declared type with confidence >= 0.5
        WHEN validation runs
        THEN it should ACCEPT the document."""
        pass

    def test_rejects_type_mismatch_even_high_confidence(self):
        """GIVEN a document declared as BOL but AI detects Commercial Invoice
        WHEN validation runs
        THEN it should REJECT with type mismatch error."""
        pass

    def test_handles_ai_unavailable_gracefully(self):
        """GIVEN AI classifier is unavailable
        WHEN validation runs
        THEN it should skip relevance check with INFO message."""
        pass


class TestVetCertIssueDateRule:
    """Test HORN_HOOF_002 rule."""

    def test_fails_when_issued_after_ship_date(self):
        """GIVEN a vet cert issued after ETD
        WHEN validation runs
        THEN it should fail."""
        pass

    def test_passes_when_issued_before_ship_date(self):
        """GIVEN a vet cert issued before ETD
        WHEN validation runs
        THEN it should pass."""
        pass

    def test_passes_when_issued_on_ship_date(self):
        """GIVEN a vet cert issued on same day as ETD
        WHEN validation runs
        THEN it should pass."""
        pass


class TestVetCertAuthorizedSignerRule:
    """Test HORN_HOOF_003 rule."""

    def test_warns_when_issuer_not_nigerian_authority(self):
        """GIVEN a vet cert from unknown authority
        WHEN validation runs
        THEN it should warn (not fail)."""
        pass

    def test_passes_for_nigerian_authority(self):
        """GIVEN a vet cert from 'Federal Ministry of Agriculture Nigeria'
        WHEN validation runs
        THEN it should pass."""
        pass


class TestValidationRunner:
    """Test the complete validation runner."""

    def test_runs_all_applicable_rules(self):
        """GIVEN a Horn & Hoof shipment
        WHEN validation runs
        THEN it should execute all Horn & Hoof applicable rules."""
        pass

    def test_skips_rules_for_other_product_types(self):
        """GIVEN a Sweet Potato shipment
        WHEN validation runs
        THEN it should skip Horn & Hoof specific rules."""
        pass

    def test_creates_audit_log_entry(self):
        """GIVEN a validation run
        WHEN complete
        THEN it should create an audit log entry."""
        pass

    def test_returns_complete_validation_report(self):
        """GIVEN a validation run
        WHEN complete
        THEN report should include all rule results."""
        pass
```

#### Phase 2: Implement Minimum Code (GREEN)

After each test is written and fails:
1. Implement the minimum code to make the test pass
2. Run the test to confirm it passes
3. Commit: `feat: implement X`

#### Phase 3: Refactor

After tests pass:
1. Clean up code, remove duplication
2. Ensure tests still pass
3. Commit: `refactor: clean up X`

### Test File Structure

```
tracehub/backend/tests/
├── test_document_validation_rules.py     # Unit tests for rules
├── test_document_validation_context.py   # Context factory tests
├── test_document_validation_registry.py  # Registry tests
├── test_document_validation_runner.py    # Runner tests
├── test_document_validation_api.py       # API integration tests
└── fixtures/
    └── validation_fixtures.py            # Shared test fixtures
```

---

## Requirements

### Functional Requirements

#### FR-1: Document Presence Validation
- [ ] Validate all required documents are present per shipment product type
- [ ] Required documents for Horn & Hoof (HS 0506/0507):
  - EU TRACES Certificate
  - Veterinary Health Certificate
  - Certificate of Origin
  - Bill of Lading
  - Commercial Invoice
  - Packing List
  - Export Declaration
- [ ] Flag shipments with missing documents for review

#### FR-2: Document Uniqueness Validation
- [ ] Ensure only one document of each type per shipment (no duplicates)
- [ ] Allow multiple documents only when explicitly defined (e.g., multiple packing lists for multi-container shipments)
- [ ] Flag shipments with duplicate documents for review

#### FR-3: Shipment-Level Validation Status
- [ ] Mark shipment as "needs_review" if any validation fails
- [ ] Support manual override after review with audit trail
- [ ] Allow deletion of flagged shipments after review

#### FR-4: Bill of Lading Cross-Validation
- [ ] Validate Bill of Lading container number matches shipment container number
- [ ] Validate vessel name matches if provided
- [ ] Generate warning (not error) for mismatches to allow manual review

#### FR-5: Veterinary Health Certificate Validation
- [ ] Validate certificate is signed (has issuing authority field populated)
- [ ] Validate expected issuing authority contains "Nigeria", "Nigerian", "NVRI", or "Federal"
- [ ] Validate issue date is on or before ship departure date (ETD)

#### FR-6: Validation Audit Logging
- [ ] Log all validation runs with timestamp, user, and shipment ID
- [ ] Log individual rule results (pass/fail/warning/skip)
- [ ] Log validation overrides with reason
- [ ] Maintain logs for regulatory audit purposes (90+ days retention)

#### FR-7: Extensible Rule System
- [ ] Rules implemented as pluggable components
- [ ] Support rule priorities (critical, warning, info)
- [ ] Support conditional rules (only apply to certain product types)
- [ ] Support rule versioning for regulatory change tracking

#### FR-8: AI-Based Document Relevance Validation (NEW)
- [ ] **Reject** documents where AI classification confidence < 0.3 (unrelated document)
- [ ] **Flag for review** documents where AI confidence is 0.3-0.5 (uncertain)
- [ ] **Accept** documents where AI type matches declared type with confidence >= 0.5
- [ ] **Reject** documents where AI-detected type does not match user-declared type (type mismatch)
- [ ] Support manual override with audit trail for rejected documents
- [ ] Integrate with existing `document_classifier` service (reuse, don't duplicate)
- [ ] Handle AI unavailability gracefully (skip check with INFO message)

**Confidence Thresholds:**
| Confidence | AI Type Matches Declared | Action |
|------------|-------------------------|--------|
| < 0.3 | N/A | REJECT - Document appears unrelated |
| 0.3 - 0.5 | Yes | WARNING - Flag for manual review |
| 0.3 - 0.5 | No | REJECT - Type mismatch, low confidence |
| >= 0.5 | Yes | ACCEPT |
| >= 0.5 | No | REJECT - Type mismatch, AI confident |

#### FR-9: Multi-Product Type Support
- [ ] Horn & Hoof (HS 0506/0507): EU TRACES, Vet Cert, CoO, BOL, Invoice, Packing, Export Dec
- [ ] Sweet Potato (HS 0714): Phyto, CoO, Quality, BOL, Invoice, Packing
- [ ] Hibiscus (HS 0902): Phyto, CoO, Quality, BOL, Invoice, Packing
- [ ] Ginger (HS 0910): Phyto, CoO, Quality, BOL, Invoice, Packing
- [ ] Cocoa (HS 1801): All standard + EUDR Due Diligence (future)

### Non-Functional Requirements

#### NFR-1: Performance
- [ ] Validate a shipment with 10 documents in < 500ms
- [ ] Support bulk validation of up to 100 shipments in < 30 seconds
- [ ] Non-blocking validation (async where possible)

#### NFR-2: Maintainability
- [ ] Each rule in separate class/function for easy testing
- [ ] Clear rule naming convention: `{category}_{action}_{target}`
- [ ] Comprehensive docstrings explaining rule rationale

#### NFR-3: Security
- [ ] All validation operations scoped to user's organization (multi-tenancy)
- [ ] Validation overrides require admin or compliance role
- [ ] Audit logs are immutable (append-only)

#### NFR-4: Testability (NEW)
- [ ] All rules must be unit testable in isolation
- [ ] Mock-friendly interfaces for external dependencies (AI classifier, DB)
- [ ] Test fixtures for common shipment/document scenarios

---

## Technical Approach

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Validation Engine                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────┐   ┌──────────────────┐   ┌───────────────────┐   │
│  │ Rule Registry │──▶│ Validation Runner │──▶│ Result Handler    │   │
│  └───────────────┘   └──────────────────┘   └───────────────────┘   │
│         │                    │                       │              │
│         ▼                    ▼                       ▼              │
│  ┌───────────────┐   ┌──────────────────┐   ┌───────────────────┐   │
│  │ Rule Classes  │   │ Validation       │   │ Audit Logger      │   │
│  │ - Presence    │   │ Context          │   │                   │   │
│  │ - Uniqueness  │   │ - Shipment       │   │                   │   │
│  │ - Relevance   │◀──│ - Documents      │   │                   │   │
│  │ - CrossField  │   │ - AI Results     │   │                   │   │
│  │ - DateRules   │   │ - Product type   │   │                   │   │
│  └───────────────┘   └──────────────────┘   └───────────────────┘   │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Document Classifier Service                     │    │
│  │        (Existing: services/document_classifier.py)          │    │
│  │   - AI Classification (Claude Haiku)                        │    │
│  │   - Keyword Fallback                                        │    │
│  │   - Confidence Scores                                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Integration with Existing Document Classifier

The validation engine will **reuse** the existing `document_classifier.py` service rather than duplicating AI logic.

#### Existing Service Capabilities

From `tracehub/backend/app/services/document_classifier.py`:

```python
@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float              # 0.0 to 1.0
    reference_number: Optional[str]
    detected_fields: Dict[str, Any]
    reasoning: str                 # AI explanation

class DocumentClassifier:
    def classify(self, text: str, prefer_ai: bool = True) -> ClassificationResult:
        """Main classification - tries AI first, falls back to keywords."""

    def is_ai_available(self) -> bool:
        """Check if AI classification is available."""

    def get_ai_status(self) -> Dict[str, Any]:
        """Get detailed AI availability status."""
```

#### Integration Approach

1. **Reuse Classification Results:** Access stored `DocumentContent.confidence_score` and `DocumentContent.detected_fields` from upload time
2. **On-Demand Classification:** If no stored result, call `document_classifier.classify()` during validation
3. **No Duplication:** Do NOT re-implement AI classification in validation rules

### Component Design

#### 1. Base Rule Interface

```python
# tracehub/backend/app/services/document_rules/base.py

from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class RuleSeverity(str, Enum):
    """Severity levels for validation rules."""
    CRITICAL = "critical"    # Blocks shipment, must be fixed
    ERROR = "error"          # Blocks shipment, must be fixed
    WARNING = "warning"      # Flagged for review, can proceed
    INFO = "info"            # Informational, no action required

class RuleCategory(str, Enum):
    """Categories of validation rules."""
    PRESENCE = "presence"        # Document presence checks
    UNIQUENESS = "uniqueness"    # Duplicate detection
    RELEVANCE = "relevance"      # AI-based document relevance (NEW)
    CONTENT = "content"          # Field-level validation
    CROSS_FIELD = "cross_field"  # Cross-document validation
    DATE = "date"                # Date-based rules

@dataclass
class RuleResult:
    """Result of a single rule execution."""
    rule_id: str
    rule_name: str
    passed: bool
    severity: RuleSeverity
    message: str
    category: RuleCategory
    document_type: Optional[str] = None
    document_id: Optional[str] = None
    details: Optional[dict] = None

class ValidationRule(ABC):
    """Abstract base class for all validation rules."""

    rule_id: str  # Unique identifier e.g., "RELEVANCE_001"
    name: str     # Human-readable name
    description: str
    severity: RuleSeverity = RuleSeverity.ERROR
    category: RuleCategory
    applies_to: List[str] = None  # Product types, None = all

    @abstractmethod
    def validate(self, context: "ValidationContext") -> RuleResult:
        """Execute the validation rule."""
        pass

    def should_apply(self, product_type: str) -> bool:
        """Check if rule applies to this product type."""
        if self.applies_to is None:
            return True
        return product_type in self.applies_to
```

#### 2. Validation Context (Enhanced)

```python
# tracehub/backend/app/services/document_rules/context.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict

from ..document_classifier import document_classifier, ClassificationResult

@dataclass
class DocumentWithClassification:
    """Document with its AI classification result."""
    document: Document
    classification: Optional[ClassificationResult] = None
    confidence_score: float = 0.0

@dataclass
class ValidationContext:
    """Context passed to each validation rule."""
    shipment: Shipment
    documents: List[Document]
    product_type: ProductType
    required_document_types: List[DocumentType]

    # Indexed for efficient lookups
    documents_by_type: Dict[DocumentType, List[Document]]
    document_count_by_type: Dict[DocumentType, int]

    # AI classification data (NEW)
    classifications: Dict[str, DocumentWithClassification] = field(default_factory=dict)
    ai_available: bool = False

    @classmethod
    def from_shipment(
        cls,
        shipment: Shipment,
        documents: List[Document],
        document_contents: Optional[Dict[str, "DocumentContent"]] = None,
        db: Optional[Session] = None,
    ):
        """Factory method to create context from shipment.

        Args:
            shipment: The shipment being validated
            documents: List of documents attached to shipment
            document_contents: Pre-loaded DocumentContent records (optional)
            db: Database session for loading content if not provided
        """
        docs_by_type = defaultdict(list)
        for doc in documents:
            docs_by_type[doc.document_type].append(doc)

        required_types = get_required_documents_by_product_type(
            shipment.product_type
        )

        # Build classification data from stored results or fresh classification
        classifications = {}
        ai_available = document_classifier.is_ai_available()

        for doc in documents:
            doc_id = str(doc.id)
            doc_with_class = DocumentWithClassification(document=doc)

            # Try to get stored classification from DocumentContent
            content = None
            if document_contents and doc_id in document_contents:
                content = document_contents[doc_id]
            elif db:
                content = db.query(DocumentContent).filter(
                    DocumentContent.document_id == doc.id
                ).first()

            if content:
                doc_with_class.confidence_score = content.confidence_score or 0.0
                # Reconstruct ClassificationResult from stored data
                if content.detected_fields:
                    doc_with_class.classification = ClassificationResult(
                        document_type=doc.document_type,
                        confidence=content.confidence_score or 0.0,
                        reference_number=content.detected_fields.get("reference_number"),
                        detected_fields=content.detected_fields,
                        reasoning=content.detected_fields.get("ai_reasoning", "")
                    )

            classifications[doc_id] = doc_with_class

        return cls(
            shipment=shipment,
            documents=documents,
            product_type=shipment.product_type,
            required_document_types=required_types,
            documents_by_type=dict(docs_by_type),
            document_count_by_type={k: len(v) for k, v in docs_by_type.items()},
            classifications=classifications,
            ai_available=ai_available,
        )
```

#### 3. Document Relevance Rule (NEW)

```python
# tracehub/backend/app/services/document_rules/relevance_rules.py

from typing import List
from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext

class DocumentRelevanceRule(ValidationRule):
    """Validates that uploaded document content matches declared document type.

    Uses AI classification to detect and reject:
    1. Unrelated documents (random PDFs, photos, etc.)
    2. Mismatched documents (declared as BOL but is actually an Invoice)

    Confidence Thresholds:
    - < 0.3: REJECT as unrelated (CRITICAL)
    - 0.3 - 0.5: FLAG for review if type matches, REJECT if mismatch
    - >= 0.5: ACCEPT if type matches, REJECT if mismatch
    """

    rule_id = "RELEVANCE_001"
    name = "Document Content Relevance"
    description = "Document content must match the declared document type"
    severity = RuleSeverity.CRITICAL
    category = RuleCategory.RELEVANCE

    # Configurable thresholds
    REJECT_THRESHOLD = 0.3      # Below this = definitely unrelated
    REVIEW_THRESHOLD = 0.5      # Below this but above reject = needs review

    def validate(self, context: ValidationContext) -> List[RuleResult]:
        """Validate all documents for relevance.

        Returns multiple results - one per problematic document.
        """
        results = []

        # Skip if AI is not available
        if not context.ai_available:
            results.append(RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="AI classification unavailable - relevance check skipped",
                category=self.category,
                details={"reason": "ai_unavailable"}
            ))
            return results

        for doc_id, doc_with_class in context.classifications.items():
            doc = doc_with_class.document
            confidence = doc_with_class.confidence_score
            classification = doc_with_class.classification

            # Case 1: Very low confidence - document appears unrelated
            if confidence < self.REJECT_THRESHOLD:
                results.append(RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.CRITICAL,
                    message=f"Document appears unrelated. AI confidence: {confidence:.0%}. "
                            f"Expected: {doc.document_type.value}",
                    category=self.category,
                    document_type=doc.document_type.value,
                    document_id=doc_id,
                    details={
                        "confidence": confidence,
                        "declared_type": doc.document_type.value,
                        "rejection_reason": "unrelated_document",
                        "threshold": self.REJECT_THRESHOLD,
                    }
                ))
                continue

            # Case 2: Check type match if we have classification
            if classification:
                ai_detected_type = classification.document_type
                declared_type = doc.document_type

                types_match = ai_detected_type == declared_type

                if not types_match:
                    # Type mismatch - reject regardless of confidence
                    results.append(RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        passed=False,
                        severity=RuleSeverity.CRITICAL,
                        message=f"Document type mismatch. Declared: {declared_type.value}, "
                                f"AI detected: {ai_detected_type.value} ({confidence:.0%} confidence)",
                        category=self.category,
                        document_type=doc.document_type.value,
                        document_id=doc_id,
                        details={
                            "confidence": confidence,
                            "declared_type": declared_type.value,
                            "detected_type": ai_detected_type.value,
                            "rejection_reason": "type_mismatch",
                            "ai_reasoning": classification.reasoning,
                        }
                    ))
                    continue

                # Types match but low confidence - flag for review
                if confidence < self.REVIEW_THRESHOLD:
                    results.append(RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        passed=False,
                        severity=RuleSeverity.WARNING,
                        message=f"Document type uncertain. Please verify manually. "
                                f"AI confidence: {confidence:.0%}",
                        category=self.category,
                        document_type=doc.document_type.value,
                        document_id=doc_id,
                        details={
                            "confidence": confidence,
                            "declared_type": declared_type.value,
                            "detected_type": ai_detected_type.value,
                            "flag_reason": "low_confidence",
                            "threshold": self.REVIEW_THRESHOLD,
                        }
                    ))
                    continue

        # If no issues found, return success
        if not results:
            results.append(RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="All documents match their declared types",
                category=self.category,
            ))

        return results
```

#### 4. Other Rule Implementations

```python
# tracehub/backend/app/services/document_rules/presence_rules.py

class RequiredDocumentsPresentRule(ValidationRule):
    """Validates all required documents are present for the shipment."""

    rule_id = "PRESENCE_001"
    name = "Required Documents Present"
    description = "All required documents must be uploaded for the shipment"
    severity = RuleSeverity.CRITICAL
    category = RuleCategory.PRESENCE

    def validate(self, context: ValidationContext) -> RuleResult:
        missing = []
        for doc_type in context.required_document_types:
            if doc_type not in context.documents_by_type:
                missing.append(doc_type.value)

        if missing:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Missing required documents: {', '.join(missing)}",
                category=self.category,
                details={"missing_types": missing}
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="All required documents present",
            category=self.category
        )


# tracehub/backend/app/services/document_rules/uniqueness_rules.py

class NoDuplicateDocumentsRule(ValidationRule):
    """Validates no duplicate document types exist."""

    rule_id = "UNIQUE_001"
    name = "No Duplicate Documents"
    description = "Each document type should appear only once per shipment"
    severity = RuleSeverity.ERROR
    category = RuleCategory.UNIQUENESS

    def validate(self, context: ValidationContext) -> RuleResult:
        duplicates = []
        for doc_type, count in context.document_count_by_type.items():
            if count > 1:
                duplicates.append(f"{doc_type.value} ({count} copies)")

        if duplicates:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Duplicate documents found: {', '.join(duplicates)}",
                category=self.category,
                details={"duplicates": duplicates}
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="No duplicate documents",
            category=self.category
        )


# tracehub/backend/app/services/document_rules/horn_hoof_rules.py

class VetCertIssueDateRule(ValidationRule):
    """Veterinary Health Certificate issue date must be on/before ship date."""

    rule_id = "HORN_HOOF_002"
    name = "Vet Certificate Issue Date"
    description = "Veterinary Health Certificate must be issued on or before departure"
    severity = RuleSeverity.ERROR
    category = RuleCategory.DATE
    applies_to = [ProductType.HORN_HOOF.value]

    def validate(self, context: ValidationContext) -> RuleResult:
        vet_certs = context.documents_by_type.get(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE, []
        )

        if not vet_certs:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="No veterinary certificate to validate",
                category=self.category
            )

        vet_cert = vet_certs[0]
        issue_date = vet_cert.document_date
        ship_date = context.shipment.etd

        if not issue_date:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message="Veterinary certificate missing issue date",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id)
            )

        # Convert datetime to date for comparison if needed
        if hasattr(issue_date, 'date'):
            issue_date = issue_date.date()
        if ship_date and hasattr(ship_date, 'date'):
            ship_date = ship_date.date()

        if ship_date and issue_date > ship_date:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Vet certificate issued ({issue_date}) after ship date ({ship_date})",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id)
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="Vet certificate issue date valid",
            category=self.category
        )


class VetCertAuthorizedSignerRule(ValidationRule):
    """Veterinary Health Certificate must be signed by authorized veterinarian."""

    rule_id = "HORN_HOOF_003"
    name = "Vet Certificate Authorized Signer"
    description = "Certificate must be from Nigerian veterinary authority"
    severity = RuleSeverity.WARNING
    category = RuleCategory.CONTENT
    applies_to = [ProductType.HORN_HOOF.value]

    AUTHORIZED_TERMS = ["nigeria", "nigerian", "nvri", "federal"]

    def validate(self, context: ValidationContext) -> RuleResult:
        vet_certs = context.documents_by_type.get(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE, []
        )

        if not vet_certs:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="No veterinary certificate to validate",
                category=self.category
            )

        vet_cert = vet_certs[0]
        issuer = vet_cert.issuer or ""

        if not issuer:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message="Veterinary certificate missing issuing authority",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id)
            )

        issuer_lower = issuer.lower()
        is_authorized = any(term in issuer_lower for term in self.AUTHORIZED_TERMS)

        if not is_authorized:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Issuing authority '{issuer}' may not be authorized Nigerian authority",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id),
                details={"issuer": issuer, "expected_terms": self.AUTHORIZED_TERMS}
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="Vet certificate from authorized Nigerian authority",
            category=self.category
        )
```

#### 5. Rule Registry

```python
# tracehub/backend/app/services/document_rules/registry.py

class RuleRegistry:
    """Central registry of all validation rules.

    Supports explicit registration for testability.
    """

    _instance = None
    _rules: Dict[str, ValidationRule] = {}
    _rules_by_category: Dict[RuleCategory, List[ValidationRule]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._rules = {}
            cls._instance._rules_by_category = defaultdict(list)
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset registry - useful for testing."""
        cls._instance = None

    def register(self, rule: ValidationRule):
        """Register a validation rule."""
        self._rules[rule.rule_id] = rule
        self._rules_by_category[rule.category].append(rule)

    def get_all_rules(self) -> List[ValidationRule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def get_rules_for_product_type(
        self, product_type: ProductType
    ) -> List[ValidationRule]:
        """Get rules applicable to a product type."""
        return [
            rule for rule in self._rules.values()
            if rule.should_apply(product_type.value if product_type else "other")
        ]

    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get a specific rule by ID."""
        return self._rules.get(rule_id)


def register_default_rules(registry: RuleRegistry = None):
    """Register all built-in validation rules.

    Can be called with custom registry for testing.
    """
    if registry is None:
        registry = RuleRegistry()

    from .presence_rules import RequiredDocumentsPresentRule
    from .uniqueness_rules import NoDuplicateDocumentsRule
    from .relevance_rules import DocumentRelevanceRule
    from .horn_hoof_rules import (
        VetCertIssueDateRule,
        VetCertAuthorizedSignerRule,
    )

    rules = [
        RequiredDocumentsPresentRule(),
        NoDuplicateDocumentsRule(),
        DocumentRelevanceRule(),  # NEW - AI-based relevance
        VetCertIssueDateRule(),
        VetCertAuthorizedSignerRule(),
    ]

    for rule in rules:
        registry.register(rule)

    return registry


# Initialize default registry
_default_registry = register_default_rules()

def get_registry() -> RuleRegistry:
    """Get the default rule registry."""
    return _default_registry
```

#### 6. Validation Runner

```python
# tracehub/backend/app/services/document_rules/runner.py

@dataclass
class ValidationReport:
    """Complete validation report for a shipment."""
    shipment_id: str
    shipment_reference: str
    product_type: str
    validated_at: datetime
    validated_by: str

    total_rules: int
    passed: int
    failed: int
    warnings: int
    rejected_documents: int  # NEW - count of AI-rejected docs

    is_valid: bool           # No critical/error failures
    needs_review: bool       # Has warnings or minor issues
    has_rejections: bool     # Has AI-rejected documents (NEW)

    results: List[RuleResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shipment_id": self.shipment_id,
            "shipment_reference": self.shipment_reference,
            "product_type": self.product_type,
            "validated_at": self.validated_at.isoformat(),
            "validated_by": self.validated_by,
            "summary": {
                "total_rules": self.total_rules,
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "rejected_documents": self.rejected_documents,
                "is_valid": self.is_valid,
                "needs_review": self.needs_review,
                "has_rejections": self.has_rejections,
            },
            "results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "severity": r.severity.value,
                    "message": r.message,
                    "category": r.category.value,
                    "document_type": r.document_type,
                    "document_id": r.document_id,
                    "details": r.details,
                }
                for r in self.results
            ]
        }


class ValidationRunner:
    """Executes validation rules against shipments."""

    def __init__(
        self,
        registry: RuleRegistry = None,
        audit_logger: AuditLogger = None
    ):
        self.registry = registry or get_registry()
        self.audit_logger = audit_logger

    def validate_shipment(
        self,
        shipment: Shipment,
        documents: List[Document],
        user: str = "system",
        db: Session = None,
    ) -> ValidationReport:
        """Run all applicable validation rules on a shipment."""

        # Build context with AI classification data
        context = ValidationContext.from_shipment(shipment, documents, db=db)

        # Get applicable rules
        rules = self.registry.get_rules_for_product_type(context.product_type)

        # Execute rules
        results = []
        for rule in rules:
            try:
                result = rule.validate(context)
                # Handle rules that return multiple results (like relevance)
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
            except Exception as e:
                results.append(RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message=f"Rule execution failed: {str(e)}",
                    category=rule.category,
                ))

        # Calculate summary statistics
        passed = sum(1 for r in results if r.passed)
        failed = sum(
            1 for r in results
            if not r.passed and r.severity in [RuleSeverity.CRITICAL, RuleSeverity.ERROR]
        )
        warnings = sum(
            1 for r in results
            if not r.passed and r.severity == RuleSeverity.WARNING
        )
        rejected_documents = sum(
            1 for r in results
            if not r.passed
            and r.category == RuleCategory.RELEVANCE
            and r.severity == RuleSeverity.CRITICAL
        )

        report = ValidationReport(
            shipment_id=str(shipment.id),
            shipment_reference=shipment.reference,
            product_type=context.product_type.value if context.product_type else "unknown",
            validated_at=datetime.utcnow(),
            validated_by=user,
            total_rules=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            rejected_documents=rejected_documents,
            is_valid=(failed == 0),
            needs_review=(warnings > 0),
            has_rejections=(rejected_documents > 0),
            results=results,
        )

        # Log validation run
        if db and self.audit_logger:
            self.audit_logger.log(
                action="document.validation.run",
                resource_type="shipment",
                resource_id=str(shipment.id),
                username=user,
                organization_id=str(shipment.organization_id),
                success=report.is_valid,
                details=report.to_dict(),
                db=db,
            )

        return report
```

#### 7. API Endpoints

```python
# tracehub/backend/app/routers/document_validation.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..database import get_db
from ..routers.auth import get_current_active_user
from ..schemas.auth import CurrentUser
from ..models import Shipment, Document
from ..models.shipment import ProductType
from ..services.document_rules import ValidationRunner, get_registry
from ..services.audit_log import get_audit_logger

router = APIRouter(prefix="/api/v1/validation", tags=["Document Validation"])


@router.post("/shipments/{shipment_id}/validate")
async def validate_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Validate all documents for a shipment.

    Returns validation report with all rule results including:
    - Missing required documents
    - Duplicate documents
    - AI-rejected unrelated documents
    - Vet certificate validation (for Horn & Hoof)
    """
    # Get shipment with multi-tenancy check
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(404, "Shipment not found")

    # Get all documents
    documents = db.query(Document).filter(
        Document.shipment_id == shipment_id
    ).all()

    # Run validation
    runner = ValidationRunner(audit_logger=get_audit_logger())
    report = runner.validate_shipment(
        shipment=shipment,
        documents=documents,
        user=current_user.email,
        db=db,
    )

    return report.to_dict()


@router.get("/shipments/{shipment_id}/validation-status")
async def get_validation_status(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """Get the most recent validation status for a shipment."""
    # Query audit log for most recent validation
    from ..services.audit_log import AuditLogger

    logger = AuditLogger(db)
    logs = logger.query(
        db=db,
        organization_id=str(current_user.organization_id),
        action="document.validation.run",
        resource_type="shipment",
        resource_id=str(shipment_id),
        limit=1,
    )

    if not logs:
        return {"validated": False, "message": "No validation runs found"}

    last_validation = logs[0]
    return {
        "validated": True,
        "last_validation": last_validation.timestamp.isoformat(),
        "is_valid": last_validation.success == "true",
        "details": last_validation.details,
    }


@router.get("/rules")
async def list_validation_rules(
    product_type: Optional[ProductType] = None,
):
    """List all available validation rules."""
    registry = get_registry()

    if product_type:
        rules = registry.get_rules_for_product_type(product_type)
    else:
        rules = registry.get_all_rules()

    return [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "severity": r.severity.value,
            "category": r.category.value,
            "applies_to": r.applies_to,
        }
        for r in rules
    ]


@router.post("/documents/{document_id}/override-rejection")
async def override_document_rejection(
    document_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Override an AI-rejected document with manual approval.

    Requires admin or compliance role.
    """
    if current_user.role not in ["admin", "compliance"]:
        raise HTTPException(403, "Override requires admin or compliance role")

    # Log the override
    from ..services.audit_log import get_audit_logger

    audit_logger = get_audit_logger()
    audit_logger.log(
        action="document.validation.override",
        resource_type="document",
        resource_id=str(document_id),
        username=current_user.email,
        organization_id=str(current_user.organization_id),
        success=True,
        details={
            "override_reason": reason,
            "overridden_by": current_user.email,
        },
        db=db,
    )

    return {"success": True, "message": "Rejection overridden", "document_id": str(document_id)}
```

---

## Files to Modify

### New Files

| File | Purpose |
|------|---------|
| `tracehub/backend/app/services/document_rules/__init__.py` | Package initialization, exports |
| `tracehub/backend/app/services/document_rules/base.py` | Base classes, enums, interfaces |
| `tracehub/backend/app/services/document_rules/context.py` | ValidationContext with AI data |
| `tracehub/backend/app/services/document_rules/registry.py` | RuleRegistry (testable singleton) |
| `tracehub/backend/app/services/document_rules/runner.py` | ValidationRunner, ValidationReport |
| `tracehub/backend/app/services/document_rules/presence_rules.py` | Document presence rules |
| `tracehub/backend/app/services/document_rules/uniqueness_rules.py` | Duplicate detection rules |
| `tracehub/backend/app/services/document_rules/relevance_rules.py` | **AI-based relevance validation (NEW)** |
| `tracehub/backend/app/services/document_rules/horn_hoof_rules.py` | Horn & Hoof specific rules |
| `tracehub/backend/app/routers/document_validation.py` | API endpoints |
| `tracehub/backend/app/schemas/validation.py` | Pydantic schemas for API |
| `tracehub/backend/tests/test_document_validation_rules.py` | Unit tests (TDD - write first) |
| `tracehub/backend/tests/test_document_validation_api.py` | Integration tests |
| `tracehub/backend/tests/fixtures/validation_fixtures.py` | Shared test fixtures |

### Modified Files

| File | Changes |
|------|---------|
| `tracehub/backend/app/routers/__init__.py` | Add document_validation router |
| `tracehub/backend/app/main.py` | Register new router |
| `tracehub/backend/app/services/audit_log.py` | Add validation audit action constants |

---

## Test Requirements

### Unit Tests (Write FIRST - TDD)

- [ ] `test_required_documents_present_rule_fails_with_missing_docs()`
- [ ] `test_required_documents_present_rule_passes_with_all_docs()`
- [ ] `test_no_duplicate_documents_rule_detects_duplicates()`
- [ ] `test_document_relevance_rule_rejects_unrelated_document()`
- [ ] `test_document_relevance_rule_rejects_type_mismatch()`
- [ ] `test_document_relevance_rule_flags_uncertain_document()`
- [ ] `test_document_relevance_rule_accepts_matching_document()`
- [ ] `test_document_relevance_rule_handles_ai_unavailable()`
- [ ] `test_vet_cert_date_rule_fails_after_ship_date()`
- [ ] `test_vet_cert_date_rule_passes_before_ship_date()`
- [ ] `test_vet_cert_authorized_signer_warns_unknown_authority()`
- [ ] `test_rule_registry_registers_and_retrieves_rules()`
- [ ] `test_validation_context_builds_from_shipment()`
- [ ] `test_validation_runner_executes_all_applicable_rules()`
- [ ] `test_validation_runner_creates_audit_log()`

### Integration Tests

- [ ] Test `/api/v1/validation/shipments/{id}/validate` endpoint
- [ ] Test validation with missing documents
- [ ] Test validation with duplicate documents
- [ ] Test validation with AI-rejected documents
- [ ] Test validation override endpoint
- [ ] Test multi-tenancy isolation
- [ ] Test audit log creation

### Edge Cases

- [ ] Shipment with no documents
- [ ] Shipment with unknown product type
- [ ] Document with null dates
- [ ] AI classifier unavailable
- [ ] Rule execution exception handling

---

## Compliance Check

**Product HS Codes Affected:** HS 0506, 0507 (Horn & Hoof), 0714, 0902, 0910, 1801
**EUDR Applicable:** NO - Horn & Hoof products are NOT covered by EUDR

**Required Documents (from COMPLIANCE_MATRIX.md):**
- EU TRACES Certificate (RC1479592)
- Veterinary Health Certificate (Nigerian authority)
- Certificate of Origin (Nigeria)
- Bill of Lading
- Commercial Invoice
- Packing List
- Export Declaration

**NEVER add to Horn & Hoof validation:**
- Geolocation coordinates
- Deforestation statements
- EUDR risk scores

---

## Dependencies

### Internal Dependencies
- `services/compliance.py` - Required document types by product
- `services/audit_log.py` - Audit logging infrastructure
- `services/document_classifier.py` - **AI classification for relevance validation**
- `models/document.py` - Document model and types
- `models/document_content.py` - **DocumentContent with confidence_score**
- `models/shipment.py` - Shipment model and ProductType enum

### External Dependencies
- `anthropic` - Claude API (already installed for document_classifier)

---

## Acceptance Criteria

### Functional
- [ ] All required documents validated per COMPLIANCE_MATRIX.md
- [ ] Duplicate documents detected and flagged
- [ ] **Unrelated documents rejected by AI (confidence < 0.3)**
- [ ] **Type mismatches rejected by AI**
- [ ] **Uncertain documents flagged for review (confidence 0.3-0.5)**
- [ ] Vet certificate date validation against ship date
- [ ] Vet certificate issuing authority validation
- [ ] Validation results logged to audit log
- [ ] API endpoints return complete validation report

### Quality
- [ ] All unit tests pass (>90% coverage on new code)
- [ ] All integration tests pass
- [ ] No security vulnerabilities (multi-tenancy enforced)
- [ ] Documentation updated in docstrings
- [ ] **TDD approach followed (tests written before implementation)**

### Performance
- [ ] Single shipment validation < 500ms
- [ ] Bulk validation (100 shipments) < 30 seconds

---

## Security Considerations

1. **Multi-tenancy:** All validation operations MUST filter by organization_id
2. **Audit Trail:** All validation runs logged with user identity
3. **Role-based Access:** Validation override requires admin/compliance role
4. **No EUDR for Horn/Hoof:** System MUST NOT request EUDR fields for HS 0506/0507

---

## Rollout Plan

### Phase 1: TDD Setup & Core Rules (Sprint 14 - Week 1)
- Write failing tests for all rules
- Implement base rule system
- Implement presence and uniqueness rules
- Make tests pass

### Phase 2: AI Relevance & Horn/Hoof Rules (Sprint 14 - Week 2)
- Write failing tests for relevance rules
- Implement DocumentRelevanceRule with AI integration
- Implement Horn & Hoof specific rules
- Make all tests pass

### Phase 3: API & Integration (Sprint 14 - Week 2)
- Add API endpoints
- Integration tests
- Audit logging integration

### Phase 4: Frontend Integration (Sprint 15)
- Validation status display on shipment detail
- Validation trigger button
- AI rejection feedback UI
- Override functionality for admins

---

## Future Enhancements

1. **Rule Configuration UI:** Allow compliance team to enable/disable rules
2. **Custom Rules:** Allow organization-specific rules
3. **Real-time Upload Validation:** Validate during upload, not just on demand
4. **Batch Validation:** Scheduled validation of all pending shipments
5. **Notifications:** Email/webhook when validation fails
6. **Adjustable Thresholds:** Per-organization confidence thresholds

---

**Last Updated:** 2026-01-14
**Reviewed By:** Pending
**Approved By:** Pending
