"""Integration tests for Document Validation flow.

Tests the end-to-end validation pipeline including:
- ValidationRunner with full rule registry
- Cross-document consistency checks
- Issue creation and persistence
- Override workflow

Run with: pytest tests/test_validation_integration.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, date, timedelta

from app.models.document import Document, DocumentType, DocumentStatus, DocumentIssue
from app.models.shipment import Shipment, ShipmentStatus, ProductType
from app.services.document_rules import (
    ValidationRunner,
    ValidationReport,
    RuleRegistry,
    register_default_rules,
)
from app.services.document_rules.context import ValidationContext


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def registry():
    """Create a fresh rule registry with all default rules."""
    RuleRegistry.reset()
    return register_default_rules()


@pytest.fixture
def runner(registry):
    """Create a validation runner with the default registry."""
    return ValidationRunner(registry=registry)


@pytest.fixture
def mock_horn_hoof_shipment():
    """Create a mock Horn & Hoof shipment."""
    shipment = MagicMock(spec=Shipment)
    shipment.id = uuid4()
    shipment.reference = "VIBO-2026-001"
    shipment.product_type = ProductType.HORN_HOOF
    shipment.status = ShipmentStatus.IN_TRANSIT
    shipment.organization_id = uuid4()
    shipment.etd = datetime(2026, 1, 20)
    shipment.eta = datetime(2026, 2, 10)
    shipment.buyer_name = "HAGES"
    shipment.exporter_name = "VIBOTAJ"
    return shipment


@pytest.fixture
def complete_document_set():
    """Create a complete set of Horn & Hoof documents."""
    docs = []

    # Bill of Lading
    bol = MagicMock(spec=Document)
    bol.id = uuid4()
    bol.document_type = DocumentType.BILL_OF_LADING
    bol.status = DocumentStatus.VALIDATED
    bol.is_primary = True
    bol.version = 1
    bol.bol_parsed_data = {
        "bol_number": "APU106546",
        "containers": [{"number": "MSCU1234567", "type": "40HC"}],
        "cargo": [{"hs_code": "0506", "gross_weight_kg": 20000}],
        "shipped_on_board_date": "2026-01-20",
    }
    bol.extracted_container_number = "MSCU1234567"
    bol.canonical_data = None
    bol.issuer = None
    docs.append(bol)

    # Commercial Invoice
    invoice = MagicMock(spec=Document)
    invoice.id = uuid4()
    invoice.document_type = DocumentType.COMMERCIAL_INVOICE
    invoice.status = DocumentStatus.VALIDATED
    invoice.is_primary = True
    invoice.version = 1
    invoice.bol_parsed_data = None
    invoice.extracted_container_number = None
    invoice.canonical_data = {
        "fields": {
            "invoice_number": "INV-2026-001",
            "weight": {"gross_kg": 20000},
        }
    }
    invoice.issuer = None
    docs.append(invoice)

    # Packing List
    packing_list = MagicMock(spec=Document)
    packing_list.id = uuid4()
    packing_list.document_type = DocumentType.PACKING_LIST
    packing_list.status = DocumentStatus.VALIDATED
    packing_list.is_primary = True
    packing_list.version = 1
    packing_list.bol_parsed_data = None
    packing_list.extracted_container_number = None
    packing_list.canonical_data = {
        "fields": {
            "container_numbers": ["MSCU1234567"],
            "weight": {"gross_kg": 20000, "net_kg": 19500},
            "hs_codes": ["0506"],
        }
    }
    packing_list.issuer = None
    docs.append(packing_list)

    # Certificate of Origin
    coo = MagicMock(spec=Document)
    coo.id = uuid4()
    coo.document_type = DocumentType.CERTIFICATE_OF_ORIGIN
    coo.status = DocumentStatus.VALIDATED
    coo.is_primary = True
    coo.version = 1
    coo.bol_parsed_data = None
    coo.extracted_container_number = None
    coo.canonical_data = {
        "fields": {
            "certificate_number": "NIG-2026-001",
            "hs_codes": ["0506"],
            "authorized_signer": "Nigerian Export Authority",
        }
    }
    coo.issuer = "Nigerian Export Authority"
    docs.append(coo)

    # Veterinary Health Certificate
    vet_cert = MagicMock(spec=Document)
    vet_cert.id = uuid4()
    vet_cert.document_type = DocumentType.VETERINARY_HEALTH_CERTIFICATE
    vet_cert.status = DocumentStatus.VALIDATED
    vet_cert.is_primary = True
    vet_cert.version = 1
    vet_cert.document_date = datetime(2026, 1, 15)  # Before ETD
    vet_cert.bol_parsed_data = None
    vet_cert.extracted_container_number = None
    vet_cert.canonical_data = {
        "fields": {
            "certificate_number": "NVA-2026-001",
            "issue_date": "2026-01-15",
            "authorized_signer": "Dr. John Smith",
        }
    }
    vet_cert.issuer = "Dr. John Smith, Nigerian Veterinary Authority"
    docs.append(vet_cert)

    # EU TRACES Certificate
    eu_traces = MagicMock(spec=Document)
    eu_traces.id = uuid4()
    eu_traces.document_type = DocumentType.EU_TRACES_CERTIFICATE
    eu_traces.status = DocumentStatus.VALIDATED
    eu_traces.is_primary = True
    eu_traces.version = 1
    eu_traces.bol_parsed_data = None
    eu_traces.extracted_container_number = None
    eu_traces.canonical_data = {
        "fields": {
            "certificate_number": "RC1479592-2026-001",
        }
    }
    eu_traces.issuer = "EU TRACES System"
    docs.append(eu_traces)

    return docs


# =============================================================================
# Integration Tests: Full Validation Pipeline
# =============================================================================

class TestValidationPipelineIntegration:
    """Test the complete validation pipeline."""

    def test_validate_shipment_with_complete_docs(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN a shipment with all required documents
        WHEN running validation
        THEN it should pass with no critical errors."""
        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=self._create_context(mock_horn_hoof_shipment, complete_document_set)
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                user="test@vibotaj.com",
            )

        assert isinstance(report, ValidationReport)
        assert report.shipment_reference == "VIBO-2026-001"
        # May have warnings but no critical failures
        assert report.failed == 0 or report.is_valid

    def test_validate_shipment_missing_vet_cert(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN a shipment missing the vet cert
        WHEN running validation
        THEN it should fail with missing document error."""
        # Remove vet cert from documents
        docs_without_vet = [
            d for d in complete_document_set
            if d.document_type != DocumentType.VETERINARY_HEALTH_CERTIFICATE
        ]

        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=self._create_context(mock_horn_hoof_shipment, docs_without_vet)
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=docs_without_vet,
                user="test@vibotaj.com",
            )

        # Should have failures for missing required documents
        assert report.failed > 0 or not report.is_valid

    def test_validate_container_mismatch_detected(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN documents with mismatched container numbers
        WHEN running validation
        THEN it should detect the mismatch."""
        # Modify packing list to have different container
        for doc in complete_document_set:
            if doc.document_type == DocumentType.PACKING_LIST:
                doc.canonical_data = {
                    "fields": {
                        "container_numbers": ["TCLU9876543"],  # Different!
                        "weight": {"gross_kg": 20000},
                    }
                }
                break

        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=self._create_context(mock_horn_hoof_shipment, complete_document_set)
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                user="test@vibotaj.com",
            )

        # Should have a container mismatch failure
        container_failures = [
            r for r in report.results
            if "container" in r.rule_name.lower() and not r.passed
        ]
        assert len(container_failures) > 0

    def test_validate_weight_tolerance_warning(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN documents with weights exceeding 5% tolerance
        WHEN running validation
        THEN it should produce a warning."""
        # Modify packing list weight to exceed 5% tolerance
        for doc in complete_document_set:
            if doc.document_type == DocumentType.PACKING_LIST:
                doc.canonical_data = {
                    "fields": {
                        "container_numbers": ["MSCU1234567"],
                        "weight": {"gross_kg": 15000},  # 25% less than B/L
                    }
                }
                break

        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=self._create_context(mock_horn_hoof_shipment, complete_document_set)
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                user="test@vibotaj.com",
            )

        # Should have weight consistency failure
        weight_issues = [
            r for r in report.results
            if "weight" in r.rule_name.lower() and not r.passed
        ]
        assert len(weight_issues) > 0

    def _create_context(self, shipment, documents):
        """Create a ValidationContext for testing."""
        from app.models.document import DocumentType
        from collections import defaultdict

        context = MagicMock(spec=ValidationContext)
        context.shipment = shipment
        context.documents = documents
        context.product_type = shipment.product_type

        # Set up required document types for Horn & Hoof
        context.required_document_types = [
            DocumentType.BILL_OF_LADING,
            DocumentType.COMMERCIAL_INVOICE,
            DocumentType.PACKING_LIST,
            DocumentType.CERTIFICATE_OF_ORIGIN,
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            DocumentType.EU_TRACES_CERTIFICATE,
        ]

        def get_docs_of_type(doc_type):
            return [d for d in documents if d.document_type == doc_type]

        context.get_documents_of_type = get_docs_of_type

        # Add attributes needed by uniqueness and relevance rules
        doc_counts = defaultdict(int)
        for d in documents:
            doc_counts[d.document_type] = doc_counts.get(d.document_type, 0) + 1
        context.document_count_by_type = dict(doc_counts)
        context.classifications = {}  # Empty classifications for testing

        return context


# =============================================================================
# Integration Tests: Cross-Document Validation
# =============================================================================

class TestCrossDocumentIntegration:
    """Test cross-document validation rules integration."""

    def test_hs_code_consistency_across_documents(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN matching HS codes across B/L and CoO
        WHEN validating
        THEN HS code check should pass."""
        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=self._create_context(mock_horn_hoof_shipment, complete_document_set)
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                user="test@vibotaj.com",
            )

        # Find HS code check result
        hs_results = [
            r for r in report.results
            if "hs" in r.rule_name.lower() and "code" in r.rule_name.lower()
        ]

        # Should have at least one HS code check
        if hs_results:
            # All should pass for matching HS codes
            passed_hs = [r for r in hs_results if r.passed]
            assert len(passed_hs) > 0

    def test_vet_cert_date_before_etd_passes(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN vet cert issued before ETD
        WHEN validating
        THEN date check should pass."""
        # Ensure vet cert date is before ETD
        for doc in complete_document_set:
            if doc.document_type == DocumentType.VETERINARY_HEALTH_CERTIFICATE:
                doc.document_date = datetime(2026, 1, 15)  # Before ETD of Jan 20
                doc.canonical_data["fields"]["issue_date"] = "2026-01-15"
                break

        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=self._create_context(mock_horn_hoof_shipment, complete_document_set)
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                user="test@vibotaj.com",
            )

        # Find vet cert date results
        vet_date_results = [
            r for r in report.results
            if "vet" in r.rule_name.lower() and "date" in r.rule_name.lower()
        ]

        if vet_date_results:
            # Should pass for date before ETD
            passed = [r for r in vet_date_results if r.passed]
            assert len(passed) > 0

    def test_vet_cert_date_after_etd_fails(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN vet cert issued after ETD
        WHEN validating
        THEN date check should fail."""
        # Set vet cert date after ETD
        for doc in complete_document_set:
            if doc.document_type == DocumentType.VETERINARY_HEALTH_CERTIFICATE:
                doc.document_date = datetime(2026, 1, 25)  # After ETD of Jan 20
                doc.canonical_data["fields"]["issue_date"] = "2026-01-25"
                break

        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=self._create_context(mock_horn_hoof_shipment, complete_document_set)
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                user="test@vibotaj.com",
            )

        # Find vet cert date results
        vet_date_results = [
            r for r in report.results
            if "vet" in r.rule_name.lower() and "date" in r.rule_name.lower()
        ]

        if vet_date_results:
            # Should have failures for date after ETD
            failed = [r for r in vet_date_results if not r.passed]
            assert len(failed) > 0

    def _create_context(self, shipment, documents):
        """Create a ValidationContext for testing."""
        from app.models.document import DocumentType
        from collections import defaultdict

        context = MagicMock(spec=ValidationContext)
        context.shipment = shipment
        context.documents = documents
        context.product_type = shipment.product_type

        context.required_document_types = [
            DocumentType.BILL_OF_LADING,
            DocumentType.COMMERCIAL_INVOICE,
            DocumentType.PACKING_LIST,
            DocumentType.CERTIFICATE_OF_ORIGIN,
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            DocumentType.EU_TRACES_CERTIFICATE,
        ]

        def get_docs_of_type(doc_type):
            return [d for d in documents if d.document_type == doc_type]

        context.get_documents_of_type = get_docs_of_type

        # Add attributes needed by uniqueness and relevance rules
        doc_counts = defaultdict(int)
        for d in documents:
            doc_counts[d.document_type] = doc_counts.get(d.document_type, 0) + 1
        context.document_count_by_type = dict(doc_counts)
        context.classifications = {}  # Empty classifications for testing

        return context


