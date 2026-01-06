import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models import OrganizationMembership, OrgRole
from app.routers.auth import get_current_active_user, get_password_hash
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions
import uuid

# Use Postgres for testing
SQLALCHEMY_DATABASE_URL = "postgresql://tracehub:tracehub@localhost:5433/tracehub_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    # Setup: Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    # Teardown: Close and drop with CASCADE to handle circular dependencies
    db.close()
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS container_events CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS document_contents CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS origins CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS products CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS shipments CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS organization_memberships CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS invitations CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS organizations CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS parties CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS reference_registry CASCADE"))
        conn.commit()

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
        name="VIBOTAJ HQ",
        slug="vibotaj",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="hq@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture(scope="module")
def org_witatrade(db_session):
    org = Organization(
        name="WITATRADE",
        slug="witatrade",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="info@witatrade.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture(scope="module")
def admin_vibotaj(db_session, org_vibotaj):
    user = User(
        email="admin@vibotaj.com",
        full_name="Vibotaj Admin",
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
def admin_witatrade(db_session, org_witatrade):
    user = User(
        email="admin@witatrade.de",
        full_name="Witatrade Admin",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=org_witatrade.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def mock_auth(user):
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

def test_admin_create_user(client, admin_vibotaj):
    app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_vibotaj)
    
    user_data = {
        "email": "new_compliance@vibotaj.com",
        "full_name": "New Compliance",
        "password": "Password123!",
        "role": "compliance"
    }
    
    response = client.post("/api/users", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["role"] == "compliance"
    
    del app.dependency_overrides[get_current_active_user]

def test_org_isolation_list(client, admin_vibotaj, admin_witatrade):
    # As Vibotaj Admin
    app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_vibotaj)
    response = client.get("/api/users")
    assert response.status_code == 200
    vibotaj_users = response.json()["items"]
    assert any(u["email"] == admin_vibotaj.email for u in vibotaj_users)
    assert not any(u["email"] == admin_witatrade.email for u in vibotaj_users)
    
    # As Witatrade Admin
    app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_witatrade)
    response = client.get("/api/users")
    assert response.status_code == 200
    witatrade_users = response.json()["items"]
    assert any(u["email"] == admin_witatrade.email for u in witatrade_users)
    assert not any(u["email"] == admin_vibotaj.email for u in witatrade_users)
    
    del app.dependency_overrides[get_current_active_user]

def test_unauthorized_create_user(client, admin_witatrade):
    # Create a viewer first
    # (Actually we can just mock a viewer)
    def mock_viewer():
        return CurrentUser(
            id=uuid.uuid4(),
            email="viewer@test.com",
            full_name="Viewer",
            role=UserRole.VIEWER,
            is_active=True,
            organization_id=admin_witatrade.organization_id,
            permissions=[]
        )
    
    app.dependency_overrides[get_current_active_user] = mock_viewer
    
    user_data = {
        "email": "fail@test.com",
        "full_name": "Should Fail",
        "password": "Password123!",
        "role": "admin"
    }
    
    response = client.post("/api/users", json=user_data)
    assert response.status_code == 403
    
    del app.dependency_overrides[get_current_active_user]

def test_update_user(client, admin_vibotaj, db_session):
    app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_vibotaj)
    
    # Create a user to update
    user = User(
        email="update@test.com",
        full_name="To Update",
        hashed_password=get_password_hash("Pass123!"),
        role=UserRole.VIEWER,
        organization_id=admin_vibotaj.organization_id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    update_data = {"full_name": "Updated Name", "role": "compliance"}
    response = client.patch(f"/api/users/{user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["role"] == "compliance"
    
    del app.dependency_overrides[get_current_active_user]

def test_deactivate_user(client, admin_vibotaj, db_session):
    app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_vibotaj)
    
    # Create a user to deactivate
    user = User(
        email="deactivate@test.com",
        full_name="To Deactivate",
        hashed_password=get_password_hash("Pass123!"),
        role=UserRole.VIEWER,
        organization_id=admin_vibotaj.organization_id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.delete(f"/api/users/{user.id}")
    assert response.status_code == 200
    
    # Verify in DB
    db_session.refresh(user)
    assert user.is_active is False
    
    del app.dependency_overrides[get_current_active_user]
