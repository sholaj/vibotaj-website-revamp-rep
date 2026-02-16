"""Banking backend protocol for trade finance operations (PRD-021).

Provider-agnostic interface for banking API interactions.
Same pattern as EmailBackend (PRD-020), LLMBackend (PRD-019), StorageBackend (PRD-005).

Implementations:
- MockBankingBackend: Dev/test (simulates bank responses)
- Future: GTBankBackend, UBABackend
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol
from enum import StrEnum


class LCStatus(StrEnum):
    """Letter of Credit status."""

    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    NOT_FOUND = "not_found"


class PaymentStatus(StrEnum):
    """Payment status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NOT_FOUND = "not_found"


@dataclass
class LCVerification:
    """Result of Letter of Credit verification."""

    lc_number: str
    status: LCStatus
    issuing_bank: str
    beneficiary: str = ""
    amount: float = 0.0
    currency: str = "EUR"
    expiry_date: Optional[str] = None
    terms: List[str] = field(default_factory=list)
    provider: str = ""
    error: Optional[str] = None


@dataclass
class PaymentInfo:
    """Payment status information."""

    reference: str
    status: PaymentStatus
    amount: float = 0.0
    currency: str = "EUR"
    payer: str = ""
    payee: str = ""
    initiated_at: Optional[str] = None
    completed_at: Optional[str] = None
    provider: str = ""
    error: Optional[str] = None


@dataclass
class ForexRate:
    """Foreign exchange rate information."""

    base_currency: str
    quote_currency: str
    buy_rate: float
    sell_rate: float
    mid_rate: float
    timestamp: str = ""
    provider: str = ""


class BankingBackend(Protocol):
    """Protocol for banking/trade finance operations.

    Implementations must provide LC verification,
    payment status tracking, and forex rate lookups.
    Provider-specific details (API key, etc.) are
    handled internally.
    """

    def verify_lc(self, lc_number: str, issuing_bank: str) -> LCVerification:
        """Verify a Letter of Credit.

        Args:
            lc_number: LC reference number.
            issuing_bank: Name or SWIFT code of the issuing bank.

        Returns:
            LCVerification with validity status and terms.
        """
        ...

    def get_payment_status(self, reference: str) -> PaymentInfo:
        """Get the status of a payment.

        Args:
            reference: Payment reference number.

        Returns:
            PaymentInfo with current status and details.
        """
        ...

    def get_forex_rate(self, base_currency: str, quote_currency: str) -> ForexRate:
        """Get the current foreign exchange rate.

        Args:
            base_currency: Base currency code (e.g., 'NGN').
            quote_currency: Quote currency code (e.g., 'EUR').

        Returns:
            ForexRate with buy/sell/mid rates.
        """
        ...

    def is_available(self) -> bool:
        """Check if the banking backend is operational."""
        ...

    def get_provider_name(self) -> str:
        """Return the provider identifier (e.g. 'gtbank', 'uba', 'mock')."""
        ...

    def get_status(self) -> Dict[str, object]:
        """Return detailed status information."""
        ...