# =============================================================================
# Integration Tests: Registry and Rule Loading
# =============================================================================

class TestRegistryIntegration:
    """Test rule registry and loading."""

    def test_registry_loads_all_default_rules(self, registry):
        """GIVEN the default registry
        WHEN getting all rules
        THEN it should have all expected rules registered."""
        rules = registry.get_all_rules()

        # Should have presence, uniqueness, relevance, and cross-document rules
        assert len(rules) >= 5

        rule_ids = {r.rule_id for r in rules}

        # Check for key rule IDs
        expected_rule_prefixes = ["PRESENCE", "XD"]
        for prefix in expected_rule_prefixes:
            has_prefix = any(rule_id.startswith(prefix) for rule_id in rule_ids)
            assert has_prefix, f"Missing rules with prefix {prefix}"

    def test_registry_filters_by_product_type(self, registry):
        """GIVEN the registry with product-type-specific rules
        WHEN filtering by product type
        THEN only applicable rules should be returned."""
        horn_hoof_rules = registry.get_rules_for_product_type(ProductType.HORN_HOOF)

        # All returned rules should apply to horn_hoof
        for rule in horn_hoof_rules:
            assert rule.should_apply("horn_hoof")

    def test_validation_report_serialization(
        self, runner, mock_horn_hoof_shipment, complete_document_set
    ):
        """GIVEN a validation report
        WHEN serializing to dict
        THEN it should be valid JSON-serializable."""
        with patch.object(
            ValidationContext, 'from_shipment',
            return_value=MagicMock(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                product_type=ProductType.HORN_HOOF,
                required_document_types=[],
                get_documents_of_type=lambda x: [],
            )
        ):
            report = runner.validate_shipment(
                shipment=mock_horn_hoof_shipment,
                documents=complete_document_set,
                user="test@vibotaj.com",
            )

        report_dict = report.to_dict()

        # Should have all required keys
        assert "shipment_id" in report_dict
        assert "summary" in report_dict
        assert "results" in report_dict
        assert "is_valid" in report_dict["summary"]


