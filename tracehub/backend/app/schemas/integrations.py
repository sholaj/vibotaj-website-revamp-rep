"""Pydantic schemas for third-party integrations (PRD-021)."""

from datetime import datetime
from enum import StrEnum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IntegrationType(StrEnum):
    """Supported integration types."""

    CUSTOMS = "customs"
    BANKING = "banking"


class IntegrationConfigResponse(BaseModel):
    """Integration configuration for an organization."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    integration_type: str
    provider: str
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_success: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


class IntegrationConfigUpdate(BaseModel):
    """Update integration configuration."""

    provider: str = Field(min_length=1, max_length=50)
    config: Dict[str, object] = Field(default_factory=dict)
    is_active: bool = True


class IntegrationsListResponse(BaseModel):
    """List of integration configs for an organization."""

    customs: Optional[IntegrationConfigResponse] = None
    banking: Optional[IntegrationConfigResponse] = None


class TestConnectionRequest(BaseModel):
    """Request to test an integration connection."""

    integration_type: IntegrationType


class TestConnectionResponse(BaseModel):
    """Result of a connection test."""

    integration_type: str
    provider: str
    success: bool
    message: str
    response_time_ms: Optional[int] = None


class IntegrationLogResponse(BaseModel):
    """Single integration log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    integration_type: str
    provider: str
    method: str
    request_summary: Optional[str] = None
    status: str
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    shipment_id: Optional[UUID] = None
    created_at: datetime


class IntegrationLogsListResponse(BaseModel):
    """List of integration log entries."""

    logs: List[IntegrationLogResponse]
    total: int


# --- Customs-specific schemas ---


class PreClearanceRequest(BaseModel):
    """Request for customs pre-clearance check."""

    hs_code: str = Field(min_length=2, max_length=10)
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(default="DE", min_length=2, max_length=2)


class PreClearanceResponse(BaseModel):
    """Pre-clearance check result."""

    hs_code: str
    origin_country: str
    status: str
    required_documents: List[str]
    restrictions: List[str]
    notes: str
    provider: str


class DutyCalculationRequest(BaseModel):
    """Request for duty calculation."""

    hs_code: str = Field(min_length=2, max_length=10)
    cif_value: float = Field(gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    quantity: float = Field(default=1.0, gt=0)


class DutyCalculationResponse(BaseModel):
    """Duty calculation result."""

    hs_code: str
    cif_value: float
    currency: str
    import_duty_rate: float
    import_duty_amount: float
    vat_rate: float
    vat_amount: float
    surcharges: List[Dict[str, object]]
    total_duty: float
    provider: str


class DeclarationRequest(BaseModel):
    """Request to submit an export declaration."""

    shipment_reference: str = Field(min_length=1)
    hs_code: str = Field(min_length=2, max_length=10)
    exporter_name: str = Field(min_length=1)
    consignee_name: str = Field(min_length=1)
    cif_value: float = Field(gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class DeclarationResponse(BaseModel):
    """Export declaration result."""

    reference_number: str
    status: str
    submitted_at: Optional[str] = None
    provider: str
    error: Optional[str] = None


# --- Banking-specific schemas ---


class LCVerifyRequest(BaseModel):
    """Request to verify a Letter of Credit."""

    lc_number: str = Field(min_length=1)
    issuing_bank: str = Field(min_length=1)


class LCVerifyResponse(BaseModel):
    """LC verification result."""

    lc_number: str
    status: str
    issuing_bank: str
    beneficiary: str
    amount: float
    currency: str
    expiry_date: Optional[str] = None
    terms: List[str]
    provider: str
    error: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Payment status result."""

    reference: str
    status: str
    amount: float
    currency: str
    payer: str
    payee: str
    initiated_at: Optional[str] = None
    completed_at: Optional[str] = None
    provider: str
    error: Optional[str] = None


class ForexRateResponse(BaseModel):
    """Forex rate result."""

    base_currency: str
    quote_currency: str
    buy_rate: float
    sell_rate: float
    mid_rate: float
    timestamp: str
    provider: str
