"""Container event model for tracking milestones."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base


class EventStatus(str, enum.Enum):
    """Container tracking event status types (matches production DB)."""
    BOOKED = "BOOKED"
    GATE_IN = "GATE_IN"
    LOADED = "LOADED"
    DEPARTED = "DEPARTED"
    IN_TRANSIT = "IN_TRANSIT"
    TRANSSHIPMENT = "TRANSSHIPMENT"
    ARRIVED = "ARRIVED"
    DISCHARGED = "DISCHARGED"
    GATE_OUT = "GATE_OUT"
    DELIVERED = "DELIVERED"
    OTHER = "OTHER"


class ContainerEvent(Base):
    """Container event entity - tracking milestones from carrier APIs."""

    __tablename__ = "container_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Event details (matches production schema)
    event_status = Column(Enum(EventStatus, name="eventstatus", create_type=False), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)

    # Location
    location_code = Column(String(20))  # UN/LOCODE
    location_name = Column(String(255))

    # Vessel info
    vessel_name = Column(String(100))
    voyage_number = Column(String(50))

    # Description
    description = Column(Text)

    # Source tracking
    source = Column(String(50))  # API source
    raw_data = Column(JSONB)  # Original API response

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="container_events")
    organization = relationship("Organization", back_populates="container_events")

    def __repr__(self):
        return f"<ContainerEvent {self.event_status.value} at {self.location_name}>"
