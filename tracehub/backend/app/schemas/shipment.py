"""Shipment schemas for API responses.

Updated to match production database schema (Sprint 8).
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from ..models.shipment import ShipmentStatus


class ShipmentCreate(BaseModel):
    """Schema for creating a new shipment."""
    reference: str
    container_number: str
    bl_number: Optional[str] = None
    booking_ref: Optional[str] = None  # Renamed from booking_reference
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    carrier_code: Optional[str] = None  # New field
    carrier_name: Optional[str] = None  # New field
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    atd: Optional[datetime] = None
    ata: Optional[datetime] = None
    pol_code: Optional[str] = None
    pol_name: Optional[str] = None
    pod_code: Optional[str] = None
    pod_name: Optional[str] = None
    incoterms: Optional[str] = None
    status: Optional[ShipmentStatus] = ShipmentStatus.DRAFT  # Changed default
    exporter_name: Optional[str] = None  # New field (replaces supplier_id)
    importer_name: Optional[str] = None  # New field (replaces buyer_id)
    eudr_compliant: Optional[bool] = False  # New field
    eudr_statement_id: Optional[str] = None  # New field
    organization_id: UUID  # Required for multi-tenancy
    # For historical shipments, set is_historical=True
    is_historical: Optional[bool] = False
    notes: Optional[str] = None


class ShipmentUpdate(BaseModel):
    """Schema for updating a shipment."""
    reference: Optional[str] = None
    container_number: Optional[str] = None
    bl_number: Optional[str] = None
    booking_ref: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    carrier_code: Optional[str] = None
    carrier_name: Optional[str] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    atd: Optional[datetime] = None
    ata: Optional[datetime] = None
    pol_code: Optional[str] = None
    pol_name: Optional[str] = None
    pod_code: Optional[str] = None
    pod_name: Optional[str] = None
    incoterms: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    exporter_name: Optional[str] = None
    importer_name: Optional[str] = None
    eudr_compliant: Optional[bool] = None
    eudr_statement_id: Optional[str] = None


class ProductInfo(BaseModel):
    """Product information in responses."""
    id: UUID
    hs_code: str
    description: Optional[str] = None
    quantity_net_kg: Optional[float] = None
    quantity_gross_kg: Optional[float] = None
    packaging_type: Optional[str] = None

    class Config:
        from_attributes = True


class EventInfo(BaseModel):
    """Container event in responses."""
    id: UUID
    event_status: str  # Matches ContainerEvent.event_status
    event_time: Optional[datetime] = None  # Can be null for some events
    location_code: Optional[str] = None
    location_name: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None

    class Config:
        from_attributes = True

    @validator('event_status', pre=True)
    def convert_event_status(cls, v):
        """Convert enum value to string."""
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v is not None else v


class DocumentInfo(BaseModel):
    """Document information in responses."""
    id: UUID
    document_type: str
    name: str
    status: str
    reference_number: Optional[str] = None
    issue_date: Optional[datetime] = None
    file_path: Optional[str] = None

    class Config:
        from_attributes = True

    @validator('document_type', 'status', pre=True)
    def convert_enum_to_str(cls, v):
        """Convert enum values to strings."""
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v is not None else v


class DocumentSummary(BaseModel):
    """Document completeness summary."""
    total_required: int
    total_uploaded: int
    complete: int
    missing: List[str]
    pending_validation: int
    is_complete: bool


class OrganizationInfo(BaseModel):
    """Organization information in responses."""
    id: UUID
    name: str
    slug: str
    type: str

    class Config:
        from_attributes = True


class ShipmentResponse(BaseModel):
    """Basic shipment response matching production database schema."""
    id: UUID
    reference: str
    container_number: str
    bl_number: Optional[str] = None
    booking_ref: Optional[str] = None  # Renamed from booking_reference
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    carrier_code: Optional[str] = None  # New field
    carrier_name: Optional[str] = None  # New field
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    atd: Optional[datetime] = None
    ata: Optional[datetime] = None
    pol_code: Optional[str] = None
    pol_name: Optional[str] = None
    pod_code: Optional[str] = None
    pod_name: Optional[str] = None
    incoterms: Optional[str] = None
    status: ShipmentStatus
    exporter_name: Optional[str] = None  # New field (replaces supplier relationship)
    importer_name: Optional[str] = None  # New field (replaces buyer relationship)
    eudr_compliant: Optional[bool] = False  # New field
    eudr_statement_id: Optional[str] = None  # New field
    organization_id: UUID  # New field for multi-tenancy
    created_at: datetime
    updated_at: datetime
    # Include products for HS code-based compliance checks (e.g., Horn & Hoof exemption)
    products: List[ProductInfo] = []

    class Config:
        from_attributes = True


class ShipmentListResponse(BaseModel):
    """Response for paginated shipment list."""
    items: List[ShipmentResponse]
    total: int
    page: int
    limit: int
    pages: int


class ShipmentDetailResponse(BaseModel):
    """Detailed shipment response with related entities."""
    shipment: ShipmentResponse
    organization: Optional[OrganizationInfo] = None
    latest_event: Optional[EventInfo] = None
    documents: List[DocumentInfo] = []
    document_summary: DocumentSummary

    class Config:
        from_attributes = True
