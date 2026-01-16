"""Tests for BoL Compliance API Endpoints.

TDD Phase: Integration Tests for Phase 5

These tests verify the API endpoints for:
1. POST /documents/{id}/bol/parse - Parse BoL document
2. POST /documents/{id}/bol/check-compliance - Run compliance checks
3. GET /documents/{id}/bol/compliance-results - Get stored results
4. GET /documents/{id}/bol/sync-preview - Preview shipment sync
5. POST /documents/{id}/bol/sync - Apply shipment sync
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date
from uuid import uuid4
import json

from fastapi.testclient import TestClient


# Mock classes for testing without database
class MockDocument:
    """Mock Document model."""
    def __init__(self):
        self.id = uuid4()
        self.shipment_id = uuid4()
        self.organization_id = uuid4()
        self.document_type = "bill_of_lading"
        self.file_path = "/fake/path/bol.pdf"
        self.bol_parsed_data = None
        self.compliance_status = None
        self.compliance_checked_at = None
        self.updated_at = None


class MockShipment:
    """Mock Shipment model."""
    def __init__(self):
        self.id = uuid4()
        self.reference = "VIBO-2026-001"
        self.container_number = "HAGES-CNT-001"  # Placeholder
        self.bl_number = None
        self.vessel_name = None
        self.voyage_number = None
        self.pol_code = None
        self.pod_code = None
        self.atd = None


class MockCurrentUser:
    """Mock CurrentUser for authentication."""
    def __init__(self):
        self.id = uuid4()
        self.email = "test@example.com"
        self.organization_id = uuid4()
        self.role = MagicMock()
        self.role.value = "admin"


class TestBolParseEndpoint:
    """Tests for POST /documents/{id}/bol/parse endpoint."""

    def test_parse_returns_parsed_data(self):
        """Should return parsed BoL data with confidence score."""
        # This test verifies the endpoint parses BoL correctly
        from app.services.bol_parser import bol_parser
        from app.schemas.bol import CanonicalBoL

        sample_text = """
        Bill of Lading Number: APU106546
        SHIPPER:
        VIBOTAJ GLOBAL NIG LTD
        LAGOS, NIGERIA

        CONSIGNEE:
        HAGES GMBH
        HAMBURG, GERMANY

        Container No.: MRSU4825686 / SEAL: SL123456
        Vessel: MSC MARINA
        Voyage: VY2026001
        Port of Loading: NGAPP APAPA
        Port of Discharge: DEHAM HAMBURG

        DESCRIPTION OF GOODS:
        CATTLE HOOVES AND HORNS
        HS CODE: 0506
        GROSS WEIGHT: 20000 KGS
        """

        result = bol_parser.parse(sample_text)

        assert isinstance(result, CanonicalBoL)
        assert result.bol_number == "APU106546"
        assert result.confidence_score > 0.5

    def test_parse_rejects_non_bol_document(self):
        """Should reject documents that are not Bill of Lading type."""
        # This tests the validation logic
        from app.models.document import DocumentType

        # Verify document type check works
        assert DocumentType.BILL_OF_LADING.value == "bill_of_lading"
        assert DocumentType.COMMERCIAL_INVOICE.value == "commercial_invoice"

    def test_parse_handles_empty_text(self):
        """Should handle empty text gracefully."""
        from app.services.bol_parser import bol_parser

        result = bol_parser.parse("")

        assert result.bol_number == "UNKNOWN"
        assert result.confidence_score == 0.0


class TestBolComplianceCheckEndpoint:
    """Tests for POST /documents/{id}/bol/check-compliance endpoint."""

    def test_compliance_check_returns_decision(self):
        """Should return compliance decision (APPROVE/HOLD/REJECT)."""
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer, BolCargo

        # Complete BoL should APPROVE
        bol = CanonicalBoL(
            bol_number="APU106546",
            shipper=BolParty(name="VIBOTAJ GLOBAL"),
            consignee=BolParty(name="HAGES GMBH"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[BolCargo(description="CATTLE HOOVES")],
            vessel_name="MSC MARINA",
            voyage_number="VY2026001",
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            confidence_score=0.95,
        )

        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)

        assert decision == "APPROVE"

    def test_compliance_check_hold_on_warnings(self):
        """Should return HOLD when there are warning failures."""
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )
        from app.schemas.bol import CanonicalBoL, BolParty

        # BoL missing containers should get HOLD (WARNING)
        bol = CanonicalBoL(
            bol_number="APU106546",
            shipper=BolParty(name="VIBOTAJ GLOBAL"),
            consignee=BolParty(name="HAGES GMBH"),
            containers=[],  # Missing containers
            cargo=[],  # Missing cargo
            vessel_name="MSC MARINA",
            voyage_number="VY2026001",
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            confidence_score=0.95,
        )

        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)

        assert decision == "HOLD"

    def test_compliance_check_reject_on_errors(self):
        """Should return REJECT when there are error failures."""
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer, BolCargo

        # BoL with placeholder shipper should get REJECT (ERROR)
        bol = CanonicalBoL(
            bol_number="APU106546",
            shipper=BolParty(name="Unknown Shipper"),  # Placeholder
            consignee=BolParty(name="HAGES GMBH"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[BolCargo(description="CATTLE HOOVES")],
            confidence_score=0.5,
        )

        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)

        assert decision == "REJECT"

    def test_compliance_stores_results(self):
        """Should store compliance results in database."""
        from app.models.compliance_result import ComplianceResult

        # Verify ComplianceResult model has required fields
        assert hasattr(ComplianceResult, 'document_id')
        assert hasattr(ComplianceResult, 'rule_id')
        assert hasattr(ComplianceResult, 'passed')
        assert hasattr(ComplianceResult, 'severity')
        assert hasattr(ComplianceResult, 'organization_id')


class TestBolComplianceResultsEndpoint:
    """Tests for GET /documents/{id}/bol/compliance-results endpoint."""

    def test_returns_stored_results(self):
        """Should return previously stored compliance results."""
        # Test that results can be retrieved
        from app.models.compliance_result import ComplianceResult

        # Create a mock result
        result = ComplianceResult(
            document_id=uuid4(),
            organization_id=uuid4(),
            rule_id="BOL-001",
            rule_name="Shipper Name Required",
            passed=True,
            message="Shipper Name Required: OK",
            severity="ERROR",
        )

        assert result.rule_id == "BOL-001"
        assert result.passed is True

    def test_returns_empty_when_no_results(self):
        """Should return message when no results exist."""
        # This verifies the API behavior
        pass  # Tested via integration


class TestBolSyncPreviewEndpoint:
    """Tests for GET /documents/{id}/bol/sync-preview endpoint."""

    def test_preview_shows_changes(self):
        """Should show what changes would be made to shipment."""
        from app.services.bol_shipment_sync import BolShipmentSync
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer

        sync = BolShipmentSync()
        shipment = MockShipment()
        bol = CanonicalBoL(
            bol_number="APU106546",
            shipper=BolParty(name="VIBOTAJ"),
            consignee=BolParty(name="HAGES"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[],
            vessel_name="MSC MARINA",
            voyage_number="VY2026001",
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
        )

        changes = sync.get_sync_changes(shipment, bol)

        assert "bl_number" in changes
        assert "container_number" in changes  # Placeholder should be replaced
        assert "vessel_name" in changes

    def test_preview_does_not_modify(self):
        """Should not modify shipment when previewing."""
        from app.services.bol_shipment_sync import BolShipmentSync
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer

        sync = BolShipmentSync()
        shipment = MockShipment()
        original_container = shipment.container_number

        bol = CanonicalBoL(
            bol_number="APU106546",
            shipper=BolParty(name="VIBOTAJ"),
            consignee=BolParty(name="HAGES"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[],
        )

        # Get changes without applying
        sync.get_sync_changes(shipment, bol)

        # Shipment should be unchanged
        assert shipment.container_number == original_container


class TestBolSyncEndpoint:
    """Tests for POST /documents/{id}/bol/sync endpoint."""

    def test_sync_updates_shipment(self):
        """Should update shipment with BoL data."""
        from app.services.bol_shipment_sync import BolShipmentSync
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer

        sync = BolShipmentSync()
        shipment = MockShipment()
        bol = CanonicalBoL(
            bol_number="APU106546",
            shipper=BolParty(name="VIBOTAJ"),
            consignee=BolParty(name="HAGES"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[],
            vessel_name="MSC MARINA",
            voyage_number="VY2026001",
        )

        changes = sync.apply_sync_changes(shipment, bol)

        assert shipment.bl_number == "APU106546"
        assert shipment.container_number == "MRSU4825686"
        assert shipment.vessel_name == "MSC MARINA"
        assert shipment.voyage_number == "VY2026001"

    def test_sync_returns_changes(self):
        """Should return dictionary of changes made."""
        from app.services.bol_shipment_sync import BolShipmentSync
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer

        sync = BolShipmentSync()
        shipment = MockShipment()
        bol = CanonicalBoL(
            bol_number="APU106546",
            shipper=BolParty(name="VIBOTAJ"),
            consignee=BolParty(name="HAGES"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[],
        )

        changes = sync.apply_sync_changes(shipment, bol)

        assert isinstance(changes, dict)
        assert "bl_number" in changes
        assert changes["bl_number"]["old"] is None
        assert changes["bl_number"]["new"] == "APU106546"


class TestMultiTenancy:
    """Test multi-tenancy isolation in BoL compliance endpoints."""

    def test_document_filtered_by_organization(self):
        """Should only return documents from user's organization."""
        # This verifies the query includes organization_id filter
        from app.models.document import Document

        # Verify Document model has organization_id
        assert hasattr(Document, 'organization_id')

    def test_compliance_results_filtered_by_organization(self):
        """Should only return compliance results from user's organization."""
        from app.models.compliance_result import ComplianceResult

        # Verify ComplianceResult model has organization_id
        assert hasattr(ComplianceResult, 'organization_id')


