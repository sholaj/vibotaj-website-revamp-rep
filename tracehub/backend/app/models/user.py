"""User model for authentication and authorization."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class UserRole(str, enum.Enum):
    """User roles for role-based access control.

    Role hierarchy (highest to lowest):
    - admin: Full access to everything
    - compliance: Can validate/approve documents, view all shipments
    - buyer: Read-only view of their shipments and documents
    - supplier: Can upload documents, view assigned shipments
    - viewer: Read-only access to all data
    """
    ADMIN = "admin"
    COMPLIANCE = "compliance"
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

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Optional: Link to party for buyer/supplier roles
    # party_id = Column(UUID(as_uuid=True), ForeignKey("parties.id"), nullable=True)

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
