"""Integration credential model for third-party API configs (PRD-021).

Stores per-org API credentials and configuration for customs and banking integrations.
Scoped by organization_id for multi-tenancy.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from ..database import Base


class IntegrationCredential(Base):
    """Organization-scoped integration configuration."""

    __tablename__ = "integration_credentials"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "integration_type",
            name="uq_integration_credentials_org_type",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    integration_type = Column(String(50), nullable=False)  # 'customs', 'banking'
    provider = Column(String(50), nullable=False)  # 'ncs', 'son', 'gtbank', 'mock'
    config = Column(JSON, nullable=False, default=dict)  # provider-specific config
    is_active = Column(Boolean, nullable=False, default=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_success = Column(Boolean, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization = relationship("Organization", backref="integration_credentials")

    def __repr__(self) -> str:
        return (
            f"<IntegrationCredential org={self.organization_id} "
            f"type={self.integration_type} provider={self.provider}>"
        )
