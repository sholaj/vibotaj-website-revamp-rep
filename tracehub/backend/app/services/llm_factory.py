"""LLM backend factory — returns the correct backend based on config.

Usage in FastAPI routes:
    from ..services.llm_factory import get_llm
    llm: LLMBackend = Depends(get_llm)

PRD-019: AI Document Classification v2
"""

import logging

from ..config import get_settings
from .llm import LLMBackend

logger = logging.getLogger(__name__)

# Module-level singleton (initialized lazily)
_backend: LLMBackend | None = None


def _create_backend() -> LLMBackend:
    """Create the appropriate LLM backend based on config."""
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "anthropic":
        from .llm_anthropic import AnthropicBackend

        return AnthropicBackend()

    if provider == "mock":
        from .llm_mock import MockLLMBackend

        return MockLLMBackend()

    # Unknown provider — fall back to mock with warning
    logger.warning(
        "Unknown llm_provider=%s — falling back to mock backend", provider
    )
    from .llm_mock import MockLLMBackend

    return MockLLMBackend(available=False)


def get_llm() -> LLMBackend:
    """FastAPI dependency — returns the configured LLM backend.

    The backend is created once and reused across requests.
    """
    global _backend
    if _backend is None:
        _backend = _create_backend()
    return _backend


def reset_llm() -> None:
    """Reset the singleton (for testing)."""
    global _backend
    _backend = None
