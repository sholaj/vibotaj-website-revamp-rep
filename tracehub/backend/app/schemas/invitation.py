"""Invitation schemas for API requests and responses.

Sprint 13.1: Backend Invitation Endpoints

These schemas are specifically for the invitation management endpoints.
Some overlap with schemas/organization.py but provide more focused models
for the invitation workflow.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import re

from ..models.organization import OrgRole, InvitationStatus, OrganizationType


class InvitationCreate(BaseModel):
    """Schema for creating a new invitation.

    Used by POST /organizations/{org_id}/invitations
    """
    email: EmailStr = Field(..., description="Email address to invite")
    org_role: OrgRole = Field(
        default=OrgRole.MEMBER,
        description="Role to assign when invitation is accepted"
    )
    message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Custom message to include in the invitation email"
    )


class InvitationResponse(BaseModel):
    """Schema for invitation response.

    Returned by invitation management endpoints.
    Does not include the token (which is only returned on creation).
    """
    id: UUID
    organization_id: UUID
    organization_name: Optional[str] = None
    email: str
    org_role: OrgRole
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvitationCreateResponse(BaseModel):
    """Schema for invitation creation response.

    Includes the invitation_url which contains the token.
    This is only returned once during creation.
    """
    id: UUID
    organization_id: UUID
    organization_name: str
    email: str
    org_role: OrgRole
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime
    invitation_url: str = Field(
        ...,
        description="URL for the invitee to accept the invitation (includes token)"
    )

    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    """Schema for paginated invitation list."""
    items: List[InvitationResponse]
    total: int
    limit: int
    offset: int


class InvitationAcceptInfo(BaseModel):
    """Schema for public invitation details (for acceptance page).

    Used by GET /accept/{token} to show invitation details
    before the user accepts.
    """
    organization_name: str
    organization_type: OrganizationType
    email: str
    org_role: OrgRole
    expires_at: datetime
    invited_by_name: Optional[str] = None
    custom_message: Optional[str] = None
    requires_registration: bool = Field(
        ...,
        description="True if the invitee needs to create an account"
    )


class AcceptInvitation(BaseModel):
    """Schema for accepting an invitation.

    Used by POST /accept/{token}
    For existing users, only the token is needed (passed in URL).
    For new users, full_name and password are required.
    """
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Required for new users"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="Required for new users"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class AcceptedInvitationResponse(BaseModel):
    """Schema for successful invitation acceptance.

    Used by POST /accept/{token}
    """
    success: bool = True
    message: str
    user_id: UUID
    organization_id: UUID
    organization_name: str
    org_role: OrgRole
    is_new_user: bool = Field(
        ...,
        description="True if a new user account was created"
    )
    access_token: Optional[str] = Field(
        None,
        description="JWT token for immediate login (only for new users)"
    )
    token_type: str = "bearer"


class ResendInvitationResponse(BaseModel):
    """Schema for invitation resend response."""
    id: UUID
    email: str
    org_role: OrgRole
    status: InvitationStatus
    expires_at: datetime
    message: str = "Invitation resent successfully"
    invitation_url: str = Field(
        ...,
        description="New URL for the invitee to accept the invitation"
    )


class InvitationError(BaseModel):
    """Schema for invitation-related errors."""
    error: str
    code: str
    details: Optional[dict] = None
