"""Tests for banking backend protocol, mock implementation, and factory (PRD-021)."""

from app.services.banking import (
    BankingBackend,
    ForexRate,
    LCStatus,
    LCVerification,
    PaymentInfo,
    PaymentStatus,
)
from app.services.banking_mock import MockBankingBackend
from app.services.banking_factory import get_banking_backend, reset_banking_backend


class TestLCVerification:
    """Tests for LCVerification dataclass."""

    def test_defaults(self):
        lc = LCVerification(
            lc_number="LC-001",
            status=LCStatus.VALID,
            issuing_bank="GTBank",
        )
        assert lc.beneficiary == ""
        assert lc.amount == 0.0
        assert lc.currency == "EUR"
        assert lc.terms == []
        assert lc.error is None

    def test_with_terms(self):
        lc = LCVerification(
            lc_number="LC-001",
            status=LCStatus.VALID,
            issuing_bank="GTBank",
            terms=["Full B/L required", "CoO required"],
        )
        assert len(lc.terms) == 2


class TestPaymentInfo:
    """Tests for PaymentInfo dataclass."""

    def test_defaults(self):
        pi = PaymentInfo(
            reference="PAY-001",
            status=PaymentStatus.COMPLETED,
        )
        assert pi.amount == 0.0
        assert pi.payer == ""
        assert pi.initiated_at is None

    def test_all_statuses(self):
        for s in PaymentStatus:
            pi = PaymentInfo(reference="X", status=s)
            assert pi.status == s


class TestForexRate:
    """Tests for ForexRate dataclass."""

    def test_basic(self):
        rate = ForexRate(
            base_currency="NGN",
            quote_currency="EUR",
            buy_rate=1680.0,
            sell_rate=1720.0,
            mid_rate=1700.0,
        )
        assert rate.timestamp == ""
        assert rate.provider == ""

    def test_spread(self):
        rate = ForexRate(
            base_currency="NGN",
            quote_currency="EUR",
            buy_rate=1680.0,
            sell_rate=1720.0,
            mid_rate=1700.0,
        )
        assert rate.sell_rate > rate.buy_rate


class TestLCStatus:
    """Tests for LCStatus enum."""

    def test_all_statuses(self):
        assert LCStatus.VALID == "valid"
        assert LCStatus.EXPIRED == "expired"
        assert LCStatus.REVOKED == "revoked"
        assert LCStatus.PENDING == "pending"
        assert LCStatus.NOT_FOUND == "not_found"


class TestMockBankingBackend:
    """Tests for MockBankingBackend."""

    def setup_method(self):
        self.backend = MockBankingBackend()

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

    def test_verify_lc_default(self):
        """Default LC verification returns valid."""
        result = self.backend.verify_lc("LC-001", "GTBank")
        assert result.status == LCStatus.VALID
        assert result.lc_number == "LC-001"
        assert result.issuing_bank == "GTBank"
        assert result.beneficiary == "VIBOTAJ Global Nigeria Ltd"
        assert result.amount == 50000.0
        assert len(result.terms) > 0

    def test_verify_lc_override(self):
        """Test LC override for expired LC."""
        expired_lc = LCVerification(
            lc_number="LC-EXPIRED",
            status=LCStatus.EXPIRED,
            issuing_bank="GTBank",
        )
        self.backend.set_lc_response("LC-EXPIRED", expired_lc)
        result = self.backend.verify_lc("LC-EXPIRED", "GTBank")
        assert result.status == LCStatus.EXPIRED

    def test_get_payment_status_default(self):
        """Default payment status returns completed."""
        result = self.backend.get_payment_status("PAY-001")
        assert result.status == PaymentStatus.COMPLETED
        assert result.reference == "PAY-001"
        assert result.amount == 50000.0
        assert result.payer == "HAGES GmbH"

    def test_get_payment_status_override(self):
        """Test payment override for pending payment."""
        pending = PaymentInfo(
            reference="PAY-PENDING",
            status=PaymentStatus.PENDING,
            amount=25000.0,
        )
        self.backend.set_payment_response("PAY-PENDING", pending)
        result = self.backend.get_payment_status("PAY-PENDING")
        assert result.status == PaymentStatus.PENDING
        assert result.amount == 25000.0

    def test_get_forex_rate_ngn_eur(self):
        """Known currency pair returns realistic rates."""
        result = self.backend.get_forex_rate("NGN", "EUR")
        assert result.base_currency == "NGN"
        assert result.quote_currency == "EUR"
        assert result.buy_rate == 1680.0
        assert result.sell_rate == 1720.0
        assert result.mid_rate == 1700.0
        assert result.timestamp != ""

    def test_get_forex_rate_ngn_usd(self):
        result = self.backend.get_forex_rate("NGN", "USD")
        assert result.mid_rate == 1570.0

    def test_get_forex_rate_unknown_pair(self):
        """Unknown pair returns 1:1 rates."""
        result = self.backend.get_forex_rate("JPY", "CHF")
        assert result.buy_rate == 1.0
        assert result.sell_rate == 1.0
        assert result.mid_rate == 1.0

    def test_call_count_tracking(self):
        assert self.backend.call_count == 0
        self.backend.verify_lc("LC-001", "GTBank")
        assert self.backend.call_count == 1
        self.backend.get_forex_rate("NGN", "EUR")
        assert self.backend.call_count == 2

    def test_last_method_tracking(self):
        assert self.backend.last_method is None
        self.backend.verify_lc("LC-001", "GTBank")
        assert self.backend.last_method == "verify_lc"
        self.backend.get_payment_status("PAY-001")
        assert self.backend.last_method == "get_payment_status"

    def test_reset(self):
        self.backend.verify_lc("LC-001", "GTBank")
        self.backend.set_lc_response(
            "X", LCVerification(lc_number="X", status=LCStatus.VALID, issuing_bank="Y")
        )
        self.backend.reset()
        assert self.backend.call_count == 0
        assert self.backend.last_method is None


class TestBankingFactory:
    """Tests for banking factory."""

    def setup_method(self):
        reset_banking_backend()

    def teardown_method(self):
        reset_banking_backend()

    def test_default_returns_mock(self):
        backend = get_banking_backend()
        assert backend.get_provider_name() == "mock"
        assert backend.is_available() is True

    def test_singleton_returns_same_instance(self):
        b1 = get_banking_backend()
        b2 = get_banking_backend()
        assert b1 is b2

    def test_reset_creates_new_instance(self):
        b1 = get_banking_backend()
        reset_banking_backend()
        b2 = get_banking_backend()
        assert b1 is not b2


class TestBankingBackendProtocol:
    """Test that MockBankingBackend satisfies BankingBackend Protocol."""

    def test_mock_has_all_protocol_methods(self):
        backend = MockBankingBackend()
        assert hasattr(backend, "verify_lc")
        assert hasattr(backend, "get_payment_status")
        assert hasattr(backend, "get_forex_rate")
        assert hasattr(backend, "is_available")
        assert hasattr(backend, "get_provider_name")
        assert hasattr(backend, "get_status")

    def test_mock_satisfies_protocol_typing(self):
        backend: BankingBackend = MockBankingBackend()
        assert backend.is_available() is True
