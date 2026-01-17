"""Canonical Bill of Lading Schema.

This module defines the standardized data structure for Bill of Lading documents.
When a BoL is present, it is the SOURCE OF TRUTH for shipment details.

The schema is designed to:
1. Work with ALL product types (Horn & Hoof, agricultural, general cargo)
2. Support multiple containers and cargo items
3. Provide validation for ISO 6346 container numbers
4. Enable reliable data extraction from BoL documents
"""

import re
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BolParty(BaseModel):
    """Party involved in the shipment (shipper, consignee, notify party).

    Attributes:
        name: Company or individual name (required)
        address: Full address (optional)
        country: Country name or code (optional)
    """
    name: str = Field(..., min_length=1, description="Party name")
    address: Optional[str] = Field(None, description="Full address")
    country: Optional[str] = Field(None, description="Country name or code")


class BolContainer(BaseModel):
    """Container details from Bill of Lading.

    Attributes:
        number: Container number in ISO 6346 format (4 letters + 7 digits)
        seal_number: Seal number(s) on the container
        type: Container type code (20GP, 40HC, etc.)
        weight_kg: Weight in kilograms
    """
    number: str = Field(..., min_length=1, description="Container number (ISO 6346)")
    seal_number: Optional[str] = Field(None, description="Seal number")
    type: Optional[str] = Field(None, description="Container type (20GP, 40HC, etc.)")
    weight_kg: Optional[float] = Field(None, ge=0, description="Weight in kg")

    @field_validator('number', mode='before')
    @classmethod
    def normalize_container_number(cls, v: str) -> str:
        """Normalize container number to uppercase without spaces."""
        if v:
            return v.upper().replace(' ', '').replace('-', '')
        return v


class BolCargo(BaseModel):
    """Cargo/goods details from Bill of Lading.

    Attributes:
        description: Cargo description (required)
        hs_code: Harmonized System code for customs
        quantity: Quantity of goods
        unit: Unit of measure (MT, KG, PCS, etc.)
        gross_weight_kg: Gross weight in kilograms
        net_weight_kg: Net weight in kilograms
    """
    description: str = Field(..., min_length=1, description="Cargo description")
    hs_code: Optional[str] = Field(None, description="HS code for customs")
    quantity: Optional[float] = Field(None, ge=0, description="Quantity")
    unit: Optional[str] = Field(None, description="Unit of measure")
    gross_weight_kg: Optional[float] = Field(None, ge=0, description="Gross weight in kg")
    net_weight_kg: Optional[float] = Field(None, ge=0, description="Net weight in kg")


class CanonicalBoL(BaseModel):
    """Canonical Bill of Lading schema.

    This is the SOURCE OF TRUTH for shipment details when a BoL is present.
    Parsed BoL data should update shipment records automatically.

    Required fields:
        - bol_number: The B/L reference number
        - shipper: The shipping party
        - consignee: The receiving party
        - containers: List of containers (can be empty)
        - cargo: List of cargo items (can be empty)

    Optional fields:
        - notify_party: Party to notify on arrival
        - vessel_name: Name of the vessel
        - voyage_number: Voyage reference
        - port_of_loading: Origin port (UN/LOCODE)
        - port_of_discharge: Destination port (UN/LOCODE)
        - place_of_delivery: Final delivery location
        - date_of_issue: Date the BoL was issued
        - shipped_on_board_date: Date cargo was loaded
        - freight_terms: PREPAID or COLLECT
        - raw_text: Original text for debugging
        - confidence_score: Parser confidence (0.0-1.0)
    """
    # Required fields
    bol_number: str = Field(..., min_length=1, description="Bill of Lading number")
    shipper: BolParty = Field(..., description="Shipper/Exporter details")
    consignee: BolParty = Field(..., description="Consignee/Importer details")
    containers: List[BolContainer] = Field(default_factory=list, description="Container list")
    cargo: List[BolCargo] = Field(default_factory=list, description="Cargo items")

    # Optional fields
    notify_party: Optional[BolParty] = Field(None, description="Notify party")
    vessel_name: Optional[str] = Field(None, description="Vessel name")
    voyage_number: Optional[str] = Field(None, description="Voyage number")
    port_of_loading: Optional[str] = Field(None, description="Port of loading (UN/LOCODE)")
    port_of_discharge: Optional[str] = Field(None, description="Port of discharge (UN/LOCODE)")
    place_of_delivery: Optional[str] = Field(None, description="Final delivery place")
    date_of_issue: Optional[date] = Field(None, description="BoL issue date")
    shipped_on_board_date: Optional[date] = Field(None, description="On board date")
    freight_terms: Optional[str] = Field(None, description="Freight terms (PREPAID/COLLECT)")
    raw_text: Optional[str] = Field(None, description="Raw extracted text")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Parser confidence")

    def get_primary_container(self) -> Optional[str]:
        """Get the primary (first) container number."""
        if self.containers:
            return self.containers[0].number
        return None

    def get_hs_codes(self) -> List[str]:
        """Get all HS codes from cargo items."""
        return [c.hs_code for c in self.cargo if c.hs_code]

    def get_total_weight_kg(self) -> Optional[float]:
        """Calculate total gross weight from cargo items."""
        weights = [c.gross_weight_kg for c in self.cargo if c.gross_weight_kg]
        return sum(weights) if weights else None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bol_number": "APU106546",
                "shipper": {
                    "name": "VIBOTAJ GLOBAL NIG LTD",
                    "address": "Lagos, Nigeria",
                    "country": "Nigeria"
                },
                "consignee": {
                    "name": "HAGES GMBH",
                    "address": "Hamburg, Germany",
                    "country": "Germany"
                },
                "containers": [
                    {"number": "MRSU4825686", "type": "40HC", "seal_number": "SL123456"}
                ],
                "cargo": [
                    {"description": "CATTLE HOOVES AND HORNS", "hs_code": "0506", "gross_weight_kg": 20000}
                ],
                "vessel_name": "MSC MARINA",
                "voyage_number": "VY2026001",
                "port_of_loading": "NGAPP",
                "port_of_discharge": "DEHAM",
                "shipped_on_board_date": "2026-01-12",
                "freight_terms": "PREPAID",
                "confidence_score": 0.95
            }
        }
    )

    def is_complete(self) -> bool:
        """Check if BoL has minimum required data for compliance."""
        return bool(
            self.bol_number and
            self.shipper and self.shipper.name and
            self.consignee and self.consignee.name and
            self.containers and
            self.cargo
        )
