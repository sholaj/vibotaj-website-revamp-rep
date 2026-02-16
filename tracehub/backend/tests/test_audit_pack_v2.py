"""Tests for audit pack v2 service (PRD-017).

Tests: Supabase Storage integration, signed URL generation,
compliance in metadata/PDF, caching, and status endpoints.
"""

import io
import json
import zipfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.models import DocumentStatus
from app.models.shipment import ShipmentStatus
from app.services.audit_pack import (
    generate_audit_pack,
    get_audit_pack_status,
    get_or_generate_audit_pack,
    _is_pack_outdated,
    _get_storage_key,
    _build_contents_list,
    AUDIT_PACK_BUCKET,
)
from app.schemas.audit_pack import AuditPackStatusResponse


# --- Helpers ---

def make_shipment(
    org_id=None,
    reference="VIBO-2026-001",
    audit_pack_generated_at=None,
    audit_pack_storage_path=None,
):
    """Create a mock shipment."""
    shipment = MagicMock()
    shipment.id = uuid4()
    shipment.organization_id = org_id or uuid4()
    shipment.reference = reference
    shipment.container_number = "MSCU1234567"
    shipment.bl_number = "BL123456"
    shipment.vessel_name = "RHINE MAERSK"
    shipment.voyage_number = "550N"
    shipment.etd = datetime(2026, 1, 1)
    shipment.eta = datetime(2026, 1, 15)
    shipment.pol_code = "NGAPP"
    shipment.pol_name = "Apapa, Lagos"
    shipment.pod_code = "DEHAM"
    shipment.pod_name = "Hamburg"
    shipment.incoterms = "FOB"
    shipment.status = ShipmentStatus.IN_TRANSIT
    shipment.importer_name = "HAGES GmbH"
    shipment.exporter_name = "VIBOTAJ Global Nigeria Ltd"
    shipment.buyer_organization_id = uuid4()
    shipment.validation_override_reason = None
    shipment.validation_override_by = None
    shipment.validation_override_at = None
    shipment.product_type = None
    shipment.audit_pack_generated_at = audit_pack_generated_at
    shipment.audit_pack_storage_path = audit_pack_storage_path
    return shipment


def make_doc(doc_type="bill_of_lading", file_path="docs/test.pdf", updated_at=None):
    """Create a mock document."""
    doc = MagicMock()
    doc.id = uuid4()
    doc.document_type = MagicMock()
    doc.document_type.value = doc_type
    doc.file_path = file_path
    doc.file_name = "test.pdf"
    doc.status = DocumentStatus.COMPLIANCE_OK
    doc.updated_at = updated_at or datetime(2026, 2, 15, 10, 0, 0)
    doc.issues = []
    return doc


def make_storage():
    """Create a mock StorageBackend."""
    storage = AsyncMock()
    storage.upload = AsyncMock(return_value="audit-packs/org/test.zip")
    storage.download_url = AsyncMock(return_value="https://supabase.co/storage/v1/object/sign/test")
    storage.exists = AsyncMock(return_value=False)
    storage.delete = AsyncMock(return_value=True)
    return storage


def make_db(documents=None, products=None, events=None):
    """Create a mock database session."""
    db = MagicMock()
    documents = documents or []
    products = products or []
    events = events or []

    def query_side_effect(model):
        mock_query = MagicMock()
        mock_filter = MagicMock()

        model_name = getattr(model, "__name__", str(model))
        if model_name == "Document":
            mock_filter.all.return_value = documents
        elif model_name == "Product":
            mock_filter.all.return_value = products
        elif model_name == "ContainerEvent":
            mock_filter.order_by.return_value.all.return_value = events
            mock_filter.all.return_value = events
        elif model_name == "ComplianceResult":
            mock_filter.all.return_value = []
        elif model_name == "DocumentIssue":
            mock_filter.all.return_value = []
        else:
            mock_filter.all.return_value = []

        mock_query.filter.return_value = mock_filter
        return mock_query

    db.query = MagicMock(side_effect=query_side_effect)
    db.commit = MagicMock()
    return db


# --- Tests ---


class TestStorageKey:
    """Tests for _get_storage_key."""

    def test_builds_correct_key(self):
        shipment = make_shipment()
        key = _get_storage_key(shipment)
        assert str(shipment.organization_id) in key
        assert shipment.reference in key
        assert key.endswith("-audit-pack.zip")


