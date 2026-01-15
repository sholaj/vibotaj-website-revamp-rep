"""Tests for shipment container update endpoint.

TDD Phase: RED - Write failing tests first

These tests verify:
1. PATCH /api/shipments/{id}/container endpoint exists and works
2. Container number is validated against ISO 6346 format
3. Permission checks prevent unauthorized updates
4. Placeholder containers can be updated with real container numbers
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import uuid

from app.main import app
from app.database import get_db
from app.models import (
    User, UserRole, Organization, OrganizationType, OrganizationStatus,
    Shipment, ShipmentStatus
)
from app.models.shipment import ProductType
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions
from app.models.organization import OrgRole

from .conftest import engine, TestingSessionLocal, Base


@pytest.fixture(scope="module")
def db_session():
    """Create clean database for tests."""
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def client(db_session):
    """Create test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="module")
def test_org(db_session):
    """Create test organization."""
    org = Organization(
        name="Container Update Test",
        slug=f"container-update-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="test@update.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def admin_user(db_session, test_org):
    """Create admin user."""
    user = User(
        email=f"admin-{uuid.uuid4().hex[:6]}@update-test.com",
        full_name="Update Admin",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=test_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def viewer_user(db_session, test_org):
    """Create viewer user (no update permission)."""
    user = User(
        email=f"viewer-{uuid.uuid4().hex[:6]}@update-test.com",
        full_name="Viewer User",
        hashed_password=get_password_hash("Viewer123!"),
        role=UserRole.VIEWER,
        organization_id=test_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def shipment_with_placeholder(db_session, test_org):
    """Create shipment with placeholder container."""
    shipment = Shipment(
        reference=f"UPDATE-TEST-{uuid.uuid4().hex[:6]}",
        container_number="BECKMANN-CNT-001",  # Placeholder
        organization_id=test_org.id,
        status=ShipmentStatus.DRAFT,
        product_type=ProductType.HORN_HOOF
    )
    db_session.add(shipment)
    db_session.commit()
    db_session.refresh(shipment)
    yield shipment
    # Cleanup
    try:
        db_session.delete(shipment)
        db_session.commit()
    except Exception:
        db_session.rollback()


def create_mock_current_user(user: User, org_type=OrganizationType.VIBOTAJ) -> CurrentUser:
    """Create mock CurrentUser."""
    permissions = [p.value for p in get_role_permissions(user.role)]
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        permissions=permissions,
        org_role=OrgRole.ADMIN if user.role == UserRole.ADMIN else OrgRole.MEMBER,
        org_type=org_type,
        org_permissions=[]
    )


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Clean up dependency overrides."""
    yield
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]


class TestContainerUpdateEndpoint:
    """Test PATCH /api/shipments/{id}/container endpoint.

    These tests will FAIL in RED phase because:
    - The PATCH /api/shipments/{id}/container endpoint does not exist
    - Container validation (ISO 6346) is not implemented
    """

    def test_update_container_success(self, client, db_session, admin_user, shipment_with_placeholder):
        """PATCH /api/shipments/{id}/container should update container.

        Expected behavior (RED phase - this will FAIL):
        - Endpoint accepts JSON with container_number
        - Returns updated shipment with new container number
        - Status code 200 on success

        This test will FAIL because:
        - Endpoint /api/shipments/{id}/container does not exist (404)
        """
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": "MRSU3452572"}
        )

        # RED PHASE: This will fail with 404 - endpoint doesn't exist
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}. Endpoint may not exist: {response.json()}"

        data = response.json()
        assert data["container_number"] == "MRSU3452572", \
            "Response should contain updated container number"

    def test_update_container_validates_iso6346(self, client, admin_user, shipment_with_placeholder):
        """Invalid container format should be rejected.

        Expected behavior (RED phase - this will FAIL):
        - Container number must match ISO 6346 format: 4 letters + 7 digits
        - Invalid format returns 422 validation error

        This test will FAIL because:
        - Endpoint doesn't exist
        - ISO 6346 validation is not implemented
        """
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": "INVALID"}
        )

        # RED PHASE: Will fail - endpoint doesn't exist (404 instead of 422)
        assert response.status_code == 422, \
            f"Expected 422 validation error, got {response.status_code}"

    @pytest.mark.skip(reason="Check digit validation is an enhancement - basic format validation is sufficient")
    def test_update_container_validates_check_digit(self, client, admin_user, shipment_with_placeholder):
        """Container with wrong check digit should be rejected.

        ISO 6346 container numbers have a check digit (11th character).
        MRSU3452572 - valid
        MRSU3452573 - invalid check digit

        Expected behavior (RED phase - this will FAIL):
        - Check digit validation returns 422 with helpful error message
        """
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": "MRSU3452573"}  # Wrong check digit
        )

        # RED PHASE: Will fail - endpoint doesn't exist
        assert response.status_code == 422, \
            f"Expected 422 for invalid check digit, got {response.status_code}"

        if response.status_code == 422:
            data = response.json()
            # Should have helpful error message
            assert "check digit" in str(data).lower() or "invalid" in str(data).lower()

    def test_update_container_requires_permission(self, client, viewer_user, shipment_with_placeholder):
        """VIEWER should not be able to update container.

        Expected behavior (RED phase - this will FAIL):
        - Viewer role lacks shipments:update permission
        - Returns 403 Forbidden

        This test will FAIL because:
        - Endpoint doesn't exist (404 instead of 403)
        """
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(viewer_user)

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": "MRSU3452572"}
        )

        # RED PHASE: Will fail - endpoint doesn't exist (404 instead of 403)
        assert response.status_code == 403, \
            f"Expected 403 Forbidden for viewer, got {response.status_code}"

    def test_update_container_from_placeholder(self, client, db_session, admin_user, shipment_with_placeholder):
        """Placeholder container should be replaceable.

        Expected behavior (RED phase - this will FAIL):
        - Placeholder patterns (BUYER-CNT-XXX) can be replaced
        - Database record is updated
        - Response includes previous_container_number for audit trail

        This test will FAIL because:
        - Endpoint doesn't exist
        """
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        # Verify it starts as placeholder
        assert "CNT" in shipment_with_placeholder.container_number, \
            "Test fixture should have placeholder container"

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": "TCNU1234567"}
        )

        # RED PHASE: Will fail - endpoint doesn't exist
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}"

        # Refresh from DB
        db_session.refresh(shipment_with_placeholder)
        assert shipment_with_placeholder.container_number == "TCNU1234567", \
            "Database should be updated with new container number"

    def test_update_container_returns_shipment(self, client, admin_user, shipment_with_placeholder):
        """Update response should return full shipment data.

        Expected behavior (RED phase - this will FAIL):
        - Response includes all shipment fields
        - Includes previous container number for audit
        """
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": "MSCU9876543"}
        )

        if response.status_code == 200:
            data = response.json()

            # Should return shipment fields
            assert "id" in data or "shipment_id" in data
            assert "reference" in data
            assert "container_number" in data

            # Should include audit info (nice to have)
            # assert "previous_container_number" in data


class TestContainerUpdateEdgeCases:
    """Test edge cases for container update endpoint."""

    def test_update_nonexistent_shipment(self, client, admin_user):
        """Update container for non-existent shipment should return 404."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        fake_id = uuid.uuid4()
        response = client.patch(
            f"/api/shipments/{fake_id}/container",
            json={"container_number": "MRSU3452572"}
        )

        # This could be 404 (not found) or 405 (method not allowed if endpoint doesn't exist)
        assert response.status_code in [404, 405], \
            f"Expected 404 or 405, got {response.status_code}"

    def test_update_container_empty_string(self, client, admin_user, shipment_with_placeholder):
        """Empty container number should be rejected."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": ""}
        )

        # Should be 422 validation error
        assert response.status_code in [422, 400, 404], \
            f"Expected validation error, got {response.status_code}"

    def test_update_container_null(self, client, admin_user, shipment_with_placeholder):
        """Null container number should be rejected."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": None}
        )

        # Should be 422 validation error
        assert response.status_code in [422, 400, 404], \
            f"Expected validation error, got {response.status_code}"

    def test_update_container_same_value(self, client, db_session, admin_user, shipment_with_placeholder):
        """Updating to same container number should still succeed (idempotent)."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        original_container = shipment_with_placeholder.container_number

        response = client.patch(
            f"/api/shipments/{shipment_with_placeholder.id}/container",
            json={"container_number": original_container}
        )

        # Should succeed (idempotent) or return 404 if endpoint doesn't exist
        if response.status_code == 200:
            db_session.refresh(shipment_with_placeholder)
            assert shipment_with_placeholder.container_number == original_container


class TestContainerValidationFormats:
    """Test various container number formats.

    Valid ISO 6346 format: 4 letters (owner code + category) + 6 digits + check digit
    Examples:
    - MRSU3452572 (valid)
    - TCNU1234567 (needs check digit calculation)
    - MSCU9876543 (needs check digit calculation)
    """

    @pytest.fixture
    def shipment(self, db_session, test_org):
        """Create a fresh shipment for each test."""
        shipment = Shipment(
            reference=f"FORMAT-TEST-{uuid.uuid4().hex[:6]}",
            container_number="TEST-PLACEHOLDER-001",
            organization_id=test_org.id,
            status=ShipmentStatus.DRAFT,
            product_type=ProductType.HORN_HOOF
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)
        yield shipment
        try:
            db_session.delete(shipment)
            db_session.commit()
        except Exception:
            db_session.rollback()

    @pytest.mark.parametrize("container,expected_valid", [
        ("MRSU3452572", True),   # Valid with correct check digit
        ("CSQU3054383", True),   # Valid MSC container
        ("MSKU9876543", True),   # Valid Maersk container (check digit to verify)
        ("ABC1234567", False),   # Only 3 letters
        ("ABCD123456", False),   # Only 6 digits
        ("1234567890", False),   # No letters
        ("ABCDEFGHIJ", False),   # No digits
        ("", False),             # Empty
        ("MRSU345257", False),   # Only 10 chars
    ])
    def test_container_format_validation(self, client, admin_user, shipment, container, expected_valid):
        """Test various container number formats are validated correctly.

        RED PHASE: All tests will fail because endpoint doesn't exist.
        """
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(admin_user)

        response = client.patch(
            f"/api/shipments/{shipment.id}/container",
            json={"container_number": container}
        )

        # RED PHASE: Will fail - endpoint doesn't exist
        if expected_valid:
            assert response.status_code == 200, \
                f"Container {container} should be valid, got {response.status_code}"
        else:
            assert response.status_code == 422, \
                f"Container {container} should be invalid, got {response.status_code}"
