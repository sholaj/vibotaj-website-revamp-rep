"""Tests for Canonical Bill of Lading Schema.

TDD Phase: RED - Write failing tests first

These tests verify the BoL schema can:
1. Validate required fields
2. Handle optional fields gracefully
3. Validate container number format (ISO 6346)
4. Serialize to/from JSON
5. Work with all product types (Horn & Hoof, etc.)
"""

import pytest
from datetime import date
from pydantic import ValidationError

# Import will fail until schema is created (RED phase)
from app.schemas.bol import (
    BolParty,
    BolContainer,
    BolCargo,
    CanonicalBoL
)


class TestBolParty:
    """Test BolParty schema for shipper/consignee/notify party."""

    def test_party_with_all_fields(self):
        """Party with all fields should validate."""
        party = BolParty(
            name="VIBOTAJ GLOBAL NIG LTD",
            address="123 Export Street, Lagos",
            country="Nigeria"
        )
        assert party.name == "VIBOTAJ GLOBAL NIG LTD"
        assert party.address == "123 Export Street, Lagos"
        assert party.country == "Nigeria"

    def test_party_with_only_name(self):
        """Party with only name should be valid (address/country optional)."""
        party = BolParty(name="HAGES GMBH")
        assert party.name == "HAGES GMBH"
        assert party.address is None
        assert party.country is None

    def test_party_requires_name(self):
        """Party without name should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            BolParty(address="Some Address")
        assert "name" in str(exc_info.value).lower()


class TestBolContainer:
    """Test BolContainer schema for container details."""

    def test_container_with_valid_iso6346(self):
        """Container with valid ISO 6346 number should validate."""
        container = BolContainer(
            number="MRSU4825686",
            seal_number="SL123456",
            type="40HC",
            weight_kg=25000.0
        )
        assert container.number == "MRSU4825686"
        assert container.seal_number == "SL123456"
        assert container.type == "40HC"
        assert container.weight_kg == 25000.0

    def test_container_with_only_number(self):
        """Container with only number should be valid."""
        container = BolContainer(number="CAAU9221188")
        assert container.number == "CAAU9221188"
        assert container.seal_number is None

    def test_container_requires_number(self):
        """Container without number should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            BolContainer(seal_number="SL123")
        assert "number" in str(exc_info.value).lower()

    def test_container_number_format_validation(self):
        """Container number should match ISO 6346 format (4 letters + 7 digits)."""
        # Valid formats
        valid_containers = [
            "MRSU4825686",
            "CAAU9221188",
            "GCXU5659375",
            "HASU4314433",
        ]
        for num in valid_containers:
            container = BolContainer(number=num)
            assert container.number == num

    def test_container_normalizes_number(self):
        """Container number should be normalized (uppercase, no spaces)."""
        container = BolContainer(number="mrsu4825686")
        assert container.number == "MRSU4825686"