class TestIsPackOutdated:
    """Tests for _is_pack_outdated."""

    def test_outdated_when_no_generated_at(self):
        shipment = make_shipment()
        assert _is_pack_outdated(shipment, []) is True

    def test_not_outdated_when_docs_older_than_pack(self):
        gen_time = datetime(2026, 2, 16, 12, 0, 0)
        shipment = make_shipment(audit_pack_generated_at=gen_time)
        doc = make_doc(updated_at=datetime(2026, 2, 15, 10, 0, 0))
        assert _is_pack_outdated(shipment, [doc]) is False

    def test_outdated_when_doc_newer_than_pack(self):
        gen_time = datetime(2026, 2, 15, 10, 0, 0)
        shipment = make_shipment(audit_pack_generated_at=gen_time)
        doc = make_doc(updated_at=datetime(2026, 2, 16, 12, 0, 0))
        assert _is_pack_outdated(shipment, [doc]) is True

    def test_outdated_when_any_doc_newer(self):
        gen_time = datetime(2026, 2, 15, 12, 0, 0)
        shipment = make_shipment(audit_pack_generated_at=gen_time)
        old_doc = make_doc(updated_at=datetime(2026, 2, 14))
        new_doc = make_doc(updated_at=datetime(2026, 2, 16))
        assert _is_pack_outdated(shipment, [old_doc, new_doc]) is True


class TestBuildContentsList:
    """Tests for _build_contents_list."""

    def test_always_includes_index_and_metadata(self):
        contents = _build_contents_list([])
        names = [c.name for c in contents]
        assert "00-SHIPMENT-INDEX.pdf" in names
        assert "metadata.json" in names
        assert "container-tracking-log.json" in names

    def test_includes_documents_with_file_path(self):
        doc1 = make_doc(doc_type="bill_of_lading", file_path="docs/bol.pdf")
        doc2 = make_doc(doc_type="certificate_of_origin", file_path="docs/coo.pdf")
        contents = _build_contents_list([doc1, doc2])
        doc_contents = [c for c in contents if c.type == "document"]
        assert len(doc_contents) == 2
        assert doc_contents[0].document_type == "bill_of_lading"
        assert doc_contents[1].document_type == "certificate_of_origin"

    def test_skips_docs_without_file_path(self):
        doc = make_doc(file_path=None)
        contents = _build_contents_list([doc])
        doc_contents = [c for c in contents if c.type == "document"]
        assert len(doc_contents) == 0


class TestGetAuditPackStatus:
    """Tests for get_audit_pack_status."""

    def test_status_none_when_never_generated(self):
        shipment = make_shipment()
        db = make_db()
        status = get_audit_pack_status(shipment, [], db)
        assert status.status == "none"
        assert status.is_outdated is True

    def test_status_ready_when_pack_up_to_date(self):
        gen_time = datetime(2026, 2, 16, 12, 0, 0)
        shipment = make_shipment(audit_pack_generated_at=gen_time)
        doc = make_doc(updated_at=datetime(2026, 2, 15))
        db = make_db(documents=[doc])
        status = get_audit_pack_status(shipment, [doc], db)
        assert status.status == "ready"
        assert status.is_outdated is False

    def test_status_outdated_when_doc_changed(self):
        gen_time = datetime(2026, 2, 15, 10, 0, 0)
        shipment = make_shipment(audit_pack_generated_at=gen_time)
        doc = make_doc(updated_at=datetime(2026, 2, 16))
        db = make_db(documents=[doc])
        status = get_audit_pack_status(shipment, [doc], db)
        assert status.status == "outdated"
        assert status.is_outdated is True

    def test_includes_compliance_decision(self):
        shipment = make_shipment()
        db = make_db()
        status = get_audit_pack_status(shipment, [], db)
        assert status.compliance_decision in ("APPROVE", "HOLD", "REJECT")

    def test_includes_document_count(self):
        shipment = make_shipment()
        doc = make_doc()
        db = make_db(documents=[doc])
        status = get_audit_pack_status(shipment, [doc], db)
        assert status.document_count == 1


