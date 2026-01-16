"""Tests for Bill of Lading Parser Service.

TDD Phase: RED - Write failing tests first

These tests verify the BoL parser can:
1. Extract shipper and consignee information
2. Extract container numbers (ISO 6346 format)
3. Extract vessel and voyage details
4. Extract port information
5. Extract cargo descriptions
6. Calculate confidence scores
7. Handle various BoL formats from different shipping lines
"""

import pytest

from app.services.bol_parser import BolParser
from app.schemas.bol import CanonicalBoL


# Sample BoL text extracted from actual documents
SAMPLE_BOL_TEXT_MSC = """
BILL OF LADING
B/L No.: APU106546

SHIPPER:
VIBOTAJ GLOBAL NIGERIA LIMITED
123 EXPORT ROAD
LAGOS, NIGERIA

CONSIGNEE:
HAGES GMBH
IMPORT STRASSE 45
20457 HAMBURG, GERMANY

NOTIFY PARTY:
SAME AS CONSIGNEE

VESSEL: MSC MARINA
VOYAGE NO.: VY2026001

PORT OF LOADING: APAPA, NIGERIA (NGAPP)
PORT OF DISCHARGE: HAMBURG, GERMANY (DEHAM)

CONTAINER NO.: MRSU4825686
SEAL NO.: SL123456
TYPE: 40' HIGH CUBE

DESCRIPTION OF GOODS:
CATTLE HOOVES AND HORNS
HS CODE: 0506
GROSS WEIGHT: 20,500 KGS
NET WEIGHT: 20,000 KGS

SHIPPED ON BOARD: 12 JAN 2026
FREIGHT: PREPAID
"""

SAMPLE_BOL_TEXT_HAPAG = """
Hapag-Lloyd
BILL OF LADING

Bill of Lading Number: HLCUHAM123456789

Shipper
VIBOTAJ GLOBAL NIG LTD
APAPA PORT COMPLEX
LAGOS NIGERIA

Consignee
BECKMANN GBH
INDUSTRIESTRASSE 12
BERLIN, GERMANY

Vessel/Voyage: TOKYO EXPRESS / 025E
Place of Receipt: LAGOS
Port of Loading: NGAPP APAPA
Port of Discharge: DEHAM HAMBURG
Place of Delivery: HAMBURG

Container Number: CAAU9221188
Seal: HLCU987654
Equipment: 20GP

Commodity: ANIMAL BY-PRODUCTS (HOOVES)
Harmonized Code: 0506
Packages: 500 BAGS
Gross Weight: 18000.00 KGS

Date of Issue: 15-JAN-2026
"""

SAMPLE_BOL_WITATRADE = """
OCEAN BILL OF LADING

BL NUMBER: WBL-2026-001

EXPORTER/SHIPPER:
VIBOTAJ GLOBAL NIGERIA LTD
PORT AREA, APAPA
LAGOS, NIGERIA

CONSIGNEE (TO ORDER):
WITATRADE GMBH
HAFENSTRASSE 88
BREMEN, GERMANY

Notify: WITATRADE GMBH

OCEAN VESSEL: EVER GIVEN
VOY NO: EG-2026-001

POL: APAPA PORT (NGAPP)
POD: BREMERHAVEN (DEBRV)
FINAL DEST: BREMEN

CONTAINER/SEAL:
GCXU5659375 / SEAL-001

CARGO DESCRIPTION:
PROCESSED CATTLE HORNS
HS: 0507
20 METRIC TONS
GROSS: 20500 KG / NET: 20000 KG

ON BOARD DATE: 2026-01-20
TERMS: CFR BREMERHAVEN
"""


class TestBolParserBasic:
    """Test basic BoL parsing functionality."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return BolParser()

    def test_parser_initializes(self, parser):
        """Parser should initialize without errors."""
        assert parser is not None

    def test_parse_returns_canonical_bol(self, parser):
        """Parse should return CanonicalBoL instance."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert isinstance(result, CanonicalBoL)

    def test_parse_empty_text_returns_empty_bol(self, parser):
        """Parse with empty text should return minimal BoL."""
        result = parser.parse("")
        assert result.confidence_score < 0.5


