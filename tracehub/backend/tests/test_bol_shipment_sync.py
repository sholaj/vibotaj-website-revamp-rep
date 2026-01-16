"""Tests for BoL Shipment Sync Service.

TDD Phase: RED - Write failing tests first

These tests verify the shipment auto-population from parsed BoL:
1. Container numbers are updated from BoL
2. Vessel and voyage info is updated
3. Port information is updated
4. Placeholder containers are detected and replaced
5. Real ISO 6346 containers are not overwritten
6. B/L number is updated
7. All product types work correctly
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from app.services.bol_shipment_sync import (
    BolShipmentSync,
    is_placeholder_container,
)
from app.schemas.bol import (
    CanonicalBoL,
    BolParty,
    BolContainer,
    BolCargo,
)


# Test fixtures
@pytest.fixture
def complete_bol():
    """Create a complete parsed BoL."""
    return CanonicalBoL(
        bol_number="APU106546",
        shipper=BolParty(name="VIBOTAJ GLOBAL NIG LTD", country="Nigeria"),
        consignee=BolParty(name="HAGES GMBH", country="Germany"),
        containers=[
            BolContainer(number="MRSU4825686", type="40HC", seal_number="SL123456")
        ],
        cargo=[
            BolCargo(description="CATTLE HOOVES AND HORNS", hs_code="0506", gross_weight_kg=20000)
        ],
        vessel_name="MSC MARINA",
        voyage_number="VY2026001",
        port_of_loading="NGAPP",
        port_of_discharge="DEHAM",
        shipped_on_board_date=date(2026, 1, 12),
        confidence_score=0.95,
    )


@pytest.fixture
def mock_shipment():
    """Create a mock shipment object."""
    shipment = MagicMock()
    shipment.id = "test-shipment-123"
    shipment.reference = "VIBO-2026-001"
    shipment.container_number = "HAGES-CNT-001"  # Placeholder
    shipment.bl_number = None
    shipment.vessel_name = None
    shipment.voyage_number = None
    shipment.pol_code = None
    shipment.pol_name = None
    shipment.pod_code = None
    shipment.pod_name = None
    shipment.atd = None
    return shipment


@pytest.fixture
def sync_service():
    """Create sync service instance."""
    return BolShipmentSync()


class TestPlaceholderDetection:
    """Test placeholder container detection."""

    def test_detect_buyer_cnt_placeholder(self):
        """Should detect BUYER-CNT-XXX as placeholder."""
        assert is_placeholder_container("HAGES-CNT-001") is True
        assert is_placeholder_container("BECKMANN-CNT-002") is True
        assert is_placeholder_container("WITATRADE-CNT-003") is True

    def test_detect_tbd_placeholder(self):
        """Should detect TBD as placeholder."""
        assert is_placeholder_container("TBD") is True
        assert is_placeholder_container("tbd") is True

    def test_detect_tbc_placeholder(self):
        """Should detect TBC as placeholder."""
        assert is_placeholder_container("TBC") is True
        assert is_placeholder_container("tbc") is True

    def test_detect_pending_placeholder(self):
        """Should detect PENDING as placeholder."""
        assert is_placeholder_container("PENDING") is True
        assert is_placeholder_container("pending") is True

    def test_detect_empty_as_placeholder(self):
        """Should detect empty string as placeholder."""
        assert is_placeholder_container("") is True
        assert is_placeholder_container(None) is True

    def test_real_container_not_placeholder(self):
        """Should NOT detect valid ISO 6346 as placeholder."""
        assert is_placeholder_container("MRSU4825686") is False
        assert is_placeholder_container("CAAU9221188") is False
        assert is_placeholder_container("GCXU5659375") is False


class TestBolShipmentSyncContainer:
    """Test container number sync from BoL."""

    def test_updates_container_from_bol(self, sync_service, complete_bol, mock_shipment):
        """Should update container number from BoL when placeholder."""
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "container_number" in changes
        assert changes["container_number"]["old"] == "HAGES-CNT-001"
        assert changes["container_number"]["new"] == "MRSU4825686"

    def test_does_not_overwrite_real_container(self, sync_service, complete_bol, mock_shipment):
        """Should NOT overwrite valid ISO 6346 container."""
        mock_shipment.container_number = "CAAU9221188"  # Real container
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "container_number" not in changes

    def test_updates_tbd_container(self, sync_service, complete_bol, mock_shipment):
        """Should update TBD placeholder."""
        mock_shipment.container_number = "TBD"
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "container_number" in changes
        assert changes["container_number"]["new"] == "MRSU4825686"


class TestBolShipmentSyncBlNumber:
    """Test B/L number sync from BoL."""

    def test_updates_bl_number_from_bol(self, sync_service, complete_bol, mock_shipment):
        """Should always update B/L number from BoL."""
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "bl_number" in changes
        assert changes["bl_number"]["new"] == "APU106546"

    def test_updates_existing_bl_number(self, sync_service, complete_bol, mock_shipment):
        """Should update even if B/L number already exists."""
        mock_shipment.bl_number = "OLD-BL-123"
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "bl_number" in changes
        assert changes["bl_number"]["old"] == "OLD-BL-123"
        assert changes["bl_number"]["new"] == "APU106546"


class TestBolShipmentSyncVessel:
    """Test vessel and voyage sync from BoL."""

    def test_updates_vessel_name(self, sync_service, complete_bol, mock_shipment):
        """Should update vessel name from BoL."""
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "vessel_name" in changes
        assert changes["vessel_name"]["new"] == "MSC MARINA"

    def test_updates_voyage_number(self, sync_service, complete_bol, mock_shipment):
        """Should update voyage number from BoL."""
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "voyage_number" in changes
        assert changes["voyage_number"]["new"] == "VY2026001"


class TestBolShipmentSyncPorts:
    """Test port information sync from BoL."""

    def test_updates_port_of_loading(self, sync_service, complete_bol, mock_shipment):
        """Should update POL code from BoL."""
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "pol_code" in changes
        assert changes["pol_code"]["new"] == "NGAPP"

    def test_updates_port_of_discharge(self, sync_service, complete_bol, mock_shipment):
        """Should update POD code from BoL."""
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "pod_code" in changes
        assert changes["pod_code"]["new"] == "DEHAM"


class TestBolShipmentSyncDates:
    """Test date sync from BoL."""

    def test_updates_departure_date(self, sync_service, complete_bol, mock_shipment):
        """Should update ATD from shipped on board date."""
        changes = sync_service.get_sync_changes(mock_shipment, complete_bol)

        assert "atd" in changes
        assert changes["atd"]["new"] == date(2026, 1, 12)


class TestBolShipmentSyncApply:
    """Test applying sync changes to shipment."""

    def test_apply_changes_updates_shipment(self, sync_service, complete_bol, mock_shipment):
        """Should apply all changes to shipment object."""
        changes = sync_service.apply_sync_changes(mock_shipment, complete_bol)

        assert mock_shipment.bl_number == "APU106546"
        assert mock_shipment.container_number == "MRSU4825686"
        assert mock_shipment.vessel_name == "MSC MARINA"
        assert mock_shipment.voyage_number == "VY2026001"
        assert mock_shipment.pol_code == "NGAPP"
        assert mock_shipment.pod_code == "DEHAM"

    def test_apply_returns_changes_dict(self, sync_service, complete_bol, mock_shipment):
        """Should return dictionary of changes made."""
        changes = sync_service.apply_sync_changes(mock_shipment, complete_bol)

        assert isinstance(changes, dict)
        assert "bl_number" in changes
        assert "container_number" in changes


class TestBolShipmentSyncProductTypes:
    """Test sync works for all product types."""

    def test_sync_horn_and_hoof_bol(self, sync_service, mock_shipment):
        """Should sync Horn & Hoof BoL correctly."""
        bol = CanonicalBoL(
            bol_number="HORN-BOL-001",
            shipper=BolParty(name="VIBOTAJ GLOBAL"),
            consignee=BolParty(name="HAGES GMBH"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[BolCargo(description="CATTLE HOOVES", hs_code="0506")],
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
        )
        changes = sync_service.get_sync_changes(mock_shipment, bol)

        assert "container_number" in changes
        assert changes["container_number"]["new"] == "MRSU4825686"

    def test_sync_agricultural_bol(self, sync_service, mock_shipment):
        """Should sync agricultural BoL correctly."""
        bol = CanonicalBoL(
            bol_number="AGR-BOL-001",
            shipper=BolParty(name="FARM EXPORT"),
            consignee=BolParty(name="FOOD IMPORT"),
            containers=[BolContainer(number="TCNU1234567")],
            cargo=[BolCargo(description="COCOA BEANS", hs_code="1801")],
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
        )
        changes = sync_service.get_sync_changes(mock_shipment, bol)

        assert "container_number" in changes
        assert changes["container_number"]["new"] == "TCNU1234567"

    def test_sync_general_cargo_bol(self, sync_service, mock_shipment):
        """Should sync general cargo BoL correctly."""
        bol = CanonicalBoL(
            bol_number="GEN-BOL-001",
            shipper=BolParty(name="EXPORT CO"),
            consignee=BolParty(name="IMPORT GMBH"),
            containers=[BolContainer(number="MSKU9876543")],
            cargo=[BolCargo(description="GENERAL MERCHANDISE", hs_code="9999")],
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
        )
        changes = sync_service.get_sync_changes(mock_shipment, bol)

        assert "container_number" in changes
        assert changes["container_number"]["new"] == "MSKU9876543"


class TestBolShipmentSyncEdgeCases:
    """Test edge cases for sync service."""

    def test_handles_bol_without_container(self, sync_service, mock_shipment):
        """Should handle BoL with no containers gracefully."""
        bol = CanonicalBoL(
            bol_number="NO-CONT-001",
            shipper=BolParty(name="SHIPPER"),
            consignee=BolParty(name="CONSIGNEE"),
            containers=[],  # No containers
            cargo=[],
        )
        changes = sync_service.get_sync_changes(mock_shipment, bol)

        # Should still update B/L number but not container
        assert "bl_number" in changes
        assert "container_number" not in changes

    def test_handles_bol_without_ports(self, sync_service, mock_shipment):
        """Should handle BoL with no port information."""
        bol = CanonicalBoL(
            bol_number="NO-PORTS-001",
            shipper=BolParty(name="SHIPPER"),
            consignee=BolParty(name="CONSIGNEE"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[],
            port_of_loading=None,
            port_of_discharge=None,
        )
        changes = sync_service.get_sync_changes(mock_shipment, bol)

        # Should still update container but not ports
        assert "container_number" in changes
        assert "pol_code" not in changes
        assert "pod_code" not in changes

    def test_handles_bol_with_unknown_placeholder(self, sync_service, mock_shipment):
        """Should not update if BoL has placeholder container (UNKNOWN)."""
        bol = CanonicalBoL(
            bol_number="UNKNOWN",  # Parser placeholder
            shipper=BolParty(name="Unknown Shipper"),
            consignee=BolParty(name="Unknown Consignee"),
            containers=[],
            cargo=[],
        )
        changes = sync_service.get_sync_changes(mock_shipment, bol)

        # Should not update B/L number if it's UNKNOWN placeholder
        assert "bl_number" not in changes or changes["bl_number"]["new"] != "UNKNOWN"


class TestBolShipmentSyncExtractPortCode:
    """Test port code extraction helper."""

    def test_extracts_un_locode_from_parentheses(self, sync_service):
        """Should extract UN/LOCODE from parentheses."""
        code = sync_service._extract_port_code("HAMBURG, GERMANY (DEHAM)")
        assert code == "DEHAM"

    def test_extracts_un_locode_from_prefix(self, sync_service):
        """Should extract UN/LOCODE from prefix."""
        code = sync_service._extract_port_code("NGAPP APAPA")
        assert code == "NGAPP"

    def test_returns_input_if_already_code(self, sync_service):
        """Should return input if already a short code."""
        code = sync_service._extract_port_code("DEHAM")
        assert code == "DEHAM"

    def test_handles_full_port_name(self, sync_service):
        """Should handle full port name without code."""
        code = sync_service._extract_port_code("APAPA, NIGERIA")
        # Should attempt to extract a code or return None
        assert code is None or len(code) <= 10
