
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import uuid
from datetime import datetime

from app.main import app
from app.database import get_db
from app.models import (
    User, UserRole,
    Organization, OrganizationType, OrganizationStatus, OrgRole,
    Shipment, ShipmentStatus, ProductType,
    Document, DocumentType, DocumentStatus,
    Product,
    ContainerEvent, EventType
)
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
        name="VIBOTAJ Delete Test",
        slug="vibotaj-del",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="del@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture(scope="module")
def vibotaj_user(db_session, org_vibotaj):
    user = User(
        email="del@vibotaj.com",
        full_name="VIBOTAJ Delete",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

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

def test_delete_shipment_with_dependencies(client, db_session, vibotaj_user, org_vibotaj):
    """Test deleting a shipment that has related products, documents, and events (repro TICKET-007)."""
    app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(vibotaj_user)
    
    # 1. Create a shipment with dependencies
    shipment = Shipment(
        reference=f"DEL-{uuid.uuid4().hex[:6]}",
        container_number="DEL1234567",
        organization_id=org_vibotaj.id,
        status=ShipmentStatus.DRAFT,
        product_type=ProductType.HORN_HOOF
    )
    db_session.add(shipment)
    db_session.commit()
    
    # Add a product
    product = Product(
        shipment_id=shipment.id,
        hs_code="0506",
        description="Test Product",
        quantity_net_kg=1000,
        quantity_gross_kg=1100
    )
    db_session.add(product)
    
    # Add a document
    doc = Document(
        shipment_id=shipment.id,
        organization_id=org_vibotaj.id,
        name="Test Doc",
        document_type=DocumentType.BILL_OF_LADING,
        status=DocumentStatus.UPLOADED
    )
    db_session.add(doc)
    
    # Add an event
    event = ContainerEvent(
        shipment_id=shipment.id,
        event_type=EventType.LOADED,
        event_time=datetime.utcnow(),
        description="Loaded"
    )
    db_session.add(event)
    
    db_session.commit()
    
    # Verify creation
    assert db_session.query(Shipment).filter_by(id=shipment.id).first() is not None
    assert db_session.query(Product).filter_by(shipment_id=shipment.id).first() is not None
    assert db_session.query(Document).filter_by(shipment_id=shipment.id).first() is not None
    
    # 2. Try to delete via API
    response = client.delete(f"/api/shipments/{shipment.id}")
    
    # 3. Assert success (204 No Content)
    assert response.status_code == 204, f"Delete failed: {response.status_code} - {response.text}"
    
    # 4. Verify deletion in DB
    assert db_session.query(Shipment).filter_by(id=shipment.id).first() is None
    assert db_session.query(Product).filter_by(shipment_id=shipment.id).first() is None
    assert db_session.query(Document).filter_by(shipment_id=shipment.id).first() is None
    assert db_session.query(ContainerEvent).filter_by(shipment_id=shipment.id).first() is None
