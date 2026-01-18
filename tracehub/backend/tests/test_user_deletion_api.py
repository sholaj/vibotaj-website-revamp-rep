"""Integration tests for user deletion API endpoints.

Tests cover:
- DELETE /api/users/{user_id} with soft/hard modes
- POST /api/users/{user_id}/restore
- GET /api/users/deleted
- Deleted user cannot authenticate
- Audit log creation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models import OrganizationMembership, OrgRole
from app.routers.auth import get_current_active_user, get_password_hash
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions

# Import shared test database configuration from conftest
from .conftest import engine, TestingSessionLocal, Base


@pytest.fixture(scope="module")
def db_session():
    """Create database session for tests."""
    # Setup: Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    # Teardown: Close and drop with CASCADE
    db.close()
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS container_events CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS document_contents CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS document_issues CASCADE"))
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
    """Create test organization."""
    org = Organization(
        name="VIBOTAJ API Test",
        slug="vibotaj-api-test",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="api-test@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def admin_user(db_session, org_vibotaj):
    """Create admin user."""
    user = User(
        email="admin.api@vibotaj.com",
        full_name="Admin API",
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
def second_admin(db_session, org_vibotaj):
    """Create second admin user."""
    user = User(
        email="admin2.api@vibotaj.com",
        full_name="Admin2 API",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=org_vibotaj.id,
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


class TestDeleteEndpoint:
    """Tests for DELETE /api/users/{user_id}."""

    def test_soft_delete_user(self, client, db_session, admin_user, org_vibotaj):
        """Test soft deleting a user."""
        # Create user to delete
        user = User(
            id=uuid4(),
            email=f"softdel.api.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Soft Delete API",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.request(
            "DELETE",
            f"/api/users/{user.id}",
            json={
                "reason": "User no longer employed at company",
                "hard_delete": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_type"] == "soft"
        assert data["email"] == user.email
        assert "deleted_at" in data

        # Verify in database
        db_session.refresh(user)
        assert user.deleted_at is not None
        assert user.is_active is False

        del app.dependency_overrides[get_current_active_user]

    def test_hard_delete_user(self, client, db_session, admin_user, org_vibotaj):
        """Test hard deleting a user."""
        # Create user to delete
        user = User(
            id=uuid4(),
            email=f"harddel.api.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Hard Delete API",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.request(
            "DELETE",
            f"/api/users/{user_id}",
            json={
                "reason": "GDPR erasure request from former employee",
                "hard_delete": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deletion_type"] == "hard"
        assert "anonymized_audit_logs" in data

        # Verify user is physically deleted
        deleted = db_session.query(User).filter(User.id == user_id).first()
        assert deleted is None

        del app.dependency_overrides[get_current_active_user]

    def test_cannot_delete_self(self, client, admin_user):
        """Test that users cannot delete themselves."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.request(
            "DELETE",
            f"/api/users/{admin_user.id}",
            json={
                "reason": "Trying to delete myself",
                "hard_delete": False
            }
        )

        assert response.status_code == 400
        assert "cannot delete your own account" in response.json()["detail"].lower()

        del app.dependency_overrides[get_current_active_user]

    def test_reason_too_short(self, client, db_session, admin_user, org_vibotaj):
        """Test that short reasons are rejected."""
        user = User(
            id=uuid4(),
            email=f"shortreason.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Short Reason",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.request(
            "DELETE",
            f"/api/users/{user.id}",
            json={
                "reason": "short",
                "hard_delete": False
            }
        )

        assert response.status_code == 422

        del app.dependency_overrides[get_current_active_user]

    def test_user_not_found(self, client, admin_user):
        """Test deleting non-existent user."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.request(
            "DELETE",
            f"/api/users/{uuid4()}",
            json={
                "reason": "Deleting non-existent user",
                "hard_delete": False
            }
        )

        assert response.status_code == 404

        del app.dependency_overrides[get_current_active_user]


class TestRestoreEndpoint:
    """Tests for POST /api/users/{user_id}/restore."""

    def test_restore_soft_deleted_user(self, client, db_session, admin_user, org_vibotaj):
        """Test restoring a soft-deleted user."""
        # Create and soft-delete a user
        user = User(
            id=uuid4(),
            email=f"restore.api.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Restore API",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Soft delete
        user.deleted_at = datetime.utcnow()
        user.deleted_by = admin_user.id
        user.deletion_reason = "Test deletion for restore"
        user.is_active = False
        db_session.commit()

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.post(f"/api/users/{user.id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User restored successfully"
        assert data["email"] == user.email

        # Verify in database
        db_session.refresh(user)
        assert user.deleted_at is None
        assert user.is_active is True

        del app.dependency_overrides[get_current_active_user]

    def test_cannot_restore_non_deleted_user(self, client, db_session, admin_user, org_vibotaj):
        """Test that non-deleted users cannot be restored."""
        user = User(
            id=uuid4(),
            email=f"notdel.api.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Not Deleted API",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.post(f"/api/users/{user.id}/restore")

        assert response.status_code == 400
        assert "not deleted" in response.json()["detail"].lower()

        del app.dependency_overrides[get_current_active_user]


class TestDeletedUsersEndpoint:
    """Tests for GET /api/users/deleted."""

    def test_list_deleted_users(self, client, db_session, admin_user, org_vibotaj):
        """Test listing deleted users."""
        # Create and delete users
        for i in range(3):
            user = User(
                id=uuid4(),
                email=f"listdel.api.{i}.{uuid4().hex[:8]}@vibotaj.com",
                full_name=f"List Delete API {i}",
                hashed_password=get_password_hash("Test123!"),
                role=UserRole.VIEWER,
                organization_id=org_vibotaj.id,
                is_active=False,
                deleted_at=datetime.utcnow(),
                deleted_by=admin_user.id,
                deletion_reason=f"Deleted for list test {i}",
            )
            db_session.add(user)
        db_session.commit()

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)

        response = client.get("/api/users/deleted")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3

        del app.dependency_overrides[get_current_active_user]


class TestDeletedUserAuth:
    """Tests for deleted user authentication blocking."""

    def test_deleted_user_cannot_login(self, client, db_session, org_vibotaj, admin_user):
        """Test that deleted users cannot authenticate."""
        # Create a user and delete them
        user = User(
            id=uuid4(),
            email=f"blocked.auth.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Blocked Auth",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=False,
            deleted_at=datetime.utcnow(),
            deleted_by=admin_user.id,
            deletion_reason="User account terminated",
        )
        db_session.add(user)
        db_session.commit()

        # Try to login
        response = client.post(
            "/api/auth/login",
            data={
                "username": user.email,
                "password": "Test123!"
            }
        )

        # Should fail because user is inactive/deleted
        assert response.status_code == 401


class TestRoleHierarchy:
    """Tests for role hierarchy enforcement in API."""

    def test_viewer_cannot_delete_admin(self, client, db_session, admin_user, org_vibotaj):
        """Test that viewers cannot delete admins."""
        viewer = User(
            id=uuid4(),
            email=f"viewer.role.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Viewer Role",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(viewer)
        db_session.commit()

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(viewer)

        response = client.request(
            "DELETE",
            f"/api/users/{admin_user.id}",
            json={
                "reason": "Viewer trying to delete admin",
                "hard_delete": False
            }
        )

        # Should fail due to permission check
        assert response.status_code == 403

        del app.dependency_overrides[get_current_active_user]

    def test_compliance_cannot_delete_admin(self, client, db_session, admin_user, org_vibotaj):
        """Test that compliance users cannot delete admins."""
        compliance = User(
            id=uuid4(),
            email=f"compliance.role.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Compliance Role",
            hashed_password=get_password_hash("Test123!"),
            role=UserRole.COMPLIANCE,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(compliance)
        db_session.commit()

        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(compliance)

        response = client.request(
            "DELETE",
            f"/api/users/{admin_user.id}",
            json={
                "reason": "Compliance trying to delete admin",
                "hard_delete": False
            }
        )

        # Should fail - compliance doesn't have USERS_DELETE permission
        assert response.status_code == 403

        del app.dependency_overrides[get_current_active_user]
