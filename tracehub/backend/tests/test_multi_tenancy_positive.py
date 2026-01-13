
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models.shipment import Shipment, ShipmentStatus, ProductType
from app.models.document import Document, DocumentType, DocumentStatus
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions
from app.models.organization import OrgRole

from .conftest import engine, TestingSessionLocal, Base

@pytest.fixture(scope="module")
def db_session():
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
    org = Organization(
        name="VIBOTAJ Positive Test",
        slug="vibotaj-pos",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="pos@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture(scope="module")
def vibotaj_user(db_session, org_vibotaj):
    user = User(
        email="pos@vibotaj.com",
        full_name="VIBOTAJ Positive",
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
def vibotaj_shipment(db_session, org_vibotaj):
    shipment = Shipment(
        reference=f"POS-{uuid.uuid4().hex[:6]}",
        container_number="POS1234567",
        organization_id=org_vibotaj.id,
        status=ShipmentStatus.DRAFT,
        product_type=ProductType.HORN_HOOF
    )
    db_session.add(shipment)
    db_session.commit()
    return shipment

@pytest.fixture(scope="module")
def vibotaj_document(db_session, vibotaj_shipment, org_vibotaj):
    # SEC-001 fix: Documents MUST have organization_id set for proper multi-tenancy isolation.
    # The upload endpoint now sets organization_id from current_user.organization_id.
    doc = Document(
        shipment_id=vibotaj_shipment.id,
        name="Positive Test Doc",
        document_type=DocumentType.BILL_OF_LADING,
        status=DocumentStatus.UPLOADED,
        file_name="pos.pdf",
        organization_id=org_vibotaj.id  # SEC-001: Required for document visibility
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc

def create_mock_current_user(user: User) -> CurrentUser:
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
        org_type=OrganizationType.VIBOTAJ,
        org_permissions=[]
    )

@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

def test_vibotaj_user_can_access_own_document(client, vibotaj_user, vibotaj_document):
    """Test that a user CAN see their own document (Positive Test)."""
    app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)
    
    # Try to get the document
    response = client.get(f"/api/documents/{vibotaj_document.id}")
    
    # If this returns 404, then we have a bug: Users can't see their own docs because organization_id is missing/mismatched
    assert response.status_code == 200, f"Failed to access own document. Status: {response.status_code}, Response: {response.json()}"