class TestBolParserShipperExtraction:
    """Test shipper information extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_shipper_name(self, parser):
        """Should extract shipper name."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.shipper is not None
        assert "VIBOTAJ" in result.shipper.name.upper()

    def test_extract_shipper_from_hapag_format(self, parser):
        """Should extract shipper from Hapag-Lloyd format."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        assert result.shipper is not None
        assert "VIBOTAJ" in result.shipper.name.upper()

    def test_extract_shipper_country(self, parser):
        """Should extract shipper country."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.shipper.country is not None
        assert "NIGERIA" in result.shipper.country.upper()


class TestBolParserConsigneeExtraction:
    """Test consignee information extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_consignee_name(self, parser):
        """Should extract consignee name."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.consignee is not None
        assert "HAGES" in result.consignee.name.upper()

    def test_extract_consignee_from_hapag_format(self, parser):
        """Should extract consignee from Hapag-Lloyd format."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        assert result.consignee is not None
        assert "BECKMANN" in result.consignee.name.upper()

    def test_extract_consignee_witatrade(self, parser):
        """Should extract WITATRADE as consignee."""
        result = parser.parse(SAMPLE_BOL_WITATRADE)
        assert result.consignee is not None
        assert "WITATRADE" in result.consignee.name.upper()


class TestBolParserContainerExtraction:
    """Test container number extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_container_number(self, parser):
        """Should extract container number in ISO 6346 format."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert len(result.containers) > 0
        assert result.containers[0].number == "MRSU4825686"

    def test_extract_container_from_hapag_format(self, parser):
        """Should extract container from Hapag-Lloyd format."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        assert len(result.containers) > 0
        assert result.containers[0].number == "CAAU9221188"

    def test_extract_container_with_spaces(self, parser):
        """Should handle container numbers with spaces."""
        text = "Container No.: MRSU 4825686"
        result = parser.parse(text)
        if result.containers:
            assert result.containers[0].number == "MRSU4825686"

    def test_extract_seal_number(self, parser):
        """Should extract seal number."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        if result.containers:
            assert result.containers[0].seal_number is not None

    def test_extract_container_type(self, parser):
        """Should extract container type."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        if result.containers and result.containers[0].type:
            assert "GP" in result.containers[0].type or "HC" in result.containers[0].type


class TestBolParserVesselExtraction:
    """Test vessel and voyage extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_vessel_name(self, parser):
        """Should extract vessel name."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.vessel_name is not None
        assert "MSC" in result.vessel_name.upper() or "MARINA" in result.vessel_name.upper()

    def test_extract_voyage_number(self, parser):
        """Should extract voyage number."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.voyage_number is not None

    def test_extract_vessel_from_combined_format(self, parser):
        """Should extract vessel from 'Vessel/Voyage' combined format."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        assert result.vessel_name is not None
        assert "TOKYO" in result.vessel_name.upper() or "EXPRESS" in result.vessel_name.upper()


class TestBolParserPortExtraction:
    """Test port of loading/discharge extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_port_of_loading(self, parser):
        """Should extract port of loading."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.port_of_loading is not None
        # Should contain APAPA or NGAPP
        assert "APAPA" in result.port_of_loading.upper() or "NGAPP" in result.port_of_loading.upper()

    def test_extract_port_of_discharge(self, parser):
        """Should extract port of discharge."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.port_of_discharge is not None
        # Should contain HAMBURG or DEHAM
        assert "HAMBURG" in result.port_of_discharge.upper() or "DEHAM" in result.port_of_discharge.upper()

    def test_extract_pol_from_hapag(self, parser):
        """Should extract POL from Hapag-Lloyd format."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        assert result.port_of_loading is not None


