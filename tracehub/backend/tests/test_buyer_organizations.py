"""
Tests for GET /api/organizations/buyers endpoint.

TDD Red Phase: These tests should FAIL initially until the endpoint is implemented.

The endpoint should:
- List all organizations with type=BUYER
- Require authentication
- Return a list of OrganizationInfo objects (id, name, slug, type)
- Be ordered alphabetically by name

Sprint 9: Shipment Creation - Phase 3 (Buyer Selection)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import (
    Organization, OrganizationType, OrganizationStatus,
    OrganizationMembership, OrgRole
)
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions

# Import shared test database configuration from conftest
from .conftest import engine, TestingSessionLocal, Base, create_mock_auth


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
def vibotaj_org(db_session):
    """Create the VIBOTAJ organization - platform owner."""
    org = Organization(
        name="VIBOTAJ Global",
        slug=f"vibotaj-test-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="test@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org  # No cleanup - schema dropped at module start


@pytest.fixture(scope="module")
def supplier_org(db_session):
    """Create a SUPPLIER organization."""
    org = Organization(
        name="Nigerian Supplier Ltd",
        slug=f"ng-supplier-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.SUPPLIER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@ng-supplier.ng"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org  # No cleanup - schema dropped at module start


@pytest.fixture(scope="module")
def buyer_hages(db_session):
    """Create HAGES - a German buyer organization."""
    org = Organization(
        name="HAGES GmbH",
        slug=f"hages-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org  # No cleanup - schema dropped at module start


@pytest.fixture(scope="module")
def buyer_witatrade(db_session):
    """Create Witatrade - another German buyer organization."""
    org = Organization(
        name="Witatrade GmbH",
        slug=f"witatrade-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@witatrade.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org  # No cleanup - schema dropped at module start


@pytest.fixture(scope="module")
def buyer_beckman(db_session):
    """Create Beckman GBH - another German buyer organization."""
    org = Organization(
        name="Beckman GBH",
        slug=f"beckman-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@beckman.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org  # No cleanup - schema dropped at module start


@pytest.fixture(scope="module")
def vibotaj_admin(db_session, vibotaj_org):
    """Create an admin user for VIBOTAJ."""
    user = User(
        email=f"admin-{uuid.uuid4().hex[:6]}@vibotaj.com",
        full_name="VIBOTAJ Admin",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=vibotaj_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create organization membership
    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=vibotaj_org.id,
        org_role=OrgRole.ADMIN,
        is_primary=True
    )
    db_session.add(membership)
    db_session.commit()

    return user  # No cleanup - schema dropped at module start


class TestBuyerOrganizationsEndpoint:
    """Tests for GET /api/organizations/buyers endpoint."""

    def test_get_buyer_organizations_returns_only_buyers(
        self, client, db_session, vibotaj_org, vibotaj_admin,
        buyer_hages, buyer_witatrade, buyer_beckman, supplier_org
    ):
        """Should only return organizations with type=BUYER."""
        # Override authentication
        mock_user = create_mock_auth(vibotaj_admin)
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        try:
            response = client.get("/api/organizations/buyers")

            assert response.status_code == 200
            data = response.json()

            # Should be a list of organizations
            assert isinstance(data, list)

            # All returned organizations should be BUYER type
            for org in data:
                assert org["type"] == "buyer"

            # Should include our buyer organizations
            org_names = [org["name"] for org in data]
            assert "HAGES GmbH" in org_names
            assert "Witatrade GmbH" in org_names
            assert "Beckman GBH" in org_names

        finally:
            del app.dependency_overrides[get_current_active_user]

    def test_get_buyer_organizations_excludes_vibotaj(
        self, client, db_session, vibotaj_org, vibotaj_admin, buyer_hages
    ):
        """Should not return VIBOTAJ type organizations."""
        mock_user = create_mock_auth(vibotaj_admin)
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        try:
            response = client.get("/api/organizations/buyers")

            assert response.status_code == 200
            data = response.json()

            # No VIBOTAJ organizations should be in the response
            for org in data:
                assert org["type"] != "vibotaj"

            # Specifically check our VIBOTAJ org is not included
            org_ids = [org["id"] for org in data]
            assert str(vibotaj_org.id) not in org_ids

        finally:
            del app.dependency_overrides[get_current_active_user]

    def test_get_buyer_organizations_excludes_suppliers(
        self, client, db_session, vibotaj_admin, supplier_org, buyer_hages
    ):
        """Should not return SUPPLIER type organizations."""
        mock_user = create_mock_auth(vibotaj_admin)
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        try:
            response = client.get("/api/organizations/buyers")

            assert response.status_code == 200
            data = response.json()

            # No SUPPLIER organizations should be in the response
            for org in data:
                assert org["type"] != "supplier"

            # Specifically check our supplier org is not included
            org_ids = [org["id"] for org in data]
            assert str(supplier_org.id) not in org_ids

        finally:
            del app.dependency_overrides[get_current_active_user]

    def test_get_buyer_organizations_requires_authentication(self, client, db_session):
        """Should return 401 without authentication."""
        # Ensure no auth override is active
        if get_current_active_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_active_user]

        response = client.get("/api/organizations/buyers")

        # Should require authentication
        assert response.status_code == 401

    def test_get_buyer_organizations_empty_when_no_buyers(self, client, db_session):
        """Should return empty list if no buyers exist."""
        # Create a fresh DB state with only non-buyer orgs
        # First, delete all existing orgs
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM organization_memberships"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("DELETE FROM organizations"))
            conn.commit()

        # Create only a VIBOTAJ org and user
        vibotaj = Organization(
            name="VIBOTAJ Only",
            slug=f"vibotaj-only-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="only@vibotaj.com"
        )
        db_session.add(vibotaj)
        db_session.commit()
        db_session.refresh(vibotaj)

        user = User(
            email=f"user-only-{uuid.uuid4().hex[:6]}@vibotaj.com",
            full_name="Only User",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.ADMIN,
            organization_id=vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        mock_user = create_mock_auth(user)
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        try:
            response = client.get("/api/organizations/buyers")

            assert response.status_code == 200
            data = response.json()

            # Should return empty list
            assert isinstance(data, list)
            assert len(data) == 0

        finally:
            del app.dependency_overrides[get_current_active_user]
            db_session.delete(user)
            db_session.delete(vibotaj)
            db_session.commit()

    def test_get_buyer_organizations_response_schema(
        self, client, db_session, vibotaj_admin, buyer_hages
    ):
        """Response should match OrganizationInfo schema (id, name, slug, type)."""
        # Recreate the buyer org if it was deleted
        buyer = Organization(
            name="Schema Test Buyer",
            slug=f"schema-buyer-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="schema@buyer.de"
        )
        db_session.add(buyer)
        db_session.commit()
        db_session.refresh(buyer)

        # Also recreate the admin user and their org
        vibotaj = Organization(
            name="VIBOTAJ Schema Test",
            slug=f"vibotaj-schema-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="schema@vibotaj.com"
        )
        db_session.add(vibotaj)
        db_session.commit()
        db_session.refresh(vibotaj)

        user = User(
            email=f"schema-user-{uuid.uuid4().hex[:6]}@vibotaj.com",
            full_name="Schema Test User",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.ADMIN,
            organization_id=vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        mock_user = create_mock_auth(user)
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        try:
            response = client.get("/api/organizations/buyers")

            assert response.status_code == 200
            data = response.json()

            # Should have at least one buyer
            assert len(data) > 0

            # Check that each organization has the required fields
            for org in data:
                # Required fields per OrganizationInfo schema
                assert "id" in org
                assert "name" in org
                assert "slug" in org
                assert "type" in org

                # Validate field types
                assert isinstance(org["id"], str)  # UUID as string
                assert isinstance(org["name"], str)
                assert isinstance(org["slug"], str)
                assert org["type"] == "buyer"

        finally:
            del app.dependency_overrides[get_current_active_user]
            db_session.delete(user)
            db_session.delete(vibotaj)
            db_session.delete(buyer)
            db_session.commit()


class TestBuyerOrganizationsOrdering:
    """Tests for ordering of buyer organizations."""

    def test_buyer_organizations_ordered_by_name(self, client, db_session):
        """Should return buyers alphabetically ordered by name."""
        # Clean up any existing data
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM organization_memberships"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("DELETE FROM organizations"))
            conn.commit()

        # Create a VIBOTAJ org for the admin user
        vibotaj = Organization(
            name="VIBOTAJ Order Test",
            slug=f"vibotaj-order-{uuid.uuid4().hex[:6]}",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="order@vibotaj.com"
        )
        db_session.add(vibotaj)
        db_session.commit()
        db_session.refresh(vibotaj)

        # Create admin user
        user = User(
            email=f"order-user-{uuid.uuid4().hex[:6]}@vibotaj.com",
            full_name="Order Test User",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.ADMIN,
            organization_id=vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create buyers in non-alphabetical order to test sorting
        buyers_data = [
            ("Zebra Trading", "zebra"),
            ("Alpha Corp", "alpha"),
            ("Mega Import", "mega"),
            ("Beta GmbH", "beta"),
        ]

        created_buyers = []
        for name, slug_prefix in buyers_data:
            buyer = Organization(
                name=name,
                slug=f"{slug_prefix}-{uuid.uuid4().hex[:6]}",
                type=OrganizationType.BUYER,
                status=OrganizationStatus.ACTIVE,
                contact_email=f"info@{slug_prefix}.de"
            )
            db_session.add(buyer)
            created_buyers.append(buyer)

        db_session.commit()
        for buyer in created_buyers:
            db_session.refresh(buyer)

        mock_user = create_mock_auth(user)
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        try:
            response = client.get("/api/organizations/buyers")

            assert response.status_code == 200
            data = response.json()

            # Should have 4 buyers
            assert len(data) == 4

            # Extract names in order returned
            returned_names = [org["name"] for org in data]

            # Should be alphabetically sorted
            expected_order = ["Alpha Corp", "Beta GmbH", "Mega Import", "Zebra Trading"]
            assert returned_names == expected_order

        finally:
            del app.dependency_overrides[get_current_active_user]
            for buyer in created_buyers:
                db_session.delete(buyer)
            db_session.delete(user)
            db_session.delete(vibotaj)
            db_session.commit()
