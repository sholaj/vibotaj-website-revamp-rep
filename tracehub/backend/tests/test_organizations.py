"""
Organization and multi-tenancy tests for TraceHub API.

Tests cover:
- Organization model behavior
- Organization CRUD operations
- Organization membership
- Multi-tenancy data isolation
- Organization types and statuses
- Cross-tenant access (VIBOTAJ type)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import (
    Organization, OrganizationType, OrganizationStatus,
    OrganizationMembership, OrgRole
)
from app.models.shipment import Shipment, ShipmentStatus
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions

# Import shared test database configuration from conftest
from .conftest import engine, TestingSessionLocal, Base


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


class TestOrganizationModel:
    """Tests for Organization model behavior."""

    def test_create_vibotaj_organization(self, db_session):
        """Should create a VIBOTAJ type organization."""
        org = Organization(
            name="VIBOTAJ Test HQ",
            slug=f"vibotaj-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="test@vibotaj.com"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        
        assert org.id is not None
        assert org.type == OrganizationType.VIBOTAJ
        assert org.status == OrganizationStatus.ACTIVE
        
        db_session.delete(org)
        db_session.commit()

    def test_create_buyer_organization(self, db_session):
        """Should create a BUYER type organization."""
        org = Organization(
            name="German Buyer GmbH",
            slug=f"german-buyer-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="info@german-buyer.de",
            tax_id="DE123456789",
            registration_number="HRB12345"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        
        assert org.type == OrganizationType.BUYER
        assert org.tax_id == "DE123456789"
        
        db_session.delete(org)
        db_session.commit()

    def test_create_supplier_organization(self, db_session):
        """Should create a SUPPLIER type organization."""
        org = Organization(
            name="Nigerian Supplier Ltd",
            slug=f"ng-supplier-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.SUPPLIER,
            status=OrganizationStatus.ACTIVE,
            contact_email="info@ng-supplier.ng"
        )
        db_session.add(org)
        db_session.commit()
        
        assert org.type == OrganizationType.SUPPLIER
        
        db_session.delete(org)
        db_session.commit()

    def test_organization_slug_uniqueness(self, db_session):
        """Duplicate slugs should fail."""
        unique_slug = f"unique-slug-{uuid.uuid4().hex[:6]}"
        
        org1 = Organization(
            name="First Org",
            slug=unique_slug,
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="first@test.com"
        )
        db_session.add(org1)
        db_session.commit()
        
        org2 = Organization(
            name="Second Org",
            slug=unique_slug,  # Same slug
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="second@test.com"
        )
        db_session.add(org2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
        
        db_session.rollback()
        db_session.delete(org1)
        db_session.commit()

    def test_organization_to_dict(self, db_session):
        """Should convert organization to dictionary."""
        org = Organization(
            name="Dict Test Org",
            slug=f"dict-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="dict@test.com"
        )
        db_session.add(org)
        db_session.commit()
        
        org_dict = org.to_dict()
        
        assert org_dict["name"] == "Dict Test Org"
        assert org_dict["type"] == "buyer"
        assert org_dict["status"] == "active"
        
        db_session.delete(org)
        db_session.commit()


class TestOrganizationStatus:
    """Tests for organization status transitions."""

    def test_organization_status_values(self):
        """Should have expected status values."""
        assert OrganizationStatus.ACTIVE.value == "active"
        assert OrganizationStatus.SUSPENDED.value == "suspended"
        assert OrganizationStatus.PENDING_SETUP.value == "pending_setup"

    def test_create_pending_organization(self, db_session):
        """Should create organization in pending status."""
        org = Organization(
            name="Pending Org",
            slug=f"pending-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.PENDING_SETUP,
            contact_email="pending@test.com"
        )
        db_session.add(org)
        db_session.commit()
        
        assert org.status == OrganizationStatus.PENDING_SETUP
        
        db_session.delete(org)
        db_session.commit()

    def test_suspend_organization(self, db_session):
        """Should be able to suspend organization."""
        org = Organization(
            name="To Suspend",
            slug=f"suspend-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="suspend@test.com"
        )
        db_session.add(org)
        db_session.commit()
        
        org.status = OrganizationStatus.SUSPENDED
        db_session.commit()
        db_session.refresh(org)
        
        assert org.status == OrganizationStatus.SUSPENDED
        
        db_session.delete(org)
        db_session.commit()


class TestOrganizationType:
    """Tests for organization types."""

    def test_organization_type_values(self):
        """Should have expected type values."""
        assert OrganizationType.VIBOTAJ.value == "vibotaj"
        assert OrganizationType.BUYER.value == "buyer"
        assert OrganizationType.SUPPLIER.value == "supplier"
        assert OrganizationType.LOGISTICS_AGENT.value == "logistics_agent"

    def test_logistics_agent_organization(self, db_session):
        """Should create logistics agent organization."""
        org = Organization(
            name="Freight Forwarder Inc",
            slug=f"freight-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.LOGISTICS_AGENT,
            status=OrganizationStatus.ACTIVE,
            contact_email="freight@forwarder.com"
        )
        db_session.add(org)
        db_session.commit()
        
        assert org.type == OrganizationType.LOGISTICS_AGENT
        
        db_session.delete(org)
        db_session.commit()


class TestMultiTenancyIsolation:
    """Tests for multi-tenancy data isolation."""

    @pytest.fixture
    def org_a(self, db_session):
        """Create organization A."""
        org = Organization(
            name="Organization A",
            slug=f"org-a-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="org-a@test.com"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        yield org
        db_session.delete(org)
        db_session.commit()

    @pytest.fixture
    def org_b(self, db_session):
        """Create organization B."""
        org = Organization(
            name="Organization B",
            slug=f"org-b-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="org-b@test.com"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        yield org
        db_session.delete(org)
        db_session.commit()

    @pytest.fixture
    def user_a(self, db_session, org_a):
        """Create user for organization A."""
        user = User(
            email=f"user-a-{uuid.uuid4().hex[:6]}@test.com",
            full_name="User A",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.ADMIN,
            organization_id=org_a.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user
        db_session.delete(user)
        db_session.commit()

    @pytest.fixture
    def user_b(self, db_session, org_b):
        """Create user for organization B."""
        user = User(
            email=f"user-b-{uuid.uuid4().hex[:6]}@test.com",
            full_name="User B",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.ADMIN,
            organization_id=org_b.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user
        db_session.delete(user)
        db_session.commit()

    @pytest.fixture
    def shipment_a(self, db_session, org_a):
        """Create shipment for organization A."""
        shipment = Shipment(
            reference=f"ORG-A-{uuid.uuid4().hex[:6]}",
            container_number="ORGA1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=org_a.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)
        yield shipment
        db_session.delete(shipment)
        db_session.commit()

    @pytest.fixture
    def shipment_b(self, db_session, org_b):
        """Create shipment for organization B."""
        shipment = Shipment(
            reference=f"ORG-B-{uuid.uuid4().hex[:6]}",
            container_number="ORGB7654321",
            status=ShipmentStatus.DRAFT,
            organization_id=org_b.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(shipment)
        db_session.commit()
        db_session.refresh(shipment)
        yield shipment
        db_session.delete(shipment)
        db_session.commit()

    def test_query_filter_by_organization(
        self, db_session, org_a, org_b, shipment_a, shipment_b
    ):
        """Shipments should be filterable by organization."""
        # Query for org A
        org_a_shipments = db_session.query(Shipment).filter(
            Shipment.organization_id == org_a.id
        ).all()
        
        assert len(org_a_shipments) >= 1
        for s in org_a_shipments:
            assert s.organization_id == org_a.id
        
        # Query for org B
        org_b_shipments = db_session.query(Shipment).filter(
            Shipment.organization_id == org_b.id
        ).all()
        
        assert len(org_b_shipments) >= 1
        for s in org_b_shipments:
            assert s.organization_id == org_b.id

    def test_shipment_belongs_to_organization(
        self, db_session, org_a, shipment_a
    ):
        """Shipment should reference its organization."""
        assert shipment_a.organization_id == org_a.id


class TestOrganizationRelationships:
    """Tests for organization relationships."""

    def test_organization_has_users(self, db_session):
        """Organization should have users relationship."""
        org = Organization(
            name="Relationship Test Org",
            slug=f"rel-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="rel@test.com"
        )
        db_session.add(org)
        db_session.commit()
        
        user = User(
            email=f"rel-user-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Rel User",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.ADMIN,
            organization_id=org.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        db_session.refresh(org)
        assert len(org.users) >= 1
        assert user in org.users
        
        db_session.delete(user)
        db_session.delete(org)
        db_session.commit()

    def test_organization_has_shipments(self, db_session):
        """Organization should have shipments relationship."""
        org = Organization(
            name="Shipments Test Org",
            slug=f"ship-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="ship@test.com"
        )
        db_session.add(org)
        db_session.commit()
        
        shipment = Shipment(
            reference=f"REL-SHIP-{uuid.uuid4().hex[:6]}",
            container_number="RELS1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=org.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(shipment)
        db_session.commit()
        
        db_session.refresh(org)
        assert len(org.shipments) >= 1
        
        db_session.delete(shipment)
        db_session.delete(org)
        db_session.commit()


class TestOrganizationMembership:
    """Tests for organization membership functionality."""

    def test_create_membership(self, db_session):
        """Should create organization membership."""
        org = Organization(
            name="Membership Test Org",
            slug=f"memb-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="memb@test.com"
        )
        db_session.add(org)
        db_session.commit()
        
        user = User(
            email=f"memb-user-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Memb User",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.VIEWER,
            organization_id=org.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        membership = OrganizationMembership(
            user_id=user.id,
            organization_id=org.id,
            org_role=OrgRole.MEMBER
        )
        db_session.add(membership)
        db_session.commit()
        
        assert membership.id is not None
        assert membership.org_role == OrgRole.MEMBER
        
        db_session.delete(membership)
        db_session.delete(user)
        db_session.delete(org)
        db_session.commit()


class TestOrganizationSettings:
    """Tests for organization settings (JSON field)."""

    def test_organization_settings_json(self, db_session):
        """Should store and retrieve JSON settings."""
        org = Organization(
            name="Settings Test Org",
            slug=f"settings-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="settings@test.com",
            settings={
                "notifications_enabled": True,
                "auto_approve_documents": False,
                "default_currency": "EUR"
            }
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        
        assert org.settings["notifications_enabled"] is True
        assert org.settings["auto_approve_documents"] is False
        assert org.settings["default_currency"] == "EUR"
        
        db_session.delete(org)
        db_session.commit()

    def test_organization_address_json(self, db_session):
        """Should store and retrieve JSON address."""
        org = Organization(
            name="Address Test Org",
            slug=f"address-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="address@test.com",
            address={
                "street": "123 Main Street",
                "city": "Hamburg",
                "postal_code": "20095",
                "country": "Germany"
            }
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        
        assert org.address["city"] == "Hamburg"
        assert org.address["country"] == "Germany"

        db_session.delete(org)
        db_session.commit()


# =============================================================================
# API Endpoint Tests for Organization Management
# Tests for routes in app/routers/organizations.py
# =============================================================================

class TestOrganizationAPI:
    """Tests for organization CRUD API endpoints."""

    @pytest.fixture
    def admin_org(self, db_session):
        """Create organization for admin user."""
        org = Organization(
            name="Admin Org",
            slug=f"admin-org-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="admin@vibotaj.com"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        yield org
        # Cleanup handled by cascading deletes

    @pytest.fixture
    def admin_user(self, db_session, admin_org):
        """Create admin user."""
        user = User(
            email=f"admin-{uuid.uuid4().hex[:6]}@vibotaj.com",
            full_name="Admin User",
            hashed_password=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            organization_id=admin_org.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user

    @pytest.fixture
    def viewer_user(self, db_session, admin_org):
        """Create viewer user (non-admin)."""
        user = User(
            email=f"viewer-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Viewer User",
            hashed_password=get_password_hash("Viewer123!"),
            role=UserRole.VIEWER,
            organization_id=admin_org.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user

    @pytest.fixture
    def auth_admin_client(self, client, admin_user):
        """Client authenticated as admin."""
        permissions = [p.value for p in get_role_permissions(admin_user.role)]
        mock_user = CurrentUser(
            id=admin_user.id,
            email=admin_user.email,
            full_name=admin_user.full_name,
            role=admin_user.role,
            is_active=True,
            organization_id=admin_user.organization_id,
            permissions=permissions
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        yield client
        del app.dependency_overrides[get_current_active_user]

    @pytest.fixture
    def auth_viewer_client(self, client, viewer_user):
        """Client authenticated as viewer (non-admin)."""
        permissions = [p.value for p in get_role_permissions(viewer_user.role)]
        mock_user = CurrentUser(
            id=viewer_user.id,
            email=viewer_user.email,
            full_name=viewer_user.full_name,
            role=viewer_user.role,
            is_active=True,
            organization_id=viewer_user.organization_id,
            permissions=permissions
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        yield client
        del app.dependency_overrides[get_current_active_user]

    def test_create_organization_as_admin(self, auth_admin_client):
        """Admin should be able to create organization."""
        org_data = {
            "name": "New Test Buyer",
            "slug": f"new-buyer-{uuid.uuid4().hex[:6]}",
            "type": "buyer",
            "contact_email": "new@buyer.com"
        }
        response = auth_admin_client.post("/api/organizations", json=org_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == org_data["name"]
        assert data["slug"] == org_data["slug"]
        assert data["type"] == "buyer"
        assert data["status"] == "active"

    def test_create_organization_as_viewer_forbidden(self, auth_viewer_client):
        """Non-admin should not be able to create organization."""
        org_data = {
            "name": "Forbidden Org",
            "slug": f"forbidden-{uuid.uuid4().hex[:6]}",
            "type": "buyer",
            "contact_email": "forbidden@test.com"
        }
        response = auth_viewer_client.post("/api/organizations", json=org_data)
        assert response.status_code == 403

    def test_create_organization_duplicate_slug(self, auth_admin_client, db_session):
        """Duplicate slug should fail."""
        # First org
        unique_slug = f"dup-slug-{uuid.uuid4().hex[:6]}"
        org_data = {
            "name": "First Org",
            "slug": unique_slug,
            "type": "buyer",
            "contact_email": "first@test.com"
        }
        response = auth_admin_client.post("/api/organizations", json=org_data)
        assert response.status_code == 201

        # Duplicate slug
        org_data2 = {
            "name": "Second Org",
            "slug": unique_slug,
            "type": "supplier",
            "contact_email": "second@test.com"
        }
        response = auth_admin_client.post("/api/organizations", json=org_data2)
        assert response.status_code == 400

    def test_list_organizations(self, auth_admin_client):
        """Should list organizations with pagination."""
        response = auth_admin_client.get("/api/organizations")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_list_organizations_filter_by_type(self, auth_admin_client, db_session):
        """Should filter organizations by type."""
        # Create a buyer org
        buyer_org = Organization(
            name="Filter Test Buyer",
            slug=f"filter-buyer-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="filter@buyer.com"
        )
        db_session.add(buyer_org)
        db_session.commit()

        response = auth_admin_client.get("/api/organizations?type=buyer")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["type"] == "buyer"

    def test_list_organizations_search(self, auth_admin_client, db_session):
        """Should search organizations by name."""
        # Create org with unique name
        search_name = f"Searchable-{uuid.uuid4().hex[:6]}"
        org = Organization(
            name=search_name,
            slug=f"search-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="search@test.com"
        )
        db_session.add(org)
        db_session.commit()

        response = auth_admin_client.get(f"/api/organizations?search={search_name[:10]}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    def test_get_organization(self, auth_admin_client, db_session):
        """Should get organization by ID."""
        org = Organization(
            name="Get Test Org",
            slug=f"get-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="get@test.com"
        )
        db_session.add(org)
        db_session.commit()

        response = auth_admin_client.get(f"/api/organizations/{org.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(org.id)
        assert data["name"] == org.name

    def test_get_organization_not_found(self, auth_admin_client):
        """Should return 404 for non-existent organization."""
        fake_id = str(uuid.uuid4())
        response = auth_admin_client.get(f"/api/organizations/{fake_id}")
        assert response.status_code == 404

    def test_update_organization(self, auth_admin_client, db_session):
        """Should update organization."""
        org = Organization(
            name="Update Test Org",
            slug=f"update-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="update@test.com"
        )
        db_session.add(org)
        db_session.commit()

        update_data = {"name": "Updated Name", "contact_email": "updated@test.com"}
        response = auth_admin_client.patch(f"/api/organizations/{org.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["contact_email"] == "updated@test.com"


class TestOrganizationMembershipAPI:
    """Tests for organization membership API endpoints."""

    @pytest.fixture
    def admin_org(self, db_session):
        """Create organization for admin user."""
        org = Organization(
            name="Member API Org",
            slug=f"memb-api-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="membapi@vibotaj.com"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        yield org

    @pytest.fixture
    def target_org(self, db_session):
        """Create target organization for membership tests."""
        org = Organization(
            name="Target Org for Members",
            slug=f"target-org-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="target@test.com"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        yield org

    @pytest.fixture
    def admin_user(self, db_session, admin_org):
        """Create admin user."""
        user = User(
            email=f"memb-admin-{uuid.uuid4().hex[:6]}@vibotaj.com",
            full_name="Member Admin",
            hashed_password=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            organization_id=admin_org.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user

    @pytest.fixture
    def test_user(self, db_session, admin_org):
        """Create test user to add as member."""
        user = User(
            email=f"test-memb-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Test Member User",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=admin_org.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user

    @pytest.fixture
    def auth_admin_client(self, client, admin_user):
        """Client authenticated as admin."""
        permissions = [p.value for p in get_role_permissions(admin_user.role)]
        mock_user = CurrentUser(
            id=admin_user.id,
            email=admin_user.email,
            full_name=admin_user.full_name,
            role=admin_user.role,
            is_active=True,
            organization_id=admin_user.organization_id,
            permissions=permissions
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        yield client
        del app.dependency_overrides[get_current_active_user]

    def test_add_member_to_organization(self, auth_admin_client, target_org, test_user):
        """Should add user as member to organization."""
        member_data = {
            "user_id": str(test_user.id),
            "org_role": "member"
        }
        response = auth_admin_client.post(
            f"/api/organizations/{target_org.id}/members",
            json=member_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert data["organization_id"] == str(target_org.id)
        assert data["org_role"] == "member"

    def test_add_member_duplicate(self, auth_admin_client, target_org, test_user, db_session):
        """Should not add duplicate member."""
        # Add member first
        membership = OrganizationMembership(
            user_id=test_user.id,
            organization_id=target_org.id,
            org_role=OrgRole.MEMBER
        )
        db_session.add(membership)
        db_session.commit()

        # Try to add again
        member_data = {
            "user_id": str(test_user.id),
            "org_role": "admin"
        }
        response = auth_admin_client.post(
            f"/api/organizations/{target_org.id}/members",
            json=member_data
        )
        assert response.status_code == 400

    def test_list_organization_members(self, auth_admin_client, target_org, test_user, db_session):
        """Should list organization members."""
        # Add member
        membership = OrganizationMembership(
            user_id=test_user.id,
            organization_id=target_org.id,
            org_role=OrgRole.MEMBER
        )
        db_session.add(membership)
        db_session.commit()

        response = auth_admin_client.get(f"/api/organizations/{target_org.id}/members")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_remove_member_from_organization(self, auth_admin_client, target_org, test_user, db_session):
        """Should remove member from organization."""
        # Add member first
        membership = OrganizationMembership(
            user_id=test_user.id,
            organization_id=target_org.id,
            org_role=OrgRole.MEMBER
        )
        db_session.add(membership)
        db_session.commit()

        response = auth_admin_client.delete(
            f"/api/organizations/{target_org.id}/members/{test_user.id}"
        )
        assert response.status_code == 204

    def test_update_member_role(self, auth_admin_client, target_org, test_user, db_session):
        """Should update member role."""
        # Add member first
        membership = OrganizationMembership(
            user_id=test_user.id,
            organization_id=target_org.id,
            org_role=OrgRole.MEMBER
        )
        db_session.add(membership)
        db_session.commit()

        update_data = {"org_role": "admin"}
        response = auth_admin_client.patch(
            f"/api/organizations/{target_org.id}/members/{test_user.id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["org_role"] == "admin"


class TestOrganizationPermissions:
    """Tests for organization API permission checks."""

    @pytest.fixture
    def vibotaj_org(self, db_session):
        """Create VIBOTAJ organization."""
        org = Organization(
            name="Perm Test VIBOTAJ",
            slug=f"perm-vibotaj-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="perm@vibotaj.com"
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        yield org

    @pytest.fixture
    def compliance_user(self, db_session, vibotaj_org):
        """Create compliance user (not admin)."""
        user = User(
            email=f"compliance-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Compliance User",
            hashed_password=get_password_hash("Compliance123!"),
            role=UserRole.COMPLIANCE,
            organization_id=vibotaj_org.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user

    @pytest.fixture
    def auth_compliance_client(self, client, compliance_user):
        """Client authenticated as compliance user."""
        permissions = [p.value for p in get_role_permissions(compliance_user.role)]
        mock_user = CurrentUser(
            id=compliance_user.id,
            email=compliance_user.email,
            full_name=compliance_user.full_name,
            role=compliance_user.role,
            is_active=True,
            organization_id=compliance_user.organization_id,
            permissions=permissions
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        yield client
        del app.dependency_overrides[get_current_active_user]

    def test_compliance_cannot_create_organization(self, auth_compliance_client):
        """Compliance user should not be able to create organizations."""
        org_data = {
            "name": "Unauthorized Org",
            "slug": f"unauth-{uuid.uuid4().hex[:6]}",
            "type": "buyer",
            "contact_email": "unauth@test.com"
        }
        response = auth_compliance_client.post("/api/organizations", json=org_data)
        assert response.status_code == 403

    def test_compliance_cannot_add_members(self, auth_compliance_client, vibotaj_org):
        """Compliance user should not be able to add organization members."""
        member_data = {
            "user_id": str(uuid.uuid4()),
            "org_role": "member"
        }
        response = auth_compliance_client.post(
            f"/api/organizations/{vibotaj_org.id}/members",
            json=member_data
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_access(self, db_session):
        """Unauthenticated requests should be rejected."""
        # Create a fresh client without auth overrides
        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        # Store existing overrides and clear them
        saved_overrides = dict(app.dependency_overrides)
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = override_get_db

        unauth_client = TestClient(app)
        response = unauth_client.get("/api/organizations")
        assert response.status_code == 401

        # Restore overrides
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved_overrides)


class TestOrganizationDeletion:
    """Tests for organization deletion endpoint."""

    @pytest.fixture
    def admin_user_and_client(self, db_session, client):
        """Create admin user and authenticated client."""
        org = Organization(
            name="Admin Test Org",
            slug=f"admin-test-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="admin@test.com"
        )
        db_session.add(org)
        db_session.commit()

        admin = User(
            email=f"admin-delete-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Admin User",
            hashed_password=get_password_hash("test123"),
            role=UserRole.ADMIN,
            is_active=True,
            organization_id=org.id
        )
        db_session.add(admin)
        db_session.commit()

        permissions = get_role_permissions(UserRole.ADMIN)
        mock_user = CurrentUser(
            id=admin.id,
            email=admin.email,
            full_name=admin.full_name,
            role=UserRole.ADMIN,
            is_active=True,
            organization_id=org.id,
            permissions=permissions
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        yield {"user": admin, "org": org, "client": client}
        del app.dependency_overrides[get_current_active_user]
        
        # Cleanup
        db_session.delete(admin)
        db_session.delete(org)
        db_session.commit()

    @pytest.fixture
    def deletable_org(self, db_session):
        """Create an organization that can be deleted."""
        org = Organization(
            name="Deletable Org",
            slug=f"deletable-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="delete@test.com"
        )
        db_session.add(org)
        db_session.commit()
        yield org
        # May already be deleted, so check first
        existing = db_session.get(Organization, org.id)
        if existing:
            db_session.delete(existing)
            db_session.commit()

    def test_delete_organization_success(self, admin_user_and_client, deletable_org, db_session):
        """Should successfully soft-delete an organization."""
        client = admin_user_and_client["client"]
        
        response = client.delete(
            f"/api/organizations/{deletable_org.id}?reason=No longer needed for testing purposes"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == deletable_org.slug
        assert data["name"] == deletable_org.name
        assert "suspended" in data["message"].lower() or deletable_org.name in data["message"]
        assert data["members_affected"] == 0
        
        # Verify status changed
        db_session.refresh(deletable_org)
        assert deletable_org.status == OrganizationStatus.SUSPENDED

    def test_delete_organization_not_found(self, admin_user_and_client):
        """Should return 404 for non-existent organization."""
        client = admin_user_and_client["client"]
        fake_id = uuid.uuid4()
        
        response = client.delete(
            f"/api/organizations/{fake_id}?reason=Testing non-existent organization"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_vibotaj_organization_forbidden(self, admin_user_and_client, db_session):
        """Should not allow deletion of VIBOTAJ organization."""
        client = admin_user_and_client["client"]
        
        # Create a VIBOTAJ org
        vibotaj_org = Organization(
            name="VIBOTAJ Protected",
            slug=f"vibotaj-prot-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="protected@vibotaj.com"
        )
        db_session.add(vibotaj_org)
        db_session.commit()
        
        response = client.delete(
            f"/api/organizations/{vibotaj_org.id}?reason=Testing deletion of VIBOTAJ org"
        )
        
        assert response.status_code == 400
        assert "VIBOTAJ" in response.json()["detail"]
        
        # Cleanup
        db_session.delete(vibotaj_org)
        db_session.commit()

    def test_delete_organization_with_shipments_forbidden(self, admin_user_and_client, db_session):
        """Should not allow deletion of organization with active shipments."""
        client = admin_user_and_client["client"]
        
        # Create an org with a shipment
        org_with_shipments = Organization(
            name="Org With Shipments",
            slug=f"org-ships-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="ships@test.com"
        )
        db_session.add(org_with_shipments)
        db_session.commit()
        
        # Create a shipment for this org
        shipment = Shipment(
            reference=f"TEST-{uuid.uuid4().hex[:6]}",
            status=ShipmentStatus.IN_TRANSIT,
            organization_id=org_with_shipments.id
        )
        db_session.add(shipment)
        db_session.commit()
        
        response = client.delete(
            f"/api/organizations/{org_with_shipments.id}?reason=Testing deletion with shipments"
        )
        
        assert response.status_code == 400
        assert "shipment" in response.json()["detail"].lower()
        
        # Cleanup
        db_session.delete(shipment)
        db_session.delete(org_with_shipments)
        db_session.commit()

    def test_delete_organization_reason_required(self, admin_user_and_client, deletable_org):
        """Should require a reason for deletion."""
        client = admin_user_and_client["client"]
        
        # No reason parameter
        response = client.delete(f"/api/organizations/{deletable_org.id}")
        assert response.status_code == 422  # Validation error

    def test_delete_organization_reason_too_short(self, admin_user_and_client, deletable_org):
        """Should require reason to be at least 10 characters."""
        client = admin_user_and_client["client"]
        
        response = client.delete(
            f"/api/organizations/{deletable_org.id}?reason=short"
        )
        assert response.status_code == 422  # Validation error

    def test_delete_organization_deactivates_members(self, admin_user_and_client, db_session):
        """Should deactivate all organization members on deletion."""
        client = admin_user_and_client["client"]
        
        # Create org with members
        org = Organization(
            name="Org With Members",
            slug=f"org-members-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="members@test.com"
        )
        db_session.add(org)
        db_session.commit()
        
        # Create test user
        test_user = User(
            email=f"member-test-{uuid.uuid4().hex[:6]}@test.com",
            full_name="Test Member",
            hashed_password=get_password_hash("test123"),
            role=UserRole.BUYER,
            is_active=True,
            organization_id=org.id
        )
        db_session.add(test_user)
        db_session.commit()
        
        # Create membership
        from app.models.organization import MembershipStatus
        membership = OrganizationMembership(
            user_id=test_user.id,
            organization_id=org.id,
            org_role=OrgRole.MEMBER,
            status=MembershipStatus.ACTIVE,
            is_primary=True,
            joined_at=datetime.utcnow()
        )
        db_session.add(membership)
        db_session.commit()
        
        response = client.delete(
            f"/api/organizations/{org.id}?reason=Testing member deactivation on org delete"
        )
        
        assert response.status_code == 200
        assert response.json()["members_affected"] == 1
        
        # Verify membership is suspended
        db_session.refresh(membership)
        assert membership.status == MembershipStatus.SUSPENDED
        
        # Cleanup
        db_session.delete(membership)
        db_session.delete(test_user)
        db_session.delete(org)
        db_session.commit()
