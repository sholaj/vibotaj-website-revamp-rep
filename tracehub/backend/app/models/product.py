"""Product model for goods in a shipment."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class Product(Base):
    """Product entity - goods being shipped (matches production schema)."""

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Product identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    hs_code = Column(String(20))  # Harmonized System code

    # Quantities
    quantity_net_kg = Column(Float)
    quantity_gross_kg = Column(Float)
    quantity_units = Column(Integer)

    # Packaging
    packaging = Column(String(100))

    # Batch and quality
    batch_number = Column(String(100))
    lot_number = Column(String(100))
    moisture_content = Column(Float)
    quality_grade = Column(String(50))

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="products")
    organization = relationship("Organization", back_populates="products")

    def __repr__(self):
        return f"<Product {self.hs_code}: {self.name[:30] if self.name else 'N/A'}>"
