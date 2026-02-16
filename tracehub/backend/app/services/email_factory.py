"""Email backend factory — returns the correct backend based on config.

Usage in FastAPI routes:
    from ..services.email_factory import get_email_backend
    email: EmailBackend = Depends(get_email_backend)

PRD-020: Email Notifications
"""

import logging

from ..config import get_settings
from .email import EmailBackend

logger = logging.getLogger(__name__)

# Module-level singleton (initialized lazily)
_backend: EmailBackend | None = None


def _create_backend() -> EmailBackend:
    """Create the appropriate email backend based on config."""
    settings = get_settings()
    provider = settings.email_provider

    if provider == "resend":
        from .email_resend import ResendBackend

        return ResendBackend()

    if provider == "console":
        from .email_console import ConsoleBackend

        return ConsoleBackend()

    # Unknown provider — fall back to console with warning
    logger.warning(
        "Unknown email_provider=%s — falling back to console backend", provider
    )
    from .email_console import ConsoleBackend

    return ConsoleBackend(available=False)


def get_email_backend() -> EmailBackend:
    """FastAPI dependency — returns the configured email backend.

    The backend is created once and reused across requests.
    """
    global _backend
    if _backend is None:
        _backend = _create_backend()
    return _backend


def reset_email_backend() -> None:
    """Reset the singleton (for testing)."""
    global _backend
    _backend = None
