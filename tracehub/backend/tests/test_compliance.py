"""
Compliance validation tests - TDD examples for EUDR and document requirements.

These tests demonstrate the TraceHub compliance logic, especially the
critical rule that horn/hoof products (HS 0506/0507) are NOT covered by EUDR.
"""
import pytest

from app.services.compliance import (
    is_eudr_required,
    get_required_documents_by_hs_code,
    EUDR_HS_CODES,
)
from app.models import DocumentType


class TestIsEUDRRequired:
    """Tests for the is_eudr_required() function.

    This is the centralized function that determines if an HS code
    requires EUDR compliance documentation.
    """

    def test_horn_not_eudr_required(self):
        """HS 0506 (horn) does NOT require EUDR."""
        assert is_eudr_required("0506") is False
        assert is_eudr_required("0506.10") is False
        assert is_eudr_required("0506.90.00") is False

    def test_hoof_not_eudr_required(self):
        """HS 0507 (hoof) does NOT require EUDR."""
        assert is_eudr_required("0507") is False
        assert is_eudr_required("0507.90") is False
        assert is_eudr_required("0507.10.00") is False

    def test_sweet_potato_not_eudr_required(self):
        """HS 0714.20 (sweet potato pellets) does NOT require EUDR."""
        assert is_eudr_required("0714") is False
        assert is_eudr_required("0714.20") is False

    def test_hibiscus_not_eudr_required(self):
        """HS 0902.10 (hibiscus flowers) does NOT require EUDR."""
        assert is_eudr_required("0902") is False
        assert is_eudr_required("0902.10") is False

    def test_ginger_not_eudr_required(self):
        """HS 0910.11 (dried ginger) does NOT require EUDR."""
        assert is_eudr_required("0910") is False
        assert is_eudr_required("0910.11") is False

    def test_cocoa_is_eudr_required(self):
        """HS 1801 (cocoa beans) IS covered by EUDR."""
        assert is_eudr_required("1801") is True
        assert is_eudr_required("1801.00") is True
        assert is_eudr_required("1801.00.00") is True

    def test_coffee_is_eudr_required(self):
        """HS 0901 (coffee) IS covered by EUDR."""
        assert is_eudr_required("0901") is True
        assert is_eudr_required("0901.11") is True

    def test_palm_oil_is_eudr_required(self):
        """HS 1511 (palm oil) IS covered by EUDR."""
        assert is_eudr_required("1511") is True
        assert is_eudr_required("1511.10") is True

    def test_rubber_is_eudr_required(self):
        """HS 4001 (rubber) IS covered by EUDR."""
        assert is_eudr_required("4001") is True
        assert is_eudr_required("4001.10") is True

    def test_soya_is_eudr_required(self):
        """HS 1201 (soya) IS covered by EUDR."""
        assert is_eudr_required("1201") is True
        assert is_eudr_required("1201.90") is True

    def test_unknown_hs_code_not_eudr_required(self):
        """Unknown HS codes default to NOT requiring EUDR."""
        assert is_eudr_required("9999") is False
        assert is_eudr_required("0000.00") is False

    def test_empty_hs_code_not_eudr_required(self):
        """Empty or invalid HS codes return False."""
        assert is_eudr_required("") is False
        assert is_eudr_required("   ") is False

    @pytest.mark.parametrize("hs_code,expected", [
        ("0506.10", False),  # Horn - NO EUDR
        ("0507.90", False),  # Hoof - NO EUDR
        ("0714.20", False),  # Sweet potato - NO EUDR
        ("0902.10", False),  # Hibiscus - NO EUDR
        ("0910.11", False),  # Ginger - NO EUDR
        ("1801.00", True),   # Cocoa - YES EUDR
        ("0901.00", True),   # Coffee - YES EUDR
        ("1511.00", True),   # Palm oil - YES EUDR
        ("4001.00", True),   # Rubber - YES EUDR
        ("1201.00", True),   # Soya - YES EUDR
    ])
    def test_eudr_by_hs_code_parametrized(self, hs_code, expected):
        """Parametrized test for EUDR requirement by HS code."""
        result = is_eudr_required(hs_code)
        assert result == expected, f"HS {hs_code}: expected {expected}, got {result}"