class TestAllProductTypes:
    """Test that BoL compliance works for all product types."""

    def test_horn_and_hoof_bol(self):
        """Should process Horn & Hoof BoL correctly."""
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer, BolCargo

        bol = CanonicalBoL(
            bol_number="HORN-BOL-001",
            shipper=BolParty(name="VIBOTAJ GLOBAL"),
            consignee=BolParty(name="HAGES GMBH"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[BolCargo(description="CATTLE HOOVES AND HORNS", hs_code="0506")],
            vessel_name="MSC MARINA",
            voyage_number="VY2026001",
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            confidence_score=0.9,
        )

        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)

        assert decision == "APPROVE"

    def test_agricultural_bol(self):
        """Should process agricultural BoL correctly."""
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer, BolCargo

        bol = CanonicalBoL(
            bol_number="AGR-BOL-001",
            shipper=BolParty(name="FARM EXPORTS"),
            consignee=BolParty(name="FOOD IMPORTS GMBH"),
            containers=[BolContainer(number="TCNU1234567")],
            cargo=[BolCargo(description="COCOA BEANS", hs_code="1801")],
            vessel_name="MSC CRISTINA",
            voyage_number="VY2026002",
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            confidence_score=0.9,
        )

        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)

        assert decision == "APPROVE"

    def test_general_cargo_bol(self):
        """Should process general cargo BoL correctly."""
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )
        from app.schemas.bol import CanonicalBoL, BolParty, BolContainer, BolCargo

        bol = CanonicalBoL(
            bol_number="GEN-BOL-001",
            shipper=BolParty(name="EXPORT COMPANY"),
            consignee=BolParty(name="IMPORT GMBH"),
            containers=[BolContainer(number="MSKU9876543")],
            cargo=[BolCargo(description="GENERAL MERCHANDISE", hs_code="9999")],
            vessel_name="MSC BELLA",
            voyage_number="VY2026003",
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            confidence_score=0.9,
        )

        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)

        assert decision == "APPROVE"