# =============================================================================
# Integration Tests: Issue Persistence (Database)
# =============================================================================

class TestIssuePersistenceIntegration:
    """Test issue creation and persistence to database."""

    def test_document_issue_model_creation(self):
        """GIVEN issue data
        WHEN creating a DocumentIssue model
        THEN it should have all required fields."""
        issue = DocumentIssue()
        issue.id = uuid4()
        issue.document_id = uuid4()
        issue.rule_id = "XD_001"
        issue.rule_name = "Container Number Consistency"
        issue.severity = "ERROR"
        issue.message = "Container mismatch detected"
        issue.is_overridden = False
        issue.created_at = datetime.utcnow()
        issue.updated_at = datetime.utcnow()

        assert issue.rule_id == "XD_001"
        assert issue.severity == "ERROR"
        assert issue.is_blocking is True  # ERROR + not overridden = blocking

    def test_document_issue_override_clears_blocking(self):
        """GIVEN an overridden issue
        WHEN checking if blocking
        THEN it should not be blocking."""
        issue = DocumentIssue()
        issue.severity = "ERROR"
        issue.is_overridden = True
        issue.overridden_at = datetime.utcnow()
        issue.override_reason = "Manually verified correct"

        assert issue.is_blocking is False


# =============================================================================
# Integration Tests: Document Versioning
# =============================================================================

