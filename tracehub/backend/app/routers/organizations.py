"""Organizations router for TraceHub API.

Provides endpoints for organization management, listing, and member management.
Admin-only access for most operations.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
import math

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models.organization import (
    Organization,
    OrganizationType as OrgTypeModel,
    OrganizationStatus as OrgStatusModel,
    OrganizationMembership,
    OrgRole as OrgRoleModel,
    MembershipStatus as MemberStatusModel,
)
from ..models.user import User as UserModel
from ..schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListItem,
    OrganizationListResponse,
    OrganizationType,
    OrganizationStatus,
    OrgRole,
    MembershipStatus,
    MembershipCreate,
    MembershipUpdate,
    MembershipResponse,
    MembershipListResponse,
)
from ..schemas.shipment import OrganizationInfo
from ..schemas.user import CurrentUser
from .auth import get_current_active_user
from ..services.permissions import Permission, has_permission

router = APIRouter()


def check_admin_permission(user: CurrentUser) -> None:
    """Check if user has system admin permission, raise 403 if not."""
    if not has_permission(user.role, Permission.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System admin access required"
        )


# ============ Organization CRUD Endpoints ============


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new organization. Admin only.

    Creates a new organization with the specified type (buyer, supplier, logistics_agent).
    The slug must be unique across all organizations.
    """
    check_admin_permission(current_user)

    # Check if slug already exists
    existing = db.query(Organization).filter(Organization.slug == org_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with slug '{org_data.slug}' already exists"
        )

    # Create organization
    org = Organization(
        name=org_data.name,
        slug=org_data.slug,
        type=OrgTypeModel(org_data.type.value),
        status=OrgStatusModel.ACTIVE,
        contact_email=org_data.contact_email,
        contact_phone=org_data.contact_phone,
        address=org_data.address.model_dump() if org_data.address else None,
        tax_id=org_data.tax_id,
        registration_number=org_data.registration_number,
        settings=org_data.settings.model_dump() if org_data.settings else None,
        created_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    # Get member count (0 for new org)
    return _org_to_response(org, member_count=0)


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    type: Optional[OrganizationType] = Query(None, description="Filter by organization type"),
    status: Optional[OrganizationStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name"),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all organizations with filtering and pagination. Admin only."""
    check_admin_permission(current_user)

    # Build base query with member count subquery
    member_count_subq = (
        db.query(
            OrganizationMembership.organization_id,
            func.count(OrganizationMembership.id).label("member_count")
        )
        .filter(OrganizationMembership.status == MemberStatusModel.ACTIVE)
        .group_by(OrganizationMembership.organization_id)
        .subquery()
    )

    query = db.query(Organization)

    # Apply filters
    if type:
        query = query.filter(Organization.type == OrgTypeModel(type.value))
    if status:
        query = query.filter(Organization.status == OrgStatusModel(status.value))
    if search:
        search_term = f"%{search}%"
        query = query.filter(Organization.name.ilike(search_term))

    # Get total count
    total = query.count()

    # Calculate pagination
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total > 0 else 1

    # Get organizations
    orgs = (
        query
        .order_by(Organization.name)
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Get member counts for all orgs in one query
    org_ids = [org.id for org in orgs]
    member_counts = dict(
        db.query(
            OrganizationMembership.organization_id,
            func.count(OrganizationMembership.id)
        )
        .filter(
            OrganizationMembership.organization_id.in_(org_ids),
            OrganizationMembership.status == MemberStatusModel.ACTIVE
        )
        .group_by(OrganizationMembership.organization_id)
        .all()
    )

    # Also count users directly assigned (legacy - user.organization_id)
    user_counts = dict(
        db.query(
            UserModel.organization_id,
            func.count(UserModel.id)
        )
        .filter(UserModel.organization_id.in_(org_ids))
        .group_by(UserModel.organization_id)
        .all()
    )

    items = []
    for org in orgs:
        # Combine membership count and direct user count
        count = member_counts.get(org.id, 0) + user_counts.get(org.id, 0)
        items.append(OrganizationListItem(
            id=org.id,
            name=org.name,
            slug=org.slug,
            type=OrganizationType(org.type.value),
            status=OrganizationStatus(org.status.value),
            member_count=count,
            created_at=org.created_at,
        ))

    return OrganizationListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/buyers", response_model=List[OrganizationInfo])
async def list_buyer_organizations(
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all buyer organizations for dropdown selection.

    Returns organizations with type=BUYER, ordered by name.
    Used for the buyer organization dropdown in shipment creation form.
    """
    buyers = db.query(Organization).filter(
        Organization.type == OrgTypeModel.BUYER,
        Organization.status == OrgStatusModel.ACTIVE
    ).order_by(Organization.name).all()

    return buyers


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get organization details by ID. Admin only."""
    check_admin_permission(current_user)

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Get member count
    member_count = db.query(func.count(OrganizationMembership.id)).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.status == MemberStatusModel.ACTIVE
    ).scalar()

    # Also count direct users
    user_count = db.query(func.count(UserModel.id)).filter(
        UserModel.organization_id == org_id
    ).scalar()

    return _org_to_response(org, member_count=member_count + user_count)


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    org_data: OrganizationUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update organization details. Admin only.

    Note: slug and type cannot be changed after creation.
    """
    check_admin_permission(current_user)

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update fields
    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "address" and value:
            setattr(org, field, value)
        elif field == "settings" and value:
            setattr(org, field, value)
        else:
            setattr(org, field, value)

    org.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(org)

    # Get member count
    member_count = db.query(func.count(OrganizationMembership.id)).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.status == MemberStatusModel.ACTIVE
    ).scalar()

    user_count = db.query(func.count(UserModel.id)).filter(
        UserModel.organization_id == org_id
    ).scalar()

    return _org_to_response(org, member_count=member_count + user_count)


# ============ Member Management Endpoints ============


@router.get("/{org_id}/members", response_model=MembershipListResponse)
async def list_organization_members(
    org_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List members of an organization. Admin only."""
    check_admin_permission(current_user)

    # Verify org exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Query memberships with user details
    query = (
        db.query(OrganizationMembership, UserModel)
        .join(UserModel, OrganizationMembership.user_id == UserModel.id)
        .filter(OrganizationMembership.organization_id == org_id)
    )

    # Get total count
    total = query.count()

    # Calculate pagination
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total > 0 else 1

    # Get members
    results = (
        query
        .order_by(OrganizationMembership.joined_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []
    for membership, user in results:
        items.append(MembershipResponse(
            id=membership.id,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            email=user.email,
            full_name=user.full_name,
            org_role=OrgRole(membership.org_role.value),
            status=MembershipStatus(membership.status.value),
            is_primary=membership.is_primary,
            joined_at=membership.joined_at,
            last_active_at=membership.last_active_at,
            invited_by=membership.invited_by,
        ))

    # Also include users directly assigned to this org (legacy)
    direct_users_query = (
        db.query(UserModel)
        .filter(UserModel.organization_id == org_id)
        .filter(~UserModel.id.in_(
            db.query(OrganizationMembership.user_id)
            .filter(OrganizationMembership.organization_id == org_id)
        ))
    )

    direct_users = direct_users_query.all()
    for user in direct_users:
        items.append(MembershipResponse(
            id=user.id,  # Use user id as membership id for direct users
            user_id=user.id,
            organization_id=org_id,
            email=user.email,
            full_name=user.full_name,
            org_role=OrgRole.MEMBER,  # Default role for legacy direct users
            status=MembershipStatus.ACTIVE,
            is_primary=True,
            joined_at=user.created_at,
            last_active_at=user.last_login,
            invited_by=None,
        ))

    return MembershipListResponse(
        items=items,
        total=total + len(direct_users),
        page=page,
        limit=limit,
        pages=pages
    )


@router.post("/{org_id}/members", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    org_id: UUID,
    member_data: MembershipCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a user to an organization. Admin only.

    Creates a new membership linking the user to the organization with the specified role.
    """
    check_admin_permission(current_user)

    # Verify org exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Verify user exists
    user = db.query(UserModel).filter(UserModel.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check for existing membership
    existing = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == member_data.user_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization"
        )

    # Check if this is user's first membership (make it primary)
    existing_memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == member_data.user_id
    ).count()
    is_primary = existing_memberships == 0

    # Create membership
    membership = OrganizationMembership(
        user_id=member_data.user_id,
        organization_id=org_id,
        org_role=OrgRoleModel(member_data.org_role.value),
        status=MemberStatusModel.ACTIVE,
        is_primary=is_primary,
        joined_at=datetime.utcnow(),
        invited_by=current_user.id,
    )

    db.add(membership)
    db.commit()
    db.refresh(membership)

    return MembershipResponse(
        id=membership.id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        email=user.email,
        full_name=user.full_name,
        org_role=OrgRole(membership.org_role.value),
        status=MembershipStatus(membership.status.value),
        is_primary=membership.is_primary,
        joined_at=membership.joined_at,
        last_active_at=membership.last_active_at,
        invited_by=membership.invited_by,
    )


@router.patch("/{org_id}/members/{user_id}", response_model=MembershipResponse)
async def update_organization_member(
    org_id: UUID,
    user_id: UUID,
    member_data: MembershipUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a member's role or status. Admin only."""
    check_admin_permission(current_user)

    # Find membership
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )

    # Update fields
    if member_data.org_role is not None:
        membership.org_role = OrgRoleModel(member_data.org_role.value)
    if member_data.status is not None:
        membership.status = MemberStatusModel(member_data.status.value)

    db.commit()
    db.refresh(membership)

    # Get user details
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    return MembershipResponse(
        id=membership.id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        email=user.email if user else None,
        full_name=user.full_name if user else None,
        org_role=OrgRole(membership.org_role.value),
        status=MembershipStatus(membership.status.value),
        is_primary=membership.is_primary,
        joined_at=membership.joined_at,
        last_active_at=membership.last_active_at,
        invited_by=membership.invited_by,
    )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a user from an organization. Admin only.

    Cannot remove the last admin from an organization.
    """
    check_admin_permission(current_user)

    # Find membership
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )

    # Check if this is the last admin
    if membership.org_role == OrgRoleModel.ADMIN:
        admin_count = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.org_role == OrgRoleModel.ADMIN,
            OrganizationMembership.status == MemberStatusModel.ACTIVE
        ).count()

        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin from an organization"
            )

    # If removing primary membership, reassign primary to another membership
    if membership.is_primary:
        other_membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.id != membership.id
        ).first()

        if other_membership:
            other_membership.is_primary = True

    db.delete(membership)
    db.commit()


# ============ Helper Functions ============


def _org_to_response(org: Organization, member_count: int = 0) -> OrganizationResponse:
    """Convert Organization model to OrganizationResponse schema."""
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        type=OrganizationType(org.type.value),
        status=OrganizationStatus(org.status.value),
        contact_email=org.contact_email,
        contact_phone=org.contact_phone,
        address=org.address,
        tax_id=org.tax_id,
        registration_number=org.registration_number,
        logo_url=org.logo_url,
        settings=org.settings,
        member_count=member_count,
        created_at=org.created_at,
        updated_at=org.updated_at,
        created_by=org.created_by,
    )