class TestBolCargo:
    """Test BolCargo schema for cargo details."""

    def test_cargo_with_all_fields(self):
        """Cargo with all fields should validate."""
        cargo = BolCargo(
            description="CATTLE HOOVES AND HORNS",
            hs_code="0506",
            quantity=20.0,
            unit="MT",
            gross_weight_kg=20500.0,
            net_weight_kg=20000.0
        )
        assert cargo.description == "CATTLE HOOVES AND HORNS"
        assert cargo.hs_code == "0506"
        assert cargo.quantity == 20.0

    def test_cargo_with_only_description(self):
        """Cargo with only description should be valid."""
        cargo = BolCargo(description="ANIMAL BY-PRODUCTS")
        assert cargo.description == "ANIMAL BY-PRODUCTS"
        assert cargo.hs_code is None

    def test_cargo_requires_description(self):
        """Cargo without description should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            BolCargo(hs_code="0506")
        assert "description" in str(exc_info.value).lower()


class TestCanonicalBoL:
    """Test CanonicalBoL schema - the main Bill of Lading model."""

    @pytest.fixture
    def valid_bol_data(self):
        """Valid BoL data for testing."""
        return {
            "bol_number": "APU106546",
            "shipper": {
                "name": "VIBOTAJ GLOBAL NIG LTD",
                "address": "Lagos, Nigeria",
                "country": "Nigeria"
            },
            "consignee": {
                "name": "HAGES GMBH",
                "address": "Hamburg, Germany",
                "country": "Germany"
            },
            "containers": [
                {"number": "MRSU4825686", "type": "40HC"}
            ],
            "cargo": [
                {"description": "CATTLE HOOVES", "hs_code": "0506"}
            ],
            "vessel_name": "MSC MARINA",
            "voyage_number": "VY2026001",
            "port_of_loading": "NGAPP",
            "port_of_discharge": "DEHAM",
            "date_of_issue": "2026-01-10",
            "shipped_on_board_date": "2026-01-12"
        }

    def test_bol_validates_required_fields(self, valid_bol_data):
        """BoL with all required fields should validate."""
        bol = CanonicalBoL(**valid_bol_data)
        assert bol.bol_number == "APU106546"
        assert bol.shipper.name == "VIBOTAJ GLOBAL NIG LTD"
        assert bol.consignee.name == "HAGES GMBH"

    def test_bol_requires_bol_number(self, valid_bol_data):
        """BoL without bol_number should fail."""
        del valid_bol_data["bol_number"]
        with pytest.raises(ValidationError) as exc_info:
            CanonicalBoL(**valid_bol_data)
        assert "bol_number" in str(exc_info.value).lower()

    def test_bol_requires_shipper(self, valid_bol_data):
        """BoL without shipper should fail."""
        del valid_bol_data["shipper"]
        with pytest.raises(ValidationError) as exc_info:
            CanonicalBoL(**valid_bol_data)
        assert "shipper" in str(exc_info.value).lower()

    def test_bol_requires_consignee(self, valid_bol_data):
        """BoL without consignee should fail."""
        del valid_bol_data["consignee"]
        with pytest.raises(ValidationError) as exc_info:
            CanonicalBoL(**valid_bol_data)
        assert "consignee" in str(exc_info.value).lower()

    def test_bol_handles_optional_fields(self):
        """BoL with only required fields should be valid."""
        bol = CanonicalBoL(
            bol_number="TEST123",
            shipper=BolParty(name="Shipper Co"),
            consignee=BolParty(name="Consignee Co"),
            containers=[],
            cargo=[]
        )
        assert bol.vessel_name is None
        assert bol.port_of_loading is None
        assert bol.notify_party is None

    def test_bol_serializes_to_json(self, valid_bol_data):
        """BoL should serialize to JSON."""
        bol = CanonicalBoL(**valid_bol_data)
        json_str = bol.model_dump_json()
        assert "APU106546" in json_str
        assert "VIBOTAJ" in json_str

    def test_bol_deserializes_from_dict(self, valid_bol_data):
        """BoL should deserialize from dictionary."""
        bol = CanonicalBoL.model_validate(valid_bol_data)
        assert bol.bol_number == "APU106546"

    def test_bol_confidence_score_default(self):
        """BoL should have default confidence score of 0.0."""
        bol = CanonicalBoL(
            bol_number="TEST",
            shipper=BolParty(name="Test"),
            consignee=BolParty(name="Test"),
            containers=[],
            cargo=[]
        )
        assert bol.confidence_score == 0.0

    def test_bol_confidence_score_set(self, valid_bol_data):
        """BoL confidence score should be settable."""
        valid_bol_data["confidence_score"] = 0.95
        bol = CanonicalBoL(**valid_bol_data)
        assert bol.confidence_score == 0.95

    def test_bol_with_multiple_containers(self, valid_bol_data):
        """BoL should support multiple containers."""
        valid_bol_data["containers"] = [
            {"number": "MRSU4825686", "type": "40HC"},
            {"number": "CAAU9221188", "type": "20GP"},
        ]
        bol = CanonicalBoL(**valid_bol_data)
        assert len(bol.containers) == 2
        assert bol.containers[0].number == "MRSU4825686"
        assert bol.containers[1].number == "CAAU9221188"

    def test_bol_with_multiple_cargo(self, valid_bol_data):
        """BoL should support multiple cargo items."""
        valid_bol_data["cargo"] = [
            {"description": "CATTLE HOOVES", "hs_code": "0506"},
            {"description": "CATTLE HORNS", "hs_code": "0507"},
        ]
        bol = CanonicalBoL(**valid_bol_data)
        assert len(bol.cargo) == 2

    def test_bol_with_notify_party(self, valid_bol_data):
        """BoL should support notify party."""
        valid_bol_data["notify_party"] = {
            "name": "NOTIFY AGENT",
            "address": "Notify Address"
        }
        bol = CanonicalBoL(**valid_bol_data)
        assert bol.notify_party.name == "NOTIFY AGENT"

    def test_bol_freight_terms(self, valid_bol_data):
        """BoL should support freight terms."""
        valid_bol_data["freight_terms"] = "PREPAID"
        bol = CanonicalBoL(**valid_bol_data)
        assert bol.freight_terms == "PREPAID"

    def test_bol_raw_text_storage(self, valid_bol_data):
        """BoL should store raw text for debugging."""
        valid_bol_data["raw_text"] = "BILL OF LADING\nShipper: VIBOTAJ..."
        bol = CanonicalBoL(**valid_bol_data)
        assert "BILL OF LADING" in bol.raw_text


class TestBolSchemaProductTypes:
    """Test BoL schema works for all product types."""

    def test_bol_horn_and_hoof_product(self):
        """BoL should work for Horn & Hoof products (HS 0506/0507)."""
        bol = CanonicalBoL(
            bol_number="HORN-BOL-001",
            shipper=BolParty(name="VIBOTAJ GLOBAL"),
            consignee=BolParty(name="HAGES GMBH"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[
                BolCargo(description="CATTLE HOOVES", hs_code="0506"),
                BolCargo(description="CATTLE HORNS", hs_code="0507"),
            ]
        )
        assert len(bol.cargo) == 2
        assert bol.cargo[0].hs_code == "0506"
        assert bol.cargo[1].hs_code == "0507"

    def test_bol_generic_product(self):
        """BoL should work for generic products."""
        bol = CanonicalBoL(
            bol_number="GEN-BOL-001",
            shipper=BolParty(name="Exporter"),
            consignee=BolParty(name="Importer"),
            containers=[BolContainer(number="TCNU1234567")],
            cargo=[
                BolCargo(description="GENERAL CARGO", hs_code="9999"),
            ]
        )
        assert bol.cargo[0].description == "GENERAL CARGO"

    def test_bol_agricultural_product(self):
        """BoL should work for agricultural products."""
        bol = CanonicalBoL(
            bol_number="AGR-BOL-001",
            shipper=BolParty(name="Farm Export"),
            consignee=BolParty(name="Food Import"),
            containers=[BolContainer(number="MSKU9876543")],
            cargo=[
                BolCargo(description="COCOA BEANS", hs_code="1801"),
            ]
        )
        assert bol.cargo[0].hs_code == "1801"
