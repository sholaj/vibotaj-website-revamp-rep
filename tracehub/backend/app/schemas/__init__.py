"""Pydantic schemas for API requests/responses."""

from .shipment import ShipmentResponse, ShipmentDetailResponse, ShipmentListResponse, DocumentSummary
from .document import DocumentResponse, DocumentUploadRequest
from .analytics import (
    ShipmentStatsResponse,
    DocumentStatsResponse,
    ComplianceMetricsResponse,
    TrackingStatsResponse,
    DashboardStatsResponse,
    ShipmentTrendsResponse,
    DocumentDistributionResponse,
)
from .eudr import (
    EUDRStatusResponse,
    EUDRValidationResponse,
    OriginVerificationRequest,
    OriginValidationResponse,
    GeolocationCheckRequest,
    GeolocationCheckResponse,
    ProductionDateCheckRequest,
    ProductionDateCheckResponse,
    CountryRiskLevels,
    EUDRRegulationInfo,
    RiskLevel,
    EUDRValidationStatus,
    VerificationMethod,
)

__all__ = [
    "ShipmentResponse",
    "ShipmentDetailResponse",
    "ShipmentListResponse",
    "DocumentSummary",
    "DocumentResponse",
    "DocumentUploadRequest",
    "ShipmentStatsResponse",
    "DocumentStatsResponse",
    "ComplianceMetricsResponse",
    "TrackingStatsResponse",
    "DashboardStatsResponse",
    "ShipmentTrendsResponse",
    "DocumentDistributionResponse",
    "EUDRStatusResponse",
    "EUDRValidationResponse",
    "OriginVerificationRequest",
    "OriginValidationResponse",
    "GeolocationCheckRequest",
    "GeolocationCheckResponse",
    "ProductionDateCheckRequest",
    "ProductionDateCheckResponse",
    "CountryRiskLevels",
    "EUDRRegulationInfo",
    "RiskLevel",
    "EUDRValidationStatus",
    "VerificationMethod",
]
