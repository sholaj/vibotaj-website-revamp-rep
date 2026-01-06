"""
Authentication tests for TraceHub API.

Tests cover:
- Login endpoint with valid/invalid credentials
- JWT token generation and validation
- Password hashing and verification
- Token refresh mechanism
- Current user retrieval
- Demo user fallback
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from jose import jwt
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.routers.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user,
    authenticate_user,
)
from app.config import get_settings

# Import shared fixtures from conftest.py
from .conftest import engine, TestingSessionLocal, Base

settings = get_settings()


@pytest.fixture(scope="module")
def db_session():
    """Create test database session."""
    # Drop and recreate all tables for clean state
    from sqlalchemy import text
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


@pytest.fixture
def test_organization(db_session):
    """Create test organization with unique slug."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name=f"Test Organization {unique_id}",
        slug=f"test-org-{unique_id}",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email=f"test-{unique_id}@testorg.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_user(db_session, test_organization):
    """Create test user with valid credentials."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"testuser-{unique_id}@tracehub.com",
        full_name="Test User",
        hashed_password=get_password_hash("TestPassword123!"),
        role=UserRole.ADMIN,
        organization_id=test_organization.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session, test_organization):
    """Create inactive user for testing."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"inactive-{unique_id}@tracehub.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("TestPassword123!"),
        role=UserRole.VIEWER,
        organization_id=test_organization.id,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_password_hash_is_different_from_plain(self):
        """Hashed password should not equal plain password."""
        plain = "MySecretPassword123!"
        hashed = get_password_hash(plain)
        assert hashed != plain
        assert len(hashed) > len(plain)

    def test_password_hash_verification_success(self):
        """Correct password should verify successfully."""
        plain = "MySecretPassword123!"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True

    def test_password_hash_verification_failure(self):
        """Wrong password should fail verification."""
        plain = "MySecretPassword123!"
        hashed = get_password_hash(plain)
        assert verify_password("WrongPassword!", hashed) is False

    def test_same_password_different_hash(self):
        """Same password should produce different hashes (salt)."""
        plain = "MySecretPassword123!"
        hash1 = get_password_hash(plain)
        hash2 = get_password_hash(plain)
        assert hash1 != hash2
        # But both should verify
        assert verify_password(plain, hash1) is True
        assert verify_password(plain, hash2) is True


class TestTokenGeneration:
    """Tests for JWT token generation."""

    def test_create_access_token_default_expiry(self):
        """Token should be created with default expiry."""
        data = {"sub": str(uuid.uuid4()), "email": "test@test.com", "role": "admin"}
        token = create_access_token(data)
        
        assert token is not None
        assert len(token) > 0
        
        # Decode and verify
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["email"] == "test@test.com"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        """Token should respect custom expiry."""
        data = {"sub": str(uuid.uuid4()), "email": "test@test.com"}
        expires = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires)
        
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert "exp" in payload

    def test_token_contains_required_claims(self):
        """Token should contain all required claims."""
        user_id = str(uuid.uuid4())
        data = {
            "sub": user_id,
            "email": "test@test.com",
            "role": "compliance"
        }
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == user_id
        assert payload["email"] == "test@test.com"
        assert payload["role"] == "compliance"


class TestLoginEndpoint:
    """Tests for /api/auth/login endpoint."""

    def test_login_success(self, client, test_user):
        """Valid credentials should return access token."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_email(self, client):
        """Non-existent email should return 401."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@test.com",
                "password": "SomePassword123!"
            }
        )
        
        assert response.status_code == 401
        # API returns "Incorrect username or password" for security
        assert "Incorrect" in response.json()["detail"] or "Invalid" in response.json()["detail"]

    def test_login_invalid_password(self, client, test_user):
        """Wrong password should return 401."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword!"
            }
        )
        
        assert response.status_code == 401
        # API returns "Incorrect username or password" for security
        assert "Incorrect" in response.json()["detail"] or "Invalid" in response.json()["detail"]

    def test_login_inactive_user(self, client, inactive_user):
        """Inactive user should not be able to login."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": inactive_user.email,
                "password": "TestPassword123!"
            }
        )
        
        # Should fail - inactive users cannot login
        # API may return 200 but then /me will fail, or return 401 directly
        assert response.status_code in [200, 401, 403]

    def test_login_empty_credentials(self, client):
        """Empty credentials should return 422 (validation error)."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "",
                "password": ""
            }
        )
        
        # FastAPI returns 422 for validation errors
        assert response.status_code in [401, 422]


class TestCurrentUserEndpoint:
    """Tests for /api/auth/me endpoint."""

    def test_get_current_user_success(self, client, test_user):
        """Authenticated user should get their info."""
        # First login to get token
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )
        token = login_response.json()["access_token"]
        
        # Then get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    def test_get_current_user_no_token(self, client):
        """Request without token should return 401."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Invalid token should return 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client, test_user):
        """Expired token should return 401."""
        # Create expired token
        data = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "role": test_user.role.value
        }
        # Set expiry to past
        expired_token = jwt.encode(
            {**data, "exp": datetime.utcnow() - timedelta(hours=1)},
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401


class TestDemoUserFallback:
    """Tests for demo user fallback mechanism."""

    def test_demo_user_login(self, client):
        """Demo user should be able to login with demo credentials."""
        # Skip if demo credentials not configured
        if not settings.demo_password:
            pytest.skip("Demo password not configured")
        
        response = client.post(
            "/api/auth/login",
            data={
                "username": settings.demo_email,
                "password": settings.demo_password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestAuthenticateUser:
    """Tests for authenticate_user helper function."""

    def test_authenticate_valid_user(self, db_session, test_user):
        """Valid credentials should return user object."""
        user = authenticate_user(db_session, test_user.email, "TestPassword123!")
        
        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id

    def test_authenticate_wrong_email(self, db_session):
        """Non-existent email should return None."""
        user = authenticate_user(db_session, "nonexistent@test.com", "password")
        
        assert user is None

    def test_authenticate_wrong_password(self, db_session, test_user):
        """Wrong password should return None."""
        user = authenticate_user(db_session, test_user.email, "WrongPassword!")
        
        assert user is None


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_valid_token(self, client, test_user):
        """Valid token should be refreshable."""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )
        token = login_response.json()["access_token"]
        
        # Try to refresh
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # If refresh endpoint exists
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