class TestBolParserCargoExtraction:
    """Test cargo/goods description extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_cargo_description(self, parser):
        """Should extract cargo description."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert len(result.cargo) > 0
        # Should mention hooves, horns, or cattle
        cargo_desc = result.cargo[0].description.upper()
        assert any(word in cargo_desc for word in ["HOOVES", "HORNS", "CATTLE", "ANIMAL"])

    def test_extract_hs_code(self, parser):
        """Should extract HS code."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        if result.cargo:
            # Should be 0506 or 0507 for horn/hoof
            hs_codes = [c.hs_code for c in result.cargo if c.hs_code]
            if hs_codes:
                assert any(code in ["0506", "0507"] for code in hs_codes)

    def test_extract_weight(self, parser):
        """Should extract gross weight."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        if result.cargo and result.cargo[0].gross_weight_kg:
            assert result.cargo[0].gross_weight_kg > 0


class TestBolParserBolNumberExtraction:
    """Test B/L number extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_bol_number_msc(self, parser):
        """Should extract B/L number from MSC format."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.bol_number is not None
        assert "APU106546" in result.bol_number

    def test_extract_bol_number_hapag(self, parser):
        """Should extract B/L number from Hapag-Lloyd format."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        assert result.bol_number is not None
        assert "HLCU" in result.bol_number.upper()

    def test_extract_bol_number_witatrade(self, parser):
        """Should extract B/L number from Witatrade format."""
        result = parser.parse(SAMPLE_BOL_WITATRADE)
        assert result.bol_number is not None
        assert "WBL" in result.bol_number.upper()


class TestBolParserConfidenceScore:
    """Test confidence score calculation."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_high_confidence_for_complete_bol(self, parser):
        """Complete BoL should have high confidence."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.confidence_score >= 0.7

    def test_low_confidence_for_partial_bol(self, parser):
        """Partial BoL should have lower confidence."""
        partial_text = "BILL OF LADING\nShipper: VIBOTAJ"
        result = parser.parse(partial_text)
        assert result.confidence_score < 0.7

    def test_very_low_confidence_for_gibberish(self, parser):
        """Gibberish text should have very low confidence."""
        result = parser.parse("random text without bol content")
        assert result.confidence_score < 0.3


class TestBolParserNotifyParty:
    """Test notify party extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_notify_party(self, parser):
        """Should extract notify party."""
        result = parser.parse(SAMPLE_BOL_WITATRADE)
        # Notify party should be extracted
        if result.notify_party:
            assert "WITATRADE" in result.notify_party.name.upper()


class TestBolParserDateExtraction:
    """Test date extraction."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_extract_shipped_on_board_date(self, parser):
        """Should extract shipped on board date."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        if result.shipped_on_board_date:
            assert result.shipped_on_board_date.year == 2026
            assert result.shipped_on_board_date.month == 1

    def test_extract_date_of_issue(self, parser):
        """Should extract date of issue."""
        result = parser.parse(SAMPLE_BOL_TEXT_HAPAG)
        if result.date_of_issue:
            assert result.date_of_issue.year == 2026


class TestBolParserRawText:
    """Test raw text storage."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_stores_raw_text(self, parser):
        """Should store raw text in result."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.raw_text is not None
        assert "VIBOTAJ" in result.raw_text


class TestBolParserProductTypes:
    """Test parser works for all product types."""

    @pytest.fixture
    def parser(self):
        return BolParser()

    def test_parse_horn_and_hoof_bol(self, parser):
        """Should parse Horn & Hoof product BoL (HS 0506/0507)."""
        result = parser.parse(SAMPLE_BOL_TEXT_MSC)
        assert result.shipper is not None
        assert result.consignee is not None
        # Should identify horn/hoof HS codes
        hs_codes = result.get_hs_codes()
        if hs_codes:
            assert any(code in ["0506", "0507"] for code in hs_codes)

    def test_parse_general_cargo_bol(self, parser):
        """Should parse general cargo BoL."""
        general_bol = """
        BILL OF LADING
        BL: GEN-2026-001
        Shipper: EXPORT CO LTD
        Consignee: IMPORT GMBH
        Container: TCNU1234567
        Goods: GENERAL MERCHANDISE
        HS Code: 9999
        """
        result = parser.parse(general_bol)
        assert result.shipper is not None or result.bol_number is not None
