"""Shipment schemas for API responses."""

from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime

from ..models.shipment import ShipmentStatus


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
    location_name: Optional[str] = None
    vessel_name: Optional[str] = None

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
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    pol_code: Optional[str] = None
    pol_name: Optional[str] = None
    pod_code: Optional[str] = None
    pod_name: Optional[str] = None
    incoterms: Optional[str] = None
    status: ShipmentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShipmentDetailResponse(BaseModel):
    """Detailed shipment response with related entities."""
    shipment: Any  # Shipment ORM object
    latest_event: Optional[Any] = None
    documents: List[Any] = []
    document_summary: DocumentSummary

    class Config:
        from_attributes = True
