"""Document schemas for API responses."""

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from ..models.document import DocumentType, DocumentStatus


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: UUID
    shipment_id: UUID
    document_type: DocumentType
    document_types: List[str] = []  # Multiple document types in single PDF
    name: str
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    status: DocumentStatus
    required: bool
    reference_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    validated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    """Document upload request."""
    shipment_id: UUID
    document_type: DocumentType  # Primary type
    document_types: Optional[List[str]] = None  # Additional types if PDF contains multiple docs
    reference_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
