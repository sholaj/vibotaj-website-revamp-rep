"""Onboarding service for self-service signup and guided setup.

PRD-024: Self-Service Onboarding Flow

Provides functions for:
- Creating organizations via public signup
- Managing onboarding wizard state
- Generating unique slugs
- Calculating trial periods
"""

import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..models.organization import (
    Organization,
    OrganizationMembership,
    OrganizationStatus,
    OrgRole,
    MembershipStatus,
)
from ..models.user import User
from ..schemas.onboarding import (
    OnboardingState,
    OnboardingStep,
    PlanInfo,
    PlanTier,
    PublicSignupRequest,
)

logger = logging.getLogger(__name__)

# Trial duration for paid plans
TRIAL_DAYS = 14

# All onboarding steps in order
ALL_ONBOARDING_STEPS = [
    OnboardingStep.PROFILE,
    OnboardingStep.ORGANIZATION,
    OnboardingStep.INVITE_TEAM,
    OnboardingStep.TOUR,
]


def generate_unique_slug(db: Session, base_slug: str) -> str:
    """Generate a unique organization slug.

    If the base slug is taken, appends a numeric suffix.

    Args:
        db: Database session.
        base_slug: The desired slug (lowercase, alphanumeric + hyphens).

    Returns:
        A unique slug string.
    """
    # Normalize slug
    slug = re.sub(r"[^a-z0-9-]", "", base_slug.lower().strip())
    slug = re.sub(r"-+", "-", slug).strip("-")

    if not slug:
        slug = "org"

    # Check if base slug is available
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if not existing:
        return slug

    # Append numeric suffix
    for i in range(1, 100):
        candidate = f"{slug}-{i}"
        existing = db.query(Organization).filter(Organization.slug == candidate).first()
        if not existing:
            return candidate

    # Fallback: append short UUID
    return f"{slug}-{uuid.uuid4().hex[:6]}"


def is_slug_available(db: Session, slug: str) -> bool:
    """Check if an organization slug is available.

    Args:
        db: Database session.
        slug: The slug to check.

    Returns:
        True if the slug is not taken.
    """
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    return existing is None


def calculate_trial_end(plan_tier: PlanTier) -> Optional[datetime]:
    """Calculate trial end date for a plan tier.

    Free plans don't have trials. Paid plans get TRIAL_DAYS.

    Args:
        plan_tier: The selected plan tier.

    Returns:
        Trial end datetime, or None for free plans.
    """
    if plan_tier == PlanTier.FREE:
        return None
    return datetime.utcnow() + timedelta(days=TRIAL_DAYS)


def create_organization_with_signup(
    db: Session,
    request: PublicSignupRequest,
    user: User,
) -> Organization:
    """Create a new organization from a public signup request.

    Creates the organization with pending_setup status and adds
    the signing-up user as the admin.

    Args:
        db: Database session.
        request: The signup request data.
        user: The authenticated user creating the organization.

    Returns:
        The created Organization.

    Raises:
        ValueError: If slug is taken or user already owns an org.
    """
    # Verify slug is available
    if not is_slug_available(db, request.org_slug):
        raise ValueError(f"Slug '{request.org_slug}' is already taken")

    # Build plan info
    now = datetime.utcnow()
    plan_info = PlanInfo(
        tier=request.plan_tier,
        selected_at=now,
        trial_ends_at=calculate_trial_end(request.plan_tier),
    )

    # Build onboarding state
    onboarding_state = OnboardingState()

    # Build settings with plan and onboarding
    settings_dict = {
        "plan": plan_info.model_dump(mode="json"),
        "onboarding": onboarding_state.model_dump(mode="json"),
    }

    # Create organization
    org = Organization(
        name=request.org_name,
        slug=request.org_slug,
        type=request.org_type,
        status=OrganizationStatus.PENDING_SETUP,
        contact_email=request.contact_email,
        contact_phone=request.contact_phone,
        settings=settings_dict,
        created_at=now,
        created_by=user.id,
    )

    if request.address:
        org.address = request.address.model_dump()

    db.add(org)
    db.flush()  # Get the org ID before creating membership

    # Create admin membership
    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org.id,
        org_role=OrgRole.ADMIN,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
        joined_at=now,
    )
    db.add(membership)

    db.commit()
    db.refresh(org)

    logger.info(
        f"Created organization '{org.name}' (slug={org.slug}) via self-service signup "
        f"by user {user.email}, plan={request.plan_tier.value}"
    )

    return org


