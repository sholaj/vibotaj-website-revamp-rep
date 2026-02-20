"""Onboarding router for self-service signup and guided setup.

PRD-024: Self-Service Onboarding Flow

Provides endpoints for:
- Public self-service signup (creates org + membership)
- Onboarding state management (get, update, complete)
- Slug availability check
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.organization import (
    OrganizationMembership,
    OrgRole as OrgRoleModel,
    MembershipStatus,
)
from ..schemas.onboarding import (
    PublicSignupRequest,
    PublicSignupResponse,
    OnboardingStepUpdate,
    OnboardingStateResponse,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
    PlanInfo,
    SlugCheckResponse,
)
from ..schemas.user import CurrentUser
from .auth import get_current_active_user
from ..services.onboarding import (
    create_organization_with_signup,
    get_onboarding_state,
    update_onboarding_step,
    complete_onboarding,
    is_slug_available,
    generate_unique_slug,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Public Endpoints (No Auth Required) ============


@router.get(
    "/public/check-slug/{slug}",
    response_model=SlugCheckResponse,
    summary="Check slug availability",
    description="Check if an organization slug is available. Public endpoint.",
)
async def check_slug_availability(
    slug: str,
    db: Session = Depends(get_db),
):
    """Check if a slug is available for a new organization."""
    available = is_slug_available(db, slug)
    suggestion = None
    if not available:
        suggestion = generate_unique_slug(db, slug)

    return SlugCheckResponse(
        slug=slug,
        available=available,
        suggestion=suggestion,
    )


@router.post(
    "/public/signup",
    response_model=PublicSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Public self-service signup",
    description="Create a new organization via self-service signup. Requires authentication (user must register with PropelAuth first).",
)
async def public_signup(
    request: PublicSignupRequest,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new organization with the authenticated user as admin.

    Flow: User registers with PropelAuth first, then calls this endpoint
    to create their organization.
    """
    try:
        org = create_organization_with_signup(db, request, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SIGNUP_CONFLICT", "message": str(e)},
        )

    settings = org.settings or {}
    plan_data = settings.get("plan", {})
    plan = PlanInfo(**plan_data) if plan_data else PlanInfo()

    return PublicSignupResponse(
        organization_id=org.id,
        organization_name=org.name,
        organization_slug=org.slug,
        status=org.status,
        plan=plan,
    )


# ============ Authenticated Onboarding Endpoints ============


def _check_org_membership(
    current_user: CurrentUser, org_id: UUID, db: Session
) -> OrganizationMembership:
    """Verify user is an active member of the organization.

    Returns the membership if valid, raises 403 otherwise.
    """
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )

    return membership


@router.get(
    "/organizations/{org_id}/onboarding",
    response_model=OnboardingStateResponse,
    summary="Get onboarding state",
    description="Get the current onboarding progress for an organization.",
)
async def get_org_onboarding(
    org_id: UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get onboarding state for an organization."""
    _check_org_membership(current_user, org_id, db)

    state = get_onboarding_state(db, org_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"},
        )

    return OnboardingStateResponse(**state)


@router.patch(
    "/organizations/{org_id}/onboarding",
    response_model=OnboardingStateResponse,
    summary="Update onboarding step",
    description="Mark an onboarding step as completed.",
)
async def update_org_onboarding(
    org_id: UUID,
    step_update: OnboardingStepUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark an onboarding step as completed."""
    membership = _check_org_membership(current_user, org_id, db)

    # Only admins can update onboarding
    if membership.org_role != OrgRoleModel.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update onboarding",
        )

    try:
        state = update_onboarding_step(db, org_id, step_update.step)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ONBOARDING_ERROR", "message": str(e)},
        )

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"},
        )

    return OnboardingStateResponse(**state)


@router.post(
    "/organizations/{org_id}/onboarding/complete",
    response_model=OnboardingCompleteResponse,
    summary="Complete onboarding",
    description="Complete onboarding and activate the organization.",
)
async def complete_org_onboarding(
    org_id: UUID,
    request: OnboardingCompleteRequest,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Complete onboarding and set org status to active."""
    membership = _check_org_membership(current_user, org_id, db)

    # Only admins can complete onboarding
    if membership.org_role != OrgRoleModel.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can complete onboarding",
        )

    try:
        org = complete_onboarding(db, org_id, skip=request.skip)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ONBOARDING_ERROR", "message": str(e)},
        )

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORG_NOT_FOUND", "message": "Organization not found"},
        )

    action = "skipped" if request.skip else "completed"
    return OnboardingCompleteResponse(
        organization_id=org.id,
        status=org.status,
        message=f"Onboarding {action}. Organization is now active.",
    )
