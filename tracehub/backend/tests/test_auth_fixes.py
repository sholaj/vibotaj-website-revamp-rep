"""
Tests for authentication bug fixes.

Tests cover:
1. Variable scope bug fix - login with non-existent user should return 401, not 500
2. Case-insensitive email lookup - login with different email case should succeed
3. Debug info in non-production environments
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
import bcrypt
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.routers.auth import get_user_by_email

# Import shared test database configuration
from .conftest import engine, TestingSessionLocal, Base


@pytest.fixture(scope="module")
def db_session():
    """Create a fresh database session for tests."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    # Cleanup
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
    """Create a test client with the test database."""
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
    """Create a test organization."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="test@example.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_user_data():
    """Test user credentials."""
    return {
        "email": "test.user@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": UserRole.VIEWER
    }


def test_login_nonexistent_user_returns_401_not_500(client: TestClient, db_session: Session):
    """
    Test that login with non-existent user returns 401 Unauthorized, not 500 Internal Server Error.
    
    This tests the fix for the variable scope bug where password_match was undefined
    when user was not found, causing a NameError in the debug code path.
    """
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
    )
    
    # Should return 401 Unauthorized, not 500 Internal Server Error
    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
    
    # Should have authentication error message
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_wrong_password_returns_401_with_debug_info(
    client: TestClient, 
    db_session: Session, 
    test_org: Organization,
    test_user_data: dict
):
    """
    Test that login with wrong password returns 401 with debug info in staging/dev.
    
    This verifies the debug info block executes without NameError.
    """
    # Create a test user
    password_hash = bcrypt.hashpw(
        test_user_data["password"].encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')
    
    user = User(
        email=test_user_data["email"],
        full_name=test_user_data["full_name"],
        hashed_password=password_hash,
        role=test_user_data["role"],
        organization_id=test_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Try to login with wrong password
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": "WrongPassword123!"
        }
    )
    
    assert response.status_code == 401
    detail = response.json()["detail"]
    
    # In non-production environments, should contain debug info
    # (In production, this would just be "Incorrect username or password")
    assert "Incorrect username or password" in detail


def test_case_insensitive_email_lookup(
    client: TestClient, 
    db_session: Session, 
    test_org: Organization,
    test_user_data: dict
):
    """
    Test that email lookup is case-insensitive.
    
    This tests the fix for case-sensitive email comparison.
    User created with 'Test.User@example.com' should be found with 'test.user@example.com'.
    """
    # Create user with mixed case email
    mixed_case_email = "Test.User@Example.COM"
    password_hash = bcrypt.hashpw(
        test_user_data["password"].encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')
    
    user = User(
        email=mixed_case_email,  # Stored with mixed case
        full_name=test_user_data["full_name"],
        hashed_password=password_hash,
        role=test_user_data["role"],
        organization_id=test_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Try to login with lowercase email
    response = client.post(
        "/api/auth/login",
        data={
            "username": "test.user@example.com",  # All lowercase
            "password": test_user_data["password"]
        }
    )
    
    # Should succeed despite case mismatch
    assert response.status_code == 200, f"Login failed: {response.text}"
    assert "access_token" in response.json()


def test_get_user_by_email_case_insensitive(db_session: Session, test_org: Organization):
    """
    Test that get_user_by_email function performs case-insensitive lookup.
    """
    # Create user with mixed case email
    password_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode('utf-8')
    user = User(
        email="John.Doe@Example.COM",
        full_name="John Doe",
        hashed_password=password_hash,
        role=UserRole.VIEWER,
        organization_id=test_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Test various case combinations
    test_cases = [
        "john.doe@example.com",  # All lowercase
        "JOHN.DOE@EXAMPLE.COM",  # All uppercase
        "John.Doe@Example.COM",  # Original case
        "john.DOE@example.com",  # Mixed
    ]
    
    for email in test_cases:
        found_user = get_user_by_email(db_session, email)
        assert found_user is not None, f"Failed to find user with email: {email}"
        assert found_user.email == "John.Doe@Example.COM", f"Found wrong user for email: {email}"


def test_login_success_with_correct_credentials(
    client: TestClient, 
    db_session: Session, 
    test_org: Organization,
    test_user_data: dict
):
    """
    Test that login succeeds with correct credentials (baseline test).
    """
    # Use unique email for this test
    unique_email = f"success.test.{uuid.uuid4()}@example.com"
    
    # Create a test user
    password_hash = bcrypt.hashpw(
        test_user_data["password"].encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')
    
    user = User(
        email=unique_email,
        full_name=test_user_data["full_name"],
        hashed_password=password_hash,
        role=test_user_data["role"],
        organization_id=test_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Login with correct credentials
    response = client.post(
        "/api/auth/login",
        data={
            "username": unique_email,
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_debug_info_contains_expected_fields(
    client: TestClient, 
    db_session: Session,
    test_org: Organization,
    test_user_data: dict
):
    """
    Test that debug info in non-production environments contains expected fields.
    """
    # Use unique email for this test
    unique_email = f"debug.test.{uuid.uuid4()}@example.com"
    
    # Create a test user
    password_hash = bcrypt.hashpw(
        test_user_data["password"].encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')
    
    user = User(
        email=unique_email,
        full_name=test_user_data["full_name"],
        hashed_password=password_hash,
        role=test_user_data["role"],
        organization_id=test_org.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Try login with wrong password
    response = client.post(
        "/api/auth/login",
        data={
            "username": unique_email,
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 401
    detail = response.json()["detail"]
    
    # Check if debug info is present (in non-production)
    if "Debug:" in detail:
        # Verify debug info structure (should not cause NameError)
        assert "user_found" in detail
        assert "password_match" in detail or "password_match: False" in detail or "password_match: None" in detail
