"""Pydantic schemas for BoL parse results (PRD-018).

Field-level confidence scores and structured parse status
for the v2 auto-parse pipeline.
"""

from pydantic import BaseModel
from typing import Optional, List


class BolFieldResult(BaseModel):
    """A single extracted field with its confidence score."""
    value: Optional[str] = None
    confidence: float = 0.0


class BolComplianceResult(BaseModel):
    """Summary compliance result from BoL check."""
    decision: str  # APPROVE, HOLD, REJECT
    rules_passed: int = 0
    rules_failed: int = 0
    rules_total: int = 0


class BolParsedResponse(BaseModel):
    """Response for GET /documents/{id}/bol/parsed endpoint."""
    document_id: str
    parse_status: str  # "parsed", "pending", "failed", "not_bol"
    parsed_at: Optional[str] = None
    confidence_score: float = 0.0
    fields: dict[str, BolFieldResult] = {}
    compliance: Optional[BolComplianceResult] = None
    auto_synced: bool = False


class SyncChange(BaseModel):
    """A single field change in sync preview."""
    field: str
    current: Optional[str] = None
    new_value: Optional[str] = None
    is_placeholder: bool = False
    will_update: bool = False


class BolSyncPreviewResponse(BaseModel):
    """Response for GET /documents/{id}/bol/sync-preview (enhanced)."""
    document_id: str
    shipment_id: str
    shipment_reference: str
    changes: List[SyncChange] = []
    auto_synced: bool = False
