"""Integration tests for document validation API endpoints.

Tests the /api/validation/* endpoints for:
- Shipment validation
- Validation status checks
- Rule listing
- Override functionality

Run with: pytest tests/test_document_validation_api.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app
from app.models.document import DocumentType, DocumentStatus
from app.models.shipment import ProductType
from app.routers.auth import get_current_active_user
from app.database import get_db


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    user = Mock()
    user.id = uuid4()
    user.email = "test@vibotaj.com"
    user.organization_id = uuid4()
    user.role = "admin"
    return user


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def client_with_auth(mock_current_user, mock_db_session):
    """Create test client with authentication override."""
    # Override the auth dependency
    app.dependency_overrides[get_current_active_user] = lambda: mock_current_user
    app.dependency_overrides[get_db] = lambda: mock_db_session

    client = TestClient(app)
    yield client, mock_current_user, mock_db_session

    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create test client without auth (for testing auth requirement)."""
    # Clear any existing overrides
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.fixture
def mock_shipment(mock_current_user):
    """Create mock shipment."""
    shipment = Mock()
    shipment.id = uuid4()
    shipment.reference = "VIBO-2026-TEST"
    shipment.organization_id = mock_current_user.organization_id
    shipment.product_type = ProductType.HORN_HOOF
    shipment.etd = datetime(2026, 2, 15)
    # Validation override fields (Sprint 12)
    shipment.validation_override_reason = None
    shipment.validation_override_by = None
    shipment.validation_override_at = None
    return shipment


@pytest.fixture
def mock_document():
    """Factory for mock documents."""
    def _create(doc_type=DocumentType.BILL_OF_LADING, org_id=None):
        doc = Mock()
        doc.id = uuid4()
        doc.document_type = doc_type
        doc.name = f"test_{doc_type.value}.pdf"
        doc.status = DocumentStatus.UPLOADED
        doc.document_date = datetime(2026, 2, 10)
        doc.issuer = "Federal Ministry of Agriculture Nigeria"
        doc.organization_id = org_id
        return doc
    return _create


# =============================================================================
# Test: GET /api/validation/rules (No Auth Required)
# =============================================================================

class TestListValidationRules:
    """Test GET /api/validation/rules endpoint."""

    def test_list_all_rules(self, client):
        """Should return all registered validation rules."""
        response = client.get("/api/validation/rules")

        assert response.status_code == 200
        rules = response.json()

        # Should have at least our 5 core rules
        assert len(rules) >= 5

        # Check structure
        for rule in rules:
            assert "rule_id" in rule
            assert "name" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "category" in rule

    def test_filter_rules_by_product_type(self, client):
        """Should filter rules by product type."""
        # Horn & Hoof should include vet cert rules
        response = client.get("/api/validation/rules?product_type=horn_hoof")
        assert response.status_code == 200
        rules = response.json()
        rule_ids = [r["rule_id"] for r in rules]
        assert "HORN_HOOF_002" in rule_ids
        assert "HORN_HOOF_003" in rule_ids

        # Sweet potato should NOT include vet cert rules
        response = client.get("/api/validation/rules?product_type=sweet_potato")
        assert response.status_code == 200
        rules = response.json()
        rule_ids = [r["rule_id"] for r in rules]
        assert "HORN_HOOF_002" not in rule_ids
        assert "HORN_HOOF_003" not in rule_ids

    def test_filter_rules_by_category(self, client):
        """Should filter rules by category."""
        response = client.get("/api/validation/rules?category=presence")
        assert response.status_code == 200
        rules = response.json()

        # All returned rules should be in presence category
        for rule in rules:
            assert rule["category"] == "presence"

    def test_invalid_product_type_returns_400(self, client):
        """Should return 400 for invalid product type."""
        response = client.get("/api/validation/rules?product_type=invalid_type")
        assert response.status_code == 400
        assert "Invalid product_type" in response.json()["detail"]

    def test_invalid_category_returns_400(self, client):
        """Should return 400 for invalid category."""
        response = client.get("/api/validation/rules?category=invalid_cat")
        assert response.status_code == 400
        assert "Invalid category" in response.json()["detail"]


