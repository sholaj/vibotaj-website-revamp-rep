"""Audit log model for tracking user actions."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..database import Base


class AuditLog(Base):
    """Audit log entity - tracks all user actions for compliance and debugging."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who performed the action
    user_id = Column(String(100), nullable=True)  # Can be null for system actions
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45))  # IPv6 can be up to 45 chars
    user_agent = Column(String(500))

    # What action was performed
    action = Column(String(100), nullable=False)  # e.g., "shipment.view", "document.upload"
    resource_type = Column(String(50))  # e.g., "shipment", "document"
    resource_id = Column(String(100))  # ID of the affected resource

    # Request details
    request_id = Column(String(100), index=True)  # For correlating related logs
    method = Column(String(10))  # HTTP method
    path = Column(String(500))  # Request path

    # Result
    status_code = Column(String(10))  # HTTP status code
    success = Column(String(10), default="true")  # Whether action succeeded

    # Additional context
    details = Column(JSONB, default={})  # Flexible JSON for action-specific data
    error_message = Column(Text)  # Error details if action failed

    # Timing
    duration_ms = Column(String(20))  # Request duration
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_audit_logs_user_timestamp', 'username', 'timestamp'),
        Index('ix_audit_logs_action_timestamp', 'action', 'timestamp'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username} at {self.timestamp}>"
