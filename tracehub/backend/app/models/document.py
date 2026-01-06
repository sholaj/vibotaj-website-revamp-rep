"""Document model for shipment documentation."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
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
    """Document lifecycle states.

    Note: DB has (UPLOADED, PENDING_VALIDATION, VALIDATED, REJECTED, EXPIRED)
    but code also uses (DRAFT, COMPLIANCE_OK, COMPLIANCE_FAILED, LINKED, ARCHIVED)
    Keeping both sets for compatibility until refactor.
    """
    # DB values
    UPLOADED = "UPLOADED"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    # Legacy/code values (TODO: migrate these)
    DRAFT = "DRAFT"
    COMPLIANCE_OK = "COMPLIANCE_OK"
    COMPLIANCE_FAILED = "COMPLIANCE_FAILED"
    LINKED = "LINKED"
    ARCHIVED = "ARCHIVED"


class Document(Base):
    """Document entity - files attached to shipments (matches production schema)."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)

    # Document classification
    name = Column(String(255), nullable=False)
    document_type = Column(Enum(DocumentType, name="documenttype", create_type=False), nullable=False)
    status = Column(Enum(DocumentStatus, name="documentstatus", create_type=False), nullable=False)

    # File information
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)  # Named file_size in DB, not file_size_bytes
    mime_type = Column(String(100))

    # Document metadata
    document_date = Column(DateTime(timezone=True))  # Named document_date in DB, not issue_date
    expiry_date = Column(DateTime(timezone=True))
    issuer = Column(String(255))  # Named issuer in DB, not issuing_authority
    reference_number = Column(String(100))

    # Validation
    validation_notes = Column(Text)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime(timezone=True))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="documents")
    contents = relationship("DocumentContent", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document {self.document_type.value}: {self.name}>"
