"""Tests for BoL auto-parse pipeline (PRD-018).

Tests: auto-parse on upload trigger, confidence-based auto-sync,
cross-document weight validation, field-level confidence, parse status.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4
from datetime import datetime

from app.models.document import DocumentType, DocumentStatus
from app.schemas.bol import CanonicalBoL, BolParty, BolContainer, BolCargo
from app.services.bol_auto_parse import (
    auto_parse_bol,
    get_parsed_bol_data,
    get_enhanced_sync_preview,
    cross_validate_weights,
    _build_field_confidence,
    AUTO_SYNC_CONFIDENCE_THRESHOLD,
)


# --- Helpers ---

def make_bol(confidence=0.85, bol_number="MSC1234567"):
    """Create a test CanonicalBoL."""
    return CanonicalBoL(
        bol_number=bol_number,
        shipper=BolParty(name="VIBOTAJ Global Nigeria Ltd", country="Nigeria"),
        consignee=BolParty(name="HAGES GmbH", country="Germany"),
        containers=[BolContainer(number="MSCU1234567", type="40HC")],
        cargo=[BolCargo(
            description="Cattle Horns",
            hs_code="0506",
            gross_weight_kg=25000.0,
        )],
        vessel_name="RHINE MAERSK",
        voyage_number="550N",
        port_of_loading="NGAPP",
        port_of_discharge="DEHAM",
        confidence_score=confidence,
    )


def make_document(
    doc_type=DocumentType.BILL_OF_LADING,
    bol_parsed_data=None,
    compliance_status=None,
    file_path="docs/test.pdf",
):
    """Create a mock document."""
    doc = MagicMock()
    doc.id = uuid4()
    doc.organization_id = uuid4()
    doc.shipment_id = uuid4()
    doc.document_type = doc_type
    doc.file_path = file_path
    doc.file_name = "test.pdf"
    doc.status = DocumentStatus.UPLOADED
    doc.bol_parsed_data = bol_parsed_data
    doc.compliance_status = compliance_status
    doc.compliance_checked_at = None
    doc.reference_number = None
    doc.issue_date = None
    doc.issuing_authority = None
    doc.updated_at = datetime(2026, 2, 16, 10, 0)
    doc.extra_data = {}
    return doc


def make_shipment(org_id=None, container_number=None):
    """Create a mock shipment."""
    shipment = MagicMock()
    shipment.id = uuid4()
    shipment.organization_id = org_id or uuid4()
    shipment.reference = "VIBO-2026-001"
    shipment.container_number = container_number
    shipment.bl_number = None
    shipment.vessel_name = None
    shipment.voyage_number = None
    shipment.pol_code = None
    shipment.pod_code = None
    shipment.atd = None
    shipment.validation_override_reason = None
    return shipment


def make_db(shipment=None, documents=None, products=None, compliance_results=None):
    """Create a mock database session."""
    db = MagicMock()
    documents = documents or []
    products = products or []
    compliance_results = compliance_results or []

    def query_side_effect(model):
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_delete = MagicMock()

        model_name = getattr(model, "__name__", str(model))
        if model_name == "Shipment":
            mock_filter.first.return_value = shipment
        elif model_name == "Document":
            mock_filter.all.return_value = documents
        elif model_name == "Product":
            mock_filter.all.return_value = products
        elif model_name == "ComplianceResult":
            mock_filter.all.return_value = compliance_results
            mock_filter.delete.return_value = 0
        else:
            mock_filter.all.return_value = []
            mock_filter.first.return_value = None

        mock_query.filter.return_value = mock_filter
        return mock_query

    db.query = MagicMock(side_effect=query_side_effect)
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    return db


# --- Tests ---


class TestBuildFieldConfidence:
    """Tests for field-level confidence extraction."""

    def test_all_fields_present(self):
        bol = make_bol(confidence=0.85)
        fields = _build_field_confidence(bol)
        assert "bol_number" in fields
        assert "shipper" in fields
        assert "consignee" in fields
        assert "container_number" in fields
        assert "vessel_name" in fields
        assert "port_of_loading" in fields
        assert "port_of_discharge" in fields
        assert fields["bol_number"].value == "MSC1234567"
        assert fields["bol_number"].confidence > 0

    def test_missing_fields_have_zero_confidence(self):
        bol = CanonicalBoL(
            bol_number="UNKNOWN",
            shipper=BolParty(name="Unknown Shipper"),
            consignee=BolParty(name="Unknown Consignee"),
            containers=[],
            cargo=[],
            confidence_score=0.0,
        )
        fields = _build_field_confidence(bol)
        assert fields["bol_number"].confidence == 0.0
        assert fields["shipper"].confidence == 0.0
        assert fields["consignee"].confidence == 0.0
        assert fields["container_number"].confidence == 0.0

    def test_partial_fields(self):
        bol = CanonicalBoL(
            bol_number="MSC123",
            shipper=BolParty(name="VIBOTAJ"),
            consignee=BolParty(name="Unknown Consignee"),
            containers=[],
            cargo=[],
            confidence_score=0.30,
        )
        fields = _build_field_confidence(bol)
        assert fields["bol_number"].confidence > 0
        assert fields["shipper"].confidence > 0
        assert fields["consignee"].confidence == 0.0


class TestAutoParseBoL:
    """Tests for auto_parse_bol pipeline."""

    @patch("app.services.bol_auto_parse._extract_text_from_document")
    @patch("app.services.bol_auto_parse.bol_parser")
    def test_returns_parsed_result(self, mock_parser, mock_extract):
        mock_extract.return_value = "B/L No.: MSC1234567\nShipper: VIBOTAJ"
        mock_parser.parse.return_value = make_bol()

        doc = make_document()
        shipment = make_shipment(org_id=doc.organization_id)
        db = make_db(shipment=shipment)

        result = auto_parse_bol(doc, db, auto_sync=False)
        assert result.parse_status == "parsed"
        assert result.confidence_score == 0.85
        assert "bol_number" in result.fields

    @patch("app.services.bol_auto_parse._extract_text_from_document")
    def test_returns_failed_when_no_text(self, mock_extract):
        mock_extract.return_value = None
        doc = make_document()
        db = make_db()

        result = auto_parse_bol(doc, db)
        assert result.parse_status == "failed"

    def test_returns_not_bol_for_wrong_type(self):
        doc = make_document(doc_type=DocumentType.COMMERCIAL_INVOICE)
        db = make_db()

        result = auto_parse_bol(doc, db)
        assert result.parse_status == "not_bol"

    @patch("app.services.bol_auto_parse._extract_text_from_document")
    @patch("app.services.bol_auto_parse.bol_parser")
    @patch("app.services.bol_auto_parse.apply_sync_changes")
    def test_auto_syncs_when_high_confidence(self, mock_sync, mock_parser, mock_extract):
        mock_extract.return_value = "B/L text"
        mock_parser.parse.return_value = make_bol(confidence=0.85)
        mock_sync.return_value = [{"field": "bl_number", "old": None, "new": "MSC1234567"}]

        doc = make_document()
        shipment = make_shipment(org_id=doc.organization_id)
        db = make_db(shipment=shipment)

        result = auto_parse_bol(doc, db, auto_sync=True)
        assert result.auto_synced is True
        mock_sync.assert_called_once()

    @patch("app.services.bol_auto_parse._extract_text_from_document")
    @patch("app.services.bol_auto_parse.bol_parser")
    @patch("app.services.bol_auto_parse.apply_sync_changes")
    def test_no_auto_sync_when_low_confidence(self, mock_sync, mock_parser, mock_extract):
        mock_extract.return_value = "B/L text"
        mock_parser.parse.return_value = make_bol(confidence=0.30)

        doc = make_document()
        shipment = make_shipment(org_id=doc.organization_id)
        db = make_db(shipment=shipment)

        result = auto_parse_bol(doc, db, auto_sync=True)
        assert result.auto_synced is False
        mock_sync.assert_not_called()

    @patch("app.services.bol_auto_parse._extract_text_from_document")
    @patch("app.services.bol_auto_parse.bol_parser")
    def test_runs_compliance_check(self, mock_parser, mock_extract):
        mock_extract.return_value = "B/L text"
        mock_parser.parse.return_value = make_bol()

        doc = make_document()
        shipment = make_shipment(org_id=doc.organization_id)
        db = make_db(shipment=shipment)

        result = auto_parse_bol(doc, db, auto_sync=False)
        assert result.compliance is not None
        assert result.compliance.decision in ("APPROVE", "HOLD", "REJECT")


class TestGetParsedBolData:
    """Tests for get_parsed_bol_data."""

    def test_returns_pending_when_not_parsed(self):
        doc = make_document(bol_parsed_data=None)
        db = make_db()
        result = get_parsed_bol_data(doc, db)
        assert result.parse_status == "pending"

    def test_returns_not_bol_for_wrong_type(self):
        doc = make_document(doc_type=DocumentType.PACKING_LIST)
        db = make_db()
        result = get_parsed_bol_data(doc, db)
        assert result.parse_status == "not_bol"

    def test_returns_parsed_data(self):
        bol = make_bol()
        doc = make_document(
            bol_parsed_data=bol.model_dump(mode="json"),
            compliance_status="APPROVE",
        )
        db = make_db()
        result = get_parsed_bol_data(doc, db)
        assert result.parse_status == "parsed"
        assert result.confidence_score == 0.85
        assert result.fields["bol_number"].value == "MSC1234567"


class TestGetEnhancedSyncPreview:
    """Tests for enhanced sync preview."""

    def test_returns_changes_for_empty_shipment(self):
        bol = make_bol()
        doc = make_document(bol_parsed_data=bol.model_dump(mode="json"))
        shipment = make_shipment(org_id=doc.organization_id)
        db = make_db(shipment=shipment)

        result = get_enhanced_sync_preview(doc, db)
        assert len(result.changes) > 0
        bl_change = next((c for c in result.changes if c.field == "bl_number"), None)
        assert bl_change is not None
        assert bl_change.new_value == "MSC1234567"
        assert bl_change.will_update is True

    def test_detects_placeholder_container(self):
        bol = make_bol()
        doc = make_document(bol_parsed_data=bol.model_dump(mode="json"))
        shipment = make_shipment(
            org_id=doc.organization_id,
            container_number="HAGES-CNT-001",
        )
        db = make_db(shipment=shipment)

        result = get_enhanced_sync_preview(doc, db)
        cnt_change = next((c for c in result.changes if c.field == "container_number"), None)
        assert cnt_change is not None
        assert cnt_change.is_placeholder is True
        assert cnt_change.will_update is True

    def test_empty_preview_when_no_parsed_data(self):
        doc = make_document(bol_parsed_data=None)
        db = make_db()

        result = get_enhanced_sync_preview(doc, db)
        assert len(result.changes) == 0


class TestCrossValidateWeights:
    """Tests for cross-document weight validation."""

    def test_no_issues_within_tolerance(self):
        bol = make_bol()
        bol_doc = make_document(
            doc_type=DocumentType.BILL_OF_LADING,
            bol_parsed_data=bol.model_dump(mode="json"),
        )
        pl_doc = make_document(doc_type=DocumentType.PACKING_LIST)

        product = MagicMock()
        product.quantity_gross_kg = 25000.0

        shipment = make_shipment(org_id=bol_doc.organization_id)
        db = make_db(
            shipment=shipment,
            documents=[bol_doc, pl_doc],
            products=[product],
        )

        issues = cross_validate_weights(shipment, db)
        assert len(issues) == 0

    def test_issue_when_weight_exceeds_tolerance(self):
        bol = make_bol()
        bol_doc = make_document(
            doc_type=DocumentType.BILL_OF_LADING,
            bol_parsed_data=bol.model_dump(mode="json"),
        )
        pl_doc = make_document(doc_type=DocumentType.PACKING_LIST)

        product = MagicMock()
        product.quantity_gross_kg = 20000.0  # 25000 vs 20000 = 20% diff

        shipment = make_shipment(org_id=bol_doc.organization_id)
        db = make_db(
            shipment=shipment,
            documents=[bol_doc, pl_doc],
            products=[product],
        )

        issues = cross_validate_weights(shipment, db)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "CROSS-001"
        assert issues[0]["severity"] == "WARNING"

    def test_no_issues_when_no_bol(self):
        shipment = make_shipment()
        db = make_db(shipment=shipment, documents=[])
        issues = cross_validate_weights(shipment, db)
        assert len(issues) == 0

    def test_no_issues_when_no_weight(self):
        bol = CanonicalBoL(
            bol_number="MSC123",
            shipper=BolParty(name="VIBOTAJ"),
            consignee=BolParty(name="HAGES"),
            containers=[],
            cargo=[BolCargo(description="Cargo", gross_weight_kg=None)],
            confidence_score=0.5,
        )
        bol_doc = make_document(
            doc_type=DocumentType.BILL_OF_LADING,
            bol_parsed_data=bol.model_dump(mode="json"),
        )
        pl_doc = make_document(doc_type=DocumentType.PACKING_LIST)

        shipment = make_shipment(org_id=bol_doc.organization_id)
        db = make_db(shipment=shipment, documents=[bol_doc, pl_doc])
        issues = cross_validate_weights(shipment, db)
        assert len(issues) == 0


class TestAutoSyncThreshold:
    """Tests for the auto-sync confidence threshold."""

    def test_threshold_is_70_percent(self):
        assert AUTO_SYNC_CONFIDENCE_THRESHOLD == 0.70
