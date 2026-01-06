"""Party model for buyers, suppliers, and other stakeholders."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class PartyType(str, enum.Enum):
    """Types of parties involved in shipments."""
    SUPPLIER = "supplier"
    BUYER = "buyer"
    SHIPPER = "shipper"
    CONSIGNEE = "consignee"
    NOTIFY_PARTY = "notify_party"


class Party(Base):
    """Party entity representing companies/individuals in shipments."""

    __tablename__ = "parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(PartyType), nullable=False)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(String(500))
    city = Column(String(100))
    country = Column(String(2))  # ISO country code
    registration_number = Column(String(100))
    tax_id = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # Note: In Sprint 8, direct FK relationships were removed:
    # - shipments_as_buyer/supplier removed (shipments use exporter_name/importer_name strings)
    # - origins relationship removed (origins use supplier_name string, not FK to parties)

    def __repr__(self):
        return f"<Party {self.company_name} ({self.type.value})>"
