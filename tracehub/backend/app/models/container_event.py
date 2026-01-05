"""Container event model for tracking milestones."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base


class EventType(str, enum.Enum):
    """Container tracking event types."""
    BOOKING_CONFIRMED = "booking_confirmed"
    GATE_IN = "gate_in"
    LOADED = "loaded"
    DEPARTED = "departed"
    TRANSSHIPMENT = "transshipment"
    ARRIVED = "arrived"
    DISCHARGED = "discharged"
    GATE_OUT = "gate_out"
    DELIVERED = "delivered"
    CUSTOMS_HOLD = "customs_hold"
    CUSTOMS_RELEASED = "customs_released"
    EMPTY_RETURN = "empty_return"
    UNKNOWN = "unknown"


class ContainerEvent(Base):
    """Container event entity - tracking milestones from carrier APIs."""

    __tablename__ = "container_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)

    # Event details
    event_type = Column(Enum(EventType), nullable=False)
    event_timestamp = Column(DateTime, nullable=False)

    # Location
    location_name = Column(String(255))
    location_code = Column(String(10))  # UN/LOCODE
    location_lat = Column(Numeric(10, 7))
    location_lng = Column(Numeric(10, 7))

    # Vessel info
    vessel_name = Column(String(100))
    voyage_number = Column(String(50))

    # Delay tracking
    delay_hours = Column(Integer)

    # Source tracking
    source = Column(String(50), default="jsoncargo")  # API source
    external_id = Column(String(100))  # ID from tracking API
    raw_payload = Column(JSONB)  # Original API response

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="container_events")

    def __repr__(self):
        return f"<ContainerEvent {self.event_type.value} at {self.location_name}>"
