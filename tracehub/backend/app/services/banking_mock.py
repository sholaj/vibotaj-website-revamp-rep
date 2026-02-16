"""Mock banking backend for development and testing (PRD-021).

Simulates bank API responses with configurable behavior.
Same pattern as ConsoleBackend (email), MockLLMBackend (LLM).
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from .banking import (
    ForexRate,
    LCStatus,
    LCVerification,
    PaymentInfo,
    PaymentStatus,
)

logger = logging.getLogger(__name__)

# Mock forex rates (NGN-based)
MOCK_FOREX_RATES: Dict[str, Dict[str, float]] = {
    "NGN-EUR": {"buy": 1680.0, "sell": 1720.0, "mid": 1700.0},
    "NGN-USD": {"buy": 1550.0, "sell": 1590.0, "mid": 1570.0},
    "NGN-GBP": {"buy": 1950.0, "sell": 2000.0, "mid": 1975.0},
    "EUR-NGN": {"buy": 0.000580, "sell": 0.000600, "mid": 0.000590},
    "USD-NGN": {"buy": 0.000630, "sell": 0.000650, "mid": 0.000640},
}


class MockBankingBackend:
    """Mock banking backend for dev/test.

    Simulates bank responses with realistic data.
    Tracks calls for test assertions.
    """

    def __init__(self, available: bool = True) -> None:
        self._available = available
        self._call_count = 0
        self._last_method: Optional[str] = None
        self._lc_overrides: Dict[str, LCVerification] = {}
        self._payment_overrides: Dict[str, PaymentInfo] = {}

    def verify_lc(self, lc_number: str, issuing_bank: str) -> LCVerification:
        """Simulate LC verification."""
        self._call_count += 1
        self._last_method = "verify_lc"

        # Check for test overrides
        if lc_number in self._lc_overrides:
            return self._lc_overrides[lc_number]

        # Default: return a valid LC
        logger.info(
            "[MockBanking] LC verification: lc=%s bank=%s → VALID",
            lc_number,
            issuing_bank,
        )

        return LCVerification(
            lc_number=lc_number,
            status=LCStatus.VALID,
            issuing_bank=issuing_bank,
            beneficiary="VIBOTAJ Global Nigeria Ltd",
            amount=50000.0,
            currency="EUR",
            expiry_date="2026-06-30",
            terms=[
                "Shipment within 30 days of LC issuance",
                "Full set of clean on-board B/L required",
                "Certificate of Origin required",
            ],
            provider=self.get_provider_name(),
        )

    def get_payment_status(self, reference: str) -> PaymentInfo:
        """Simulate payment status lookup."""
        self._call_count += 1
        self._last_method = "get_payment_status"

        # Check for test overrides
        if reference in self._payment_overrides:
            return self._payment_overrides[reference]

        # Default: return a completed payment
        logger.info("[MockBanking] Payment status: ref=%s → COMPLETED", reference)

        return PaymentInfo(
            reference=reference,
            status=PaymentStatus.COMPLETED,
            amount=50000.0,
            currency="EUR",
            payer="HAGES GmbH",
            payee="VIBOTAJ Global Nigeria Ltd",
            initiated_at="2026-02-01T10:00:00Z",
            completed_at="2026-02-03T14:30:00Z",
            provider=self.get_provider_name(),
        )

    def get_forex_rate(self, base_currency: str, quote_currency: str) -> ForexRate:
        """Simulate forex rate lookup."""
        self._call_count += 1
        self._last_method = "get_forex_rate"

        pair = f"{base_currency}-{quote_currency}"
        rates = MOCK_FOREX_RATES.get(pair)

        if rates:
            logger.info(
                "[MockBanking] Forex rate: %s → mid=%.4f",
                pair,
                rates["mid"],
            )
            return ForexRate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                buy_rate=rates["buy"],
                sell_rate=rates["sell"],
                mid_rate=rates["mid"],
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider=self.get_provider_name(),
            )

        # Unknown pair — return 1:1 with warning
        logger.warning("[MockBanking] Unknown forex pair: %s — returning 1:1", pair)
        return ForexRate(
            base_currency=base_currency,
            quote_currency=quote_currency,
            buy_rate=1.0,
            sell_rate=1.0,
            mid_rate=1.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider=self.get_provider_name(),
        )

    def is_available(self) -> bool:
        """Check availability."""
        return self._available

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "mock"

    def get_status(self) -> Dict[str, object]:
        """Return status info."""
        return {
            "provider": "mock",
            "available": self._available,
            "call_count": self._call_count,
        }

    # --- Test helpers ---

    def set_available(self, available: bool) -> None:
        """Set availability for testing."""
        self._available = available

    def set_lc_response(self, lc_number: str, response: LCVerification) -> None:
        """Override LC response for testing."""
        self._lc_overrides[lc_number] = response

    def set_payment_response(self, reference: str, response: PaymentInfo) -> None:
        """Override payment response for testing."""
        self._payment_overrides[reference] = response

    def reset(self) -> None:
        """Reset state for testing."""
        self._call_count = 0
        self._last_method = None
        self._lc_overrides.clear()
        self._payment_overrides.clear()

    @property
    def call_count(self) -> int:
        """Number of API calls made."""
        return self._call_count

    @property
    def last_method(self) -> Optional[str]:
        """Last method called."""
        return self._last_method
