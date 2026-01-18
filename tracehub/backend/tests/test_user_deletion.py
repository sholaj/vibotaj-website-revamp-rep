"""Unit tests for UserDeletionService.

Tests cover:
- Soft delete success
- Hard delete success
- Cannot delete self
- Cannot delete last admin
- Role hierarchy enforcement
- Restore soft-deleted user
- Validation of deletion reason
"""

import pytest
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4

from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationType, OrganizationStatus
from app.models import OrganizationMembership, OrgRole
from app.models.audit_log import AuditLog
from app.routers.auth import get_password_hash
from app.services.user_deletion import (
    UserDeletionService,
    CannotDeleteSelfError,
    CannotDeleteLastAdminError,
    CannotDeleteHigherRoleError,
    UserNotFoundError,
    UserAlreadyDeletedError,
    UserNotDeletedError,
    InvalidDeletionReasonError,
)

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
def org_vibotaj(db_session):
    """Create test organization."""
    org = Organization(
        name="VIBOTAJ Test",
        slug="vibotaj-test",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="test@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def admin_user(db_session, org_vibotaj):
    """Create admin user."""
    user = User(
        email="admin.deletion@vibotaj.com",
        full_name="Admin Deletion",
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
    """Create second admin user (for testing last admin guard)."""
    user = User(
        email="admin2.deletion@vibotaj.com",
        full_name="Admin2 Deletion",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def viewer_user(db_session, org_vibotaj):
    """Create viewer user for each test."""
    user = User(
        id=uuid4(),
        email=f"viewer.{uuid4().hex[:8]}@vibotaj.com",
        full_name="Viewer User",
        hashed_password=get_password_hash("Viewer123!"),
        role=UserRole.VIEWER,
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def compliance_user(db_session, org_vibotaj):
    """Create compliance user for each test."""
    user = User(
        id=uuid4(),
        email=f"compliance.{uuid4().hex[:8]}@vibotaj.com",
        full_name="Compliance User",
        hashed_password=get_password_hash("Compliance123!"),
        role=UserRole.COMPLIANCE,
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def deletion_service(db_session):
    """Create UserDeletionService instance."""
    return UserDeletionService(db_session)


class TestSoftDelete:
    """Tests for soft delete functionality."""

    def test_soft_delete_success(self, db_session, deletion_service, admin_user, viewer_user):
        """Test successful soft delete."""
        reason = "Test deletion - user no longer with company"

        deleted_user = deletion_service.soft_delete_user(
            user_id=viewer_user.id,
            deleted_by=admin_user.id,
            reason=reason,
            organization_id=admin_user.organization_id,
        )

        assert deleted_user.is_deleted is True
        assert deleted_user.deleted_at is not None
        assert deleted_user.deleted_by == admin_user.id
        assert deleted_user.deletion_reason == reason
        assert deleted_user.is_active is False

    def test_soft_delete_sets_inactive(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test that soft delete also sets is_active to False."""
        user = User(
            id=uuid4(),
            email=f"active.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Active User",
            hashed_password=get_password_hash("Active123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        deleted_user = deletion_service.soft_delete_user(
            user_id=user.id,
            deleted_by=admin_user.id,
            reason="User left the company",
            organization_id=admin_user.organization_id,
        )

        assert deleted_user.is_active is False


class TestHardDelete:
    """Tests for hard delete functionality."""

    def test_hard_delete_success(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test successful hard delete."""
        user = User(
            id=uuid4(),
            email=f"harddelete.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Hard Delete User",
            hashed_password=get_password_hash("Hard123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        user_email = user.email

        result = deletion_service.hard_delete_user(
            user_id=user_id,
            deleted_by=admin_user.id,
            reason="GDPR request - full deletion required",
            organization_id=admin_user.organization_id,
        )

        assert result["user_id"] == str(user_id)
        assert result["email"] == user_email
        assert "anonymized_audit_logs" in result

        # Verify user is actually deleted
        deleted = db_session.query(User).filter(User.id == user_id).first()
        assert deleted is None

    def test_hard_delete_anonymizes_audit_logs(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test that hard delete anonymizes audit log references."""
        user = User(
            id=uuid4(),
            email=f"audit.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Audit User",
            hashed_password=get_password_hash("Audit123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Create an audit log entry for this user
        audit_log = AuditLog(
            user_id=str(user.id),
            username=user.email,
            organization_id=org_vibotaj.id,
            action="test.action",
            success="true",
            timestamp=datetime.utcnow(),
        )
        db_session.add(audit_log)
        db_session.commit()
        audit_log_id = audit_log.id

        result = deletion_service.hard_delete_user(
            user_id=user.id,
            deleted_by=admin_user.id,
            reason="User requested full data deletion",
            organization_id=admin_user.organization_id,
        )

        # Check audit log was anonymized
        db_session.expire_all()
        updated_log = db_session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        assert updated_log.username == "[deleted]"
        assert updated_log.user_id is None


class TestCannotDeleteSelf:
    """Tests for self-deletion guard."""

    def test_cannot_delete_self(self, deletion_service, admin_user):
        """Test that users cannot delete themselves."""
        with pytest.raises(CannotDeleteSelfError) as exc_info:
            deletion_service.soft_delete_user(
                user_id=admin_user.id,
                deleted_by=admin_user.id,
                reason="Trying to delete myself",
                organization_id=admin_user.organization_id,
            )

        assert "cannot delete your own account" in str(exc_info.value).lower()


class TestCannotDeleteLastAdmin:
    """Tests for last admin guard."""

    def test_cannot_delete_last_admin(self, db_session, org_vibotaj):
        """Test that the last admin cannot be deleted."""
        # Create an organization with only one admin
        org = Organization(
            name="Single Admin Org",
            slug=f"single-admin-{uuid4().hex[:8]}",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="single@test.com"
        )
        db_session.add(org)
        db_session.commit()

        # Create the only admin in this org
        only_admin = User(
            id=uuid4(),
            email=f"onlyadmin.{uuid4().hex[:8]}@test.com",
            full_name="Only Admin",
            hashed_password=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            organization_id=org.id,
            is_active=True
        )
        db_session.add(only_admin)

        # Create a super admin from VIBOTAJ org who can delete users in other orgs
        # This admin is NOT in the same org, so they won't affect the admin count
        super_admin = User(
            id=uuid4(),
            email=f"superadmin.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Super Admin",
            hashed_password=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            organization_id=org_vibotaj.id,  # Different org
            is_active=True
        )
        db_session.add(super_admin)
        db_session.commit()

        # Try to delete the only admin in org - this should fail
        deletion_service = UserDeletionService(db_session)
        with pytest.raises(CannotDeleteLastAdminError) as exc_info:
            deletion_service.soft_delete_user(
                user_id=only_admin.id,
                deleted_by=super_admin.id,  # Super admin from different org
                reason="Trying to delete last admin",
                organization_id=org.id,
            )

        assert "last admin" in str(exc_info.value).lower()


class TestRoleHierarchy:
    """Tests for role hierarchy enforcement."""

    def test_cannot_delete_higher_role(self, db_session, deletion_service, admin_user, compliance_user, org_vibotaj):
        """Test that users cannot delete users with higher roles."""
        # Compliance cannot delete admin
        with pytest.raises(CannotDeleteHigherRoleError) as exc_info:
            deletion_service.soft_delete_user(
                user_id=admin_user.id,
                deleted_by=compliance_user.id,
                reason="Trying to delete admin",
                organization_id=org_vibotaj.id,
            )

        assert "cannot delete a user with role" in str(exc_info.value).lower()

    def test_admin_can_delete_lower_role(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test that admins can delete users with lower roles."""
        viewer = User(
            id=uuid4(),
            email=f"deleteme.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Delete Me",
            hashed_password=get_password_hash("Delete123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(viewer)
        db_session.commit()

        deleted = deletion_service.soft_delete_user(
            user_id=viewer.id,
            deleted_by=admin_user.id,
            reason="Admin deleting viewer",
            organization_id=org_vibotaj.id,
        )

        assert deleted.is_deleted is True


class TestRestoreUser:
    """Tests for user restoration."""

    def test_restore_soft_deleted_user(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test restoring a soft-deleted user."""
        user = User(
            id=uuid4(),
            email=f"restore.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Restore User",
            hashed_password=get_password_hash("Restore123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Soft delete first
        deletion_service.soft_delete_user(
            user_id=user.id,
            deleted_by=admin_user.id,
            reason="Temporary deletion",
            organization_id=org_vibotaj.id,
        )

        assert user.is_deleted is True

        # Now restore
        restored = deletion_service.restore_user(
            user_id=user.id,
            restored_by=admin_user.id,
            organization_id=org_vibotaj.id,
        )

        assert restored.is_deleted is False
        assert restored.deleted_at is None
        assert restored.deleted_by is None
        assert restored.deletion_reason is None
        assert restored.is_active is True

    def test_cannot_restore_non_deleted_user(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test that non-deleted users cannot be restored."""
        user = User(
            id=uuid4(),
            email=f"notdeleted.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Not Deleted",
            hashed_password=get_password_hash("NotDel123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(UserNotDeletedError):
            deletion_service.restore_user(
                user_id=user.id,
                restored_by=admin_user.id,
                organization_id=org_vibotaj.id,
            )


class TestValidation:
    """Tests for input validation."""

    def test_reason_too_short(self, deletion_service, admin_user, viewer_user):
        """Test that short reasons are rejected."""
        with pytest.raises(InvalidDeletionReasonError) as exc_info:
            deletion_service.soft_delete_user(
                user_id=viewer_user.id,
                deleted_by=admin_user.id,
                reason="short",
                organization_id=admin_user.organization_id,
            )

        assert "at least 10 characters" in str(exc_info.value)

    def test_reason_too_long(self, deletion_service, admin_user, viewer_user):
        """Test that long reasons are rejected."""
        with pytest.raises(InvalidDeletionReasonError) as exc_info:
            deletion_service.soft_delete_user(
                user_id=viewer_user.id,
                deleted_by=admin_user.id,
                reason="x" * 501,
                organization_id=admin_user.organization_id,
            )

        assert "500 characters" in str(exc_info.value)

    def test_user_not_found(self, deletion_service, admin_user):
        """Test deletion of non-existent user."""
        with pytest.raises(UserNotFoundError):
            deletion_service.soft_delete_user(
                user_id=uuid4(),
                deleted_by=admin_user.id,
                reason="Deleting non-existent user",
                organization_id=admin_user.organization_id,
            )

    def test_already_deleted(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test that already-deleted users cannot be deleted again."""
        user = User(
            id=uuid4(),
            email=f"alreadydel.{uuid4().hex[:8]}@vibotaj.com",
            full_name="Already Deleted",
            hashed_password=get_password_hash("Already123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Delete once
        deletion_service.soft_delete_user(
            user_id=user.id,
            deleted_by=admin_user.id,
            reason="First deletion",
            organization_id=org_vibotaj.id,
        )

        # Try to delete again
        with pytest.raises(UserAlreadyDeletedError):
            deletion_service.soft_delete_user(
                user_id=user.id,
                deleted_by=admin_user.id,
                reason="Second deletion attempt",
                organization_id=org_vibotaj.id,
            )


class TestGetDeletedUsers:
    """Tests for listing deleted users."""

    def test_get_deleted_users(self, db_session, deletion_service, admin_user, org_vibotaj):
        """Test listing deleted users."""
        # Create and delete multiple users
        for i in range(3):
            user = User(
                id=uuid4(),
                email=f"listdel{i}.{uuid4().hex[:8]}@vibotaj.com",
                full_name=f"List Delete {i}",
                hashed_password=get_password_hash("List123!"),
                role=UserRole.VIEWER,
                organization_id=org_vibotaj.id,
                is_active=True
            )
            db_session.add(user)
            db_session.commit()

            deletion_service.soft_delete_user(
                user_id=user.id,
                deleted_by=admin_user.id,
                reason=f"Deleting user {i} for list test",
                organization_id=org_vibotaj.id,
            )

        deleted_users = deletion_service.get_deleted_users(org_vibotaj.id)

        # Should have at least 3 deleted users
        assert len(deleted_users) >= 3
        for user in deleted_users:
            assert user.is_deleted is True
