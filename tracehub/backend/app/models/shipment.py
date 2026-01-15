"""Shipment model - the core entity for container tracking."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class ShipmentStatus(str, enum.Enum):
    """Shipment lifecycle states matching production database."""
    DRAFT = "draft"
    DOCS_PENDING = "docs_pending"
    DOCS_COMPLETE = "docs_complete"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    CUSTOMS = "customs"
    DELIVERED = "delivered"
    ARCHIVED = "archived"


class ProductType(str, enum.Enum):
    """Product type categories aligned with compliance matrix.

    Maps to HS codes for document requirement determination.
    See docs/COMPLIANCE_MATRIX.md for full documentation.
    """
    HORN_HOOF = "horn_hoof"           # HS 0506, 0507 - Animal by-products (NO EUDR)
    SWEET_POTATO = "sweet_potato"     # HS 0714 - Sweet potato pellets (NO EUDR)
    HIBISCUS = "hibiscus"             # HS 0902 - Hibiscus flowers (NO EUDR)
    GINGER = "ginger"                 # HS 0910 - Dried ginger (NO EUDR)
    COCOA = "cocoa"                   # HS 1801 - Cocoa beans (EUDR APPLICABLE)
    OTHER = "other"                   # Other/unspecified


class Shipment(Base):
    """Shipment entity - tracks a container shipment end-to-end.

    Updated to match production database schema (Sprint 8).
    """

    __tablename__ = "shipments"
    __table_args__ = (
        UniqueConstraint('organization_id', 'reference', name='uq_shipment_org_reference'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference = Column(String(50), nullable=False)  # e.g., VIBO-2026-001

    # Container and transport details
    container_number = Column(String(20), nullable=False)  # e.g., MSCU1234567
    bl_number = Column(String(50))  # Bill of Lading number
    booking_ref = Column(String(50))  # Renamed from booking_reference
    vessel_name = Column(String(100))
    voyage_number = Column(String(50))

    # Carrier information (new fields)
    carrier_code = Column(String(10))  # e.g., MAEU, MSCU
    carrier_name = Column(String(100))  # e.g., Maersk, MSC

    # Dates (timezone-aware - Sprint 12)
    etd = Column(DateTime(timezone=True))  # Estimated time of departure
    eta = Column(DateTime(timezone=True))  # Estimated time of arrival
    atd = Column(DateTime(timezone=True))  # Actual time of departure
    ata = Column(DateTime(timezone=True))  # Actual time of arrival

    # Ports
    pol_code = Column(String(5))  # Port of Loading UN/LOCODE
    pol_name = Column(String(100))
    pod_code = Column(String(5))  # Port of Discharge UN/LOCODE
    pod_name = Column(String(100))

    # Commercial terms
    incoterms = Column(String(10))  # FOB, CIF, etc.

    # Status
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.DRAFT, nullable=False)

    # Product type (aligned with compliance matrix)
    product_type = Column(
        Enum(ProductType),
        nullable=True,  # Nullable for migration, will be required in API
        index=True  # For filtering shipments by product type
    )

    # Party names (replacing buyer_id/supplier_id relationships)
    exporter_name = Column(String(255))  # Exporting company name
    importer_name = Column(String(255))  # Importing company name

    # EUDR compliance fields
    eudr_compliant = Column(Boolean, default=False)
    eudr_statement_id = Column(String(100))  # EUDR DDS reference number

    # Organization (multi-tenancy - required)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    # Buyer organization (optional - links VIBOTAJ shipment to buyer like HAGES, Witatrade)
    buyer_organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=True,  # Backward compatible with existing shipments
        index=True  # For efficient buyer queries
    )

    # Timestamps (timezone-aware - Sprint 12)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship(
        "Organization",
        foreign_keys=[organization_id],
        back_populates="shipments"
    )
    buyer_organization = relationship(
        "Organization",
        foreign_keys=[buyer_organization_id],
        back_populates="buyer_shipments"
    )
    products = relationship("Product", back_populates="shipment", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="shipment", cascade="all, delete-orphan")
    container_events = relationship("ContainerEvent", back_populates="shipment", cascade="all, delete-orphan")
    origins = relationship("Origin", back_populates="shipment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shipment {self.reference} ({self.container_number})>"
