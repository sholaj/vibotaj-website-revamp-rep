"""Product model for goods in a shipment."""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class Product(Base):
    """Product entity - goods being shipped."""

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)

    # Product identification
    hs_code = Column(String(12), nullable=False)  # Harmonized System code
    description = Column(String(500), nullable=False)

    # Quantities
    quantity_net_kg = Column(Numeric(12, 3))
    quantity_gross_kg = Column(Numeric(12, 3))
    unit_of_measure = Column(String(10), default="KG")

    # Packaging
    packaging_type = Column(String(100))  # e.g., "Bulk bags", "Containers"
    packaging_count = Column(Integer)

    # Batch and quality
    batch_lot_number = Column(String(50))
    quality_grade = Column(String(50))
    moisture_percentage = Column(Numeric(5, 2))

    # Production
    production_date = Column(Date)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shipment = relationship("Shipment", back_populates="products")
    origins = relationship("Origin", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.hs_code}: {self.description[:30]}>"
