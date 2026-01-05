"""User model for authentication and authorization."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class UserRole(str, enum.Enum):
    """User roles for role-based access control.

    Role hierarchy (highest to lowest):
    - admin: Full access to everything
    - compliance: Can validate/approve documents, view all shipments
    - logistics_agent: Schedule containers, upload ALL documents, manage shipments
    - buyer: Read-only view of their shipments and documents
    - supplier: Upload origin certificates, provide geolocation data
    - viewer: Read-only access to all data
    """
    ADMIN = "admin"
    COMPLIANCE = "compliance"
    LOGISTICS_AGENT = "logistics_agent"
    BUYER = "buyer"
    SUPPLIER = "supplier"
    VIEWER = "viewer"


class User(Base):
    """User entity for authentication and access control."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Multi-tenancy: Link to organization
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])
    memberships = relationship("OrganizationMembership", back_populates="user", foreign_keys="OrganizationMembership.user_id")

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"

    def to_dict(self):
        """Convert user to dictionary (excludes password)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
