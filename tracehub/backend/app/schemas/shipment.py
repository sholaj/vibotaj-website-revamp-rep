"""Shipment schemas for API responses."""

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from ..models.shipment import ShipmentStatus


class ShipmentCreate(BaseModel):
    """Schema for creating a new shipment."""
    reference: str
    container_number: str
    bl_number: Optional[str] = None
    booking_reference: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    atd: Optional[datetime] = None
    ata: Optional[datetime] = None
    pol_code: Optional[str] = None
    pol_name: Optional[str] = None
    pod_code: Optional[str] = None
    pod_name: Optional[str] = None
    final_destination: Optional[str] = None
    incoterms: Optional[str] = None
    status: Optional[ShipmentStatus] = ShipmentStatus.IN_TRANSIT
    # For historical shipments, set is_historical=True
    is_historical: Optional[bool] = False
    notes: Optional[str] = None


class PartyInfo(BaseModel):
    """Party information in responses."""
    id: UUID
    company_name: str
    country: Optional[str] = None

    class Config:
        from_attributes = True


class ProductInfo(BaseModel):
    """Product information in responses."""
    id: UUID
    hs_code: str
    description: str
    quantity_net_kg: Optional[float] = None
    quantity_gross_kg: Optional[float] = None
    packaging_type: Optional[str] = None

    class Config:
        from_attributes = True


class EventInfo(BaseModel):
    """Container event in responses."""
    id: UUID
    event_type: str
    event_timestamp: datetime
    location_code: Optional[str] = None
    location_name: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None

    class Config:
        from_attributes = True


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


class DocumentSummary(BaseModel):
    """Document completeness summary."""
    total_required: int
    total_uploaded: int
    complete: int
    missing: List[str]
    pending_validation: int
    is_complete: bool


class ShipmentResponse(BaseModel):
    """Basic shipment response."""
    id: UUID
    reference: str
    container_number: str
    bl_number: Optional[str] = None
    booking_reference: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    atd: Optional[datetime] = None
    ata: Optional[datetime] = None
    pol_code: Optional[str] = None
    pol_name: Optional[str] = None
    pod_code: Optional[str] = None
    pod_name: Optional[str] = None
    final_destination: Optional[str] = None
    incoterms: Optional[str] = None
    status: ShipmentStatus
    created_at: datetime
    updated_at: datetime

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
    latest_event: Optional[EventInfo] = None
    documents: List[DocumentInfo] = []
    document_summary: DocumentSummary

    class Config:
        from_attributes = True
