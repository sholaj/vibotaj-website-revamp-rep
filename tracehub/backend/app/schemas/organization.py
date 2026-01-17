"""Organization schemas for multi-tenancy API requests and responses.

Sprint 8: Multi-Tenancy Feature
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum
import re


class OrganizationType(str, Enum):
    """Types of organizations in the system."""
    VIBOTAJ = "vibotaj"
    BUYER = "buyer"
    SUPPLIER = "supplier"
    LOGISTICS_AGENT = "logistics_agent"


class OrganizationStatus(str, Enum):
    """Organization status values."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_SETUP = "pending_setup"


class OrgRole(str, Enum):
    """Roles within an organization."""
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class MembershipStatus(str, Enum):
    """Membership status values."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class InvitationStatus(str, Enum):
    """Invitation status values."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ============ Address Schemas ============

class AddressBase(BaseModel):
    """Base address schema."""
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")


class Address(AddressBase):
    """Full address schema."""
    pass


# ============ Organization Settings Schemas ============

class NotificationPreferences(BaseModel):
    """Notification preferences for an organization."""
    email_on_shipment_update: bool = True
    email_on_document_upload: bool = True
    email_on_compliance_issue: bool = True
    email_digest_frequency: str = Field(default="daily", pattern="^(realtime|daily|weekly|never)$")


class ComplianceSettings(BaseModel):
    """Compliance-related settings for an organization."""
    eudr_enabled: bool = True
    auto_validate_documents: bool = False
    require_document_approval: bool = True
    allowed_document_types: Optional[List[str]] = None


class OrganizationSettings(BaseModel):
    """Organization settings."""
    default_currency: str = Field(default="EUR", max_length=3)
    timezone: str = Field(default="Europe/Berlin", max_length=50)
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences)
    compliance_settings: ComplianceSettings = Field(default_factory=ComplianceSettings)


# ============ Organization Schemas ============

class OrganizationBase(BaseModel):
    """Base organization schema with common fields."""
    name: str = Field(..., min_length=2, max_length=255)
    type: OrganizationType
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[Address] = None
    tax_id: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    slug: str = Field(..., min_length=2, max_length=50, pattern="^[a-z0-9-]+$")
    settings: Optional[OrganizationSettings] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Slug cannot start or end with a hyphen")
        return v


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[Address] = None
    tax_id: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    settings: Optional[OrganizationSettings] = None
    logo_url: Optional[str] = Field(None, max_length=500)


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    type: OrganizationType
    status: OrganizationStatus
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[Address] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[OrganizationSettings] = None
    member_count: Optional[int] = None
    shipment_count: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None


class OrganizationListItem(BaseModel):
    """Schema for organization in list responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    type: OrganizationType
    status: OrganizationStatus
    member_count: int = 0
    created_at: datetime


class OrganizationListResponse(BaseModel):
    """Schema for paginated organization list."""
    items: List[OrganizationListItem]
    total: int
    page: int
    limit: int
    pages: int


class OrganizationStats(BaseModel):
    """Organization statistics."""
    organization_id: UUID
    period: str = "last_30_days"
    shipments: Dict[str, int]
    documents: Dict[str, int]
    compliance: Dict[str, Any]


# ============ Membership Schemas ============

class MembershipBase(BaseModel):
    """Base membership schema."""
    org_role: OrgRole = OrgRole.MEMBER


class MembershipCreate(MembershipBase):
    """Schema for adding a user to an organization."""
    user_id: UUID


class MembershipUpdate(BaseModel):
    """Schema for updating a membership."""
    org_role: Optional[OrgRole] = None
    status: Optional[MembershipStatus] = None


class MembershipResponse(BaseModel):
    """Schema for membership response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    organization_id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    org_role: OrgRole
    status: MembershipStatus
    is_primary: bool = False
    joined_at: datetime
    last_active_at: Optional[datetime] = None
    invited_by: Optional[UUID] = None
    permissions: Optional[List[str]] = None


class MembershipListResponse(BaseModel):
    """Schema for paginated membership list."""
    items: List[MembershipResponse]
    total: int
    page: int
    limit: int
    pages: int


