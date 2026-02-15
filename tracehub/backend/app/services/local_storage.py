"""Local filesystem storage backend for development.

Stores files on disk under a configurable base directory,
mirroring the bucket/org_id/doc_id/filename path convention
used by Supabase Storage.

PRD-005: Supabase Storage for Documents
"""

import logging
import os
from pathlib import Path
from urllib.parse import quote

logger = logging.getLogger(__name__)


class LocalStorageBackend:
    """Storage backend using the local filesystem.

    Intended for development and testing. Files are stored at:
    {base_path}/{bucket}/{org_id}/{document_id}/{filename}
    """

    def __init__(self, base_path: str = "./uploads") -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("LocalStorageBackend initialized (base=%s)", self.base_path)

    async def upload(
        self, bucket: str, path: str, file: bytes, content_type: str
    ) -> str:
        """Write file to local filesystem."""
        full_path = self.base_path / bucket / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file)
        logger.info("Saved %s/%s (%d bytes)", bucket, path, len(file))
        return f"{bucket}/{path}"

    async def download_url(
        self, bucket: str, path: str, expires_in: int = 3600
    ) -> str:
        """Return a file:// URL for local development.

        In dev mode the frontend can fetch from a local endpoint
        that serves files directly. The expires_in parameter is
        ignored for local storage.
        """
        full_path = self.base_path / bucket / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {bucket}/{path}")
        # Return a relative API path that the dev server can serve
        return f"/api/storage/{bucket}/{quote(path)}"

    async def delete(self, bucket: str, path: str) -> bool:
        """Delete a file from local filesystem."""
        full_path = self.base_path / bucket / path
        if full_path.exists():
            os.remove(full_path)
            logger.info("Deleted %s/%s", bucket, path)
            return True
        return False

    async def exists(self, bucket: str, path: str) -> bool:
        """Check if a file exists on the local filesystem."""
        return (self.base_path / bucket / path).exists()
