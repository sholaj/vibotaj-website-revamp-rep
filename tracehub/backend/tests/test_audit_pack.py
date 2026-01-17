"""Tests for audit pack generation.

Tests the audit pack ZIP generation including:
- Document file inclusion (Phase 0 bug fix)
- Summary PDF generation
- Metadata JSON generation
- Tracking log JSON generation

Run with: pytest tests/test_audit_pack.py -v
"""

import io
import os
import zipfile
import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.audit_pack import generate_audit_pack
from app.services.file_utils import get_full_path, BACKEND_DIR
from app.models.document import DocumentType, DocumentStatus
from app.models.shipment import ShipmentStatus, ProductType


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_shipment():
    """Create a mock shipment."""
    shipment = Mock()
    shipment.id = uuid4()
    shipment.reference = "VIBO-2026-TEST"
    shipment.container_number = "MSCU1234567"
    shipment.bl_number = "MAEU123456789"
    shipment.vessel_name = "MAERSK SEALAND"
    shipment.voyage_number = "001W"
    shipment.etd = datetime(2026, 2, 15)
    shipment.eta = datetime(2026, 3, 1)
    shipment.pol_code = "NGAPP"
    shipment.pol_name = "Apapa"
    shipment.pod_code = "DEHAM"
    shipment.pod_name = "Hamburg"
    shipment.incoterms = "FOB"
    shipment.status = ShipmentStatus.DOCS_PENDING
    shipment.product_type = ProductType.HORN_HOOF
    shipment.importer_name = "HAGES GmbH"
    shipment.exporter_name = "VIBOTAJ Global"
    shipment.organization_id = uuid4()
    shipment.buyer_organization_id = uuid4()
    return shipment


@pytest.fixture
def mock_document():
    """Factory for mock documents."""
    def _create(doc_type=DocumentType.BILL_OF_LADING, file_path=None, file_name=None):
        doc = Mock()
        doc.id = uuid4()
        doc.document_type = doc_type
        doc.name = file_name or f"test_{doc_type.value}.pdf"
        doc.file_name = file_name or f"test_{doc_type.value}.pdf"
        doc.file_path = file_path
        doc.status = DocumentStatus.UPLOADED
        return doc
    return _create


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    return session


# =============================================================================
# Test: File Utils Path Resolution
# =============================================================================

class TestFileUtilsPathResolution:
    """Test the file_utils path resolution functions."""

    def test_get_full_path_returns_none_for_none_input(self):
        """GIVEN None file_path
        WHEN get_full_path is called
        THEN returns None."""
        assert get_full_path(None) is None

    def test_get_full_path_returns_none_for_empty_string(self):
        """GIVEN empty string file_path
        WHEN get_full_path is called
        THEN returns None."""
        assert get_full_path("") is None

    def test_get_full_path_returns_absolute_path_as_is(self):
        """GIVEN absolute file_path
        WHEN get_full_path is called
        THEN returns same path."""
        abs_path = "/absolute/path/to/file.pdf"
        assert get_full_path(abs_path) == abs_path

    def test_get_full_path_resolves_relative_path(self):
        """GIVEN relative file_path starting with ./
        WHEN get_full_path is called
        THEN returns path relative to backend dir."""
        rel_path = "./uploads/abc-123/doc.pdf"
        result = get_full_path(rel_path)
        expected = os.path.join(BACKEND_DIR, rel_path)
        assert result == expected

    def test_get_full_path_resolves_simple_relative_path(self):
        """GIVEN relative file_path without ./
        WHEN get_full_path is called
        THEN returns path relative to backend dir."""
        rel_path = "uploads/abc-123/doc.pdf"
        result = get_full_path(rel_path)
        expected = os.path.join(BACKEND_DIR, rel_path)
        assert result == expected

    def test_backend_dir_points_to_correct_location(self):
        """GIVEN BACKEND_DIR constant
        THEN it should point to tracehub/backend/."""
        assert BACKEND_DIR.endswith("backend") or "backend" in BACKEND_DIR
        assert os.path.isdir(BACKEND_DIR)


# =============================================================================
# Test: Audit Pack Document Inclusion (Phase 0 Bug Fix)
# =============================================================================

