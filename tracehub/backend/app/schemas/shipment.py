"""Shipment schemas for API responses.

Updated to match production database schema (Sprint 8).
"""

import re
from pydantic import BaseModel, validator, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from ..models.shipment import ShipmentStatus, ProductType

# ISO 6346 container number format: 4 letters + 7 digits
ISO_6346_PATTERN = re.compile(r'^[A-Z]{4}[0-9]{7}$')


class ShipmentCreate(BaseModel):
    """Schema for creating a new shipment."""
    reference: str
    container_number: str
    product_type: ProductType  # Required - determines document requirements
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
    organization_id: Optional[UUID] = None  # Auto-injected from current user if not provided
    buyer_organization_id: Optional[UUID] = None  # Optional buyer org (HAGES, Witatrade, etc.)
    # For historical shipments, set is_historical=True
    is_historical: Optional[bool] = False
    notes: Optional[str] = None

    @field_validator('container_number')
    @classmethod
    def validate_container_number(cls, v: str) -> str:
        """Validate ISO 6346 container number format.

        Format: 4 letters (owner code) + 7 digits (serial + check digit)
        Pattern: ^[A-Z]{4}[0-9]{7}$
        Examples: MRSU3452572, TCNU1234567, MSKU9876543

        Args:
            v: Container number to validate

        Returns:
            Normalized (uppercase, trimmed) container number

        Raises:
            ValueError: If container number doesn't match ISO 6346 format
        """
        if not v or not v.strip():
            raise ValueError('Container number is required')

        # Normalize: strip whitespace and uppercase
        normalized = v.strip().upper()

        # Validate ISO 6346 format
        if not ISO_6346_PATTERN.match(normalized):
            raise ValueError(
                'Invalid container number format. '
                'Expected ISO 6346 format: 4 letters + 7 digits (e.g., MRSU3452572)'
            )

        return normalized


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

    @field_validator('container_number')
    @classmethod
    def validate_container_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO 6346 container number format if provided.

        Same validation as ShipmentCreate but allows None for partial updates.
        """
        if v is None:
            return v

        if not v.strip():
            return None  # Treat empty string as None for updates

        # Normalize: strip whitespace and uppercase
        normalized = v.strip().upper()

        # Validate ISO 6346 format
        if not ISO_6346_PATTERN.match(normalized):
            raise ValueError(
                'Invalid container number format. '
                'Expected ISO 6346 format: 4 letters + 7 digits (e.g., MRSU3452572)'
            )

        return normalized


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
    product_type: Optional[ProductType] = None  # Product category for compliance requirements
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
    buyer_organization_id: Optional[UUID] = None  # Buyer org (HAGES, Witatrade, etc.)
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


class ContainerUpdateRequest(BaseModel):
    """Request to update shipment container number.

    Used for PATCH /shipments/{id}/container endpoint to update
    placeholder containers with real ISO 6346 container numbers.
    """
    container_number: str

    @field_validator('container_number')
    @classmethod
    def validate_container(cls, v: str) -> str:
        """Validate container number against ISO 6346 format.

        Format: 4 uppercase letters + 7 digits (e.g., MRSU3452572)

        Args:
            v: Container number to validate

        Returns:
            Normalized (uppercase, trimmed) container number

        Raises:
            ValueError: If container number doesn't match ISO 6346 format
        """
        if not v or not v.strip():
            raise ValueError('Container number is required')

        # Normalize: strip whitespace and uppercase
        normalized = v.strip().upper()

        # Check length
        if len(normalized) != 11:
            raise ValueError(
                'Container number must be 11 characters (ISO 6346 format: 4 letters + 7 digits)'
            )

        # Validate ISO 6346 format
        if not ISO_6346_PATTERN.match(normalized):
            raise ValueError(
                'Invalid container format. Expected: 4 letters + 7 digits (e.g., MRSU3452572)'
            )

        return normalized
