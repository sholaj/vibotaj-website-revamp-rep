"""
Invitation Endpoint Tests for TraceHub API.

Sprint 13.1: Backend Invitation Endpoints - TEST

Tests verify:
- Creating invitations requires org admin or system admin
- Listing invitations returns organization-scoped data
- Revoking invitations only works for pending status
- Resending invitations generates new token
- Public acceptance endpoints work correctly
- New user registration through invitation
- Existing user acceptance through invitation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from uuid import uuid4
from datetime import datetime, timedelta

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import (
    Organization,
    OrganizationType,
    OrganizationStatus,
    OrganizationMembership,
    MembershipStatus,
    OrgRole,
    Invitation,
    InvitationStatus,
)
from app.routers.auth import get_password_hash, get_current_active_user
from app.schemas.user import CurrentUser
from app.services.permissions import get_role_permissions
from app.services.invitation import generate_invitation_token, hash_token

# Import shared test database configuration
from .conftest import engine, TestingSessionLocal, Base


@pytest.fixture(scope="module")
def db_session():
    """Create fresh test database session."""
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
        name="VIBOTAJ Invitations Test",
        slug="vibotaj-inv-test",
        type=OrganizationType.VIBOTAJ,
        status=OrganizationStatus.ACTIVE,
        contact_email="inv-test@vibotaj.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def org_hages(db_session):
    """Create HAGES buyer organization."""
    org = Organization(
        name="HAGES Invitations Test",
        slug="hages-inv-test",
        type=OrganizationType.BUYER,
        status=OrganizationStatus.ACTIVE,
        contact_email="inv-test@hages.de"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="module")
def system_admin(db_session, org_vibotaj):
    """Create system admin user."""
    user = User(
        email="inv-sysadmin@vibotaj.com",
        full_name="System Admin Invitations",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,  # System admin
        organization_id=org_vibotaj.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create org membership
    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org_vibotaj.id,
        org_role=OrgRole.ADMIN,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
        joined_at=datetime.utcnow()
    )
    db_session.add(membership)
    db_session.commit()

    return user


@pytest.fixture(scope="module")
def org_admin(db_session, org_hages):
    """Create org admin user (not system admin)."""
    user = User(
        email="inv-orgadmin@hages.de",
        full_name="Org Admin Invitations",
        hashed_password=get_password_hash("Hages123!"),
        role=UserRole.VIEWER,  # Not a system admin
        organization_id=org_hages.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create org membership as admin
    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org_hages.id,
        org_role=OrgRole.ADMIN,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
        joined_at=datetime.utcnow()
    )
    db_session.add(membership)
    db_session.commit()

    return user


@pytest.fixture(scope="module")
def org_member(db_session, org_hages):
    """Create org member (non-admin)."""
    user = User(
        email="inv-member@hages.de",
        full_name="Org Member Invitations",
        hashed_password=get_password_hash("Member123!"),
        role=UserRole.VIEWER,
        organization_id=org_hages.id,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create org membership as member (not admin)
    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org_hages.id,
        org_role=OrgRole.MEMBER,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
        joined_at=datetime.utcnow()
    )
    db_session.add(membership)
    db_session.commit()

    return user


def create_mock_current_user(user: User, org_role: OrgRole = OrgRole.ADMIN) -> CurrentUser:
    """Create CurrentUser mock for authentication override."""
    permissions = [p.value for p in get_role_permissions(user.role)]
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        permissions=permissions,
        org_role=org_role,
        org_type=OrganizationType.VIBOTAJ if "vibotaj" in user.email else OrganizationType.BUYER,
        org_permissions=[]
    )


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Clean up dependency overrides after each test."""
    yield
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]


