"""Onboarding schemas for self-service signup and guided setup.

PRD-024: Self-Service Onboarding Flow
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum
import re

from .organization import OrganizationType, OrganizationStatus, Address


class PlanTier(str, Enum):
    """Available subscription plan tiers."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OnboardingStep(str, Enum):
    """Steps in the onboarding wizard."""

    PROFILE = "profile"
    ORGANIZATION = "organization"
    INVITE_TEAM = "invite_team"
    TOUR = "tour"


# ============ Plan Schemas ============


class PlanInfo(BaseModel):
    """Plan information stored in org settings."""

    tier: PlanTier = PlanTier.FREE
    selected_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None


# ============ Onboarding State Schemas ============


class OnboardingState(BaseModel):
    """Onboarding progress stored in org settings."""

    completed_steps: List[OnboardingStep] = Field(default_factory=list)
    completed_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None


# ============ Signup Request/Response ============


class PublicSignupRequest(BaseModel):
    """Request for public self-service signup."""

    org_name: str = Field(..., min_length=2, max_length=255)
    org_slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    org_type: OrganizationType
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)
    plan_tier: PlanTier = PlanTier.FREE
    user_full_name: str = Field(..., min_length=2, max_length=100)
    user_email: EmailStr
    address: Optional[Address] = None

    @field_validator("org_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug must contain only lowercase letters, numbers, and hyphens"
            )
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Slug cannot start or end with a hyphen")
        if "--" in v:
            raise ValueError("Slug cannot contain consecutive hyphens")
        return v


class PublicSignupResponse(BaseModel):
    """Response after successful public signup."""

    organization_id: UUID
    organization_name: str
    organization_slug: str
    status: OrganizationStatus
    plan: PlanInfo
    message: str = "Organization created successfully. Complete onboarding to activate."


# ============ Onboarding Step Update ============


class OnboardingStepUpdate(BaseModel):
    """Request to mark an onboarding step as completed."""

    step: OnboardingStep


class OnboardingStateResponse(BaseModel):
    """Response with current onboarding state."""

    organization_id: UUID
    status: OrganizationStatus
    plan: PlanInfo
    onboarding: OnboardingState
    all_steps_completed: bool = False


# ============ Onboarding Complete ============


class OnboardingCompleteRequest(BaseModel):
    """Request to complete onboarding and activate the organization."""

    skip: bool = False


class OnboardingCompleteResponse(BaseModel):
    """Response after completing onboarding."""

    organization_id: UUID
    status: OrganizationStatus
    message: str


# ============ Slug Check ============


class SlugCheckResponse(BaseModel):
    """Response for slug availability check."""

    slug: str
    available: bool
    suggestion: Optional[str] = None