class TestAuditPackDocumentInclusion:
    """Test that documents are included in the audit pack ZIP.

    This tests the Phase 0 bug fix where documents were not being
    included due to incorrect path resolution.
    """

    def test_audit_pack_includes_documents_with_existing_files(
        self, mock_shipment, mock_document, mock_db_session
    ):
        """GIVEN a shipment with documents that have files on disk
        WHEN audit pack is generated
        THEN documents are included in the ZIP file."""
        # Create a real temp file to test with
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 Test PDF content")
            temp_file_path = f.name

        try:
            # Create document with absolute path (simulating stored path)
            doc = mock_document(DocumentType.BILL_OF_LADING, file_path=temp_file_path)

            # Setup mock DB queries - documents, products, events (all return lists)
            # Configure specific return values for different model queries
            def query_side_effect(model):
                mock_query = MagicMock()
                mock_filter = MagicMock()
                mock_query.filter.return_value = mock_filter

                if model.__name__ == 'Document':
                    mock_filter.all.return_value = [doc]
                elif model.__name__ == 'ContainerEvent':
                    mock_filter.order_by.return_value.all.return_value = []
                elif model.__name__ == 'Product':
                    mock_filter.all.return_value = []
                else:
                    mock_filter.all.return_value = []
                    mock_filter.order_by.return_value.all.return_value = []

                return mock_query

            mock_db_session.query.side_effect = query_side_effect

            # Generate audit pack
            with patch('app.services.audit_pack.generate_summary_pdf') as mock_pdf:
                mock_pdf.return_value = io.BytesIO(b"%PDF-1.4 Summary")
                zip_buffer = generate_audit_pack(mock_shipment, mock_db_session)

            # Verify ZIP contains the document
            zip_buffer.seek(0)
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                names = zf.namelist()
                # Should have: 00-SHIPMENT-INDEX.pdf, 01-bill_of_lading.pdf,
                # container-tracking-log.json, metadata.json
                assert any("bill_of_lading" in name for name in names), \
                    f"Bill of Lading not found in ZIP. Contents: {names}"
        finally:
            # Cleanup
            os.unlink(temp_file_path)

    def test_audit_pack_skips_documents_without_files(
        self, mock_shipment, mock_document, mock_db_session
    ):
        """GIVEN a shipment with document that has no file on disk
        WHEN audit pack is generated
        THEN document is NOT included in ZIP (no error)."""
        # Document with non-existent file path
        doc = mock_document(
            DocumentType.COMMERCIAL_INVOICE,
            file_path="./uploads/nonexistent/file.pdf"
        )

        # Setup mock DB queries with proper model-specific returns
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model.__name__ == 'Document':
                mock_filter.all.return_value = [doc]
            elif model.__name__ == 'ContainerEvent':
                mock_filter.order_by.return_value.all.return_value = []
            elif model.__name__ == 'Product':
                mock_filter.all.return_value = []
            else:
                mock_filter.all.return_value = []
                mock_filter.order_by.return_value.all.return_value = []

            return mock_query

        mock_db_session.query.side_effect = query_side_effect

        # Generate audit pack - should not raise error
        with patch('app.services.audit_pack.generate_summary_pdf') as mock_pdf:
            mock_pdf.return_value = io.BytesIO(b"%PDF-1.4 Summary")
            zip_buffer = generate_audit_pack(mock_shipment, mock_db_session)

        # Verify ZIP was created (even without document)
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            names = zf.namelist()
            assert "00-SHIPMENT-INDEX.pdf" in names
            assert "metadata.json" in names
            # Commercial invoice should NOT be present (file doesn't exist)
            assert not any("commercial_invoice" in name for name in names)

    def test_audit_pack_includes_metadata_json(
        self, mock_shipment, mock_db_session
    ):
        """GIVEN a shipment
        WHEN audit pack is generated
        THEN metadata.json is included with correct structure."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with patch('app.services.audit_pack.generate_summary_pdf') as mock_pdf:
            mock_pdf.return_value = io.BytesIO(b"%PDF-1.4 Summary")
            zip_buffer = generate_audit_pack(mock_shipment, mock_db_session)

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            assert "metadata.json" in zf.namelist()
            metadata_content = zf.read("metadata.json").decode('utf-8')
            import json
            metadata = json.loads(metadata_content)
            assert metadata["shipment"]["reference"] == mock_shipment.reference
            assert metadata["shipment"]["container_number"] == mock_shipment.container_number

    def test_audit_pack_includes_tracking_log_json(
        self, mock_shipment, mock_db_session
    ):
        """GIVEN a shipment
        WHEN audit pack is generated
        THEN container-tracking-log.json is included."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with patch('app.services.audit_pack.generate_summary_pdf') as mock_pdf:
            mock_pdf.return_value = io.BytesIO(b"%PDF-1.4 Summary")
            zip_buffer = generate_audit_pack(mock_shipment, mock_db_session)

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            assert "container-tracking-log.json" in zf.namelist()
