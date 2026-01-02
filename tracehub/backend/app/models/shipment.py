"""Shipment model - the core entity for container tracking."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class ShipmentStatus(str, enum.Enum):
    """Shipment lifecycle states."""
    CREATED = "created"
    DOCS_PENDING = "docs_pending"
    DOCS_COMPLETE = "docs_complete"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    CLOSED = "closed"


class Shipment(Base):
    """Shipment entity - tracks a container shipment end-to-end."""

    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference = Column(String(50), unique=True, nullable=False)  # e.g., VIBO-2026-001

    # Container and transport details
    container_number = Column(String(20), nullable=False)  # e.g., MSCU1234567
    bl_number = Column(String(50))  # Bill of Lading number
    booking_reference = Column(String(50))
    vessel_name = Column(String(100))
    voyage_number = Column(String(50))

    # Dates
    etd = Column(DateTime)  # Estimated time of departure
    eta = Column(DateTime)  # Estimated time of arrival
    atd = Column(DateTime)  # Actual time of departure
    ata = Column(DateTime)  # Actual time of arrival

    # Ports
    pol_code = Column(String(5))  # Port of Loading UN/LOCODE
    pol_name = Column(String(100))
    pod_code = Column(String(5))  # Port of Discharge UN/LOCODE
    pod_name = Column(String(100))
    final_destination = Column(String(100))

    # Commercial terms
    incoterms = Column(String(10))  # FOB, CIF, etc.

    # Status
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.CREATED, nullable=False)

    # Party relationships
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("parties.id"))
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("parties.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    buyer = relationship("Party", back_populates="shipments_as_buyer", foreign_keys=[buyer_id])
    supplier = relationship("Party", back_populates="shipments_as_supplier", foreign_keys=[supplier_id])
    products = relationship("Product", back_populates="shipment", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="shipment", cascade="all, delete-orphan")
    container_events = relationship("ContainerEvent", back_populates="shipment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shipment {self.reference} ({self.container_number})>"
