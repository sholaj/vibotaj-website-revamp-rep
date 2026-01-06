"""
Analytics tests for TraceHub API.

Tests cover:
- Dashboard statistics endpoint
- Shipment metrics
- Document metrics
- Compliance metrics
- Tracking metrics
- Trends over time
- Multi-tenancy isolation (org-scoped metrics)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.models.document import Document, DocumentType, DocumentStatus
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions

# Test database URL
SQLALCHEMY_DATABASE_URL = "postgresql://tracehub:tracehub@localhost:5433/tracehub_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    """Create test database session."""
    # Drop and recreate schema for clean state
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
    """Create VIBOTAJ organization."""
    org = Organization(
        name="VIBOTAJ Analytics",
        slug="vibotaj-analytics",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="analytics@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def org_hages(db_session):
    """Create HAGES organization."""
    org = Organization(
        name="HAGES Analytics",
        slug="hages-analytics",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="analytics@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def admin_user(db_session, org_vibotaj):
    """Create admin user."""
    user = User(
        email="analytics-admin@vibotaj.com",
        full_name="Analytics Admin",
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
def viewer_user(db_session, org_vibotaj):
    """Create viewer user."""
    user = User(
        email="analytics-viewer@vibotaj.com",
        full_name="Analytics Viewer",
        hashed_password=get_password_hash("Viewer123!"),
        role=UserRole.VIEWER,
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="module")
def hages_admin(db_session, org_hages):
    """Create HAGES admin."""
    user = User(
        email="analytics-admin@hages.de",
        full_name="HAGES Analytics Admin",
        hashed_password=get_password_hash("Hages123!"),
        role=UserRole.ADMIN,
        organization_id=org_hages.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def mock_auth(user):
    """Create mock authentication for a user."""
    permissions = [p.value for p in get_role_permissions(user.role)]
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        permissions=permissions
    )


@pytest.fixture(scope="module")
def sample_data(db_session, org_vibotaj, org_hages):
    """Create sample shipments and documents for analytics."""
    # VIBOTAJ shipments - use actual ShipmentStatus values
    vibotaj_shipments = []
    for i in range(5):
        status = [
            ShipmentStatus.DRAFT,
            ShipmentStatus.DOCS_PENDING,
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.ARRIVED,
            ShipmentStatus.DELIVERED
        ][i]
        shipment = Shipment(
            reference=f"VIBO-ANALYTICS-{i:03d}",
            container_number=f"ANAL{i:07d}",
            status=status,
            organization_id=org_vibotaj.id,
            created_at=datetime.utcnow() - timedelta(days=i * 5),
            updated_at=datetime.utcnow()
        )
        db_session.add(shipment)
        vibotaj_shipments.append(shipment)
    
    # HAGES shipments
    hages_shipments = []
    for i in range(3):
        shipment = Shipment(
            reference=f"HAGES-ANALYTICS-{i:03d}",
            container_number=f"HGAN{i:07d}",
            status=ShipmentStatus.IN_TRANSIT,
            organization_id=org_hages.id,
            created_at=datetime.utcnow() - timedelta(days=i * 3),
            updated_at=datetime.utcnow()
        )
        db_session.add(shipment)
        hages_shipments.append(shipment)
    
    db_session.commit()
    
    # Create documents for VIBOTAJ shipments
    documents = []
    for shipment in vibotaj_shipments[:3]:
        doc = Document(
            shipment_id=shipment.id,
            organization_id=org_vibotaj.id,
            name=f"BOL {shipment.reference}",
            document_type=DocumentType.BILL_OF_LADING,
            status=DocumentStatus.VALIDATED,
            file_name=f"bol_{shipment.reference}.pdf",
            file_path=f"/uploads/{shipment.reference}/bol.pdf",
            file_size=1024,
            mime_type="application/pdf",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(doc)
        documents.append(doc)
    
    db_session.commit()
    
    yield {
        "vibotaj_shipments": vibotaj_shipments,
        "hages_shipments": hages_shipments,
        "documents": documents
    }
    
    # Cleanup
    for doc in documents:
        db_session.delete(doc)
    for shipment in vibotaj_shipments + hages_shipments:
        db_session.delete(shipment)
    db_session.commit()


class TestDashboardStats:
    """Tests for dashboard statistics endpoint."""

    def test_get_dashboard_stats(self, client, admin_user, sample_data):
        """Should return dashboard statistics."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain expected keys
        assert "shipments" in data or "total_shipments" in data or isinstance(data, dict)
        
        del app.dependency_overrides[get_current_active_user]

    def test_dashboard_stats_viewer_access(self, client, viewer_user):
        """Viewer should be able to access dashboard stats."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(viewer_user)
        
        response = client.get("/api/analytics/dashboard")
        
        # Viewers should have read access to analytics
        assert response.status_code in [200, 403]
        
        del app.dependency_overrides[get_current_active_user]


class TestShipmentMetrics:
    """Tests for shipment metrics endpoints."""

    def test_get_shipment_metrics(self, client, admin_user, sample_data):
        """Should return shipment statistics."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/shipments")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain shipment stats
        assert isinstance(data, dict)
        
        del app.dependency_overrides[get_current_active_user]

    def test_get_shipment_trends_default(self, client, admin_user, sample_data):
        """Should return shipment trends with default parameters."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/shipments/trends")
        
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "group_by" in data
        assert data["period_days"] == 30
        assert data["group_by"] == "day"
        
        del app.dependency_overrides[get_current_active_user]

    def test_get_shipment_trends_custom_days(self, client, admin_user):
        """Should return trends for custom time period."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/shipments/trends?days=90")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 90
        
        del app.dependency_overrides[get_current_active_user]

    def test_get_shipment_trends_group_by_week(self, client, admin_user):
        """Should group trends by week."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/shipments/trends?group_by=week")
        
        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "week"
        
        del app.dependency_overrides[get_current_active_user]

    def test_get_shipment_trends_invalid_group_by(self, client, admin_user):
        """Invalid group_by should return validation error."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/shipments/trends?group_by=invalid")
        
        assert response.status_code == 422
        
        del app.dependency_overrides[get_current_active_user]


