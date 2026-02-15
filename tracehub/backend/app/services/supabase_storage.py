"""Supabase Storage backend for production file storage.

Uses the Supabase Python client to manage files in private buckets.
Signed URLs provide time-limited access for downloads.

PRD-005: Supabase Storage for Documents
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SupabaseStorageBackend:
    """Storage backend using Supabase Storage (S3-compatible).

    Path convention: {org_id}/{document_id}/{filename}
    Full path in DB: {bucket}/{org_id}/{document_id}/{filename}
    """

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        try:
            from supabase import create_client
        except ImportError as e:
            raise ImportError(
                "supabase package required for SupabaseStorageBackend. "
                "Install with: pip install supabase"
            ) from e

        self._client: Any = create_client(supabase_url, supabase_key)
        logger.info("SupabaseStorageBackend initialized (url=%s)", supabase_url)

    async def upload(
        self, bucket: str, path: str, file: bytes, content_type: str
    ) -> str:
        """Upload file to Supabase Storage bucket."""
        self._client.storage.from_(bucket).upload(
            path,
            file,
            {"content-type": content_type, "upsert": "false"},
        )
        logger.info("Uploaded %s/%s (%d bytes)", bucket, path, len(file))
        return f"{bucket}/{path}"

    async def download_url(
        self, bucket: str, path: str, expires_in: int = 3600
    ) -> str:
        """Generate a signed download URL with time-limited access."""
        result = self._client.storage.from_(bucket).create_signed_url(
            path, expires_in
        )
        url: str = result.get("signedURL") or result.get("signedUrl", "")
        if not url:
            raise FileNotFoundError(
                f"Could not generate signed URL for {bucket}/{path}"
            )
        return url

    async def delete(self, bucket: str, path: str) -> bool:
        """Delete a file from Supabase Storage."""
        try:
            self._client.storage.from_(bucket).remove([path])
            logger.info("Deleted %s/%s", bucket, path)
            return True
        except Exception:
            logger.warning("File not found for deletion: %s/%s", bucket, path)
            return False

    async def exists(self, bucket: str, path: str) -> bool:
        """Check if a file exists by attempting to list it."""
        try:
            # List files in the parent directory and check for match
            parts = path.rsplit("/", 1)
            folder = parts[0] if len(parts) > 1 else ""
            filename = parts[-1]
            files = self._client.storage.from_(bucket).list(folder)
            return any(f.get("name") == filename for f in files)
        except Exception:
            return False
