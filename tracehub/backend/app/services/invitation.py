"""Invitation service for managing organization invitations.

Sprint 13.1: Backend Invitation Endpoints

Provides functions for:
- Creating secure invitation tokens
- Managing invitation lifecycle
- Accepting invitations and creating memberships
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.organization import (
    Invitation,
    InvitationStatus,
    OrganizationMembership,
    OrgRole,
    MembershipStatus,
    Organization,
)
from ..models.user import User

logger = logging.getLogger(__name__)

# Invitation token expiration in days
INVITATION_EXPIRATION_DAYS = 7


def generate_invitation_token() -> str:
    """Generate a cryptographically secure invitation token.

    Returns:
        A 64-character hex string (32 bytes of randomness).
    """
    return secrets.token_hex(32)


def hash_token(token: str) -> str:
    """Hash a token for secure storage.

    Uses SHA-256 to create a deterministic hash of the token.
    The hash is stored in the database, never the raw token.

    Args:
        token: The raw invitation token.

    Returns:
        A 64-character hex string hash.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create_invitation(
    db: Session,
    org_id: UUID,
    invited_email: str,
    org_role: OrgRole,
    created_by: UUID,
    message: Optional[str] = None
) -> tuple[Invitation, str]:
    """Create a new invitation to join an organization.

    Args:
        db: Database session.
        org_id: UUID of the organization.
        invited_email: Email address to invite.
        org_role: Role to assign when invitation is accepted.
        created_by: UUID of the user creating the invitation.
        message: Optional custom message to include in the invitation.

    Returns:
        Tuple of (Invitation model, raw_token).
        The raw_token should be sent to the invitee but never stored.

    Raises:
        ValueError: If organization doesn't exist.
    """
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise ValueError(f"Organization {org_id} not found")

    # Check for existing pending invitation
    existing = db.query(Invitation).filter(
        Invitation.organization_id == org_id,
        Invitation.email == invited_email.lower(),
        Invitation.status == InvitationStatus.PENDING
    ).first()

    if existing:
        # Check if existing invitation is expired
        if existing.is_expired:
            existing.status = InvitationStatus.EXPIRED
            db.commit()
        else:
            raise ValueError(f"Pending invitation already exists for {invited_email}")

    # Generate secure token
    raw_token = generate_invitation_token()
    token_hash = hash_token(raw_token)

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=INVITATION_EXPIRATION_DAYS)

    # Create invitation
    invitation = Invitation(
        organization_id=org_id,
        email=invited_email.lower(),
        org_role=org_role,
        token_hash=token_hash,
        status=InvitationStatus.PENDING,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
        created_by=created_by,
        invitation_metadata={"custom_message": message} if message else {}
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    logger.info(
        f"Created invitation for {invited_email} to org {org_id} "
        f"with role {org_role.value}, expires {expires_at.isoformat()}"
    )

    # Log email (for now, actual SMTP can be added later)
    logger.info(
        f"[EMAIL PLACEHOLDER] Would send invitation email to {invited_email}: "
        f"You've been invited to join {org.name} as {org_role.value}. "
        f"Token: {raw_token[:8]}..."
    )

    return invitation, raw_token


def get_invitation_by_token(db: Session, token: str) -> Optional[Invitation]:
    """Find an invitation by its token.

    Args:
        db: Database session.
        token: The raw invitation token (not hashed).

    Returns:
        The Invitation if found, None otherwise.
    """
    token_hash = hash_token(token)
    return db.query(Invitation).filter(Invitation.token_hash == token_hash).first()


def get_invitation_by_id(db: Session, invitation_id: UUID) -> Optional[Invitation]:
    """Find an invitation by its ID.

    Args:
        db: Database session.
        invitation_id: UUID of the invitation.

    Returns:
        The Invitation if found, None otherwise.
    """
    return db.query(Invitation).filter(Invitation.id == invitation_id).first()


def is_invitation_valid(invitation: Invitation) -> bool:
    """Check if an invitation is still valid.

    An invitation is valid if:
    - Status is PENDING
    - Not expired (current time < expires_at)

    Args:
        invitation: The invitation to check.

    Returns:
        True if the invitation can still be accepted.
    """
    if invitation.status != InvitationStatus.PENDING:
        return False

    # Use timezone-naive comparison for consistency
    now = datetime.utcnow()
    expires = invitation.expires_at

    # Handle timezone-aware datetime
    if expires.tzinfo is not None:
        expires = expires.replace(tzinfo=None)

    return now < expires


def accept_invitation(
    db: Session,
    invitation: Invitation,
    user: User
) -> OrganizationMembership:
    """Accept an invitation and create a membership.

    Args:
        db: Database session.
        invitation: The invitation to accept.
        user: The user accepting the invitation.

    Returns:
        The created OrganizationMembership.

    Raises:
        ValueError: If invitation is not valid or user email doesn't match.
    """
    # Validate invitation
    if not is_invitation_valid(invitation):
        if invitation.status == InvitationStatus.ACCEPTED:
            raise ValueError("Invitation has already been accepted")
        elif invitation.status == InvitationStatus.REVOKED:
            raise ValueError("Invitation has been revoked")
        elif invitation.status == InvitationStatus.EXPIRED or invitation.is_expired:
            raise ValueError("Invitation has expired")
        else:
            raise ValueError("Invitation is not valid")

    # Verify email matches (case-insensitive)
    if user.email.lower() != invitation.email.lower():
        raise ValueError(
            f"User email ({user.email}) does not match invitation email ({invitation.email})"
        )

    # Check for existing membership
    existing_membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == invitation.organization_id
    ).first()

    if existing_membership:
        raise ValueError("User is already a member of this organization")

    # Determine if this should be the primary organization
    existing_memberships_count = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id
    ).count()
    is_primary = existing_memberships_count == 0

    # Create membership
    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=invitation.organization_id,
        org_role=invitation.org_role,
        status=MembershipStatus.ACTIVE,
        is_primary=is_primary,
        joined_at=datetime.utcnow(),
        invited_by=invitation.created_by,
        invitation_id=invitation.id,
    )

    db.add(membership)

    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_at = datetime.utcnow()
    invitation.accepted_by = user.id

    db.commit()
    db.refresh(membership)

    logger.info(
        f"User {user.email} accepted invitation to org {invitation.organization_id} "
        f"with role {invitation.org_role.value}"
    )

    return membership