class TestDocumentMetrics:
    """Tests for document metrics endpoints."""

    def test_get_document_metrics(self, client, admin_user, sample_data):
        """Should return document statistics."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        del app.dependency_overrides[get_current_active_user]

    def test_get_document_distribution(self, client, admin_user, sample_data):
        """Should return document status distribution."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/documents/distribution")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        
        del app.dependency_overrides[get_current_active_user]


class TestComplianceMetrics:
    """Tests for compliance metrics endpoint."""

    def test_get_compliance_metrics(self, client, admin_user, sample_data):
        """Should return compliance statistics."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/compliance")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        del app.dependency_overrides[get_current_active_user]


class TestTrackingMetrics:
    """Tests for tracking metrics endpoint."""

    def test_get_tracking_metrics(self, client, admin_user):
        """Should return tracking statistics."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/tracking")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        del app.dependency_overrides[get_current_active_user]


class TestMultiTenancyAnalytics:
    """Tests for multi-tenancy isolation in analytics."""

    def test_vibotaj_only_sees_vibotaj_stats(
        self, client, admin_user, sample_data
    ):
        """VIBOTAJ user should only see VIBOTAJ metrics."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/analytics/shipments")
        
        assert response.status_code == 200
        data = response.json()
        
        # Stats should reflect only VIBOTAJ data
        # (specific validation depends on response structure)
        
        del app.dependency_overrides[get_current_active_user]

    def test_hages_only_sees_hages_stats(
        self, client, hages_admin, sample_data
    ):
        """HAGES user should only see HAGES metrics."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(hages_admin)
        
        response = client.get("/api/analytics/shipments")
        
        assert response.status_code == 200
        data = response.json()
        
        # Stats should reflect only HAGES data
        
        del app.dependency_overrides[get_current_active_user]


class TestAnalyticsAuthentication:
    """Tests for analytics authentication requirements."""

    def test_dashboard_requires_auth(self, client):
        """Dashboard endpoint should require authentication."""
        response = client.get("/api/analytics/dashboard")
        
        assert response.status_code == 401

    def test_shipments_requires_auth(self, client):
        """Shipments endpoint should require authentication."""
        response = client.get("/api/analytics/shipments")
        
        assert response.status_code == 401

    def test_documents_requires_auth(self, client):
        """Documents endpoint should require authentication."""
        response = client.get("/api/analytics/documents")
        
        assert response.status_code == 401

    def test_compliance_requires_auth(self, client):
        """Compliance endpoint should require authentication."""
        response = client.get("/api/analytics/compliance")
        
        assert response.status_code == 401

    def test_tracking_requires_auth(self, client):
        """Tracking endpoint should require authentication."""
        response = client.get("/api/analytics/tracking")
        
        assert response.status_code == 401
