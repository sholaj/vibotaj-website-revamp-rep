"""Tests for customs backend protocol, mock implementation, and factory (PRD-021)."""

from app.services.customs import (
    ClearanceStatus,
    CustomsBackend,
    DeclarationResult,
    DeclarationStatus,
    DutyCalculation,
    PreClearanceResult,
)
from app.services.customs_mock import MockCustomsBackend
from app.services.customs_factory import get_customs_backend, reset_customs_backend


class TestPreClearanceResult:
    """Tests for PreClearanceResult dataclass."""

    def test_defaults(self):
        result = PreClearanceResult(
            hs_code="0506",
            origin_country="NG",
            status=ClearanceStatus.CLEARED,
        )
        assert result.hs_code == "0506"
        assert result.origin_country == "NG"
        assert result.status == ClearanceStatus.CLEARED
        assert result.required_documents == []
        assert result.restrictions == []
        assert result.notes == ""
        assert result.provider == ""

    def test_with_documents(self):
        result = PreClearanceResult(
            hs_code="0506",
            origin_country="NG",
            status=ClearanceStatus.CLEARED,
            required_documents=["Certificate of Origin", "Bill of Lading"],
        )
        assert len(result.required_documents) == 2


class TestDutyCalculation:
    """Tests for DutyCalculation dataclass."""

    def test_defaults(self):
        calc = DutyCalculation(
            hs_code="0506",
            cif_value=10000.0,
            currency="EUR",
            import_duty_rate=0.0,
            import_duty_amount=0.0,
            vat_rate=19.0,
            vat_amount=1900.0,
        )
        assert calc.total_duty == 0.0
        assert calc.surcharges == []

    def test_with_surcharges(self):
        calc = DutyCalculation(
            hs_code="0506",
            cif_value=10000.0,
            currency="EUR",
            import_duty_rate=0.0,
            import_duty_amount=0.0,
            vat_rate=19.0,
            vat_amount=1900.0,
            surcharges=[{"name": "Processing Fee", "amount": 50.0}],
            total_duty=1950.0,
        )
        assert len(calc.surcharges) == 1
        assert calc.total_duty == 1950.0


class TestDeclarationResult:
    """Tests for DeclarationResult dataclass."""

    def test_defaults(self):
        result = DeclarationResult(
            reference_number="NCS-ABC123",
            status=DeclarationStatus.SUBMITTED,
        )
        assert result.submitted_at is None
        assert result.error is None

    def test_declaration_statuses(self):
        for s in DeclarationStatus:
            result = DeclarationResult(reference_number="X", status=s)
            assert result.status == s


class TestClearanceStatus:
    """Tests for ClearanceStatus enum."""

    def test_all_statuses(self):
        assert ClearanceStatus.CLEARED == "cleared"
        assert ClearanceStatus.PENDING_DOCS == "pending_docs"
        assert ClearanceStatus.RESTRICTED == "restricted"
        assert ClearanceStatus.PROHIBITED == "prohibited"
        assert ClearanceStatus.UNKNOWN == "unknown"


