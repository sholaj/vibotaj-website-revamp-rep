"""ReferenceRegistry model for duplicate detection."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from .document import DocumentType


class ReferenceRegistry(Base):
    """Registry of document reference numbers for duplicate detection.

    Tracks all unique reference numbers per shipment to detect when the same
    document is uploaded multiple times (potential duplicate or version conflict).
    """

    __tablename__ = "reference_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)

    # Reference number info
    reference_number = Column(String(100), nullable=False, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)

    # Link to the document content where this was first found
    document_content_id = Column(UUID(as_uuid=True), ForeignKey("document_contents.id", ondelete="SET NULL"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"))

    # Timestamps
    first_seen_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment")
    document_content = relationship("DocumentContent")
    document = relationship("Document")

    # Ensure unique reference number per shipment and document type
    __table_args__ = (
        UniqueConstraint('shipment_id', 'reference_number', 'document_type',
                         name='uq_reference_per_shipment_type'),
    )

    def __repr__(self):
        return f"<ReferenceRegistry {self.document_type.value}: {self.reference_number}>"
