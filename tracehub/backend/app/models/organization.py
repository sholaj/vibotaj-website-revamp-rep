"""Organization model for multi-tenancy support.

Sprint 8: Multi-Tenancy Feature
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Boolean, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class OrganizationType(str, enum.Enum):
    """Types of organizations in the system."""
    VIBOTAJ = "vibotaj"           # Platform owner - full system access
    BUYER = "buyer"               # Importing companies (German partners)
    SUPPLIER = "supplier"         # Exporting companies (African suppliers)
    LOGISTICS_AGENT = "logistics_agent"  # Freight forwarders, customs agents


class OrganizationStatus(str, enum.Enum):
    """Organization status values."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_SETUP = "pending_setup"


class Organization(Base):
    """Organization entity - the primary tenant boundary.

    All data in the system is scoped to an organization.
    VIBOTAJ-type organizations have cross-tenant access.
    """

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(Enum(OrganizationType), nullable=False)
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE, nullable=False)

    # Contact information
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))

    # Address (stored as JSON for flexibility)
    address = Column(JSON, default=dict)

    # Business identifiers
    tax_id = Column(String(100))
    registration_number = Column(String(100))

    # Branding
    logo_url = Column(String(500))

    # Settings (stored as JSON for flexibility)
    settings = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", foreign_keys="User.organization_id")
    shipments = relationship("Shipment", back_populates="organization", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="organization", cascade="all, delete-orphan")
    container_events = relationship("ContainerEvent", back_populates="organization", cascade="all, delete-orphan")
    origins = relationship("Origin", back_populates="organization", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_organizations_type_status", "type", "status"),
        Index("ix_organizations_name", "name"),
    )

    def __repr__(self):
        return f"<Organization {self.name} ({self.type.value})>"

    def to_dict(self):
        """Convert organization to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "type": self.type.value,
            "status": self.status.value,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "address": self.address,
            "tax_id": self.tax_id,
            "registration_number": self.registration_number,
            "logo_url": self.logo_url,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrgRole(str, enum.Enum):
    """Roles within an organization.

    Role hierarchy (highest to lowest):
    - admin: Full access to organization resources
    - manager: Can manage shipments, documents, and invite members
    - member: Standard access to organization resources
    - viewer: Read-only access
    """
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class MembershipStatus(str, enum.Enum):
    """Membership status values."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class OrganizationMembership(Base):
    """Membership linking users to organizations.

    Users can belong to multiple organizations with different roles.
    """

    __tablename__ = "organization_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    org_role = Column(Enum(OrgRole), default=OrgRole.MEMBER, nullable=False)
    status = Column(Enum(MembershipStatus), default=MembershipStatus.ACTIVE, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, default=datetime.utcnow)

    # Invitation tracking
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    invitation_id = Column(UUID(as_uuid=True), ForeignKey("invitations.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    invitation = relationship("Invitation", back_populates="accepted_membership")

    # Indexes and constraints
    __table_args__ = (
        Index("ix_membership_user_org", "user_id", "organization_id", unique=True),
        Index("ix_membership_org_role", "organization_id", "org_role"),
        Index("ix_membership_user_primary", "user_id", "is_primary"),
    )

    def __repr__(self):
        return f"<Membership user={self.user_id} org={self.organization_id} role={self.org_role.value}>"

    def to_dict(self):
        """Convert membership to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "organization_id": str(self.organization_id),
            "org_role": self.org_role.value,
            "status": self.status.value,
            "is_primary": self.is_primary,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }


class InvitationStatus(str, enum.Enum):
    """Invitation status values."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Invitation(Base):
    """Invitation to join an organization.

    Invitations use secure, single-use tokens with expiration.
    """

    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    org_role = Column(Enum(OrgRole), default=OrgRole.MEMBER, nullable=False)

    # Token (stored as hash)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)

    # Status
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Additional data (named to avoid SQLAlchemy reserved 'metadata')
    invitation_metadata = Column(JSON, default=dict)

    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    creator = relationship("User", foreign_keys=[created_by])
    accepter = relationship("User", foreign_keys=[accepted_by])
    accepted_membership = relationship("OrganizationMembership", back_populates="invitation", uselist=False)

    # Indexes
    __table_args__ = (
        Index("ix_invitation_org_email", "organization_id", "email"),
        Index("ix_invitation_status", "status"),
        Index("ix_invitation_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<Invitation {self.email} -> {self.organization_id} ({self.status.value})>"

    def to_dict(self):
        """Convert invitation to dictionary."""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "email": self.email,
            "org_role": self.org_role.value,
            "status": self.status.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "metadata": self.invitation_metadata,
        }

    @property
    def is_expired(self) -> bool:
        """Check if the invitation has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the invitation is still valid (pending and not expired)."""
        return self.status == InvitationStatus.PENDING and not self.is_expired


# Role hierarchy for permission comparisons
ORG_ROLE_HIERARCHY = {
    OrgRole.ADMIN: 4,
    OrgRole.MANAGER: 3,
    OrgRole.MEMBER: 2,
    OrgRole.VIEWER: 1,
}


def can_manage_org_role(manager_role: OrgRole, target_role: OrgRole) -> bool:
    """Check if a role can manage another role in an organization.

    You can manage roles strictly lower than your own.
    """
    return ORG_ROLE_HIERARCHY.get(manager_role, 0) > ORG_ROLE_HIERARCHY.get(target_role, 0)


def is_org_role_higher_or_equal(role: OrgRole, compared_to: OrgRole) -> bool:
    """Check if a role is higher or equal to another."""
    return ORG_ROLE_HIERARCHY.get(role, 0) >= ORG_ROLE_HIERARCHY.get(compared_to, 0)
