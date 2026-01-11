"""
Multi-Tenancy Isolation Tests for TraceHub API.

Tests verify that data is properly isolated between organizations:
- Users in Org A cannot see Org B's shipments
- Users in Org A cannot see Org B's documents
- Users in Org A cannot see Org B's audit logs
- Cross-organization access attempts return 404 (not 403, to avoid leaking existence)

These tests verify the security fixes:
- SEC-001: Audit logs filtered by organization
- SEC-002: Document duplicate check verifies org ownership

Sprint 10 - TEST-001: Multi-Tenancy Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime, timedelta
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models.shipment import Shipment, ShipmentStatus, ProductType
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.audit_log import AuditLog
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions
from app.models.organization import OrgRole

# Import shared test database configuration
from .conftest import engine, TestingSessionLocal, Base


@pytest.fixture(scope="module")
def db_session():
    """Create fresh test database session."""
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
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="module")
def org_vibotaj(db_session):
    """Create VIBOTAJ organization (exporter)."""
    org = Organization(
        name="VIBOTAJ Global",
        slug="vibotaj-mt",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="hq@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def org_hages(db_session):
    """Create HAGES organization (buyer)."""
    org = Organization(
        name="HAGES GmbH",
        slug="hages-mt",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def vibotaj_user(db_session, org_vibotaj):
    """Create VIBOTAJ admin user."""
    user = User(
        email="admin-mt@vibotaj.com",
        full_name="VIBOTAJ Admin MT",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def hages_user(db_session, org_hages):
    """Create HAGES admin user."""
    user = User(
        email="admin-mt@hages.de",
        full_name="HAGES Admin MT",
        hashed_password=get_password_hash("Hages123!"),
        role=UserRole.ADMIN,
        organization_id=org_hages.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def vibotaj_shipment(db_session, org_vibotaj):
    """Create a shipment belonging to VIBOTAJ."""
    shipment = Shipment(
        reference=f"VIB-MT-{uuid.uuid4().hex[:6]}",
        container_number="MSKU1234567",
        bl_number="BLVIB001",
        organization_id=org_vibotaj.id,
        status=ShipmentStatus.DRAFT,
        product_type=ProductType.HORN_HOOF,
        exporter_name="VIBOTAJ Global",
        importer_name="HAGES GmbH",
        pol_code="NGLOS",
        pod_code="DEHAM"
    )
    db_session.add(shipment)
    db_session.commit()
    db_session.refresh(shipment)
    return shipment


@pytest.fixture(scope="module")
def hages_shipment(db_session, org_hages):
    """Create a shipment belonging to HAGES (for testing isolation)."""
    shipment = Shipment(
        reference=f"HAG-MT-{uuid.uuid4().hex[:6]}",
        container_number="MSKU7654321",
        bl_number="BLHAG001",
        organization_id=org_hages.id,
        status=ShipmentStatus.DRAFT,
        product_type=ProductType.HORN_HOOF,
        exporter_name="HAGES GmbH",
        importer_name="Another Buyer",
        pol_code="DEHAM",
        pod_code="NLRTM"
    )
    db_session.add(shipment)
    db_session.commit()
    db_session.refresh(shipment)
    return shipment


@pytest.fixture(scope="module")
def vibotaj_document(db_session, vibotaj_shipment):
    """Create a document belonging to VIBOTAJ's shipment."""
    doc = Document(
        shipment_id=vibotaj_shipment.id,
        name="Bill of Lading - VIBOTAJ",
        document_type=DocumentType.BILL_OF_LADING,
        status=DocumentStatus.UPLOADED,
        file_name="bol_vibotaj.pdf"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture(scope="module")
def hages_document(db_session, hages_shipment):
    """Create a document belonging to HAGES's shipment."""
    doc = Document(
        shipment_id=hages_shipment.id,
        name="Bill of Lading - HAGES",
        document_type=DocumentType.BILL_OF_LADING,
        status=DocumentStatus.UPLOADED,
        file_name="bol_hages.pdf"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture(scope="module")
def vibotaj_audit_log(db_session, org_vibotaj, vibotaj_user, vibotaj_shipment):
    """Create audit log entry for VIBOTAJ."""
    log = AuditLog(
        action="CREATE",
        entity_type="shipment",
        entity_id=str(vibotaj_shipment.id),
        organization_id=org_vibotaj.id,
        user_id=str(vibotaj_user.id),
        user_email=vibotaj_user.email,
        timestamp=datetime.utcnow()
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log


@pytest.fixture(scope="module")
def hages_audit_log(db_session, org_hages, hages_user, hages_shipment):
    """Create audit log entry for HAGES."""
    log = AuditLog(
        action="CREATE",
        entity_type="shipment",
        entity_id=str(hages_shipment.id),
        organization_id=org_hages.id,
        user_id=str(hages_user.id),
        user_email=hages_user.email,
        timestamp=datetime.utcnow()
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log


def create_mock_current_user(user: User) -> CurrentUser:
    """Create CurrentUser mock for authentication override."""
    permissions = [p.value for p in get_role_permissions(user.role)]
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        permissions=permissions,
        org_role=OrgRole.ADMIN,
        org_type=OrganizationType.VIBOTAJ if "vibotaj" in user.email else OrganizationType.BUYER,
        org_permissions=[]
    )


class TestShipmentIsolation:
    """Test that users can only access their own organization's shipments."""

    def test_vibotaj_user_sees_only_vibotaj_shipments(
        self, client, db_session, vibotaj_user, vibotaj_shipment, hages_shipment
    ):
        """VIBOTAJ user should only see VIBOTAJ shipments, not HAGES shipments."""
        # Override auth to use VIBOTAJ user
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)

        response = client.get("/api/shipments")
        assert response.status_code == 200

        data = response.json()
        shipment_ids = [s["id"] for s in data.get("items", data)]

        # Should see VIBOTAJ shipment
        assert str(vibotaj_shipment.id) in shipment_ids
        # Should NOT see HAGES shipment
        assert str(hages_shipment.id) not in shipment_ids

    def test_hages_user_sees_only_hages_shipments(
        self, client, db_session, hages_user, vibotaj_shipment, hages_shipment
    ):
        """HAGES user should only see HAGES shipments, not VIBOTAJ shipments."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(hages_user)

        response = client.get("/api/shipments")
        assert response.status_code == 200

        data = response.json()
        shipment_ids = [s["id"] for s in data.get("items", data)]

        # Should see HAGES shipment
        assert str(hages_shipment.id) in shipment_ids
        # Should NOT see VIBOTAJ shipment
        assert str(vibotaj_shipment.id) not in shipment_ids

    def test_vibotaj_user_cannot_access_hages_shipment_detail(
        self, client, vibotaj_user, hages_shipment
    ):
        """VIBOTAJ user should get 404 when trying to access HAGES shipment by ID."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)

        response = client.get(f"/api/shipments/{hages_shipment.id}")
        # Should return 404, not 403 (to avoid leaking existence)
        assert response.status_code == 404

    def test_hages_user_cannot_access_vibotaj_shipment_detail(
        self, client, hages_user, vibotaj_shipment
    ):
        """HAGES user should get 404 when trying to access VIBOTAJ shipment by ID."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(hages_user)

        response = client.get(f"/api/shipments/{vibotaj_shipment.id}")
        assert response.status_code == 404


class TestDocumentIsolation:
    """Test that users can only access documents from their own organization's shipments."""

    def test_vibotaj_user_cannot_access_hages_document(
        self, client, vibotaj_user, hages_document
    ):
        """VIBOTAJ user should get 404 when trying to access HAGES document."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)

        response = client.get(f"/api/documents/{hages_document.id}")
        assert response.status_code == 404

    def test_hages_user_cannot_access_vibotaj_document(
        self, client, hages_user, vibotaj_document
    ):
        """HAGES user should get 404 when trying to access VIBOTAJ document."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(hages_user)

        response = client.get(f"/api/documents/{vibotaj_document.id}")
        assert response.status_code == 404


class TestAuditLogIsolation:
    """Test that audit logs are properly filtered by organization (SEC-001 fix)."""

    def test_vibotaj_user_sees_only_vibotaj_audit_logs(
        self, client, vibotaj_user, vibotaj_audit_log, hages_audit_log
    ):
        """VIBOTAJ user should only see VIBOTAJ audit logs."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)

        response = client.get("/api/audit/")
        assert response.status_code == 200

        data = response.json()
        logs = data.get("items", data)
        log_ids = [str(log.get("id")) for log in logs]

        # Should see VIBOTAJ audit log
        assert str(vibotaj_audit_log.id) in log_ids
        # Should NOT see HAGES audit log
        assert str(hages_audit_log.id) not in log_ids

    def test_hages_user_sees_only_hages_audit_logs(
        self, client, hages_user, vibotaj_audit_log, hages_audit_log
    ):
        """HAGES user should only see HAGES audit logs."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(hages_user)

        response = client.get("/api/audit/")
        assert response.status_code == 200

        data = response.json()
        logs = data.get("items", data)
        log_ids = [str(log.get("id")) for log in logs]

        # Should see HAGES audit log
        assert str(hages_audit_log.id) in log_ids
        # Should NOT see VIBOTAJ audit log
        assert str(vibotaj_audit_log.id) not in log_ids


class TestDuplicateCheckIsolation:
    """Test that duplicate document checks verify organization ownership (SEC-002 fix)."""

    def test_vibotaj_user_cannot_check_duplicates_for_hages_shipment(
        self, client, vibotaj_user, hages_shipment
    ):
        """VIBOTAJ user should get 404 when checking duplicates for HAGES shipment."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)

        response = client.get(f"/api/documents/shipments/{hages_shipment.id}/duplicates")
        assert response.status_code == 404

    def test_hages_user_cannot_check_duplicates_for_vibotaj_shipment(
        self, client, hages_user, vibotaj_shipment
    ):
        """HAGES user should get 404 when checking duplicates for VIBOTAJ shipment."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(hages_user)

        response = client.get(f"/api/documents/shipments/{vibotaj_shipment.id}/duplicates")
        assert response.status_code == 404


class TestEUDRIsolation:
    """Test that EUDR endpoints respect organization boundaries."""

    def test_vibotaj_user_cannot_get_eudr_status_for_hages_shipment(
        self, client, vibotaj_user, hages_shipment
    ):
        """VIBOTAJ user should get 404 for HAGES shipment EUDR status."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)

        response = client.get(f"/api/eudr/shipment/{hages_shipment.id}/status")
        assert response.status_code == 404

    def test_hages_user_cannot_get_eudr_status_for_vibotaj_shipment(
        self, client, hages_user, vibotaj_shipment
    ):
        """HAGES user should get 404 for VIBOTAJ shipment EUDR status."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(hages_user)

        response = client.get(f"/api/eudr/shipment/{vibotaj_shipment.id}/status")
        assert response.status_code == 404


# Cleanup fixture to reset dependency overrides
@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Clean up dependency overrides after each test."""
    yield
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]
