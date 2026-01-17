"""EUDR Compliance Pydantic Schemas."""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from enum import Enum


class RiskLevel(str, Enum):
    """EUDR risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class EUDRValidationStatus(str, Enum):
    """EUDR validation status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    INCOMPLETE = "incomplete"


class VerificationMethod(str, Enum):
    """Methods used to verify origin data."""
    DOCUMENT_REVIEW = "document_review"
    SUPPLIER_ATTESTATION = "supplier_attestation"
    ON_SITE_INSPECTION = "on_site_inspection"
    SATELLITE_VERIFICATION = "satellite_verification"
    THIRD_PARTY_AUDIT = "third_party_audit"
    SELF_DECLARATION = "self_declaration"


class EUDRChecklistItem(BaseModel):
    """Single item in EUDR compliance checklist."""
    item: str
    passed: bool
    details: str


class EUDRValidationCheck(BaseModel):
    """Single validation check result."""
    name: str
    passed: bool
    message: str
    severity: str = "error"


class EUDRComplianceSummary(BaseModel):
    """Summary of EUDR compliance status."""
    total_origins: int
    compliant_origins: int
    has_eudr_document: bool
    passed_checks: int
    total_checks: int


class SatelliteCheck(BaseModel):
    """Satellite verification status."""
    available: bool
    provider: Optional[str] = None
    last_checked: Optional[str] = None
    forest_loss_detected: Optional[bool] = None
    message: str


class Coordinates(BaseModel):
    """Geographic coordinates."""
    lat: Optional[float] = None
    lng: Optional[float] = None


class EUDRRiskAssessment(BaseModel):
    """Deforestation risk assessment."""
    risk_level: RiskLevel
    country_risk: RiskLevel
    coordinates: Coordinates
    satellite_check: SatelliteCheck
    recommendations: List[str]
    eudr_article: str
    assessed_at: str


class OriginValidationResult(BaseModel):
    """Validation result for a single origin."""
    is_valid: bool
    status: EUDRValidationStatus
    risk_level: RiskLevel
    risk_score: int
    checks: List[EUDRValidationCheck]
    missing_fields: List[str]
    warnings: List[str]
    errors: List[str]
    total_checks: int
    passed_checks: int


class EUDROriginValidation(BaseModel):
    """EUDR validation for an origin."""
    origin_id: str
    farm_plot_id: Optional[str] = None
    country: Optional[str] = None
    validation: OriginValidationResult
    risk: EUDRRiskAssessment


class EUDRStatusResponse(BaseModel):
    """Full EUDR compliance status response."""
    model_config = ConfigDict(from_attributes=True)

    shipment_id: str
    shipment_reference: str
    overall_status: EUDRValidationStatus
    overall_risk_level: RiskLevel
    is_compliant: bool
    checklist: List[EUDRChecklistItem]
    summary: EUDRComplianceSummary
    origin_validations: List[EUDROriginValidation]
    cutoff_date: str
    assessed_at: str


class EUDRActionItem(BaseModel):
    """Action item from validation."""
    action: str
    details: str
    priority: str = "medium"


class EUDRValidationResponse(BaseModel):
    """Response from full EUDR validation."""
    shipment_id: str
    validation_result: Dict[str, Any]
    action_items: List[EUDRActionItem]
    validated_at: str
    validated_by: str


class OriginVerificationRequest(BaseModel):
    """Request to verify/update origin data."""
    farm_plot_identifier: Optional[str] = None
    geolocation_lat: Optional[float] = Field(None, ge=-90, le=90)
    geolocation_lng: Optional[float] = Field(None, ge=-180, le=180)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    region: Optional[str] = None
    district: Optional[str] = None
    production_start_date: Optional[date] = None
    production_end_date: Optional[date] = None
    supplier_attestation_date: Optional[date] = None
    supplier_attestation_reference: Optional[str] = None
    deforestation_free_statement: Optional[str] = None
    verification_method: Optional[VerificationMethod] = None


class OriginValidationResponse(BaseModel):
    """Response from origin verification."""
    origin_id: str
    is_valid: bool
    status: EUDRValidationStatus
    risk_level: RiskLevel
    risk_score: int
    checks: List[EUDRValidationCheck]
    missing_fields: List[str]
    warnings: List[str]
    errors: List[str]


class GeolocationCheckRequest(BaseModel):
    """Request to validate geolocation."""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    country: str = Field(..., min_length=2, max_length=2)


class GeolocationCheckResponse(BaseModel):
    """Response from geolocation check."""
    coordinates: Coordinates
    country: str
    validation: OriginValidationResult
    risk_assessment: EUDRRiskAssessment


class ProductionDateCheckRequest(BaseModel):
    """Request to validate production date."""
    production_date: date


class ProductionDateCheckResponse(BaseModel):
    """Response from production date check."""
    production_date: str
    cutoff_date: str
    is_valid: bool
    message: str
    days_after_cutoff: Optional[int] = None


class CountryRiskLevels(BaseModel):
    """Country risk level information."""
    risk_levels: Dict[str, RiskLevel]
    risk_categories: Dict[str, List[str]]
    source: str
    last_updated: str


class CoveredCommodity(BaseModel):
    """EUDR covered commodity."""
    name: str
    hs_codes: List[str]


class RegulationInfo(BaseModel):
    """EUDR regulation information."""
    name: str
    official_name: str
    short_name: str
    entry_into_force: str
    applicable_from_large_operators: str
    applicable_from_sme: str


class KeyDates(BaseModel):
    """Key EUDR dates."""
    cutoff_date: str
    cutoff_description: str


class Requirements(BaseModel):
    """EUDR requirements."""
    geolocation: str
    production_date: str
    due_diligence: str
    traceability: str


class EUDRRegulationInfo(BaseModel):
    """Complete EUDR regulation information."""
    regulation: RegulationInfo
    key_dates: KeyDates
    covered_commodities: List[CoveredCommodity]
    requirements: Requirements
    compliance_checklist: List[str]
