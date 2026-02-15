# PRD-005: Supabase Storage for Documents

**Status:** Specified
**Complexity:** Low-Medium
**Target:** Week 3
**Dependencies:** PRD-002 (Supabase project), PRD-004 (FastAPI on Railway — ephemeral filesystem)
**Branch:** `feature/prd-005-supabase-storage`

---

## Problem

v1 stores uploaded files at `./uploads/{org_slug}/` on local disk (Hostinger VPS). This works on a persistent VPS but fails completely on Railway — containers are ephemeral, so uploaded files are lost on every redeploy. Document upload/download is a critical business function (compliance documents, BoLs, certificates). ~80 files currently stored on Hostinger need migration.

## Acceptance Criteria

1. 3 Supabase Storage buckets created:
   - `documents` — compliance documents, certificates, BoLs (primary)
   - `audit-packs` — generated audit pack ZIPs and PDFs
   - `exports` — CSV/Excel exports, generated reports
2. RLS on storage buckets: users access only files under their org's path prefix
3. Upload endpoint stores files in Supabase Storage instead of local disk
4. Download endpoint returns signed URLs (time-limited, 1 hour default)
5. `file_path` column in `documents` table stores Supabase storage paths (format: `{bucket}/{org_id}/{filename}`)
6. `StorageBackend` Protocol: local filesystem (dev) vs Supabase Storage (prod)
7. Migration script copies existing ~80 files from `tracehub/uploads/` to Supabase Storage
8. File size limit enforced: 50MB per upload (matches Supabase free tier)
9. v1 file storage on Hostinger is untouched

## Technical Approach

### 1. Bucket Creation

```sql
-- In Supabase dashboard or via migration
INSERT INTO storage.buckets (id, name, public) VALUES
  ('documents', 'documents', false),
  ('audit-packs', 'audit-packs', false),
  ('exports', 'exports', false);
```

All buckets are **private** — access only via signed URLs or authenticated API calls.

### 2. Storage RLS Policies

```sql
-- Upload: users can upload to their org's folder
CREATE POLICY "org_upload" ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id IN ('documents', 'audit-packs', 'exports')
    AND (storage.foldername(name))[1] = (current_setting('app.current_org_id'))::text
  );

-- Read: users can read their org's files
CREATE POLICY "org_read" ON storage.objects FOR SELECT
  USING (
    bucket_id IN ('documents', 'audit-packs', 'exports')
    AND (storage.foldername(name))[1] = (current_setting('app.current_org_id'))::text
  );

-- Delete: org admins can delete their org's files
CREATE POLICY "org_delete" ON storage.objects FOR DELETE
  USING (
    bucket_id IN ('documents', 'audit-packs', 'exports')
    AND (storage.foldername(name))[1] = (current_setting('app.current_org_id'))::text
    AND (current_setting('app.is_system_admin', true))::boolean = true
  );
```

Path structure: `{bucket}/{org_id}/{document_id}/{filename}`

### 3. StorageBackend Protocol

```python
# tracehub/backend/app/services/storage.py
from typing import Protocol

class StorageBackend(Protocol):
    async def upload(self, bucket: str, path: str, file: bytes, content_type: str) -> str:
        """Upload file, return storage path."""
        ...

    async def download_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Generate signed download URL."""
        ...

    async def delete(self, bucket: str, path: str) -> bool:
        """Delete file from storage."""
        ...

    async def exists(self, bucket: str, path: str) -> bool:
        """Check if file exists."""
        ...
```

### 4. Supabase Storage Implementation

```python
# tracehub/backend/app/services/supabase_storage.py
from supabase import create_client

class SupabaseStorageBackend:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client = create_client(supabase_url, supabase_key)

    async def upload(self, bucket: str, path: str, file: bytes, content_type: str) -> str:
        result = self.client.storage.from_(bucket).upload(path, file, {
            "content-type": content_type,
            "upsert": "false",
        })
        return f"{bucket}/{path}"

    async def download_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        result = self.client.storage.from_(bucket).create_signed_url(path, expires_in)
        return result["signedURL"]
```

### 5. Local Storage Implementation (Dev)

```python
# tracehub/backend/app/services/local_storage.py
class LocalStorageBackend:
    def __init__(self, base_path: str = "./uploads"):
        self.base_path = Path(base_path)

    async def upload(self, bucket: str, path: str, file: bytes, content_type: str) -> str:
        full_path = self.base_path / bucket / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file)
        return f"{bucket}/{path}"
```

### 6. Document Router Updates

Modify upload/download endpoints in `tracehub/backend/app/routers/documents.py`:

```python
# Upload: store in Supabase instead of local disk
storage_path = f"{org_id}/{document.id}/{file.filename}"
await storage.upload("documents", storage_path, file_content, file.content_type)
document.file_path = f"documents/{storage_path}"

# Download: return signed URL instead of FileResponse
signed_url = await storage.download_url("documents", storage_path)
return RedirectResponse(signed_url)
```

### 7. File Migration Script

```python
# scripts/migrate_files_to_supabase.py
# 1. Scan tracehub/uploads/ for all files
# 2. Map org_slug → org_id using database
# 3. Upload each file to Supabase Storage: documents/{org_id}/{filename}
# 4. Update documents.file_path in database
# 5. Verify all files accessible via signed URL
# 6. Report: files migrated, files failed, total size
```

## Files to Create/Modify

```
tracehub/backend/app/services/
  storage.py                  # NEW: StorageBackend Protocol
  supabase_storage.py         # NEW: Supabase Storage implementation
  local_storage.py            # NEW: Local filesystem implementation (dev)
tracehub/backend/app/routers/
  documents.py                # MODIFY: use StorageBackend for upload/download
tracehub/backend/app/
  config.py                   # MODIFY: add SUPABASE_URL, SUPABASE_KEY, STORAGE_BACKEND
  dependencies.py             # MODIFY: add get_storage() dependency
v2/supabase/migrations/
  013_create_storage_buckets.sql   # NEW: bucket creation + RLS
scripts/
  migrate_files_to_supabase.py     # NEW: file migration script
```

## v1 Source of Truth

| v1 File | What to Reference |
|---------|------------------|
| `tracehub/backend/app/services/file_utils.py` (93 lines) | `get_full_path()`, `file_exists()`, `delete_file()` — replace with StorageBackend |
| `tracehub/backend/app/routers/documents.py` | Upload/download endpoints — modify to use StorageBackend |
| `tracehub/uploads/` | Existing files to migrate (~80 files) |

## Testing Strategy

- Unit test: `SupabaseStorageBackend.upload()` stores file and returns correct path
- Unit test: `SupabaseStorageBackend.download_url()` returns valid signed URL
- Unit test: `LocalStorageBackend` reads/writes to local filesystem
- Unit test: `StorageBackend` Protocol compliance for both implementations
- Integration test: upload file via API → download via signed URL → content matches
- Integration test: RLS prevents cross-org file access
- Migration script dry-run: all files in `uploads/` mapped to correct Supabase paths

## Migration Notes

- v1 file storage on Hostinger is untouched — files are copied, not moved
- Existing `file_path` values in database change format: `./uploads/vibotaj/doc.pdf` → `documents/{org_id}/{doc_id}/doc.pdf`
- Signed URLs expire after 1 hour — frontend must handle expiry gracefully (re-fetch URL)
- Supabase free tier: 1GB storage, 2GB bandwidth/month — monitor usage
- `file_utils.py` functions (`get_full_path`, `file_exists`, `delete_file`) are replaced by `StorageBackend` — deprecate but don't delete (v1 still uses them)
