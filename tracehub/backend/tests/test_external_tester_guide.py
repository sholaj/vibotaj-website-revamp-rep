"""
Tests based on the External Tester Guide (tracehub/docs/EXTERNAL_TESTER_GUIDE.md).

These tests automate end-to-end scenarios described in the user guide to ensure
user stories work as expected.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import uuid
from datetime import datetime

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus, OrgRole
from app.models.shipment import Shipment, ShipmentStatus, ProductType
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions

# Import shared test database configuration
from .conftest import engine, TestingSessionLocal, Base

# NOTE: We are re-declaring fixtures here to be self-contained for this specific scenario,
# closely matching the exact data described in "Scenario 2: Multi-Organization Isolation".

@pytest.fixture(scope="module")
def db_session():
    """Create fresh test database session."""
    # Check if we are using SQLite
    is_sqlite = "sqlite" in str(engine.url)
    
    with engine.connect() as conn:
        if not is_sqlite:
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
    """Scenario 2: VIBOTAJ (Exporter) Organization."""
    org = Organization(
        name="VIBOTAJ Global",
        slug=f"vibotaj-scen2-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="shola@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    return org

@pytest.fixture(scope="module")
def hages_org(db_session):
    """Scenario 2: HAGES (Buyer) Organization."""
    org = Organization(
        name="HAGES GmbH",
        slug=f"hages-scen2-{uuid.uuid4().hex[:6]}",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="helge.bischoff@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    return org

@pytest.fixture(scope="module")
def vibotaj_admin(db_session, vibotaj_org):
    """Scenario 2: VIBOTAJ Admin user."""
    user = User(
        email="admin@vibotaj.com",
        full_name="VIBOTAJ Admin",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=vibotaj_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="module")
def hages_buyer(db_session, hages_org):
    """Scenario 2: HAGES Buyer user."""
    user = User(
        email="helge.bischoff@hages.de",
        full_name="Helge Bischoff",
        hashed_password=get_password_hash("Hages2026Helge!"),
        role=UserRole.BUYER, # Using BUYER role as per guide implication (though guide says 'Owner' which might be Admin locally)
        organization_id=hages_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

def create_mock_current_user(user: User, org_type: OrganizationType = OrganizationType.VIBOTAJ) -> CurrentUser:
    """Helper to mock authentication."""
    permissions = [p.value for p in get_role_permissions(user.role)]
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        permissions=permissions,
        org_role=OrgRole.ADMIN, # Assuming Admin-level access within Org for simplicity
        org_type=org_type,
        org_permissions=[]
    )

@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Clean up dependency overrides after each test."""
    yield
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

class TestScenario2_MultiOrganizationIsolation:
    """
    Scenario 2: Multi-Organization Isolation
    
    1. VIBOTAJ Admin creates shipment "INTERNAL-001" (no buyer assigned).
    2. VIBOTAJ Admin creates shipment "HAGES-001" (HAGES as buyer).
    3. HAGES Buyer logs in.
    4. HAGES Buyer should see only "HAGES-001".
    5. HAGES Buyer should NOT see "INTERNAL-001".
    6. HAGES Buyer tries direct URL to "INTERNAL-001" -> Should get 404.
    """

    def test_multi_organization_isolation(
        self, client, db_session, vibotaj_org, hages_org, vibotaj_admin, hages_buyer
    ):
        # 1. VIBOTAJ Admin creates shipment "INTERNAL-001" (no buyer assigned)
        internal_shipment = Shipment(
            reference="INTERNAL-001",
            container_number="INT1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=vibotaj_org.id,
            product_type=ProductType.HORN_HOOF,
            # buyer_organization_id is None
        )
        db_session.add(internal_shipment)
        
        # 2. VIBOTAJ Admin creates shipment "HAGES-001" (HAGES as buyer)
        hages_shipment = Shipment(
            reference="HAGES-001",
            container_number="HAG1234567",
            status=ShipmentStatus.DRAFT,
            organization_id=vibotaj_org.id, # Created by VIBOTAJ
            product_type=ProductType.HORN_HOOF,
            buyer_organization_id=hages_org.id # Assigned to HAGES
        )
        db_session.add(hages_shipment)
        db_session.commit()
        
        # 3. HAGES Buyer logs in
        # We mock the auth dependency to simulate login
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(hages_buyer, OrganizationType.BUYER)
        
        # 4. HAGES Buyer calls GET /api/shipments
        response = client.get("/api/shipments")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        
        shipments = response.json()
        if isinstance(shipments, dict) and "items" in shipments:
             shipments = shipments["items"]
             
        shipment_refs = [s["reference"] for s in shipments]
        
        # 5. HAGES Buyer should see "HAGES-001"
        assert "HAGES-001" in shipment_refs, "Assignments to Buyer should be visible to Buyer"
        
        # 6. HAGES Buyer should NOT see "INTERNAL-001"
        assert "INTERNAL-001" not in shipment_refs, "Internal VIBOTAJ shipments should NOT be visible to Buyer"
        
        # 7. HAGES Buyer tries direct URL to "INTERNAL-001" -> Should get 404
        # Note: We use the ID because API routes usually use ID, not reference
        response_direct = client.get(f"/api/shipments/{internal_shipment.id}")
        assert response_direct.status_code == 404, f"Direct access to internal shipment should be 404, got {response_direct.status_code}"

