"""Origin model for EUDR compliance tracking."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class RiskLevel(str, enum.Enum):
    """EUDR risk assessment levels (matches production DB)."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Origin(Base):
    """Origin entity - EUDR compliance data for product sourcing (matches production schema)."""

    __tablename__ = "origins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Farm/plot identification
    farm_name = Column(String(255))
    plot_identifier = Column(String(100))

    # Geolocation
    latitude = Column(Float)
    longitude = Column(Float)

    # Administrative location
    country = Column(String(100), nullable=False)
    region = Column(String(255))
    address = Column(Text)

    # Production dates
    production_date = Column(DateTime(timezone=True))
    harvest_date = Column(DateTime(timezone=True))

    # Supplier info
    supplier_name = Column(String(255))
    supplier_id = Column(String(100))

    # EUDR compliance
    deforestation_free = Column(Boolean)
    eudr_cutoff_compliant = Column(Boolean)

    # Risk assessment
    risk_level = Column(Enum(RiskLevel, name="risklevel", create_type=False))

    # Verification workflow
    verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))  # FK added Sprint 11
    verified_at = Column(DateTime(timezone=True))
    verification_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="origins")
    organization = relationship("Organization", back_populates="origins")

    def __repr__(self):
        return f"<Origin {self.farm_name or self.plot_identifier} ({self.country})>"

    @property
    def is_eudr_compliant(self) -> bool:
        """Check if this origin meets basic EUDR requirements."""
        has_location = self.latitude is not None and self.longitude is not None
        has_production_date = self.production_date is not None or self.harvest_date is not None
        has_farm_id = bool(self.farm_name or self.plot_identifier)
        has_country = bool(self.country)

        return all([has_location, has_production_date, has_farm_id, has_country])