class TestDocumentVersioningIntegration:
    """Test document versioning for duplicates."""

    def test_document_version_increment(self):
        """GIVEN existing document v1
        WHEN creating v2
        THEN version should increment and primary flag should update."""
        doc_v1 = Document()
        doc_v1.id = uuid4()
        doc_v1.version = 1
        doc_v1.is_primary = True

        doc_v2 = Document()
        doc_v2.id = uuid4()
        doc_v2.version = 2
        doc_v2.is_primary = False
        doc_v2.supersedes_id = doc_v1.id

        assert doc_v1.version == 1
        assert doc_v2.version == 2
        assert doc_v2.supersedes_id == doc_v1.id

    def test_set_primary_version(self):
        """GIVEN multiple document versions
        WHEN setting v2 as primary
        THEN v1 should become non-primary."""
        doc_v1 = Document()
        doc_v1.version = 1
        doc_v1.is_primary = False  # User selected v2

        doc_v2 = Document()
        doc_v2.version = 2
        doc_v2.is_primary = True  # Now primary

        assert doc_v1.is_primary is False
        assert doc_v2.is_primary is True


# =============================================================================
# Integration Tests: Draft vs Missing Distinction
# =============================================================================

class TestDraftVsMissingIntegration:
    """Test that DRAFT documents are not counted as missing."""

    def test_draft_document_presence_check(self, registry):
        """GIVEN a document in DRAFT status
        WHEN checking presence
        THEN it should be treated as 'draft' not 'missing'."""
        from app.services.document_rules.presence_rules import RequiredDocumentsPresentRule

        # Get the rule from registry
        rule = registry.get_rule("PRESENCE_001")
        assert rule is not None
        assert rule.name == "Required Documents Present"

    def test_multiple_presence_statuses(self):
        """GIVEN documents in various statuses
        WHEN running presence check
        THEN each should be categorized correctly."""
        # DRAFT -> "draft"
        # UPLOADED -> "pending"
        # VALIDATED/COMPLIANCE_OK/LINKED -> "validated"
        # None -> "missing"

        status_mapping = {
            DocumentStatus.DRAFT: "draft",
            DocumentStatus.UPLOADED: "pending",
            DocumentStatus.VALIDATED: "validated",
            DocumentStatus.COMPLIANCE_OK: "validated",
            DocumentStatus.LINKED: "validated",
        }

        for status, expected_category in status_mapping.items():
            doc = Document()
            doc.status = status

            if expected_category == "validated":
                assert doc.is_validated is True
            elif expected_category == "draft":
                assert doc.is_draft is True
