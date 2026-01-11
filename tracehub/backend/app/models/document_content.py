"""DocumentContent model for tracking individual documents within a PDF."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base
from .document import DocumentType, DocumentStatus


class DocumentContent(Base):
    """Tracks individual documents detected within a combined PDF.

    When a PDF contains multiple documents (e.g., Bill of Lading + Certificate of Origin),
    each detected document type is stored as a separate DocumentContent record.
    This allows per-document-type validation and tracking.
    """

    __tablename__ = "document_contents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    # Document classification
    document_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)

    # Page range within the PDF
    page_start = Column(Integer, nullable=False, default=1)
    page_end = Column(Integer, nullable=False, default=1)

    # Reference number extracted from this document section
    reference_number = Column(String(100))

    # AI/OCR detection results
    detected_fields = Column(JSONB, default={})  # Extracted metadata fields
    confidence_score = Column(Float, default=0.0)  # Detection confidence (0.0 - 1.0)
    detection_method = Column(String(50), default="manual")  # "ai", "keyword", "manual"

    # Validation
    validation_notes = Column(String(1000))
    validated_at = Column(DateTime(timezone=True))  # Added timezone - Sprint 11
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))  # Changed from String to UUID FK - Sprint 11

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="contents")

    def __repr__(self):
        return f"<DocumentContent {self.document_type.value} pages {self.page_start}-{self.page_end}>"
