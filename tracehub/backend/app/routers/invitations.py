"""Invitations router for TraceHub API.

Sprint 13.1: Backend Invitation Endpoints

Provides endpoints for:
- Creating invitations (org admin/system admin)
- Listing invitations for an organization
- Revoking pending invitations
- Resending invitations
- Public endpoints for accepting invitations
"""

import logging
import math
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from ..config import get_settings
from ..database import get_db
from ..models.organization import (
    Organization,
    Invitation,
    InvitationStatus,
    OrganizationMembership,
    OrgRole as OrgRoleModel,
    MembershipStatus,
)
from ..models.user import User as UserModel, UserRole
from ..schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
    InvitationCreateResponse,
    InvitationListResponse,
    InvitationAcceptInfo,
    AcceptInvitation,
    AcceptedInvitationResponse,
    ResendInvitationResponse,
)
from ..schemas.user import CurrentUser
from .auth import get_current_active_user, get_password_hash, create_access_token
from ..services.invitation import (
    create_invitation,
    get_invitation_by_token,
    get_invitation_by_id,
    is_invitation_valid,
    accept_invitation,
    revoke_invitation,
    resend_invitation,
    check_user_can_be_invited,
)
from ..services.permissions import Permission, has_permission

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def check_org_admin_permission(user: CurrentUser, org_id: UUID, db: Session) -> None:
    """Check if user has admin permission for the organization.

    User can manage invitations if:
    - They are a system admin, OR
    - They are an org admin for the specific organization

    Raises:
        HTTPException: If user doesn't have permission.
    """
    # System admin can manage any organization
    if has_permission(user.role, Permission.SYSTEM_ADMIN):
        return

    # Check if user is an org admin for this organization
    if user.organization_id == org_id and user.org_role == OrgRoleModel.ADMIN:
        return

    # Check membership in target organization
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.status == MembershipStatus.ACTIVE
    ).first()

    if membership and membership.org_role == OrgRoleModel.ADMIN:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Organization admin access required"
    )


def get_invitation_url(token: str) -> str:
    """Generate the invitation acceptance URL.

    Args:
        token: The raw invitation token.

    Returns:
        Full URL for accepting the invitation.
    """
    # Use frontend URL from settings, default to production
    base_url = getattr(settings, 'frontend_url', 'https://tracehub.vibotaj.com')
    return f"{base_url}/accept-invitation/{token}"


# ============ Organization-scoped Invitation Endpoints ============


