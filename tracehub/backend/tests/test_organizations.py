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