class MemberSuspendRequest(BaseModel):
    """Request to suspend a member."""
    reason: Optional[str] = Field(None, max_length=500)


# ============ Invitation Schemas ============

class InvitationCreate(BaseModel):
    """Schema for creating an invitation."""
    organization_id: UUID
    email: EmailStr
    org_role: OrgRole = OrgRole.MEMBER
    custom_message: Optional[str] = Field(None, max_length=1000)
    redirect_url: Optional[str] = Field(None, max_length=500)


class InvitationResponse(BaseModel):
    """Schema for invitation response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    organization_name: Optional[str] = None
    organization_type: Optional[OrganizationType] = None
    email: str
    org_role: OrgRole
    status: InvitationStatus
    custom_message: Optional[str] = None
    invitation_url: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    accepted_at: Optional[datetime] = None


class InvitationListResponse(BaseModel):
    """Schema for paginated invitation list."""
    items: List[InvitationResponse]
    total: int
    page: int
    limit: int
    pages: int


class InvitationValidateRequest(BaseModel):
    """Request to validate an invitation token."""
    token: str


class InvitationValidateResponse(BaseModel):
    """Response for invitation validation."""
    valid: bool
    invitation_id: Optional[UUID] = None
    organization_name: Optional[str] = None
    organization_type: Optional[OrganizationType] = None
    email: Optional[str] = None
    org_role: Optional[OrgRole] = None
    expires_at: Optional[datetime] = None
    requires_registration: bool = False
    custom_message: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None


class InvitationAcceptRequest(BaseModel):
    """Request to accept an invitation."""
    token: str


class InvitationAcceptResponse(BaseModel):
    """Response for invitation acceptance."""
    message: str
    membership: MembershipResponse
    new_token: str


# ============ Session Schemas ============

class UserOrganization(BaseModel):
    """Schema for organization in user's context."""
    id: UUID
    name: str
    slug: str
    type: OrganizationType
    org_role: OrgRole
    is_primary: bool
    is_current: bool = False


class SessionOrganizationsResponse(BaseModel):
    """Response for user's organizations."""
    user_id: UUID
    current_organization_id: Optional[UUID] = None
    organizations: List[UserOrganization]


class SwitchOrgRequest(BaseModel):
    """Request to switch organization context."""
    organization_id: UUID


class SwitchOrgResponse(BaseModel):
    """Response for organization switch."""
    message: str
    organization: UserOrganization
    access_token: str
    token_type: str = "bearer"
    permissions: List[str]


class SetPrimaryOrgRequest(BaseModel):
    """Request to set primary organization."""
    organization_id: UUID


class SetPrimaryOrgResponse(BaseModel):
    """Response for setting primary organization."""
    message: str
    primary_organization_id: UUID


class SessionUser(BaseModel):
    """User info in session context."""
    id: UUID
    email: str
    full_name: str
    system_role: str


class SessionOrganization(BaseModel):
    """Organization info in session context."""
    id: UUID
    name: str
    slug: str
    type: OrganizationType


class SessionMembership(BaseModel):
    """Membership info in session context."""
    org_role: OrgRole
    is_primary: bool
    joined_at: datetime


class SessionContextResponse(BaseModel):
    """Full session context response."""
    user: SessionUser
    organization: SessionOrganization
    membership: SessionMembership
    permissions: List[str]
    can_switch_organizations: bool
    organization_count: int


# ============ Updated Auth Schemas ============

class LoginResponseWithOrg(BaseModel):
    """Login response with organization context."""
    access_token: str
    token_type: str = "bearer"
    user: SessionUser
    organization: SessionOrganization
    organizations_count: int
    permissions: List[str]


class RegisterWithInvitationRequest(BaseModel):
    """Registration request with invitation token."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    invitation_token: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class RegisterWithInvitationResponse(BaseModel):
    """Registration response with organization context."""
    access_token: str
    token_type: str = "bearer"
    user: SessionUser
    organization: SessionOrganization
    membership: SessionMembership


# ============ Error Schemas ============

class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail
