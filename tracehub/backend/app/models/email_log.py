"""Email log model for tracking email delivery (PRD-020)."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class EmailLog(Base):
    """Tracks all sent emails for auditing and debugging."""

    __tablename__ = "email_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recipient_email = Column(String(320), nullable=False)
    event_type = Column(String(50), nullable=False)
    subject = Column(String(500), nullable=False)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, sent, failed
    provider = Column(String(50), nullable=False)
    provider_message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<EmailLog to={self.recipient_email} "
            f"event={self.event_type} status={self.status}>"
        )
