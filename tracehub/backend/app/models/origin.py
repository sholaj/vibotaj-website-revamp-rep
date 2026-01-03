"""Origin model for EUDR compliance tracking."""

import uuid
import enum
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Numeric, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base


class RiskLevel(str, enum.Enum):
    """EUDR risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class VerificationMethod(str, enum.Enum):
    """Methods used to verify origin data."""
    DOCUMENT_REVIEW = "document_review"
    SUPPLIER_ATTESTATION = "supplier_attestation"
    ON_SITE_INSPECTION = "on_site_inspection"
    SATELLITE_VERIFICATION = "satellite_verification"
    THIRD_PARTY_AUDIT = "third_party_audit"
    SELF_DECLARATION = "self_declaration"


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

    # Risk assessment (EUDR Article 10)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.UNKNOWN)
    risk_score = Column(Numeric(5, 2))  # 0-100 score
    risk_assessment_date = Column(DateTime)
    risk_assessment_notes = Column(Text)

    # Supplier attestation (EUDR Article 9)
    supplier_attestation_date = Column(Date)
    supplier_attestation_reference = Column(String(100))
    supplier_attestation_document_id = Column(UUID(as_uuid=True))  # Link to uploaded document

    # Verification workflow
    verified_at = Column(DateTime)
    verified_by = Column(String(100))
    verification_method = Column(Enum(VerificationMethod))
    verification_notes = Column(Text)
    verification_document_ids = Column(JSONB)  # List of supporting document IDs

    # EUDR-specific tracking
    eudr_reference_number = Column(String(100))  # Reference for EU information system
    eudr_submission_date = Column(DateTime)
    eudr_status = Column(String(50))  # Status in EU system

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="origins")
    supplier = relationship("Party", back_populates="origins")

    def __repr__(self):
        return f"<Origin {self.farm_plot_identifier} ({self.country})>"

    @property
    def is_eudr_compliant(self) -> bool:
        """Check if this origin meets basic EUDR requirements."""
        has_location = self.geolocation_lat is not None and self.geolocation_lng is not None
        has_production_date = self.production_start_date is not None or self.production_end_date is not None
        has_farm_id = bool(self.farm_plot_identifier)
        has_country = bool(self.country)

        return all([has_location, has_production_date, has_farm_id, has_country])

    @property
    def production_date_compliant(self) -> bool:
        """Check if production date is after EUDR cutoff (Dec 31, 2020)."""
        from datetime import date as date_type
        cutoff = date_type(2020, 12, 31)

        prod_date = self.production_end_date or self.production_start_date
        if prod_date is None:
            return False

        return prod_date > cutoff