def get_onboarding_state(db: Session, org_id: uuid.UUID) -> Optional[dict]:
    """Get the onboarding state for an organization.

    Args:
        db: Database session.
        org_id: Organization UUID.

    Returns:
        Dict with org status, plan, and onboarding state, or None if org not found.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None

    settings = org.settings or {}
    plan_data = settings.get("plan", {})
    onboarding_data = settings.get("onboarding", {})

    plan = PlanInfo(**plan_data) if plan_data else PlanInfo()
    onboarding = (
        OnboardingState(**onboarding_data) if onboarding_data else OnboardingState()
    )

    all_completed = set(onboarding.completed_steps) >= set(ALL_ONBOARDING_STEPS)

    return {
        "organization_id": org.id,
        "status": org.status,
        "plan": plan,
        "onboarding": onboarding,
        "all_steps_completed": all_completed,
    }


def update_onboarding_step(
    db: Session,
    org_id: uuid.UUID,
    step: OnboardingStep,
) -> Optional[dict]:
    """Mark an onboarding step as completed.

    Args:
        db: Database session.
        org_id: Organization UUID.
        step: The step to mark as completed.

    Returns:
        Updated onboarding state dict, or None if org not found.

    Raises:
        ValueError: If onboarding is already completed.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None

    settings = org.settings or {}
    onboarding_data = settings.get("onboarding", {})
    onboarding = (
        OnboardingState(**onboarding_data) if onboarding_data else OnboardingState()
    )

    if onboarding.completed_at:
        raise ValueError("Onboarding is already completed")

    # Add step if not already completed
    if step not in onboarding.completed_steps:
        onboarding.completed_steps.append(step)

    # Update settings
    settings["onboarding"] = onboarding.model_dump(mode="json")
    org.settings = settings

    # SQLAlchemy needs to detect the change on JSON columns
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(org, "settings")

    db.commit()
    db.refresh(org)

    logger.info(f"Onboarding step '{step.value}' completed for org {org.slug}")

    return get_onboarding_state(db, org_id)


def complete_onboarding(
    db: Session,
    org_id: uuid.UUID,
    skip: bool = False,
) -> Optional[Organization]:
    """Complete onboarding and activate the organization.

    Args:
        db: Database session.
        org_id: Organization UUID.
        skip: If True, marks onboarding as skipped rather than completed.

    Returns:
        The updated Organization, or None if not found.

    Raises:
        ValueError: If org is not in pending_setup status.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None

    if org.status != OrganizationStatus.PENDING_SETUP:
        raise ValueError(
            f"Organization is not in pending_setup status (current: {org.status.value})"
        )

    settings = org.settings or {}
    onboarding_data = settings.get("onboarding", {})
    onboarding = (
        OnboardingState(**onboarding_data) if onboarding_data else OnboardingState()
    )

    now = datetime.utcnow()
    if skip:
        onboarding.skipped_at = now
    else:
        onboarding.completed_at = now

    settings["onboarding"] = onboarding.model_dump(mode="json")
    org.settings = settings
    org.status = OrganizationStatus.ACTIVE

    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(org, "settings")

    db.commit()
    db.refresh(org)

    action = "skipped" if skip else "completed"
    logger.info(f"Onboarding {action} for org {org.slug}, status set to active")

    return org
