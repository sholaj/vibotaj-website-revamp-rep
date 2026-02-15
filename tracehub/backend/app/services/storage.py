"""Storage backend protocol for document file storage.

Defines the interface that both local filesystem (dev) and
Supabase Storage (prod/staging) implementations must satisfy.

PRD-005: Supabase Storage for Documents
"""

from typing import Protocol


class StorageBackend(Protocol):
    """Protocol for file storage operations.

    Implementations:
    - LocalStorageBackend: filesystem storage for development
    - SupabaseStorageBackend: Supabase Storage for production
    """

    async def upload(
        self, bucket: str, path: str, file: bytes, content_type: str
    ) -> str:
        """Upload file to storage.

        Args:
            bucket: Storage bucket name (documents, audit-packs, exports).
            path: Path within bucket ({org_id}/{document_id}/{filename}).
            file: Raw file bytes.
            content_type: MIME type (e.g. application/pdf).

        Returns:
            Full storage path: {bucket}/{path}
        """
        ...

    async def download_url(
        self, bucket: str, path: str, expires_in: int = 3600
    ) -> str:
        """Generate a signed download URL.

        Args:
            bucket: Storage bucket name.
            path: Path within bucket.
            expires_in: URL expiry in seconds (default 1 hour).

        Returns:
            Signed URL for file download.
        """
        ...

    async def delete(self, bucket: str, path: str) -> bool:
        """Delete a file from storage.

        Args:
            bucket: Storage bucket name.
            path: Path within bucket.

        Returns:
            True if deleted, False if not found.
        """
        ...

    async def exists(self, bucket: str, path: str) -> bool:
        """Check if a file exists in storage.

        Args:
            bucket: Storage bucket name.
            path: Path within bucket.

        Returns:
            True if file exists.
        """
        ...
