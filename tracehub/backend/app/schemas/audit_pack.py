"""Pydantic schemas for audit pack generation.

These schemas enforce type safety for the metadata.json structure,
preventing bugs like accessing non-existent model attributes.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PortInfo(BaseModel):
    """Port of loading/discharge info."""
    code: Optional[str] = None
    name: Optional[str] = None


class ProductMetadata(BaseModel):
    """Product info for audit pack metadata."""
    hs_code: str
    description: Optional[str] = None
    quantity_net_kg: Optional[float] = None
    quantity_gross_kg: Optional[float] = None


class PartyInfo(BaseModel):
    """Buyer or exporter party info.

    Note: Uses importer_name/exporter_name from Shipment model,
    NOT buyer/supplier relationships (which don't exist).
    """
    name: Optional[str] = None
    organization_id: Optional[str] = None


class ShipmentMetadata(BaseModel):
    """Shipment details for audit pack metadata."""
    reference: str
    container_number: Optional[str] = None
    bl_number: Optional[str] = None
    vessel: Optional[str] = None
    voyage: Optional[str] = None
    etd: Optional[str] = None
    eta: Optional[str] = None
    pol: PortInfo
    pod: PortInfo
    incoterms: Optional[str] = None
    status: str


class AuditPackMetadata(BaseModel):
    """Complete metadata.json schema for audit packs.

    This schema documents the expected structure and provides
    compile-time type checking to prevent attribute access errors.
    """
    shipment: ShipmentMetadata
    products: List[ProductMetadata]
    buyer: PartyInfo
    exporter: PartyInfo
    exported_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "shipment": {
                    "reference": "VIBO-2026-001",
                    "container_number": "MSCU1234567",
                    "bl_number": "123456789",
                    "vessel": "RHINE MAERSK",
                    "voyage": "550N",
                    "etd": "2026-01-01T00:00:00",
                    "eta": "2026-01-15T00:00:00",
                    "pol": {"code": "NGAPP", "name": "Apapa, Lagos"},
                    "pod": {"code": "DEHAM", "name": "Hamburg"},
                    "incoterms": "FOB",
                    "status": "in_transit"
                },
                "products": [
                    {
                        "hs_code": "0506.90.00",
                        "description": "Cattle Horns",
                        "quantity_net_kg": 25000.0,
                        "quantity_gross_kg": 26500.0
                    }
                ],
                "buyer": {
                    "name": "HAGES GmbH",
                    "organization_id": "uuid-here"
                },
                "exporter": {
                    "name": "VIBOTAJ Global Nigeria Ltd",
                    "organization_id": "uuid-here"
                },
                "exported_at": "2026-01-17T15:00:00"
            }
        }


class TrackingEvent(BaseModel):
    """Container tracking event for tracking log."""
    type: str
    timestamp: Optional[str] = None
    location: Optional[str] = None
    vessel: Optional[str] = None
    voyage: Optional[str] = None


class TrackingLog(BaseModel):
    """Container tracking log schema."""
    container_number: Optional[str] = None
    exported_at: str
    events: List[TrackingEvent]