class TestMockCustomsBackend:
    """Tests for MockCustomsBackend."""

    def setup_method(self):
        self.backend = MockCustomsBackend()

    def test_is_available_default_true(self):
        assert self.backend.is_available() is True

    def test_set_available(self):
        self.backend.set_available(False)
        assert self.backend.is_available() is False

    def test_provider_name(self):
        assert self.backend.get_provider_name() == "mock"

    def test_get_status(self):
        status = self.backend.get_status()
        assert status["provider"] == "mock"
        assert status["available"] is True

    def test_pre_clearance_horn_hoof(self):
        """Horn/hoof (0506) should be cleared with animal docs."""
        result = self.backend.check_pre_clearance("0506", "NG", "DE")
        assert result.status == ClearanceStatus.CLEARED
        assert "EU TRACES Certificate" in result.required_documents
        assert "Veterinary Health Certificate" in result.required_documents
        assert result.provider == "mock"

    def test_pre_clearance_cocoa(self):
        """Cocoa (1801) should be cleared with EUDR docs."""
        result = self.backend.check_pre_clearance("1801", "NG", "DE")
        assert result.status == ClearanceStatus.CLEARED
        assert "EUDR Due Diligence Statement" in result.required_documents

    def test_pre_clearance_restricted(self):
        """Petroleum products should be restricted."""
        result = self.backend.check_pre_clearance("2709", "NG", "DE")
        assert result.status == ClearanceStatus.RESTRICTED
        assert len(result.restrictions) > 0

    def test_duty_calc_zero_duty_horn_hoof(self):
        """Horn/hoof (05xx) has zero import duty."""
        result = self.backend.calculate_duty("0506", 10000.0)
        assert result.import_duty_rate == 0.0
        assert result.import_duty_amount == 0.0
        assert result.vat_rate == 19.0
        assert result.vat_amount > 0

    def test_duty_calc_with_surcharges(self):
        """Duty calc includes processing fee surcharge."""
        result = self.backend.calculate_duty("0506", 10000.0)
        assert len(result.surcharges) >= 1
        assert result.total_duty > 0

    def test_duty_calc_total_matches_components(self):
        """Total duty = import duty + VAT + surcharges."""
        result = self.backend.calculate_duty("1511", 50000.0)
        surcharge_total = sum(float(s.get("amount", 0)) for s in result.surcharges)
        expected = result.import_duty_amount + result.vat_amount + surcharge_total
        assert abs(result.total_duty - expected) < 0.01

    def test_submit_declaration(self):
        result = self.backend.submit_declaration(
            shipment_reference="SH-001",
            hs_code="0506",
            exporter_name="VIBOTAJ",
            consignee_name="HAGES",
            cif_value=25000.0,
        )
        assert result.status == DeclarationStatus.SUBMITTED
        assert result.reference_number.startswith("NCS-")
        assert result.submitted_at is not None

    def test_get_declaration_status_exists(self):
        """Should return the submitted declaration."""
        submitted = self.backend.submit_declaration(
            shipment_reference="SH-002",
            hs_code="0506",
            exporter_name="VIBOTAJ",
            consignee_name="HAGES",
            cif_value=10000.0,
        )
        result = self.backend.get_declaration_status(submitted.reference_number)
        assert result.reference_number == submitted.reference_number
        assert result.status == DeclarationStatus.SUBMITTED

    def test_get_declaration_status_not_found(self):
        result = self.backend.get_declaration_status("NONEXISTENT")
        assert result.error == "Declaration not found"

    def test_call_count_tracking(self):
        assert self.backend.call_count == 0
        self.backend.check_pre_clearance("0506", "NG")
        assert self.backend.call_count == 1
        self.backend.calculate_duty("0506", 1000.0)
        assert self.backend.call_count == 2

    def test_last_method_tracking(self):
        assert self.backend.last_method is None
        self.backend.check_pre_clearance("0506", "NG")
        assert self.backend.last_method == "check_pre_clearance"
        self.backend.calculate_duty("0506", 1000.0)
        assert self.backend.last_method == "calculate_duty"

    def test_reset(self):
        self.backend.check_pre_clearance("0506", "NG")
        self.backend.submit_declaration("SH", "0506", "A", "B", 100.0)
        self.backend.reset()
        assert self.backend.call_count == 0
        assert self.backend.last_method is None


class TestCustomsFactory:
    """Tests for customs factory."""

    def setup_method(self):
        reset_customs_backend()

    def teardown_method(self):
        reset_customs_backend()

    def test_default_returns_mock(self):
        backend = get_customs_backend()
        assert backend.get_provider_name() == "mock"
        assert backend.is_available() is True

    def test_singleton_returns_same_instance(self):
        b1 = get_customs_backend()
        b2 = get_customs_backend()
        assert b1 is b2

    def test_reset_creates_new_instance(self):
        b1 = get_customs_backend()
        reset_customs_backend()
        b2 = get_customs_backend()
        assert b1 is not b2


class TestCustomsBackendProtocol:
    """Test that MockCustomsBackend satisfies CustomsBackend Protocol."""

    def test_mock_has_all_protocol_methods(self):
        backend = MockCustomsBackend()
        assert hasattr(backend, "check_pre_clearance")
        assert hasattr(backend, "calculate_duty")
        assert hasattr(backend, "submit_declaration")
        assert hasattr(backend, "get_declaration_status")
        assert hasattr(backend, "is_available")
        assert hasattr(backend, "get_provider_name")
        assert hasattr(backend, "get_status")

    def test_mock_satisfies_protocol_typing(self):
        """Runtime check that mock can be used where Protocol is expected."""
        backend: CustomsBackend = MockCustomsBackend()
        assert backend.is_available() is True
