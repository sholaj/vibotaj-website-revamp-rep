"""Document model for shipment documentation."""

import uuid
import enum
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Enum, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base


class DocumentType(str, enum.Enum):
    """Types of shipping documents."""
    BILL_OF_LADING = "bill_of_lading"
    COMMERCIAL_INVOICE = "commercial_invoice"
    PACKING_LIST = "packing_list"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    PHYTOSANITARY_CERTIFICATE = "phytosanitary_certificate"
    FUMIGATION_CERTIFICATE = "fumigation_certificate"
    SANITARY_CERTIFICATE = "sanitary_certificate"
    INSURANCE_CERTIFICATE = "insurance_certificate"
    CUSTOMS_DECLARATION = "customs_declaration"
    CONTRACT = "contract"
    EUDR_DUE_DILIGENCE = "eudr_due_diligence"
    QUALITY_CERTIFICATE = "quality_certificate"
    # Horn & Hoof specific documents (HS 0506/0507)
    EU_TRACES_CERTIFICATE = "eu_traces_certificate"  # Animal Health Certificate for EU
    VETERINARY_HEALTH_CERTIFICATE = "veterinary_health_certificate"
    EXPORT_DECLARATION = "export_declaration"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    """Document lifecycle states."""
    DRAFT = "draft"
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    COMPLIANCE_OK = "compliance_ok"
    COMPLIANCE_FAILED = "compliance_failed"
    LINKED = "linked"
    ARCHIVED = "archived"


class Document(Base):
    """Document entity - files attached to shipments."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)

    # Document classification
    document_type = Column(Enum(DocumentType), nullable=False)  # Primary type
    document_types = Column(JSONB, default=[])  # Multiple types when PDF contains several docs
    name = Column(String(255), nullable=False)

    # File information
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))

    # Status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False)
    required = Column(Boolean, default=True)

    # Multi-document PDF flags
    is_combined = Column(Boolean, default=False)  # True if PDF contains multiple document types
    content_count = Column(Integer, default=1)  # Number of document types detected in this file
    page_count = Column(Integer)  # Total pages in the PDF

    # Document metadata
    reference_number = Column(String(100))  # Document's own reference
    issue_date = Column(Date)
    expiry_date = Column(Date)
    issuing_authority = Column(String(255))

    # Validation
    validation_notes = Column(Text)
    uploaded_by = Column(String(100))
    uploaded_at = Column(DateTime)
    validated_at = Column(DateTime)
    validated_by = Column(String(100))

    # Additional metadata (flexible)
    extra_data = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="documents")
    contents = relationship("DocumentContent", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document {self.document_type.value}: {self.name}>"
