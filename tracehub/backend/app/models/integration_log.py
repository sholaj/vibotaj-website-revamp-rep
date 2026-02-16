"""Integration log model for API call audit trail (PRD-021).

Records every customs/banking API call for debugging and compliance audit.
Scoped by organization_id for multi-tenancy.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class IntegrationLog(Base):
    """Audit log for integration API calls."""

    __tablename__ = "integration_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    integration_type = Column(String(50), nullable=False)  # 'customs', 'banking'
    provider = Column(String(50), nullable=False)  # 'ncs', 'gtbank', 'mock'
    method = Column(String(100), nullable=False)  # 'check_pre_clearance', etc.
    request_summary = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False)  # 'success', 'error', 'timeout'
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    shipment_id = Column(UUID(as_uuid=True), nullable=True)  # optional link
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<IntegrationLog type={self.integration_type} "
            f"method={self.method} status={self.status}>"
        )