@router.post(
    "/organizations/{org_id}/invitations",
    response_model=InvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invitation",
    description="Create an invitation to join the organization. Requires org admin or system admin."
)
async def create_org_invitation(
    org_id: UUID,
    invitation_data: InvitationCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new invitation to join an organization.

    The invitation email will contain a secure token that can be used to accept.
    Tokens expire after 7 days.

    **Permissions:** Organization admin or system admin.
    """
    # Check permissions
    check_org_admin_permission(current_user, org_id, db)

    # Get organization
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user can be invited
    can_invite, reason = check_user_can_be_invited(db, invitation_data.email, org_id)
    if not can_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )

    try:
        invitation, raw_token = create_invitation(
            db=db,
            org_id=org_id,
            invited_email=invitation_data.email,
            org_role=invitation_data.org_role,
            created_by=current_user.id,
            message=invitation_data.message
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    invitation_url = get_invitation_url(raw_token)

    return InvitationCreateResponse(
        id=invitation.id,
        organization_id=invitation.organization_id,
        organization_name=org.name,
        email=invitation.email,
        org_role=invitation.org_role,
        status=invitation.status,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        invitation_url=invitation_url
    )


@router.get(
    "/organizations/{org_id}/invitations",
    response_model=InvitationListResponse,
    summary="List organization invitations",
    description="List all invitations for an organization with optional filtering."
)
async def list_org_invitations(
    org_id: UUID,
    status_filter: Optional[InvitationStatus] = Query(
        None,
        alias="status",
        description="Filter by invitation status"
    ),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List invitations for an organization.

    **Permissions:** Organization admin or system admin.
    """
    # Check permissions
    check_org_admin_permission(current_user, org_id, db)

    # Verify org exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Build query
    query = db.query(Invitation).filter(Invitation.organization_id == org_id)

    if status_filter:
        query = query.filter(Invitation.status == status_filter)

    # Get total count
    total = query.count()

    # Get invitations with creator info
    invitations = (
        query
        .options(joinedload(Invitation.creator))
        .order_by(Invitation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Convert to response format
    items = []
    for inv in invitations:
        items.append(InvitationResponse(
            id=inv.id,
            organization_id=inv.organization_id,
            organization_name=org.name,
            email=inv.email,
            org_role=inv.org_role,
            status=inv.status,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
            created_by=inv.created_by,
            created_by_name=inv.creator.full_name if inv.creator else None,
            accepted_at=inv.accepted_at
        ))

    return InvitationListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.delete(
    "/organizations/{org_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an invitation",
    description="Revoke a pending invitation. Only pending invitations can be revoked."
)
async def revoke_org_invitation(
    org_id: UUID,
    invitation_id: UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a pending invitation.

    **Permissions:** Organization admin or system admin.
    """
    # Check permissions
    check_org_admin_permission(current_user, org_id, db)

    # Get invitation
    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.organization_id == org_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revoke invitation with status '{invitation.status.value}'"
        )

    try:
        revoke_invitation(db, invitation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    logger.info(
        f"User {current_user.email} revoked invitation {invitation_id} "
        f"for {invitation.email} to org {org_id}"
    )

    return None


@router.post(
    "/organizations/{org_id}/invitations/{invitation_id}/resend",
    response_model=ResendInvitationResponse,
    summary="Resend an invitation",
    description="Resend an invitation with a new token and reset expiration."
)
async def resend_org_invitation(
    org_id: UUID,
    invitation_id: UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resend an invitation.

    Generates a new token and resets the expiration to 7 days from now.
    Can resend pending or expired invitations.

    **Permissions:** Organization admin or system admin.
    """
    # Check permissions
    check_org_admin_permission(current_user, org_id, db)

    # Get invitation
    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.organization_id == org_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    try:
        updated_invitation, raw_token = resend_invitation(
            db=db,
            invitation=invitation,
            resent_by=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    invitation_url = get_invitation_url(raw_token)

    logger.info(
        f"User {current_user.email} resent invitation {invitation_id} "
        f"for {invitation.email} to org {org_id}"
    )

    return ResendInvitationResponse(
        id=updated_invitation.id,
        email=updated_invitation.email,
        org_role=updated_invitation.org_role,
        status=updated_invitation.status,
        expires_at=updated_invitation.expires_at,
        invitation_url=invitation_url
    )


# ============ Public Invitation Acceptance Endpoints ============


@router.get(
    "/accept/{token}",
    response_model=InvitationAcceptInfo,
    summary="Get invitation details",
    description="Get invitation details for the acceptance page. Public endpoint."
)
async def get_invitation_details(
    token: str,
    db: Session = Depends(get_db)
):
    """Get invitation details for the acceptance page.

    This is a public endpoint - no authentication required.
    Returns information needed to display the acceptance page.
    """
    # Find invitation by token
    invitation = get_invitation_by_token(db, token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token"
        )

    # Check if invitation is still valid
    if not is_invitation_valid(invitation):
        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been accepted"
            )
        elif invitation.status == InvitationStatus.REVOKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has been revoked"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired"
            )

    # Get organization
    org = db.query(Organization).filter(
        Organization.id == invitation.organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Get inviter name
    inviter = db.query(UserModel).filter(
        UserModel.id == invitation.created_by
    ).first()

    # Check if user already exists
    existing_user = db.query(UserModel).filter(
        UserModel.email == invitation.email.lower()
    ).first()

    # Get custom message from metadata
    custom_message = None
    if invitation.invitation_metadata:
        custom_message = invitation.invitation_metadata.get("custom_message")

    return InvitationAcceptInfo(
        organization_name=org.name,
        organization_type=org.type,
        email=invitation.email,
        org_role=invitation.org_role,
        expires_at=invitation.expires_at,
        invited_by_name=inviter.full_name if inviter else None,
        custom_message=custom_message,
        requires_registration=existing_user is None
    )


@router.post(
    "/accept/{token}",
    response_model=AcceptedInvitationResponse,
    summary="Accept an invitation",
    description="Accept an invitation. Creates user account if needed."
)
async def accept_org_invitation(
    token: str,
    accept_data: AcceptInvitation,
    db: Session = Depends(get_db)
):
    """Accept an invitation and join the organization.

    This is a public endpoint - no authentication required.

    For **existing users**: No additional data needed, just the token.
    For **new users**: `full_name` and `password` are required to create an account.
    """
    # Find invitation by token
    invitation = get_invitation_by_token(db, token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token"
        )

    # Check if invitation is still valid
    if not is_invitation_valid(invitation):
        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been accepted"
            )
        elif invitation.status == InvitationStatus.REVOKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has been revoked"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired"
            )

    # Get organization
    org = db.query(Organization).filter(
        Organization.id == invitation.organization_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user exists
    user = db.query(UserModel).filter(
        UserModel.email == invitation.email.lower()
    ).first()

    is_new_user = user is None
    access_token = None

    if is_new_user:
        # Validate required fields for new user
        if not accept_data.full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_name is required for new users"
            )
        if not accept_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="password is required for new users"
            )

        # Create new user
        user = UserModel(
            email=invitation.email.lower(),
            full_name=accept_data.full_name,
            hashed_password=get_password_hash(accept_data.password),
            role=UserRole.VIEWER,  # Default role for new users
            organization_id=invitation.organization_id,
            is_active=True,
            created_at=datetime.utcnow(),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Created new user {user.email} via invitation")

        # Generate access token for new user
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value
            }
        )

    # Accept the invitation
    try:
        membership = accept_invitation(db, invitation, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    logger.info(
        f"User {user.email} accepted invitation to org {org.name} "
        f"with role {invitation.org_role.value}"
    )

    return AcceptedInvitationResponse(
        success=True,
        message=f"Successfully joined {org.name}",
        user_id=user.id,
        organization_id=org.id,
        organization_name=org.name,
        org_role=invitation.org_role,
        is_new_user=is_new_user,
        access_token=access_token
    )
