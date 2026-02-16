"""Pydantic schemas for document classification (PRD-019).

Classification result types for the v2 AI document classifier
with provider-agnostic LLM abstraction.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional


class ClassificationAlternative(BaseModel):
    """An alternative classification suggestion."""

    document_type: str
    confidence: float


class ClassificationResponse(BaseModel):
    """Response from the classification endpoint."""

    document_type: str
    confidence: float
    method: str  # "ai", "keyword"
    provider: str  # "anthropic", "mock", "keyword"
    reference_number: Optional[str] = None
    key_fields: Dict[str, str] = {}
    reasoning: str = ""
    alternatives: List[ClassificationAlternative] = []


class ClassificationInUpload(BaseModel):
    """Classification result embedded in the upload response."""

    suggested_type: str
    confidence: float
    method: str
    auto_applied: bool = False


class ReclassifyResponse(BaseModel):
    """Response from the reclassify endpoint."""

    document_id: str
    previous_type: str
    new_type: str
    classification: ClassificationResponse
    auto_applied: bool = False