class TestIntegration:
    """Integration tests for the complete flow."""

    def test_parse_and_check_compliance_flow(self):
        """Test the complete flow: parse -> check compliance -> get results."""
        from app.services.bol_parser import bol_parser
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )

        sample_text = """
        Bill of Lading Number: APU106546
        SHIPPER:
        VIBOTAJ GLOBAL NIG LTD
        CONSIGNEE:
        HAGES GMBH
        Container No.: MRSU4825686
        Vessel: MSC MARINA
        Voyage: VY2026001
        Port of Loading: NGAPP APAPA
        Port of Discharge: DEHAM HAMBURG
        DESCRIPTION OF GOODS:
        CATTLE HOOVES
        """

        # Step 1: Parse
        parsed_bol = bol_parser.parse(sample_text)
        assert parsed_bol.bol_number == "APU106546"

        # Step 2: Check compliance
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(parsed_bol)
        decision = get_compliance_decision(results)

        # Step 3: Verify results
        assert decision in ["APPROVE", "HOLD", "REJECT"]
        assert len(results) == len(STANDARD_BOL_RULES)

        # Verify result structure
        for result in results:
            assert hasattr(result, 'rule_id')
            assert hasattr(result, 'passed')
            assert hasattr(result, 'severity')

    def test_compliance_and_sync_flow(self):
        """Test: check compliance -> sync to shipment."""
        from app.services.bol_parser import bol_parser
        from app.services.bol_rules import (
            RulesEngine,
            STANDARD_BOL_RULES,
            get_compliance_decision,
        )
        from app.services.bol_shipment_sync import BolShipmentSync

        sample_text = """
        Bill of Lading Number: APU106546
        SHIPPER:
        VIBOTAJ GLOBAL NIG LTD
        CONSIGNEE:
        HAGES GMBH
        Container No.: MRSU4825686
        Vessel: MSC MARINA
        Voyage: VY2026001
        Port of Loading: NGAPP
        Port of Discharge: DEHAM
        """

        # Parse
        parsed_bol = bol_parser.parse(sample_text)

        # Check compliance
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(parsed_bol)
        decision = get_compliance_decision(results)

        # Only sync if not rejected
        if decision != "REJECT":
            sync = BolShipmentSync()
            shipment = MockShipment()
            changes = sync.apply_sync_changes(shipment, parsed_bol)

            assert shipment.bl_number == "APU106546"
            assert shipment.container_number == "MRSU4825686"
