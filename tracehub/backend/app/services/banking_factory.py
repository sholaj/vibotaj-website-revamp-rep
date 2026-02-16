"""Banking backend factory — returns the correct backend based on config.

Usage in FastAPI routes:
    from ..services.banking_factory import get_banking_backend
    banking: BankingBackend = Depends(get_banking_backend)

PRD-021: Third-Party Integrations
"""

import logging

from ..config import get_settings
from .banking import BankingBackend

logger = logging.getLogger(__name__)

# Module-level singleton (initialized lazily)
_backend: BankingBackend | None = None


def _create_backend() -> BankingBackend:
    """Create the appropriate banking backend based on config."""
    settings = get_settings()
    provider = settings.banking_provider

    if provider == "mock":
        from .banking_mock import MockBankingBackend

        return MockBankingBackend()

    # Future providers: "gtbank", "uba"
    # if provider == "gtbank":
    #     from .banking_gtbank import GTBankBackend
    #     return GTBankBackend()

    # Unknown provider — fall back to mock with warning
    logger.warning(
        "Unknown banking_provider=%s — falling back to mock backend", provider
    )
    from .banking_mock import MockBankingBackend

    return MockBankingBackend(available=False)


def get_banking_backend() -> BankingBackend:
    """FastAPI dependency — returns the configured banking backend.

    The backend is created once and reused across requests.
    """
    global _backend
    if _backend is None:
        _backend = _create_backend()
    return _backend


def reset_banking_backend() -> None:
    """Reset the singleton (for testing)."""
    global _backend
    _backend = None
