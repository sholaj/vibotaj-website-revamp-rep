"""Storage backend factory — returns the correct backend based on config.

Usage in FastAPI routes:
    from ..services.storage_factory import get_storage
    storage: StorageBackend = Depends(get_storage)

PRD-005: Supabase Storage for Documents
"""

import logging
from functools import lru_cache

from ..config import get_settings
from .storage import StorageBackend
from .local_storage import LocalStorageBackend

logger = logging.getLogger(__name__)

# Module-level singleton (initialized lazily)
_backend: StorageBackend | None = None


def _create_backend() -> StorageBackend:
    """Create the appropriate storage backend based on config."""
    settings = get_settings()

    if settings.storage_backend == "supabase":
        if not settings.supabase_url or not settings.supabase_service_key:
            logger.warning(
                "storage_backend=supabase but SUPABASE_URL/SUPABASE_SERVICE_KEY "
                "not set — falling back to local storage"
            )
            return LocalStorageBackend(base_path=settings.upload_dir)

        from .supabase_storage import SupabaseStorageBackend

        return SupabaseStorageBackend(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )

    return LocalStorageBackend(base_path=settings.upload_dir)


def get_storage() -> StorageBackend:
    """FastAPI dependency — returns the configured storage backend.

    The backend is created once and reused across requests.
    """
    global _backend
    if _backend is None:
        _backend = _create_backend()
    return _backend