class TestGetRuleDetails:
    """Test GET /api/validation/rules/{rule_id} endpoint."""

    def test_get_existing_rule(self, client):
        """Should return rule details for valid rule_id."""
        response = client.get("/api/validation/rules/PRESENCE_001")

        assert response.status_code == 200
        rule = response.json()
        assert rule["rule_id"] == "PRESENCE_001"
        assert rule["name"] == "Required Documents Present"
        assert rule["category"] == "presence"

    def test_get_nonexistent_rule_returns_404(self, client):
        """Should return 404 for unknown rule_id."""
        response = client.get("/api/validation/rules/NONEXISTENT_001")

        assert response.status_code == 404
        assert "Rule not found" in response.json()["detail"]


# =============================================================================
# Test: POST /api/validation/shipments/{id}/validate
# =============================================================================

class TestValidateShipment:
    """Test POST /api/validation/shipments/{id}/validate endpoint."""

    def test_validate_shipment_requires_auth(self, client):
        """Should require authentication."""
        shipment_id = uuid4()
        response = client.post(f"/api/validation/shipments/{shipment_id}/validate")

        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]

    def test_validate_shipment_not_found(self, client_with_auth, mock_shipment):
        """Should return 404 for non-existent shipment."""
        client, mock_user, mock_db = client_with_auth

        # Setup mock to return None for shipment query
        mock_db.query.return_value.filter.return_value.first.return_value = None

        shipment_id = uuid4()
        response = client.post(f"/api/validation/shipments/{shipment_id}/validate")

        assert response.status_code == 404

    def test_validate_shipment_success(self, client_with_auth, mock_shipment, mock_document):
        """Should return validation report for valid shipment."""
        client, mock_user, mock_db = client_with_auth

        # Make shipment match user's org
        mock_shipment.organization_id = mock_user.organization_id

        # Setup mock query chain
        query_mock = MagicMock()
        mock_db.query.return_value = query_mock

        # Track which model is being queried
        call_count = [0]

        def filter_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: shipment query
                result.first.return_value = mock_shipment
            else:
                # Second call: documents query
                result.all.return_value = [mock_document(DocumentType.BILL_OF_LADING)]
            return result

        query_mock.filter.side_effect = filter_side_effect

        response = client.post(f"/api/validation/shipments/{mock_shipment.id}/validate")

        assert response.status_code == 200
        data = response.json()
        assert "shipment_id" in data or "summary" in data


# =============================================================================
# Test: GET /api/validation/shipments/{id}/status
# =============================================================================