class TestCreateInvitation:
    """Test invitation creation endpoint."""

    def test_system_admin_can_create_invitation(
        self, client, system_admin, org_hages
    ):
        """System admin should be able to create invitation for any org."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(system_admin)

        response = client.post(
            f"/api/invitations/organizations/{org_hages.id}/invitations",
            json={
                "email": "newuser@example.com",
                "org_role": "member",
                "message": "Welcome to our team!"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["org_role"] == "member"
        assert data["status"] == "pending"
        assert "invitation_url" in data
        assert data["organization_id"] == str(org_hages.id)

    def test_org_admin_can_create_invitation_for_own_org(
        self, client, org_admin, org_hages
    ):
        """Org admin should be able to create invitation for their own org."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_admin, OrgRole.ADMIN
        )

        response = client.post(
            f"/api/invitations/organizations/{org_hages.id}/invitations",
            json={
                "email": "colleague@example.com",
                "org_role": "viewer"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "colleague@example.com"
        assert data["org_role"] == "viewer"

    def test_org_member_cannot_create_invitation(
        self, client, org_member, org_hages
    ):
        """Regular org member should not be able to create invitations."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_member, OrgRole.MEMBER
        )

        response = client.post(
            f"/api/invitations/organizations/{org_hages.id}/invitations",
            json={
                "email": "blocked@example.com",
                "org_role": "viewer"
            }
        )

        assert response.status_code == 403

    def test_duplicate_pending_invitation_rejected(
        self, client, system_admin, org_hages
    ):
        """Cannot create duplicate pending invitation for same email."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(system_admin)

        # First invitation should succeed
        response1 = client.post(
            f"/api/invitations/organizations/{org_hages.id}/invitations",
            json={"email": "duplicate@example.com", "org_role": "member"}
        )
        assert response1.status_code == 201

        # Second invitation for same email should fail
        response2 = client.post(
            f"/api/invitations/organizations/{org_hages.id}/invitations",
            json={"email": "duplicate@example.com", "org_role": "admin"}
        )
        assert response2.status_code == 400
        assert "pending invitation" in response2.json()["detail"].lower()

    def test_invalid_email_rejected(
        self, client, system_admin, org_hages
    ):
        """Invalid email format should be rejected."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(system_admin)

        response = client.post(
            f"/api/invitations/organizations/{org_hages.id}/invitations",
            json={"email": "not-an-email", "org_role": "member"}
        )

        assert response.status_code == 422  # Validation error


class TestListInvitations:
    """Test invitation listing endpoint."""

    def test_admin_can_list_org_invitations(
        self, client, org_admin, org_hages
    ):
        """Org admin should be able to list invitations for their org."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_admin, OrgRole.ADMIN
        )

        response = client.get(
            f"/api/invitations/organizations/{org_hages.id}/invitations"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_invitations_with_status_filter(
        self, client, org_admin, org_hages
    ):
        """Should be able to filter invitations by status."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_admin, OrgRole.ADMIN
        )

        response = client.get(
            f"/api/invitations/organizations/{org_hages.id}/invitations?status=pending"
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "pending"

    def test_member_cannot_list_invitations(
        self, client, org_member, org_hages
    ):
        """Regular member should not see invitation list."""
        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_member, OrgRole.MEMBER
        )

        response = client.get(
            f"/api/invitations/organizations/{org_hages.id}/invitations"
        )

        assert response.status_code == 403


class TestRevokeInvitation:
    """Test invitation revocation endpoint."""

    def test_admin_can_revoke_pending_invitation(
        self, client, db_session, org_admin, org_hages
    ):
        """Org admin should be able to revoke pending invitations."""
        # Create an invitation to revoke
        raw_token = generate_invitation_token()
        invitation = Invitation(
            organization_id=org_hages.id,
            email="torevoke@example.com",
            org_role=OrgRole.MEMBER,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            created_by=org_admin.id
        )
        db_session.add(invitation)
        db_session.commit()
        db_session.refresh(invitation)

        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_admin, OrgRole.ADMIN
        )

        response = client.delete(
            f"/api/invitations/organizations/{org_hages.id}/invitations/{invitation.id}"
        )

        assert response.status_code == 204

        # Verify status changed
        db_session.refresh(invitation)
        assert invitation.status == InvitationStatus.REVOKED

    def test_cannot_revoke_accepted_invitation(
        self, client, db_session, org_admin, org_hages
    ):
        """Cannot revoke an already accepted invitation."""
        raw_token = generate_invitation_token()
        invitation = Invitation(
            organization_id=org_hages.id,
            email="accepted@example.com",
            org_role=OrgRole.MEMBER,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.ACCEPTED,
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            created_by=org_admin.id,
            accepted_at=datetime.utcnow()
        )
        db_session.add(invitation)
        db_session.commit()
        db_session.refresh(invitation)

        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_admin, OrgRole.ADMIN
        )

        response = client.delete(
            f"/api/invitations/organizations/{org_hages.id}/invitations/{invitation.id}"
        )

        assert response.status_code == 400
        assert "accepted" in response.json()["detail"].lower()


class TestResendInvitation:
    """Test invitation resend endpoint."""

    def test_admin_can_resend_invitation(
        self, client, db_session, org_admin, org_hages
    ):
        """Org admin should be able to resend a pending invitation."""
        raw_token = generate_invitation_token()
        old_token_hash = hash_token(raw_token)
        old_expires = datetime.utcnow() + timedelta(days=1)  # Expires soon

        invitation = Invitation(
            organization_id=org_hages.id,
            email="resend@example.com",
            org_role=OrgRole.MEMBER,
            token_hash=old_token_hash,
            status=InvitationStatus.PENDING,
            expires_at=old_expires,
            created_at=datetime.utcnow(),
            created_by=org_admin.id
        )
        db_session.add(invitation)
        db_session.commit()
        db_session.refresh(invitation)

        app.dependency_overrides[get_current_active_user] = lambda: create_mock_current_user(
            org_admin, OrgRole.ADMIN
        )

        response = client.post(
            f"/api/invitations/organizations/{org_hages.id}/invitations/{invitation.id}/resend"
        )

        assert response.status_code == 200
        data = response.json()
        assert "invitation_url" in data
        assert data["status"] == "pending"

        # Verify token was regenerated
        db_session.refresh(invitation)
        assert invitation.token_hash != old_token_hash
        # Compare datetimes - handle timezone-aware vs naive
        new_expires = invitation.expires_at
        if new_expires.tzinfo is not None:
            new_expires = new_expires.replace(tzinfo=None)
        assert new_expires > old_expires


class TestPublicAcceptEndpoints:
    """Test public invitation acceptance endpoints."""

    def test_get_invitation_by_valid_token(
        self, client, db_session, org_admin, org_hages
    ):
        """Public endpoint should return invitation details for valid token."""
        raw_token = generate_invitation_token()
        invitation = Invitation(
            organization_id=org_hages.id,
            email="public@example.com",
            org_role=OrgRole.MEMBER,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            created_by=org_admin.id,
            invitation_metadata={"custom_message": "Welcome aboard!"}
        )
        db_session.add(invitation)
        db_session.commit()

        # No auth override needed - this is a public endpoint
        response = client.get(f"/api/invitations/accept/{raw_token}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "public@example.com"
        assert data["organization_name"] == org_hages.name
        assert data["org_role"] == "member"
        assert data["custom_message"] == "Welcome aboard!"
        assert "requires_registration" in data

    def test_get_invitation_invalid_token_returns_404(self, client):
        """Invalid token should return 404."""
        response = client.get("/api/invitations/accept/invalid-token-12345")
        assert response.status_code == 404

    def test_get_expired_invitation_returns_400(
        self, client, db_session, org_admin, org_hages
    ):
        """Expired invitation should return 400."""
        raw_token = generate_invitation_token()
        invitation = Invitation(
            organization_id=org_hages.id,
            email="expired@example.com",
            org_role=OrgRole.MEMBER,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Already expired
            created_at=datetime.utcnow() - timedelta(days=8),
            created_by=org_admin.id
        )
        db_session.add(invitation)
        db_session.commit()

        response = client.get(f"/api/invitations/accept/{raw_token}")
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_accept_invitation_new_user(
        self, client, db_session, org_admin, org_hages
    ):
        """New user should be able to create account and accept invitation."""
        raw_token = generate_invitation_token()
        new_email = f"newuser-{uuid4().hex[:6]}@example.com"
        invitation = Invitation(
            organization_id=org_hages.id,
            email=new_email,
            org_role=OrgRole.MEMBER,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            created_by=org_admin.id
        )
        db_session.add(invitation)
        db_session.commit()

        response = client.post(
            f"/api/invitations/accept/{raw_token}",
            json={
                "full_name": "New Test User",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_new_user"] is True
        assert data["org_role"] == "member"
        assert "access_token" in data  # New user gets token for immediate login

    def test_accept_invitation_existing_user(
        self, client, db_session, org_admin, org_hages, org_vibotaj
    ):
        """Existing user should be able to accept invitation without creating account."""
        # Create an existing user (not in org_hages)
        existing_email = f"existing-{uuid4().hex[:6]}@vibotaj.com"
        existing_user = User(
            email=existing_email,
            full_name="Existing User",
            hashed_password=get_password_hash("Password123!"),
            role=UserRole.VIEWER,
            organization_id=org_vibotaj.id,
            is_active=True
        )
        db_session.add(existing_user)
        db_session.commit()
        db_session.refresh(existing_user)

        # Create invitation for existing user
        raw_token = generate_invitation_token()
        invitation = Invitation(
            organization_id=org_hages.id,
            email=existing_email,
            org_role=OrgRole.VIEWER,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            created_by=org_admin.id
        )
        db_session.add(invitation)
        db_session.commit()

        response = client.post(
            f"/api/invitations/accept/{raw_token}",
            json={}  # No additional data needed for existing user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_new_user"] is False
        assert data["user_id"] == str(existing_user.id)

    def test_accept_invitation_missing_password_for_new_user(
        self, client, db_session, org_admin, org_hages
    ):
        """New user must provide password."""
        raw_token = generate_invitation_token()
        new_email = f"nopass-{uuid4().hex[:6]}@example.com"
        invitation = Invitation(
            organization_id=org_hages.id,
            email=new_email,
            org_role=OrgRole.MEMBER,
            token_hash=hash_token(raw_token),
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            created_by=org_admin.id
        )
        db_session.add(invitation)
        db_session.commit()

        response = client.post(
            f"/api/invitations/accept/{raw_token}",
            json={"full_name": "Missing Password"}
            # No password provided
        )

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()


class TestTokenSecurity:
    """Test security of invitation tokens."""

    def test_token_is_properly_hashed(self, db_session, org_admin, org_hages):
        """Verify tokens are hashed before storage."""
        from app.services.invitation import create_invitation

        invitation, raw_token = create_invitation(
            db=db_session,
            org_id=org_hages.id,
            invited_email="hash-test@example.com",
            org_role=OrgRole.MEMBER,
            created_by=org_admin.id
        )

        # Raw token should NOT be stored
        assert invitation.token_hash != raw_token
        # Hash should be SHA-256 (64 hex chars)
        assert len(invitation.token_hash) == 64
        # Hash should be deterministic
        assert invitation.token_hash == hash_token(raw_token)

    def test_different_tokens_have_different_hashes(self):
        """Each token should produce a unique hash."""
        token1 = generate_invitation_token()
        token2 = generate_invitation_token()

        assert token1 != token2
        assert hash_token(token1) != hash_token(token2)
