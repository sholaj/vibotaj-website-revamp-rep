#!/usr/bin/env python3
"""Migrate v1 local files to Supabase Storage.

Copies files from tracehub/uploads/ to Supabase Storage buckets,
updates file_path in the documents table, and verifies via signed URLs.

Usage:
    # Dry run (default) — shows what would happen
    python scripts/migrate_files_to_supabase.py

    # Execute migration
    python scripts/migrate_files_to_supabase.py --execute

    # Verify previously migrated files
    python scripts/migrate_files_to_supabase.py --verify

PRD-005: Supabase Storage for Documents
"""

import argparse
import logging
import mimetypes
import os
import sys
from pathlib import Path
from uuid import UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tracehub" / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_supabase_client():
    """Create Supabase client from environment."""
    try:
        from supabase import create_client
    except ImportError:
        logger.error("supabase package not installed: pip install supabase")
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        logger.error("Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
        sys.exit(1)

    return create_client(url, key)


def get_db_session():
    """Create a database session for reading document records."""
    from app.database import SessionLocal
    return SessionLocal()


def scan_uploads(uploads_dir: Path) -> list[dict]:
    """Scan the uploads directory for files to migrate."""
    files = []
    if not uploads_dir.exists():
        logger.warning("Uploads directory not found: %s", uploads_dir)
        return files

    for file_path in uploads_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(uploads_dir)
            content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            files.append({
                "local_path": file_path,
                "relative_path": str(rel_path),
                "size_bytes": file_path.stat().st_size,
                "content_type": content_type,
            })

    return files


def map_file_to_storage_path(relative_path: str, db) -> dict | None:
    """Map a local file path to a Supabase storage path using the DB.

    Returns dict with bucket, storage_path, document_id, org_id.
    """
    from app.models import Document

    # v1 stores paths like: ./uploads/{shipment_id}/{filename}
    # or ./uploads/{org_slug}/{filename}
    parts = Path(relative_path).parts

    # Try to find the document by matching the file path pattern
    search_pattern = f"%{relative_path}%"
    doc = db.query(Document).filter(
        Document.file_path.like(search_pattern)
    ).first()

    if doc:
        org_id = str(doc.organization_id) if doc.organization_id else "unknown"
        doc_id = str(doc.id)
        filename = Path(relative_path).name
        return {
            "bucket": "documents",
            "storage_path": f"{org_id}/{doc_id}/{filename}",
            "document_id": doc_id,
            "org_id": org_id,
        }

    # Fallback: use directory structure as-is
    filename = Path(relative_path).name
    parent = parts[0] if len(parts) > 1 else "unmapped"
    return {
        "bucket": "documents",
        "storage_path": f"{parent}/{filename}",
        "document_id": None,
        "org_id": parent,
    }


def migrate(execute: bool = False, verify: bool = False) -> None:
    """Run the migration."""
    uploads_dir = Path(__file__).resolve().parent.parent / "tracehub" / "uploads"
    files = scan_uploads(uploads_dir)

    if not files:
        logger.info("No files found in %s", uploads_dir)
        return

    logger.info("Found %d files to migrate (total %.1f MB)",
                len(files),
                sum(f["size_bytes"] for f in files) / 1024 / 1024)

    db = get_db_session()
    supabase = get_supabase_client() if (execute or verify) else None

    migrated = 0
    failed = 0
    skipped = 0

    for f in files:
        mapping = map_file_to_storage_path(f["relative_path"], db)
        if not mapping:
            logger.warning("SKIP: could not map %s", f["relative_path"])
            skipped += 1
            continue

        bucket = mapping["bucket"]
        storage_path = mapping["storage_path"]
        new_file_path = f"{bucket}/{storage_path}"

        if verify:
            # Verify file exists in Supabase
            try:
                result = supabase.storage.from_(bucket).create_signed_url(
                    storage_path, 60
                )
                url = result.get("signedURL") or result.get("signedUrl")
                status = "OK" if url else "MISSING"
            except Exception as e:
                status = f"ERROR: {e}"
            logger.info("VERIFY %s → %s: %s", f["relative_path"], new_file_path, status)
            continue

        if not execute:
            logger.info(
                "DRY RUN: %s → %s (%s, %.1f KB)",
                f["relative_path"],
                new_file_path,
                f["content_type"],
                f["size_bytes"] / 1024,
            )
            continue

        # Execute: upload to Supabase
        try:
            file_bytes = f["local_path"].read_bytes()
            supabase.storage.from_(bucket).upload(
                storage_path,
                file_bytes,
                {"content-type": f["content_type"], "upsert": "false"},
            )

            # Update document record if we have a document_id
            if mapping["document_id"]:
                from app.models import Document
                doc = db.query(Document).filter(
                    Document.id == mapping["document_id"]
                ).first()
                if doc:
                    doc.file_path = new_file_path
                    db.commit()

            logger.info("MIGRATED: %s → %s", f["relative_path"], new_file_path)
            migrated += 1
        except Exception as e:
            logger.error("FAILED: %s → %s: %s", f["relative_path"], new_file_path, e)
            failed += 1

    db.close()

    logger.info("--- Migration Summary ---")
    logger.info("Total files: %d", len(files))
    if execute:
        logger.info("Migrated: %d", migrated)
        logger.info("Failed: %d", failed)
        logger.info("Skipped: %d", skipped)
    elif not verify:
        logger.info("Mode: DRY RUN (use --execute to migrate)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate files to Supabase Storage")
    parser.add_argument("--execute", action="store_true", help="Actually perform the migration")
    parser.add_argument("--verify", action="store_true", help="Verify previously migrated files")
    args = parser.parse_args()

    if args.execute:
        logger.warning("=== EXECUTING MIGRATION (files will be uploaded to Supabase) ===")
    elif args.verify:
        logger.info("=== VERIFYING MIGRATION ===")
    else:
        logger.info("=== DRY RUN MODE (no changes will be made) ===")

    migrate(execute=args.execute, verify=args.verify)


if __name__ == "__main__":
    main()
