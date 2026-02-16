"""Compliance Result model for storing BoL compliance check results."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class ComplianceResult(Base):
    """Compliance result entity - stores individual rule check results.

    Each compliance check of a document generates multiple ComplianceResult
    records, one for each rule evaluated.
    """

    __tablename__ = "compliance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Rule information
    rule_id = Column(String(20), nullable=False)  # e.g., BOL-001
    rule_name = Column(String(100), nullable=False)  # Human-readable name
    passed = Column(Boolean, nullable=False)
    message = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)  # ERROR, WARNING, INFO
    field_path = Column(String(100), nullable=True)  # Field that was evaluated

    # Shipment-level result (PRD-016: shipment compliance aggregation)
    shipment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Document type tracking (PRD-016: generalize beyond BoL)
    document_type = Column(String(50), nullable=True)

    # Timestamps
    checked_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Organization (multi-tenancy)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    document = relationship("Document", back_populates="compliance_results")

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"<ComplianceResult {self.rule_id}: {status}>"