def revoke_invitation(db: Session, invitation: Invitation) -> Invitation:
    """Revoke a pending invitation.

    Args:
        db: Database session.
        invitation: The invitation to revoke.

    Returns:
        The updated Invitation.

    Raises:
        ValueError: If invitation is not in PENDING status.
    """
    if invitation.status != InvitationStatus.PENDING:
        raise ValueError(f"Cannot revoke invitation with status {invitation.status.value}")

    invitation.status = InvitationStatus.REVOKED

    db.commit()
    db.refresh(invitation)

    logger.info(f"Revoked invitation {invitation.id} for {invitation.email}")

    return invitation


def resend_invitation(
    db: Session,
    invitation: Invitation,
    resent_by: UUID
) -> tuple[Invitation, str]:
    """Resend an invitation by generating a new token and resetting expiration.

    Args:
        db: Database session.
        invitation: The invitation to resend.
        resent_by: UUID of the user resending the invitation.

    Returns:
        Tuple of (updated Invitation, new_raw_token).

    Raises:
        ValueError: If invitation cannot be resent.
    """
    if invitation.status not in [InvitationStatus.PENDING, InvitationStatus.EXPIRED]:
        raise ValueError(f"Cannot resend invitation with status {invitation.status.value}")

    # Generate new token
    raw_token = generate_invitation_token()
    token_hash = hash_token(raw_token)

    # Reset expiration
    expires_at = datetime.utcnow() + timedelta(days=INVITATION_EXPIRATION_DAYS)

    # Update invitation
    invitation.token_hash = token_hash
    invitation.expires_at = expires_at
    invitation.status = InvitationStatus.PENDING

    # Track resend in metadata
    metadata = invitation.invitation_metadata or {}
    resend_history = metadata.get("resend_history", [])
    resend_history.append({
        "resent_at": datetime.utcnow().isoformat(),
        "resent_by": str(resent_by)
    })
    metadata["resend_history"] = resend_history
    invitation.invitation_metadata = metadata

    db.commit()
    db.refresh(invitation)

    # Get organization for logging
    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    org_name = org.name if org else "Unknown"

    logger.info(
        f"Resent invitation for {invitation.email} to org {org_name}, "
        f"new expiration {expires_at.isoformat()}"
    )

    # Log email (for now, actual SMTP can be added later)
    logger.info(
        f"[EMAIL PLACEHOLDER] Would resend invitation email to {invitation.email}: "
        f"Reminder: You've been invited to join {org_name}. "
        f"Token: {raw_token[:8]}..."
    )

    return invitation, raw_token


def expire_stale_invitations(db: Session) -> int:
    """Mark expired invitations as EXPIRED.

    This can be called periodically to clean up stale invitations.

    Args:
        db: Database session.

    Returns:
        Number of invitations marked as expired.
    """
    now = datetime.utcnow()

    expired_count = db.query(Invitation).filter(
        Invitation.status == InvitationStatus.PENDING,
        Invitation.expires_at < now
    ).update({"status": InvitationStatus.EXPIRED})

    db.commit()

    if expired_count > 0:
        logger.info(f"Marked {expired_count} stale invitations as expired")

    return expired_count


def check_user_can_be_invited(db: Session, email: str, org_id: UUID) -> tuple[bool, Optional[str]]:
    """Check if a user can be invited to an organization.

    Args:
        db: Database session.
        email: Email address to check.
        org_id: Organization ID.

    Returns:
        Tuple of (can_invite: bool, reason: Optional[str]).
        If can_invite is False, reason explains why.
    """
    email_lower = email.lower()

    # Check for existing user
    existing_user = db.query(User).filter(User.email == email_lower).first()

    if existing_user:
        # Check if already a member
        existing_membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == existing_user.id,
            OrganizationMembership.organization_id == org_id
        ).first()

        if existing_membership:
            return False, "User is already a member of this organization"

    # Check for pending invitation
    pending_invitation = db.query(Invitation).filter(
        Invitation.organization_id == org_id,
        Invitation.email == email_lower,
        Invitation.status == InvitationStatus.PENDING
    ).first()

    if pending_invitation and is_invitation_valid(pending_invitation):
        return False, "A pending invitation already exists for this email"

    return True, None
