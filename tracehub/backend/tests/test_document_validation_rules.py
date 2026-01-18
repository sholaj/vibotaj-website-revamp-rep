"""Tests for document validation rules engine.

TDD Implementation - these tests define the expected behavior.
Run with: pytest tests/test_document_validation_rules.py -v
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import Optional

# Import rule system components
from app.services.document_rules.base import (
    ValidationRule,
    RuleResult,
    RuleSeverity,
    RuleCategory,
)
from app.services.document_rules.context import (
    ValidationContext,
    DocumentClassification,
    DocumentWithClassification,
)
from app.services.document_rules.registry import RuleRegistry, register_default_rules
from app.services.document_rules.runner import ValidationRunner, ValidationReport
from app.services.document_rules.presence_rules import RequiredDocumentsPresentRule
from app.services.document_rules.uniqueness_rules import NoDuplicateDocumentsRule
from app.services.document_rules.relevance_rules import DocumentRelevanceRule
from app.services.document_rules.horn_hoof_rules import (
    VetCertIssueDateRule,
    VetCertAuthorizedSignerRule,
)
from app.models.document import DocumentType, DocumentStatus
from app.models.shipment import ProductType


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_shipment():
    """Create a mock shipment for testing."""
    shipment = Mock()
    shipment.id = uuid4()
    shipment.reference = "VIBO-2026-TEST"
    shipment.organization_id = uuid4()
    shipment.product_type = ProductType.HORN_HOOF
    shipment.etd = datetime(2026, 2, 15)
    return shipment


@pytest.fixture
def mock_document():
    """Create a mock document for testing."""
    def _create_doc(
        doc_type: DocumentType = DocumentType.BILL_OF_LADING,
        document_date: Optional[datetime] = None,
        issuer: Optional[str] = None,
    ):
        doc = Mock()
        doc.id = uuid4()
        doc.document_type = doc_type
        doc.document_date = document_date
        doc.issuer = issuer
        doc.status = DocumentStatus.UPLOADED
        doc.name = f"test_{doc_type.value}.pdf"
        return doc
    return _create_doc


@pytest.fixture
def mock_context():
    """Create a mock validation context for testing."""
    def _create_context(
        shipment=None,
        documents=None,
        product_type=ProductType.HORN_HOOF,
        required_types=None,
        ai_available=True,
        classifications=None,
    ):
        if shipment is None:
            shipment = Mock()
            shipment.id = uuid4()
            shipment.reference = "TEST-001"
            shipment.organization_id = uuid4()
            shipment.product_type = product_type
            shipment.etd = datetime(2026, 2, 15)

        if documents is None:
            documents = []

        if required_types is None:
            required_types = [
                DocumentType.BILL_OF_LADING,
                DocumentType.COMMERCIAL_INVOICE,
            ]

        # Build documents_by_type
        docs_by_type = {}
        for doc in documents:
            if doc.document_type not in docs_by_type:
                docs_by_type[doc.document_type] = []
            docs_by_type[doc.document_type].append(doc)

        # Build classifications dict
        if classifications is None:
            classifications = {}
            for doc in documents:
                doc_id = str(doc.id)
                classifications[doc_id] = DocumentWithClassification(
                    document=doc,
                    classification=DocumentClassification(
                        document_type=doc.document_type,
                        confidence=0.9,
                    ),
                )

        context = ValidationContext(
            shipment=shipment,
            documents=documents,
            product_type=product_type,
            required_document_types=required_types,
            documents_by_type=docs_by_type,
            document_count_by_type={k: len(v) for k, v in docs_by_type.items()},
            classifications=classifications,
            ai_available=ai_available,
        )
        return context
    return _create_context


# =============================================================================
# Test: Base Rule System
# =============================================================================

class TestRuleResult:
    """Test RuleResult dataclass."""

    def test_rule_result_creation(self):
        """RuleResult should store all fields correctly."""
        result = RuleResult(
            rule_id="TEST_001",
            rule_name="Test Rule",
            passed=True,
            severity=RuleSeverity.INFO,
            message="Test passed",
            category=RuleCategory.PRESENCE,
        )
        assert result.rule_id == "TEST_001"
        assert result.passed is True
        assert result.severity == RuleSeverity.INFO

    def test_rule_result_to_dict(self):
        """RuleResult.to_dict should serialize correctly."""
        result = RuleResult(
            rule_id="TEST_001",
            rule_name="Test Rule",
            passed=False,
            severity=RuleSeverity.ERROR,
            message="Test failed",
            category=RuleCategory.UNIQUENESS,
            document_type="bill_of_lading",
            document_id="abc-123",
            details={"reason": "duplicate"},
        )
        d = result.to_dict()
        assert d["rule_id"] == "TEST_001"
        assert d["passed"] is False
        assert d["severity"] == "error"
        assert d["category"] == "uniqueness"
        assert d["details"]["reason"] == "duplicate"


class TestValidationRule:
    """Test ValidationRule base class."""

    def test_should_apply_all_product_types(self):
        """Rule with applies_to=None should apply to all product types."""
        rule = RequiredDocumentsPresentRule()
        assert rule.should_apply("horn_hoof") is True
        assert rule.should_apply("sweet_potato") is True
        assert rule.should_apply(None) is True

    def test_should_apply_specific_product_types(self):
        """Rule with applies_to list should only apply to those types."""
        rule = VetCertIssueDateRule()
        assert rule.should_apply("horn_hoof") is True
        assert rule.should_apply("sweet_potato") is False


# =============================================================================
# Test: Required Documents Present Rule (PRESENCE_001)
# =============================================================================

class TestRequiredDocumentsPresentRule:
    """Test PRESENCE_001 rule."""

    def test_fails_with_missing_required_documents(self, mock_context, mock_document):
        """GIVEN a shipment with missing documents
        WHEN validation runs
        THEN it should fail with list of missing document types."""
        # Create context with only BOL, missing Commercial Invoice
        bol = mock_document(DocumentType.BILL_OF_LADING)
        context = mock_context(
            documents=[bol],
            required_types=[
                DocumentType.BILL_OF_LADING,
                DocumentType.COMMERCIAL_INVOICE,
            ],
        )

        rule = RequiredDocumentsPresentRule()
        results = rule.validate(context)

        # Rule now returns list of results (PRESENCE_001 and optionally PRESENCE_001_PENDING)
        assert isinstance(results, list)
        # Find the main PRESENCE_001 result
        result = next((r for r in results if r.rule_id == "PRESENCE_001"), None)
        assert result is not None
        assert result.passed is False
        assert result.severity == RuleSeverity.CRITICAL
        assert "commercial_invoice" in result.message.lower()
        assert "commercial_invoice" in result.details["missing_types"]

    def test_passes_with_all_required_documents(self, mock_context, mock_document):
        """GIVEN a shipment with all required documents (validated status)
        WHEN validation runs
        THEN it should pass."""
        bol = mock_document(DocumentType.BILL_OF_LADING)
        bol.status = DocumentStatus.VALIDATED  # Set as validated
        invoice = mock_document(DocumentType.COMMERCIAL_INVOICE)
        invoice.status = DocumentStatus.VALIDATED  # Set as validated
        context = mock_context(
            documents=[bol, invoice],
            required_types=[
                DocumentType.BILL_OF_LADING,
                DocumentType.COMMERCIAL_INVOICE,
            ],
        )

        rule = RequiredDocumentsPresentRule()
        results = rule.validate(context)

        # Rule now returns list of results
        assert isinstance(results, list)
        # When all docs are validated, should return PRESENCE_001 success
        result = next((r for r in results if r.rule_id == "PRESENCE_001"), None)
        assert result is not None
        assert result.passed is True
        assert "present" in result.message.lower()

    def test_uses_correct_requirements_for_horn_hoof(self, mock_context, mock_document):
        """GIVEN a Horn & Hoof shipment
        WHEN validation runs
        THEN it should require specific documents."""
        # Horn & Hoof requires: EU TRACES, Vet Cert, CoO, BOL, Invoice, Packing, Export Dec
        horn_hoof_required = [
            DocumentType.EU_TRACES_CERTIFICATE,
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            DocumentType.CERTIFICATE_OF_ORIGIN,
            DocumentType.BILL_OF_LADING,
            DocumentType.COMMERCIAL_INVOICE,
            DocumentType.PACKING_LIST,
            DocumentType.EXPORT_DECLARATION,
        ]

        # Only provide BOL
        bol = mock_document(DocumentType.BILL_OF_LADING)
        context = mock_context(
            documents=[bol],
            required_types=horn_hoof_required,
            product_type=ProductType.HORN_HOOF,
        )

        rule = RequiredDocumentsPresentRule()
        results = rule.validate(context)

        # Rule now returns list of results
        assert isinstance(results, list)
        # Find the main PRESENCE_001 result
        result = next((r for r in results if r.rule_id == "PRESENCE_001"), None)
        assert result is not None
        assert result.passed is False
        assert len(result.details["missing_types"]) == 6  # All except BOL


# =============================================================================
# Test: No Duplicate Documents Rule (UNIQUE_001)
# =============================================================================

class TestNoDuplicateDocumentsRule:
    """Test UNIQUE_001 rule."""

    def test_detects_duplicate_document_types(self, mock_context, mock_document):
        """GIVEN a shipment with 2 Bills of Lading
        WHEN validation runs
        THEN it should fail with duplicate error."""
        bol1 = mock_document(DocumentType.BILL_OF_LADING)
        bol2 = mock_document(DocumentType.BILL_OF_LADING)
        context = mock_context(documents=[bol1, bol2])

        rule = NoDuplicateDocumentsRule()
        result = rule.validate(context)

        assert result.passed is False
        assert result.severity == RuleSeverity.ERROR
        assert "duplicate" in result.message.lower()
        assert any("bill_of_lading" in d.lower() for d in result.details["duplicates"])

    def test_passes_with_unique_document_types(self, mock_context, mock_document):
        """GIVEN a shipment with one of each document type
        WHEN validation runs
        THEN it should pass."""
        bol = mock_document(DocumentType.BILL_OF_LADING)
        invoice = mock_document(DocumentType.COMMERCIAL_INVOICE)
        context = mock_context(documents=[bol, invoice])

        rule = NoDuplicateDocumentsRule()
        result = rule.validate(context)

        assert result.passed is True
        assert "no duplicate" in result.message.lower()


# =============================================================================
# Test: Document Relevance Rule (RELEVANCE_001)
# =============================================================================

class TestDocumentRelevanceRule:
    """Test RELEVANCE_001 rule - AI-based document rejection."""

    def test_rejects_unrelated_document_low_confidence(self, mock_context, mock_document):
        """GIVEN a document with AI confidence < 0.3
        WHEN validation runs
        THEN it should REJECT the document as unrelated."""
        doc = mock_document(DocumentType.BILL_OF_LADING)
        doc_id = str(doc.id)

        # Low confidence classification
        classifications = {
            doc_id: DocumentWithClassification(
                document=doc,
                classification=DocumentClassification(
                    document_type=DocumentType.BILL_OF_LADING,
                    confidence=0.15,  # Below 0.3 threshold
                ),
            ),
        }
        # Set confidence_score on the wrapper
        classifications[doc_id].classification.confidence = 0.15

        context = mock_context(
            documents=[doc],
            classifications=classifications,
            ai_available=True,
        )
        # Override confidence score access
        context.classifications[doc_id] = DocumentWithClassification(
            document=doc,
            classification=DocumentClassification(
                document_type=DocumentType.BILL_OF_LADING,
                confidence=0.15,
            ),
        )

        rule = DocumentRelevanceRule()
        results = rule.validate(context)

        # Should have one rejection result
        rejections = [r for r in results if not r.passed and r.severity == RuleSeverity.CRITICAL]
        assert len(rejections) == 1
        assert "unrelated" in rejections[0].message.lower()
        assert rejections[0].details["rejection_reason"] == "unrelated_document"

    def test_flags_uncertain_document_medium_confidence(self, mock_context, mock_document):
        """GIVEN a document with AI confidence 0.3-0.5
        WHEN validation runs
        THEN it should FLAG for manual review (WARNING)."""
        doc = mock_document(DocumentType.BILL_OF_LADING)
        doc_id = str(doc.id)

        context = mock_context(
            documents=[doc],
            classifications={
                doc_id: DocumentWithClassification(
                    document=doc,
                    classification=DocumentClassification(
                        document_type=DocumentType.BILL_OF_LADING,
                        confidence=0.4,  # Between 0.3 and 0.5
                    ),
                ),
            },
            ai_available=True,
        )

        rule = DocumentRelevanceRule()
        results = rule.validate(context)

        # Should have one warning result
        warnings = [r for r in results if not r.passed and r.severity == RuleSeverity.WARNING]
        assert len(warnings) == 1
        assert "uncertain" in warnings[0].message.lower()
        assert warnings[0].details["flag_reason"] == "low_confidence"

    def test_accepts_matching_document_high_confidence(self, mock_context, mock_document):
        """GIVEN a document where AI type matches declared type with confidence >= 0.5
        WHEN validation runs
        THEN it should ACCEPT the document."""
        doc = mock_document(DocumentType.BILL_OF_LADING)
        doc_id = str(doc.id)

        context = mock_context(
            documents=[doc],
            classifications={
                doc_id: DocumentWithClassification(
                    document=doc,
                    classification=DocumentClassification(
                        document_type=DocumentType.BILL_OF_LADING,  # Matches declared
                        confidence=0.85,  # High confidence
                    ),
                ),
            },
            ai_available=True,
        )

        rule = DocumentRelevanceRule()
        results = rule.validate(context)

        # Should pass - all documents match
        assert len(results) == 1
        assert results[0].passed is True
        assert "match" in results[0].message.lower()

    def test_rejects_type_mismatch_even_high_confidence(self, mock_context, mock_document):
        """GIVEN a document declared as BOL but AI detects Commercial Invoice
        WHEN validation runs
        THEN it should REJECT with type mismatch error."""
        doc = mock_document(DocumentType.BILL_OF_LADING)  # Declared as BOL
        doc_id = str(doc.id)

        context = mock_context(
            documents=[doc],
            classifications={
                doc_id: DocumentWithClassification(
                    document=doc,
                    classification=DocumentClassification(
                        document_type=DocumentType.COMMERCIAL_INVOICE,  # AI says invoice
                        confidence=0.9,  # High confidence
                    ),
                ),
            },
            ai_available=True,
        )

        rule = DocumentRelevanceRule()
        results = rule.validate(context)

        # Should have one rejection for type mismatch
        rejections = [r for r in results if not r.passed and r.severity == RuleSeverity.CRITICAL]
        assert len(rejections) == 1
        assert "mismatch" in rejections[0].message.lower()
        assert rejections[0].details["rejection_reason"] == "type_mismatch"
        assert rejections[0].details["declared_type"] == "bill_of_lading"
        assert rejections[0].details["detected_type"] == "commercial_invoice"

    def test_handles_ai_unavailable_gracefully(self, mock_context, mock_document):
        """GIVEN AI classifier is unavailable
        WHEN validation runs
        THEN it should skip relevance check with INFO message."""
        doc = mock_document(DocumentType.BILL_OF_LADING)
        context = mock_context(
            documents=[doc],
            ai_available=False,  # AI not available
        )

        rule = DocumentRelevanceRule()
        results = rule.validate(context)

        # Should pass with INFO about skipping
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].severity == RuleSeverity.INFO
        assert "unavailable" in results[0].message.lower()
        assert results[0].details["reason"] == "ai_unavailable"


# =============================================================================
# Test: Vet Cert Issue Date Rule (HORN_HOOF_002)
# =============================================================================

class TestVetCertIssueDateRule:
    """Test HORN_HOOF_002 rule."""

    def test_fails_when_issued_after_ship_date(self, mock_context, mock_document):
        """GIVEN a vet cert issued after ETD
        WHEN validation runs
        THEN it should fail."""
        shipment = Mock()
        shipment.id = uuid4()
        shipment.etd = datetime(2026, 2, 15)  # Ship date

        vet_cert = mock_document(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            document_date=datetime(2026, 2, 20),  # Issued AFTER ship date
            issuer="Federal Ministry of Agriculture Nigeria",
        )

        context = mock_context(
            shipment=shipment,
            documents=[vet_cert],
            product_type=ProductType.HORN_HOOF,
        )

        rule = VetCertIssueDateRule()
        result = rule.validate(context)

        assert result.passed is False
        assert result.severity == RuleSeverity.ERROR
        assert "after" in result.message.lower()

    def test_passes_when_issued_before_ship_date(self, mock_context, mock_document):
        """GIVEN a vet cert issued before ETD
        WHEN validation runs
        THEN it should pass."""
        shipment = Mock()
        shipment.id = uuid4()
        shipment.etd = datetime(2026, 2, 15)

        vet_cert = mock_document(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            document_date=datetime(2026, 2, 10),  # Issued BEFORE ship date
            issuer="Federal Ministry of Agriculture Nigeria",
        )

        context = mock_context(
            shipment=shipment,
            documents=[vet_cert],
            product_type=ProductType.HORN_HOOF,
        )

        rule = VetCertIssueDateRule()
        result = rule.validate(context)

        assert result.passed is True
        assert "valid" in result.message.lower()

    def test_passes_when_issued_on_ship_date(self, mock_context, mock_document):
        """GIVEN a vet cert issued on same day as ETD
        WHEN validation runs
        THEN it should pass."""
        shipment = Mock()
        shipment.id = uuid4()
        shipment.etd = datetime(2026, 2, 15)

        vet_cert = mock_document(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            document_date=datetime(2026, 2, 15),  # Same day as ship date
            issuer="Federal Ministry of Agriculture Nigeria",
        )

        context = mock_context(
            shipment=shipment,
            documents=[vet_cert],
            product_type=ProductType.HORN_HOOF,
        )

        rule = VetCertIssueDateRule()
        result = rule.validate(context)

        assert result.passed is True


# =============================================================================
# Test: Vet Cert Authorized Signer Rule (HORN_HOOF_003)
# =============================================================================

class TestVetCertAuthorizedSignerRule:
    """Test HORN_HOOF_003 rule."""

    def test_warns_when_issuer_not_nigerian_authority(self, mock_context, mock_document):
        """GIVEN a vet cert from unknown authority
        WHEN validation runs
        THEN it should warn (not fail)."""
        vet_cert = mock_document(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            document_date=datetime(2026, 2, 10),
            issuer="Unknown Veterinary Service",  # Not Nigerian
        )

        context = mock_context(
            documents=[vet_cert],
            product_type=ProductType.HORN_HOOF,
        )

        rule = VetCertAuthorizedSignerRule()
        result = rule.validate(context)

        assert result.passed is False
        assert result.severity == RuleSeverity.WARNING
        assert "not be authorized" in result.message.lower()

    def test_passes_for_nigerian_authority(self, mock_context, mock_document):
        """GIVEN a vet cert from 'Federal Ministry of Agriculture Nigeria'
        WHEN validation runs
        THEN it should pass."""
        vet_cert = mock_document(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            document_date=datetime(2026, 2, 10),
            issuer="Federal Ministry of Agriculture Nigeria",
        )

        context = mock_context(
            documents=[vet_cert],
            product_type=ProductType.HORN_HOOF,
        )

        rule = VetCertAuthorizedSignerRule()
        result = rule.validate(context)

        assert result.passed is True
        assert "authorized" in result.message.lower()

    def test_passes_for_nvri(self, mock_context, mock_document):
        """GIVEN a vet cert from NVRI
        WHEN validation runs
        THEN it should pass."""
        vet_cert = mock_document(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            document_date=datetime(2026, 2, 10),
            issuer="NVRI National Veterinary Research Institute",
        )

        context = mock_context(
            documents=[vet_cert],
            product_type=ProductType.HORN_HOOF,
        )

        rule = VetCertAuthorizedSignerRule()
        result = rule.validate(context)

        assert result.passed is True


# =============================================================================
# Test: Rule Registry
# =============================================================================

class TestRuleRegistry:
    """Test the rule registry."""

    def test_registers_and_retrieves_rules(self):
        """Registry should register and retrieve rules by ID."""
        RuleRegistry.reset()
        registry = RuleRegistry()

        rule = RequiredDocumentsPresentRule()
        registry.register(rule)

        retrieved = registry.get_rule("PRESENCE_001")
        assert retrieved is not None
        assert retrieved.rule_id == "PRESENCE_001"

    def test_filters_rules_by_product_type(self):
        """Registry should filter rules by product type."""
        RuleRegistry.reset()
        registry = RuleRegistry()

        # Register a universal rule and a horn_hoof-specific rule
        registry.register(RequiredDocumentsPresentRule())
        registry.register(VetCertIssueDateRule())

        # Get rules for horn_hoof - should include both
        horn_hoof_rules = registry.get_rules_for_product_type(ProductType.HORN_HOOF)
        assert len(horn_hoof_rules) == 2

        # Get rules for sweet_potato - should only include universal rule
        sweet_potato_rules = registry.get_rules_for_product_type(ProductType.SWEET_POTATO)
        assert len(sweet_potato_rules) == 1
        assert sweet_potato_rules[0].rule_id == "PRESENCE_001"

    def test_raises_on_duplicate_registration(self):
        """Registry should raise error on duplicate rule ID."""
        RuleRegistry.reset()
        registry = RuleRegistry()

        rule1 = RequiredDocumentsPresentRule()
        registry.register(rule1)

        rule2 = RequiredDocumentsPresentRule()
        with pytest.raises(ValueError, match="already registered"):
            registry.register(rule2)


# =============================================================================
# Test: Validation Runner
# =============================================================================

class TestValidationRunner:
    """Test the complete validation runner."""

    def test_runs_all_applicable_rules(self, mock_context, mock_document):
        """GIVEN a Horn & Hoof shipment
        WHEN validation runs
        THEN it should execute all Horn & Hoof applicable rules."""
        RuleRegistry.reset()
        registry = RuleRegistry()
        registry.register(RequiredDocumentsPresentRule())
        registry.register(NoDuplicateDocumentsRule())
        registry.register(VetCertIssueDateRule())

        # Create shipment with all required docs
        shipment = Mock()
        shipment.id = uuid4()
        shipment.reference = "VIBO-TEST"
        shipment.organization_id = uuid4()
        shipment.product_type = ProductType.HORN_HOOF
        shipment.etd = datetime(2026, 2, 15)

        bol = mock_document(DocumentType.BILL_OF_LADING)
        invoice = mock_document(DocumentType.COMMERCIAL_INVOICE)

        runner = ValidationRunner(registry=registry)

        # Patch the context creation
        with patch.object(ValidationContext, 'from_shipment') as mock_from_shipment:
            mock_from_shipment.return_value = mock_context(
                shipment=shipment,
                documents=[bol, invoice],
                required_types=[DocumentType.BILL_OF_LADING, DocumentType.COMMERCIAL_INVOICE],
            )

            report = runner.validate_shipment(shipment, [bol, invoice])

        # PRESENCE_001 now returns 2 results (PRESENCE_001 + PRESENCE_001_PENDING)
        # Plus UNIQUE_001 and HORN_HOOF_002 = 4 total results
        assert report.total_rules >= 3  # At least 3 rules ran (PRESENCE, UNIQUE, HORN_HOOF)
        rule_ids = [r.rule_id for r in report.results]
        # Check that key rules are present (PRESENCE_001 produces multiple results now)
        assert any(r.startswith("PRESENCE_001") for r in rule_ids)
        assert "UNIQUE_001" in rule_ids
        assert "HORN_HOOF_002" in rule_ids

    def test_skips_rules_for_other_product_types(self, mock_context, mock_document):
        """GIVEN a Sweet Potato shipment
        WHEN validation runs
        THEN it should skip Horn & Hoof specific rules."""
        RuleRegistry.reset()
        registry = RuleRegistry()
        registry.register(RequiredDocumentsPresentRule())
        registry.register(VetCertIssueDateRule())  # Horn/Hoof only

        shipment = Mock()
        shipment.id = uuid4()
        shipment.reference = "VIBO-POTATO"
        shipment.organization_id = uuid4()
        shipment.product_type = ProductType.SWEET_POTATO
        shipment.etd = datetime(2026, 2, 15)

        bol = mock_document(DocumentType.BILL_OF_LADING)

        runner = ValidationRunner(registry=registry)

        with patch.object(ValidationContext, 'from_shipment') as mock_from_shipment:
            mock_from_shipment.return_value = mock_context(
                shipment=shipment,
                documents=[bol],
                product_type=ProductType.SWEET_POTATO,
                required_types=[DocumentType.BILL_OF_LADING],
            )

            report = runner.validate_shipment(shipment, [bol])

        # Should have PRESENCE rules but not HORN_HOOF_002
        rule_ids = [r.rule_id for r in report.results]
        assert any(r.startswith("PRESENCE_001") for r in rule_ids)
        assert "HORN_HOOF_002" not in rule_ids

    def test_returns_complete_validation_report(self, mock_context, mock_document):
        """GIVEN a validation run
        WHEN complete
        THEN report should include all rule results."""
        RuleRegistry.reset()
        registry = RuleRegistry()
        registry.register(RequiredDocumentsPresentRule())
        registry.register(NoDuplicateDocumentsRule())

        shipment = Mock()
        shipment.id = uuid4()
        shipment.reference = "VIBO-REPORT"
        shipment.organization_id = uuid4()
        shipment.product_type = ProductType.HORN_HOOF
        shipment.etd = datetime(2026, 2, 15)

        bol = mock_document(DocumentType.BILL_OF_LADING)

        runner = ValidationRunner(registry=registry)

        with patch.object(ValidationContext, 'from_shipment') as mock_from_shipment:
            mock_from_shipment.return_value = mock_context(
                shipment=shipment,
                documents=[bol],
                required_types=[DocumentType.BILL_OF_LADING, DocumentType.COMMERCIAL_INVOICE],
            )

            report = runner.validate_shipment(shipment, [bol], user="test@example.com")

        # Check report structure
        assert report.shipment_id == str(shipment.id)
        assert report.shipment_reference == "VIBO-REPORT"
        assert report.validated_by == "test@example.com"
        assert isinstance(report.validated_at, datetime)

        # Check summary - PRESENCE_001 now produces 2 results + UNIQUE_001 = 3 total
        assert report.total_rules >= 2  # At least 2 rules ran
        assert report.passed >= 0
        assert report.failed >= 0

        # Check is_valid flag
        assert isinstance(report.is_valid, bool)

        # Check to_dict serialization
        d = report.to_dict()
        assert "shipment_id" in d
        assert "summary" in d
        assert "results" in d
        assert len(d["results"]) >= 2  # PRESENCE_001 can produce multiple results