class TestGetValidationStatus:
    """Test GET /api/validation/shipments/{id}/status endpoint."""

    def test_get_status_requires_auth(self, client):
        """Should require authentication."""
        shipment_id = uuid4()
        response = client.get(f"/api/validation/shipments/{shipment_id}/status")

        assert response.status_code in [401, 403]

    def test_get_status_not_found(self, client_with_auth):
        """Should return 404 for non-existent shipment."""
        client, mock_user, mock_db = client_with_auth

        # Setup mock to return None for shipment query
        mock_db.query.return_value.filter.return_value.first.return_value = None

        shipment_id = uuid4()
        response = client.get(f"/api/validation/shipments/{shipment_id}/status")

        assert response.status_code == 404

    def test_get_status_success(self, client_with_auth, mock_shipment, mock_document):
        """Should return status summary for valid shipment."""
        client, mock_user, mock_db = client_with_auth

        # Make shipment match user's org
        mock_shipment.organization_id = mock_user.organization_id

        # Setup mock query chain
        query_mock = MagicMock()
        mock_db.query.return_value = query_mock

        # Track which model is being queried
        call_count = [0]

        def filter_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: shipment query
                result.first.return_value = mock_shipment
            else:
                # Second call: documents query
                result.all.return_value = [mock_document(DocumentType.BILL_OF_LADING)]
            return result

        query_mock.filter.side_effect = filter_side_effect

        response = client.get(f"/api/validation/shipments/{mock_shipment.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["shipment_id"] == str(mock_shipment.id)
        assert "document_count" in data


# =============================================================================
# Test: POST /api/validation/documents/{id}/override-rejection
# =============================================================================

class TestOverrideRejection:
    """Test POST /api/validation/documents/{id}/override-rejection endpoint."""

    def test_override_requires_auth(self, client):
        """Should require authentication."""
        document_id = uuid4()
        response = client.post(
            f"/api/validation/documents/{document_id}/override-rejection",
            params={"reason": "This is a valid document"}
        )
        assert response.status_code in [401, 403]

    def test_override_requires_admin_role(self, mock_db_session, mock_document):
        """Should require admin or owner role."""
        # Create a user with viewer role
        viewer_user = Mock()
        viewer_user.id = uuid4()
        viewer_user.email = "viewer@vibotaj.com"
        viewer_user.organization_id = uuid4()
        viewer_user.role = "viewer"

        app.dependency_overrides[get_current_active_user] = lambda: viewer_user
        app.dependency_overrides[get_db] = lambda: mock_db_session

        client = TestClient(app)

        try:
            document_id = uuid4()
            response = client.post(
                f"/api/validation/documents/{document_id}/override-rejection",
                params={"reason": "This is a valid document, AI was wrong"}
            )

            assert response.status_code == 403
            assert "admin or owner role" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_override_requires_reason(self, client_with_auth):
        """Should require reason parameter."""
        client, mock_user, mock_db = client_with_auth
        mock_user.role = "admin"

        document_id = uuid4()
        response = client.post(
            f"/api/validation/documents/{document_id}/override-rejection"
        )

        # Should fail validation (missing required query param)
        assert response.status_code == 422

    def test_override_document_not_found(self, client_with_auth):
        """Should return 404 if document not found."""
        client, mock_user, mock_db = client_with_auth
        mock_user.role = "admin"

        # Setup mock to return None for document query
        mock_db.query.return_value.filter.return_value.first.return_value = None

        document_id = uuid4()
        response = client.post(
            f"/api/validation/documents/{document_id}/override-rejection",
            params={"reason": "This is a valid override reason"}
        )

        assert response.status_code == 404

    def test_override_success(self, client_with_auth, mock_document):
        """Should successfully override and log to audit."""
        client, mock_user, mock_db = client_with_auth
        mock_user.role = "admin"

        doc = mock_document(DocumentType.BILL_OF_LADING, org_id=mock_user.organization_id)

        # Setup mock to return the document
        mock_db.query.return_value.filter.return_value.first.return_value = doc

        response = client.post(
            f"/api/validation/documents/{doc.id}/override-rejection",
            params={"reason": "Document verified manually - AI classification was incorrect"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == str(doc.id)
        assert "overridden_by" in data

        # Verify audit log was created
        mock_db.add.assert_called()
        mock_db.commit.assert_called()


# =============================================================================
# Test: POST /api/validation/shipments/{id}/validate-document/{doc_id}
# =============================================================================

class TestValidateSingleDocument:
    """Test POST /api/validation/shipments/{id}/validate-document/{doc_id} endpoint."""

    def test_validate_document_requires_auth(self, client):
        """Should require authentication."""
        shipment_id = uuid4()
        document_id = uuid4()
        response = client.post(
            f"/api/validation/shipments/{shipment_id}/validate-document/{document_id}"
        )
        assert response.status_code in [401, 403]

    def test_validate_document_shipment_not_found(self, client_with_auth):
        """Should return 404 if shipment not found."""
        client, mock_user, mock_db = client_with_auth

        # Setup mock to return None for shipment
        mock_db.query.return_value.filter.return_value.first.return_value = None

        shipment_id = uuid4()
        document_id = uuid4()
        response = client.post(
            f"/api/validation/shipments/{shipment_id}/validate-document/{document_id}"
        )

        assert response.status_code == 404