class TestGetRequiredDocumentsByHsCode:
    """Tests for the get_required_documents_by_hs_code() function.

    This function returns required document types based on HS code and destination.
    """

    def test_horn_requires_traces_and_vet_cert(self):
        """Horn (0506) requires EU TRACES and Veterinary Health Certificate."""
        docs = get_required_documents_by_hs_code("0506", "DE")
        assert DocumentType.EU_TRACES_CERTIFICATE in docs
        assert DocumentType.VETERINARY_HEALTH_CERTIFICATE in docs
        # Should NOT require EUDR docs
        assert DocumentType.EUDR_DUE_DILIGENCE not in docs

    def test_hoof_requires_traces_and_vet_cert(self):
        """Hoof (0507) requires EU TRACES and Veterinary Health Certificate."""
        docs = get_required_documents_by_hs_code("0507", "DE")
        assert DocumentType.EU_TRACES_CERTIFICATE in docs
        assert DocumentType.VETERINARY_HEALTH_CERTIFICATE in docs
        assert DocumentType.EUDR_DUE_DILIGENCE not in docs

    def test_sweet_potato_requires_phyto_and_quality(self):
        """Sweet potato (0714) requires Phyto and Quality certificates."""
        docs = get_required_documents_by_hs_code("0714", "DE")
        assert DocumentType.PHYTOSANITARY_CERTIFICATE in docs
        assert DocumentType.QUALITY_CERTIFICATE in docs
        assert DocumentType.CERTIFICATE_OF_ORIGIN in docs
        # Should NOT require EUDR or animal product docs
        assert DocumentType.EUDR_DUE_DILIGENCE not in docs
        assert DocumentType.EU_TRACES_CERTIFICATE not in docs
        assert DocumentType.VETERINARY_HEALTH_CERTIFICATE not in docs

    def test_hibiscus_requires_phyto(self):
        """Hibiscus (0902) requires Phytosanitary Certificate."""
        docs = get_required_documents_by_hs_code("0902", "DE")
        assert DocumentType.PHYTOSANITARY_CERTIFICATE in docs
        assert DocumentType.CERTIFICATE_OF_ORIGIN in docs
        assert DocumentType.EUDR_DUE_DILIGENCE not in docs

    def test_ginger_requires_phyto(self):
        """Ginger (0910) requires Phytosanitary Certificate."""
        docs = get_required_documents_by_hs_code("0910", "DE")
        assert DocumentType.PHYTOSANITARY_CERTIFICATE in docs
        assert DocumentType.CERTIFICATE_OF_ORIGIN in docs
        assert DocumentType.EUDR_DUE_DILIGENCE not in docs

    def test_cocoa_requires_eudr_docs(self):
        """Cocoa (1801) requires EUDR documentation."""
        docs = get_required_documents_by_hs_code("1801", "DE")
        assert DocumentType.EUDR_DUE_DILIGENCE in docs
        assert DocumentType.CERTIFICATE_OF_ORIGIN in docs

    def test_all_shipments_require_basic_docs(self):
        """All shipments require basic export documents."""
        basic_docs = [
            DocumentType.BILL_OF_LADING,
            DocumentType.COMMERCIAL_INVOICE,
            DocumentType.CERTIFICATE_OF_ORIGIN,
        ]

        for hs_code in ["0506", "0714", "0902", "0910", "1801"]:
            docs = get_required_documents_by_hs_code(hs_code, "DE")
            for basic_doc in basic_docs:
                assert basic_doc in docs, f"{basic_doc} should be required for {hs_code}"


class TestEUDRCompliance:
    """EUDR compliance rule tests.
    
    Critical: Horn and hoof products (HS 0506/0507) are NOT in EUDR Annex I.
    They should never require geolocation or deforestation statements.
    """

    def test_horn_hoof_not_eudr_required(self, sample_horn_hoof_shipment):
        """
        Given: Horn/hoof product (HS 0506)
        When: Checking EUDR requirement
        Then: Returns False - NOT covered by EUDR
        """
        assert sample_horn_hoof_shipment["eudr_required"] is False

    def test_horn_hoof_no_geolocation_required(self, sample_horn_hoof_shipment):
        """
        Given: Horn/hoof product
        When: Getting required documents
        Then: Does NOT include geolocation fields
        """
        required = sample_horn_hoof_shipment["required_docs"]
        assert "GEOLOCATION" not in required
        assert "GEOLOCATION_DATA" not in required
        assert "DEFORESTATION_STATEMENT" not in required
        assert "EUDR_STATEMENT" not in required

    def test_sweet_potato_not_eudr_required(self, sample_sweet_potato_shipment):
        """
        Given: Sweet potato pellets (HS 0714.20)
        When: Checking EUDR requirement
        Then: Returns False - NOT covered by EUDR
        """
        assert sample_sweet_potato_shipment["eudr_required"] is False

    def test_cocoa_is_eudr_required(self, sample_cocoa_shipment):
        """
        Given: Cocoa beans (HS 1801)
        When: Checking EUDR requirement
        Then: Returns True - IS covered by EUDR
        """
        assert sample_cocoa_shipment["eudr_required"] is True

    def test_cocoa_requires_geolocation(self, sample_cocoa_shipment):
        """
        Given: Cocoa product (EUDR-applicable)
        When: Getting required documents
        Then: DOES include EUDR documentation
        """
        required = sample_cocoa_shipment["required_docs"]
        assert "GEOLOCATION_DATA" in required
        assert "EUDR_STATEMENT" in required
        assert "RISK_ASSESSMENT" in required

    @pytest.mark.parametrize("hs_code,expected", [
        ("0506.10", False),  # Horn - NO EUDR
        ("0507.90", False),  # Hoof - NO EUDR
        ("0714.20", False),  # Sweet potato - NO EUDR
        ("0902.10", False),  # Hibiscus - NO EUDR
        ("0910.11", False),  # Ginger - NO EUDR
        ("1801.00", True),   # Cocoa - YES EUDR
        ("0901.00", True),   # Coffee - YES EUDR
        ("1511.00", True),   # Palm oil - YES EUDR
    ])
    def test_eudr_by_hs_code(self, hs_code, expected):
        """Test EUDR requirement by HS code using centralized function.

        This now uses the actual is_eudr_required function from compliance module.
        """
        result = is_eudr_required(hs_code)
        assert result == expected, f"HS {hs_code} EUDR check failed: expected {expected}, got {result}"