class TestGenerateAuditPack:
    """Tests for generate_audit_pack ZIP generation."""

    def test_generates_valid_zip(self):
        shipment = make_shipment()
        db = make_db()
        result = generate_audit_pack(shipment, db)
        assert isinstance(result, io.BytesIO)
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert "00-SHIPMENT-INDEX.pdf" in names
            assert "container-tracking-log.json" in names
            assert "metadata.json" in names

    def test_metadata_includes_compliance(self):
        shipment = make_shipment()
        db = make_db()
        result = generate_audit_pack(shipment, db)
        with zipfile.ZipFile(result) as zf:
            metadata_raw = zf.read("metadata.json")
            metadata = json.loads(metadata_raw)
            assert "compliance" in metadata
            assert metadata["compliance"]["decision"] in ("APPROVE", "HOLD", "REJECT")

    def test_metadata_includes_shipment_details(self):
        shipment = make_shipment()
        db = make_db()
        result = generate_audit_pack(shipment, db)
        with zipfile.ZipFile(result) as zf:
            metadata = json.loads(zf.read("metadata.json"))
            assert metadata["shipment"]["reference"] == "VIBO-2026-001"
            assert metadata["shipment"]["container_number"] == "MSCU1234567"
            assert metadata["buyer"]["name"] == "HAGES GmbH"

    def test_tracking_log_json_valid(self):
        shipment = make_shipment()
        db = make_db()
        result = generate_audit_pack(shipment, db)
        with zipfile.ZipFile(result) as zf:
            log_raw = zf.read("container-tracking-log.json")
            log = json.loads(log_raw)
            assert log["container_number"] == "MSCU1234567"
            assert "events" in log


@pytest.mark.asyncio
class TestGetOrGenerateAuditPack:
    """Tests for get_or_generate_audit_pack (async, Storage integration)."""

    async def test_generates_and_uploads_when_no_cache(self):
        shipment = make_shipment()
        db = make_db()
        storage = make_storage()

        result = await get_or_generate_audit_pack(shipment, db, storage)
        assert result.status == "ready"
        assert result.download_url is not None
        storage.upload.assert_called_once()
        assert storage.upload.call_args[0][0] == AUDIT_PACK_BUCKET

    async def test_returns_cached_when_not_outdated(self):
        gen_time = datetime(2026, 2, 16, 12, 0, 0)
        shipment = make_shipment(
            audit_pack_generated_at=gen_time,
            audit_pack_storage_path="audit-packs/org/test.zip",
        )
        db = make_db()
        storage = make_storage()
        storage.exists = AsyncMock(return_value=True)

        result = await get_or_generate_audit_pack(shipment, db, storage)
        assert result.status == "ready"
        storage.upload.assert_not_called()

    async def test_force_regenerates_even_when_cached(self):
        gen_time = datetime(2026, 2, 16, 12, 0, 0)
        shipment = make_shipment(
            audit_pack_generated_at=gen_time,
            audit_pack_storage_path="audit-packs/org/test.zip",
        )
        db = make_db()
        storage = make_storage()

        result = await get_or_generate_audit_pack(shipment, db, storage, force=True)
        assert result.status == "ready"
        storage.upload.assert_called_once()

    async def test_regenerates_when_outdated(self):
        gen_time = datetime(2026, 2, 14)
        shipment = make_shipment(
            audit_pack_generated_at=gen_time,
            audit_pack_storage_path="audit-packs/org/test.zip",
        )
        doc = make_doc(updated_at=datetime(2026, 2, 16))
        db = make_db(documents=[doc])
        storage = make_storage()

        result = await get_or_generate_audit_pack(shipment, db, storage)
        assert result.status == "ready"
        storage.upload.assert_called_once()

    async def test_updates_shipment_cache_fields(self):
        shipment = make_shipment()
        db = make_db()
        storage = make_storage()

        await get_or_generate_audit_pack(shipment, db, storage)
        assert shipment.audit_pack_generated_at is not None
        assert shipment.audit_pack_storage_path is not None
        db.commit.assert_called()

    async def test_includes_signed_url_and_expiry(self):
        shipment = make_shipment()
        db = make_db()
        storage = make_storage()

        result = await get_or_generate_audit_pack(shipment, db, storage)
        assert result.download_url is not None
        assert result.expires_at is not None


class TestComplianceInPdf:
    """Tests for compliance section in PDF summary."""

    def test_pdf_generated_without_error(self):
        """PDF generation should not crash with compliance section."""
        shipment = make_shipment()
        db = make_db()
        result = generate_audit_pack(shipment, db)
        assert result.getbuffer().nbytes > 0

    def test_pdf_includes_index_file(self):
        shipment = make_shipment()
        db = make_db()
        result = generate_audit_pack(shipment, db)
        with zipfile.ZipFile(result) as zf:
            pdf_data = zf.read("00-SHIPMENT-INDEX.pdf")
            assert pdf_data[:4] == b"%PDF"
