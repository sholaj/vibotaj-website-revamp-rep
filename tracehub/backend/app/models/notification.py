"""Notification model for user alerts and updates."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Index
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

    # User targeting - for POC using username, can be enhanced to user_id FK later
    user_id = Column(String(100), nullable=False, index=True)

    # Notification content
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Related data for linking to shipments/documents
    data = Column(JSONB, default={})

    # Status
    read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "data": self.data or {},
            "read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