class TestDocumentRequirements:
    """Document requirement tests based on product type."""

    def test_horn_hoof_requires_traces(self, sample_horn_hoof_shipment, traces_number):
        """
        Given: Horn/hoof product
        When: Checking document requirements
        Then: EU TRACES number is required
        """
        assert "EU_TRACES" in sample_horn_hoof_shipment["required_docs"]
        assert sample_horn_hoof_shipment["traces_number"] == traces_number

    def test_horn_hoof_requires_vet_cert(self, sample_horn_hoof_shipment):
        """
        Given: Horn/hoof product (animal by-product)
        When: Checking document requirements
        Then: Veterinary Health Certificate is required
        """
        assert "VETERINARY_HEALTH_CERT" in sample_horn_hoof_shipment["required_docs"]

    def test_sweet_potato_requires_phyto(self, sample_sweet_potato_shipment):
        """
        Given: Sweet potato pellets (plant product)
        When: Checking document requirements
        Then: Phytosanitary Certificate is required
        """
        assert "PHYTOSANITARY_CERT" in sample_sweet_potato_shipment["required_docs"]

    def test_all_shipments_require_basic_docs(
        self, 
        sample_horn_hoof_shipment,
        sample_sweet_potato_shipment,
        sample_cocoa_shipment
    ):
        """
        Given: Any shipment type
        When: Checking document requirements
        Then: Basic export docs are always required
        """
        basic_docs = ["BILL_OF_LADING", "COMMERCIAL_INVOICE", "CERTIFICATE_OF_ORIGIN"]
        
        for shipment in [sample_horn_hoof_shipment, sample_sweet_potato_shipment, sample_cocoa_shipment]:
            for doc in basic_docs:
                assert doc in shipment["required_docs"], \
                    f"{doc} should be required for {shipment['product_type']}"


class TestComplianceMatrix:
    """Tests to verify compliance matrix is being followed."""

    def test_compliance_matrix_existence(self):
        """
        Given: TraceHub repository
        When: Checking for compliance documentation
        Then: COMPLIANCE_MATRIX.md exists and is accessible
        """
        import os
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        compliance_matrix = os.path.join(repo_root, "docs", "COMPLIANCE_MATRIX.md")
        
        assert os.path.exists(compliance_matrix), \
            "docs/COMPLIANCE_MATRIX.md must exist as single source of truth"

    def test_non_eudr_products_list(self, non_eudr_hs_codes):
        """
        Given: VIBOTAJ's current product portfolio
        When: Checking EUDR applicability
        Then: All current products are NOT EUDR-applicable
        """
        for hs_code in non_eudr_hs_codes.keys():
            assert is_eudr_required(hs_code) is False, \
                f"{non_eudr_hs_codes[hs_code]} (HS {hs_code}) should NOT be EUDR-applicable"


# Integration test examples (to be implemented with actual service)
class TestComplianceServiceIntegration:
    """Integration tests for compliance service (TODO: implement when service is ready)."""

    @pytest.mark.skip(reason="Requires actual compliance service implementation")
    def test_validate_shipment_compliance(self):
        """
        Given: A shipment with documents
        When: Running compliance validation
        Then: Returns validation status and missing documents
        """
        # TODO: Implement when compliance service is ready
        # from app.services.compliance import validate_shipment_compliance
        # result = validate_shipment_compliance(shipment_id="SHIP-001")
        # assert result["status"] in ["COMPLIANT", "MISSING_DOCS", "INVALID"]
        pass

    @pytest.mark.skip(reason="Requires actual compliance service implementation")
    def test_get_required_documents_by_hs_code(self):
        """
        Given: An HS code
        When: Getting required documents
        Then: Returns correct list based on COMPLIANCE_MATRIX.md
        """
        # TODO: Implement when compliance service is ready
        # from app.services.compliance import get_required_documents
        # docs = get_required_documents(hs_code="0506.10")
        # assert "EU_TRACES" in docs
        # assert "GEOLOCATION_DATA" not in docs
        pass
