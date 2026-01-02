"""Origin model for EUDR compliance tracking."""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base


class Origin(Base):
    """Origin entity - EUDR compliance data for product sourcing."""

    __tablename__ = "origins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Farm/plot identification
    farm_plot_identifier = Column(String(100), nullable=False)

    # Geolocation (EUDR requirement)
    geolocation_lat = Column(Numeric(10, 7))
    geolocation_lng = Column(Numeric(10, 7))
    geolocation_polygon = Column(JSONB)  # GeoJSON for plot boundaries

    # Administrative location
    country = Column(String(2), nullable=False)  # ISO country code
    region = Column(String(100))
    district = Column(String(100))

    # Production dates (EUDR requirement - must be after Dec 31, 2020)
    production_start_date = Column(Date)
    production_end_date = Column(Date)

    # Supplier link
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("parties.id"))

    # EUDR compliance
    deforestation_cutoff_compliant = Column(Boolean, default=False)
    due_diligence_statement_ref = Column(String(100))
    deforestation_free_statement = Column(Text)

    # Verification
    verified_at = Column(DateTime)
    verified_by = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="origins")
    supplier = relationship("Party", back_populates="origins")

    def __repr__(self):
        return f"<Origin {self.farm_plot_identifier} ({self.country})>"
