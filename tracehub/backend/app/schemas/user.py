"""User schemas for API requests and responses."""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import re

from ..models.user import UserRole
from ..models.organization import OrgRole, OrganizationType


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=128)

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


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
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


class UserResponse(BaseModel):
    """Schema for user response (excludes password)."""
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    items: List[UserResponse]
    total: int
    page: int
    limit: int
    pages: int


class UserInToken(BaseModel):
    """User data stored in JWT token."""
    id: str
    email: str
    full_name: str
    role: str


class CurrentUser(BaseModel):
    """Current authenticated user with permissions."""
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    organization_id: UUID  # Multi-tenancy: the user's organization
    permissions: List[str] = []
    # Organization-scoped permissions
    org_role: Optional[OrgRole] = None
    org_type: Optional[OrganizationType] = None
    org_permissions: List[str] = []

    class Config:
        from_attributes = True

    # Backward compatibility with old User model
    @property
    def username(self) -> str:
        """Return email as username for backward compatibility."""
        return self.email
