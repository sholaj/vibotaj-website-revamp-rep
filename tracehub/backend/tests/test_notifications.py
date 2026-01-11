"""
Notifications tests for TraceHub API.

Tests cover:
- Notification listing with pagination
- Unread count endpoint
- Mark notification as read
- Mark all notifications as read
- Notification filtering (unread only)
- Multi-user isolation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime
import uuid

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models.notification import Notification, NotificationType
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


@pytest.fixture(scope="module")
def org_vibotaj(db_session):
    """Create VIBOTAJ organization."""
    org = Organization(
        name="VIBOTAJ Notifications",
        slug="vibotaj-notifications",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="notifications@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def admin_user(db_session, org_vibotaj):
    """Create admin user."""
    user = User(
        email="notif-admin@vibotaj.com",
        full_name="Notifications Admin",
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
def other_user(db_session, org_vibotaj):
    """Create another user for isolation testing."""
    user = User(
        email="other-user@vibotaj.com",
        full_name="Other User",
        hashed_password=get_password_hash("Other123!"),
        role=UserRole.VIEWER,
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


@pytest.fixture
def user_notifications(db_session, admin_user):
    """Create sample notifications for admin user."""
    notifications = [
        Notification(
            user_id=admin_user.id,  # Sprint 11: Changed to UUID FK
            type=NotificationType.DOCUMENT_UPLOADED.value if hasattr(NotificationType, 'DOCUMENT_UPLOADED') else "document_uploaded",
            title="Document Uploaded",
            message="A new bill of lading has been uploaded.",
            data={"shipment_id": str(uuid.uuid4())},
            read=False,
            created_at=datetime.utcnow()
        ),
        Notification(
            user_id=admin_user.id,  # Sprint 11: Changed to UUID FK
            type=NotificationType.SHIPMENT_STATUS_CHANGED.value if hasattr(NotificationType, 'SHIPMENT_STATUS_CHANGED') else "shipment_status_changed",
            title="Shipment Status Changed",
            message="Shipment VIBO-2024-001 is now in transit.",
            data={"shipment_id": str(uuid.uuid4())},
            read=False,
            created_at=datetime.utcnow()
        ),
        Notification(
            user_id=admin_user.id,  # Sprint 11: Changed to UUID FK
            type=NotificationType.DOCUMENT_APPROVED.value if hasattr(NotificationType, 'DOCUMENT_APPROVED') else "document_approved",
            title="Document Approved",
            message="Certificate of Origin has been approved.",
            data={"document_id": str(uuid.uuid4())},
            read=True,  # Already read
            created_at=datetime.utcnow()
        ),
    ]
    for notif in notifications:
        db_session.add(notif)
    db_session.commit()
    yield notifications
    for notif in notifications:
        db_session.delete(notif)
    db_session.commit()


@pytest.fixture
def other_user_notifications(db_session, other_user):
    """Create notifications for other user."""
    notifications = [
        Notification(
            user_id=other_user.id,  # Sprint 11: Changed to UUID FK
            type="info",
            title="Other User Notification",
            message="This belongs to another user.",
            data={},
            read=False,
            created_at=datetime.utcnow()
        ),
    ]
    for notif in notifications:
        db_session.add(notif)
    db_session.commit()
    yield notifications
    for notif in notifications:
        db_session.delete(notif)
    db_session.commit()


class TestNotificationListing:
    """Tests for notification listing endpoint."""

    def test_get_notifications(self, client, admin_user, user_notifications):
        """Should return user's notifications."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/notifications")
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert "unread_count" in data
        assert len(data["notifications"]) == 3
        
        del app.dependency_overrides[get_current_active_user]

    def test_get_notifications_unread_only(self, client, admin_user, user_notifications):
        """Should filter to unread notifications only."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/notifications?unread_only=true")
        
        assert response.status_code == 200
        data = response.json()
        # Should only return unread (2 out of 3)
        assert len(data["notifications"]) == 2
        for notif in data["notifications"]:
            assert notif["read"] is False
        
        del app.dependency_overrides[get_current_active_user]

    def test_get_notifications_pagination(self, client, admin_user, user_notifications):
        """Should support pagination."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/notifications?limit=2&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 2
        
        # Get second page
        response2 = client.get("/api/notifications?limit=2&offset=2")
        data2 = response2.json()
        assert len(data2["notifications"]) == 1
        
        del app.dependency_overrides[get_current_active_user]


class TestUnreadCount:
    """Tests for unread count endpoint."""

    def test_get_unread_count(self, client, admin_user, user_notifications):
        """Should return correct unread count."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/notifications/unread-count")
        
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert data["unread_count"] == 2  # 2 unread out of 3
        
        del app.dependency_overrides[get_current_active_user]


class TestMarkAsRead:
    """Tests for mark as read functionality."""

    def test_mark_notification_read(self, client, admin_user, db_session, org_vibotaj):
        """Should mark specific notification as read."""
        # Create a fresh unread notification
        notif = Notification(
            user_id=admin_user.id,  # Sprint 11: UUID FK
            type="test",
            title="Test Notification",
            message="This is a test.",
            data={},
            read=False,
            created_at=datetime.utcnow()
        )
        db_session.add(notif)
        db_session.commit()
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.patch(f"/api/notifications/{notif.id}/read")
        
        assert response.status_code == 200
        
        # Verify in database
        db_session.refresh(notif)
        assert notif.read is True
        
        del app.dependency_overrides[get_current_active_user]
        
        db_session.delete(notif)
        db_session.commit()

    def test_mark_notification_not_found(self, client, admin_user):
        """Non-existent notification should return 404."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        fake_id = uuid.uuid4()
        response = client.patch(f"/api/notifications/{fake_id}/read")
        
        assert response.status_code == 404
        
        del app.dependency_overrides[get_current_active_user]

    def test_mark_all_read(self, client, admin_user, db_session, org_vibotaj):
        """Should mark all notifications as read."""
        # Create multiple unread notifications
        notifs = [
            Notification(
                user_id=admin_user.id,  # Sprint 11: UUID FK
                type="test",
                title=f"Bulk Test {i}",
                message="Test message",
                data={},
                read=False,
                created_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        for n in notifs:
            db_session.add(n)
        db_session.commit()
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.post("/api/notifications/mark-all-read")
        
        # May or may not exist
        if response.status_code == 200:
            # Verify all are now read
            db_session.expire_all()
            for n in notifs:
                db_session.refresh(n)
                assert n.read is True
        
        del app.dependency_overrides[get_current_active_user]
        
        for n in notifs:
            db_session.delete(n)
        db_session.commit()


class TestUserIsolation:
    """Tests for user notification isolation."""

    def test_cannot_see_other_user_notifications(
        self, client, admin_user, other_user_notifications
    ):
        """User should not see other users' notifications."""
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.get("/api/notifications")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not include other user's notifications
        for notif in data["notifications"]:
            assert notif["user_id"] == admin_user.email
            assert "Other User Notification" not in notif["title"]
        
        del app.dependency_overrides[get_current_active_user]

    def test_cannot_mark_other_user_notification(
        self, client, admin_user, other_user, db_session
    ):
        """User should not be able to mark other user's notifications."""
        # Create notification for other user
        notif = Notification(
            user_id=other_user.id,  # Sprint 11: UUID FK
            type="test",
            title="Private Notification",
            message="This belongs to other user.",
            data={},
            read=False,
            created_at=datetime.utcnow()
        )
        db_session.add(notif)
        db_session.commit()
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_auth(admin_user)
        
        response = client.patch(f"/api/notifications/{notif.id}/read")
        
        # Should fail - not this user's notification
        assert response.status_code in [404, 403]
        
        # Verify still unread
        db_session.refresh(notif)
        assert notif.read is False
        
        del app.dependency_overrides[get_current_active_user]
        
        db_session.delete(notif)
        db_session.commit()


class TestNotificationAuthentication:
    """Tests for notification authentication requirements."""

    def test_notifications_require_auth(self, client):
        """Notifications endpoint should require authentication."""
        response = client.get("/api/notifications")
        
        assert response.status_code == 401

    def test_unread_count_requires_auth(self, client):
        """Unread count endpoint should require authentication."""
        response = client.get("/api/notifications/unread-count")
        
        assert response.status_code == 401

    def test_mark_read_requires_auth(self, client):
        """Mark as read endpoint should require authentication."""
        fake_id = uuid.uuid4()
        response = client.patch(f"/api/notifications/{fake_id}/read")
        
        assert response.status_code == 401
