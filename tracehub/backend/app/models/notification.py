"""Notification model for user alerts and updates."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_VALIDATED = "document_validated"
    DOCUMENT_REJECTED = "document_rejected"
    ETA_CHANGED = "eta_changed"
    SHIPMENT_ARRIVED = "shipment_arrived"
    SHIPMENT_DEPARTED = "shipment_departed"
    SHIPMENT_DELIVERED = "shipment_delivered"
    COMPLIANCE_ALERT = "compliance_alert"
    EXPIRY_WARNING = "expiry_warning"
    SYSTEM_ALERT = "system_alert"


class Notification(Base):
    """Notification entity - alerts and updates for users."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User targeting - Sprint 11: Changed from String(100) to UUID FK
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification content
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Related data for linking to shipments/documents
    data = Column(JSONB, default={})

    # Status
    read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)  # Added timezone - Sprint 11

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)  # Added timezone - Sprint 11

    # Relationship to user
    user = relationship("User", back_populates="notifications")

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_notifications_user_read', 'user_id', 'read'),
        Index('ix_notifications_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Notification {self.type}: {self.title[:50]}>"

    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),  # Convert UUID to string
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "data": self.data or {},
            "read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
