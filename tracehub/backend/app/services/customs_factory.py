"""Customs backend factory — returns the correct backend based on config.

Usage in FastAPI routes:
    from ..services.customs_factory import get_customs_backend
    customs: CustomsBackend = Depends(get_customs_backend)

PRD-021: Third-Party Integrations
"""

import logging

from ..config import get_settings
from .customs import CustomsBackend

logger = logging.getLogger(__name__)

# Module-level singleton (initialized lazily)
_backend: CustomsBackend | None = None


def _create_backend() -> CustomsBackend:
    """Create the appropriate customs backend based on config."""
    settings = get_settings()
    provider = settings.customs_provider

    if provider == "mock":
        from .customs_mock import MockCustomsBackend

        return MockCustomsBackend()

    # Future providers: "ncs", "son"
    # if provider == "ncs":
    #     from .customs_ncs import NCSCustomsBackend
    #     return NCSCustomsBackend()

    # Unknown provider — fall back to mock with warning
    logger.warning(
        "Unknown customs_provider=%s — falling back to mock backend", provider
    )
    from .customs_mock import MockCustomsBackend

    return MockCustomsBackend(available=False)


def get_customs_backend() -> CustomsBackend:
    """FastAPI dependency — returns the configured customs backend.

    The backend is created once and reused across requests.
    """
    global _backend
    if _backend is None:
        _backend = _create_backend()
    return _backend


def reset_customs_backend() -> None:
    """Reset the singleton (for testing)."""
    global _backend
    _backend = None
