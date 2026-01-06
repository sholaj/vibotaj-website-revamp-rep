"""
Test fixtures for TraceHub compliance tests.

These fixtures provide sample data for testing compliance rules,
especially EUDR (EU Deforestation Regulation) applicability.
"""
import pytest


@pytest.fixture
def sample_horn_hoof_shipment():
    """Sample shipment - horn/hoof product (NO EUDR).
    
    Horn and hoof products (HS 0506/0507) are NOT covered by EUDR.
    They should never require geolocation or deforestation statements.
    """
    return {
        "id": "SHIP-001",
        "hs_code": "0506.10",
        "product_type": "HORN_HOOF",
        "product_name": "Cattle Horns",
        "eudr_required": False,  # CRITICAL: Always False for 0506/0507
        "required_docs": [
            "EU_TRACES",
            "VETERINARY_HEALTH_CERT",
            "CERTIFICATE_OF_ORIGIN",
            "BILL_OF_LADING",
            "COMMERCIAL_INVOICE",
            "PACKING_LIST",
        ],
        "traces_number": "RC1479592",
        "origin_country": "Nigeria",
        "destination": "Germany",
        "buyer": "HAGES",
    }


@pytest.fixture
def sample_sweet_potato_shipment():
    """Sample shipment - sweet potato pellets (NO EUDR)."""
    return {
        "id": "SHIP-002",
        "hs_code": "0714.20",
        "product_type": "SWEET_POTATO_PELLETS",
        "product_name": "Sweet Potato Pellets",
        "eudr_required": False,
        "required_docs": [
            "PHYTOSANITARY_CERT",
            "CERTIFICATE_OF_ORIGIN",
            "QUALITY_CERT",
            "BILL_OF_LADING",
            "COMMERCIAL_INVOICE",
        ],
        "origin_country": "Nigeria",
        "destination": "Belgium",
        "buyer": "De Lochting",
    }


@pytest.fixture
def sample_cocoa_shipment():
    """Sample shipment - cocoa beans (EUDR APPLICABLE).
    
    Cocoa (HS 1801) IS covered by EUDR and requires additional documentation.
    This is for future use when VIBOTAJ expands to cocoa products.
    """
    return {
        "id": "SHIP-003",
        "hs_code": "1801.00",
        "product_type": "COCOA",
        "product_name": "Cocoa Beans",
        "eudr_required": True,  # YES - cocoa is in EUDR Annex I
        "required_docs": [
            "CERTIFICATE_OF_ORIGIN",
            "BILL_OF_LADING",
            "COMMERCIAL_INVOICE",
            "PHYTOSANITARY_CERT",
            "EUDR_STATEMENT",
            "GEOLOCATION_DATA",
            "RISK_ASSESSMENT",
        ],
        "origin_country": "Nigeria",
        "destination": "Germany",
        "geolocation": {
            "latitude": 7.3775,
            "longitude": 3.9470,
            "polygon": [],  # Farm boundary coordinates
        },
    }


@pytest.fixture
def traces_number():
    """VIBOTAJ EU TRACES number for animal products."""
    return "RC1479592"


@pytest.fixture
def eudr_applicable_hs_codes():
    """List of HS codes that require EUDR compliance.
    
    Based on EUDR Annex I:
    - 1801: Cocoa
    - 0901: Coffee
    - 1511: Palm oil
    - 4001: Rubber
    - 1201: Soybeans
    """
    return ["1801", "0901", "1511", "4001", "1201"]


@pytest.fixture
def non_eudr_hs_codes():
    """List of VIBOTAJ product HS codes that are NOT EUDR-applicable."""
    return {
        "0506": "Horn",
        "0507": "Hoof",
        "0714.20": "Sweet Potato Pellets",
        "0902.10": "Hibiscus Flowers",
        "0910.11": "Dried Ginger",
    }
