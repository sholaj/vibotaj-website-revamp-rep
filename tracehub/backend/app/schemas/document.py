"""Document schemas for API responses."""

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from ..models.document import DocumentType, DocumentStatus


class DocumentResponse(BaseModel):
    """Document response schema - aligned with Document model field names."""
    id: UUID
    shipment_id: UUID
    document_type: DocumentType
    document_types: List[str] = []  # Multiple document types in single PDF
    name: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None  # Aligned with model (was file_size_bytes)
    mime_type: Optional[str] = None
    status: DocumentStatus
    required: bool = False
    reference_number: Optional[str] = None
    document_date: Optional[date] = None  # Aligned with model (was issue_date)
    expiry_date: Optional[date] = None
    issuer: Optional[str] = None  # Aligned with model (was issuing_authority)
    uploaded_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    validated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Container extraction fields (for BOL documents)
    extracted_container_number: Optional[str] = None
    extraction_confidence: Optional[float] = None

    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    """Document upload request - aligned with Document model field names."""
    shipment_id: UUID
    document_type: DocumentType  # Primary type
    document_types: Optional[List[str]] = None  # Additional types if PDF contains multiple docs
    reference_number: Optional[str] = None
    document_date: Optional[date] = None  # Aligned with model (was issue_date)
    expiry_date: Optional[date] = None
    issuer: Optional[str] = None  # Aligned with model (was issuing_authority)
