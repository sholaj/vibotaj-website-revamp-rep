"""Canonical Document Validation Schemas.

This module defines standardized data structures for document validation,
including canonical schemas for all document types, validation issues,
and cross-document validation results.

The schemas are designed to:
1. Provide consistent handling across all document types
2. Support document versioning and duplicate management
3. Track validation issues with override capability
4. Enable cross-document consistency checks
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class DocumentValidationStatus(str, Enum):
    """Document validation lifecycle states."""
    DRAFT = "draft"                    # Uploaded but not validated
    PENDING_REVIEW = "pending_review"  # Low confidence, needs manual review
    VALIDATED = "validated"            # Passed all validations
    INVALID = "invalid"                # Failed critical validations
    OVERRIDDEN = "overridden"          # Issues overridden by admin


class IssueSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "ERROR"      # Critical - prevents processing (REJECT)
    WARNING = "WARNING"  # Needs review but can proceed (HOLD)
    INFO = "INFO"        # Informational only


class ComparisonType(str, Enum):
    """Types of cross-document comparisons."""
    EQUALS = "EQUALS"                      # Values must be exactly equal
    SET_EQUALS = "SET_EQUALS"              # Sets must be exactly equal
    SET_CONTAINS = "SET_CONTAINS"          # Source set must contain target values
    SET_SUBSET = "SET_SUBSET"              # Source must be subset of target
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"  # Numeric values within % tolerance
    DATE_BEFORE = "DATE_BEFORE"            # Date must be before target
    DATE_BEFORE_OR_EQUAL = "DATE_BEFORE_OR_EQUAL"  # Date must be <= target
    DATE_AFTER = "DATE_AFTER"              # Date must be after target


# =============================================================================
# Common Field Schemas
# =============================================================================

class ExtractedParty(BaseModel):
    """Extracted party information (shipper, consignee, etc.)."""
    name: Optional[str] = Field(None, description="Party name")
    address: Optional[str] = Field(None, description="Full address")
    country: Optional[str] = Field(None, description="Country name or code")
    contact: Optional[str] = Field(None, description="Contact person")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")


class ExtractedWeight(BaseModel):
    """Extracted weight information."""
    gross_kg: Optional[float] = Field(None, ge=0, description="Gross weight in kg")
    net_kg: Optional[float] = Field(None, ge=0, description="Net weight in kg")
    tare_kg: Optional[float] = Field(None, ge=0, description="Tare weight in kg")
    unit: str = Field(default="KG", description="Weight unit")


class FieldConfidence(BaseModel):
    """Confidence score for an extracted field."""
    field: str = Field(..., description="Field name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source: str = Field(default="ocr", description="Extraction source (ocr, llm, manual)")


# =============================================================================
# Document-Type Specific Extracted Fields
# =============================================================================

class BillOfLadingFields(BaseModel):
    """Extracted fields from Bill of Lading."""
    bol_number: Optional[str] = None
    shipper: Optional[ExtractedParty] = None
    consignee: Optional[ExtractedParty] = None
    notify_party: Optional[ExtractedParty] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    container_numbers: List[str] = Field(default_factory=list)
    seal_numbers: List[str] = Field(default_factory=list)
    hs_codes: List[str] = Field(default_factory=list)
    cargo_description: Optional[str] = None
    weight: Optional[ExtractedWeight] = None
    shipped_on_board_date: Optional[date] = None
    issue_date: Optional[date] = None
    freight_terms: Optional[str] = None  # PREPAID, COLLECT


class PackingListFields(BaseModel):
    """Extracted fields from Packing List."""
    packing_list_number: Optional[str] = None
    shipper: Optional[ExtractedParty] = None
    consignee: Optional[ExtractedParty] = None
    container_numbers: List[str] = Field(default_factory=list)
    item_count: Optional[int] = None
    package_count: Optional[int] = None
    weight: Optional[ExtractedWeight] = None
    hs_codes: List[str] = Field(default_factory=list)
    product_descriptions: List[str] = Field(default_factory=list)
    issue_date: Optional[date] = None


class CertificateOfOriginFields(BaseModel):
    """Extracted fields from Certificate of Origin."""
    certificate_number: Optional[str] = None
    origin_country: Optional[str] = None
    exporter: Optional[ExtractedParty] = None
    importer: Optional[ExtractedParty] = None
    hs_codes: List[str] = Field(default_factory=list)
    product_description: Optional[str] = None
    weight: Optional[ExtractedWeight] = None
    issue_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    chamber_of_commerce: Optional[str] = None


class VeterinaryCertificateFields(BaseModel):
    """Extracted fields from Veterinary Health Certificate."""
    certificate_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    authorized_signer: Optional[str] = None
    signer_title: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    product_description: Optional[str] = None
    hs_codes: List[str] = Field(default_factory=list)
    animal_species: Optional[str] = None
    establishment_number: Optional[str] = None
    container_numbers: List[str] = Field(default_factory=list)
    traces_reference: Optional[str] = None  # EU TRACES number


class FumigationCertificateFields(BaseModel):
    """Extracted fields from Fumigation Certificate."""
    certificate_number: Optional[str] = None
    treatment_date: Optional[date] = None
    treatment_method: Optional[str] = None
    chemical_used: Optional[str] = None
    dosage: Optional[str] = None
    exposure_time: Optional[str] = None
    temperature: Optional[str] = None
    container_numbers: List[str] = Field(default_factory=list)
    issuing_company: Optional[str] = None
    authorized_signer: Optional[str] = None
    issue_date: Optional[date] = None


class CommercialInvoiceFields(BaseModel):
    """Extracted fields from Commercial Invoice."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    seller: Optional[ExtractedParty] = None
    buyer: Optional[ExtractedParty] = None
    currency: Optional[str] = None
    total_value: Optional[float] = None
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    weight: Optional[ExtractedWeight] = None
    hs_codes: List[str] = Field(default_factory=list)
    incoterms: Optional[str] = None
    payment_terms: Optional[str] = None


class ExportDeclarationFields(BaseModel):
    """Extracted fields from Export Declaration."""
    declaration_number: Optional[str] = None
    customs_office: Optional[str] = None
    export_date: Optional[date] = None
    exporter: Optional[ExtractedParty] = None
    hs_codes: List[str] = Field(default_factory=list)
    weight: Optional[ExtractedWeight] = None
    fob_value: Optional[float] = None
    currency: Optional[str] = None
    destination_country: Optional[str] = None


class EuTracesCertificateFields(BaseModel):
    """Extracted fields from EU TRACES Certificate."""
    traces_reference: Optional[str] = None  # e.g., RC1479592
    certificate_number: Optional[str] = None
    issue_date: Optional[date] = None
    validity_date: Optional[date] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    product_description: Optional[str] = None
    hs_codes: List[str] = Field(default_factory=list)
    establishment_number: Optional[str] = None
    container_numbers: List[str] = Field(default_factory=list)
    authorized_signer: Optional[str] = None


# Type alias for all field types
ExtractedFields = Union[
    BillOfLadingFields,
    PackingListFields,
    CertificateOfOriginFields,
    VeterinaryCertificateFields,
    FumigationCertificateFields,
    CommercialInvoiceFields,
    ExportDeclarationFields,
    EuTracesCertificateFields,
    Dict[str, Any],  # Fallback for unknown types
]


# =============================================================================
# Canonical Document Data Schema
# =============================================================================

class CanonicalDocumentData(BaseModel):
    """Canonical extracted data for any document type.

    This is stored in the canonical_data JSONB column and provides
    a standardized structure for all document types.
    """
    document_type: str = Field(..., description="Document type code")
    file_id: Optional[str] = Field(None, description="Reference to stored file")
    upload_timestamp: Optional[datetime] = Field(None, description="When document was uploaded")
    parsed_at: Optional[datetime] = Field(None, description="When document was parsed")
    parser_version: str = Field(default="1.0.0", description="Parser version used")

    # Extracted fields (type depends on document_type)
    fields: Dict[str, Any] = Field(default_factory=dict, description="Extracted fields")

    # Raw text and confidence
    raw_text: Optional[str] = Field(None, description="Raw OCR text for audit")
    confidence_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-field confidence scores"
    )
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence"
    )

    # Validation state
    status: DocumentValidationStatus = Field(
        default=DocumentValidationStatus.DRAFT,
        description="Current validation status"
    )

    # Versioning
    version: int = Field(default=1, ge=1, description="Document version number")
    is_primary: bool = Field(default=True, description="Is this the primary version")
    supersedes_id: Optional[str] = Field(None, description="ID of superseded document")

    model_config = ConfigDict(use_enum_values=True)


# =============================================================================
# Validation Issue Schema
# =============================================================================

class DocumentIssue(BaseModel):
    """A validation issue found during document or cross-document validation."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = Field(..., description="ID of the document with the issue")
    shipment_id: Optional[str] = Field(None, description="Associated shipment ID")

    # Rule information
    rule_id: str = Field(..., description="Rule identifier (e.g., DOC-001, XD-002)")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: IssueSeverity = Field(..., description="Issue severity level")
    message: str = Field(..., description="Validation failure message")

    # Field context
    field: Optional[str] = Field(None, description="Field path that failed")
    expected_value: Optional[str] = Field(None, description="Expected value")
    actual_value: Optional[str] = Field(None, description="Actual value found")

    # Cross-document context
    source_document_type: Optional[str] = Field(None, description="Source doc type")
    target_document_type: Optional[str] = Field(None, description="Target doc type")

    # Override tracking
    is_overridden: bool = Field(default=False, description="Whether overridden")
    overridden_by: Optional[str] = Field(None, description="User who overrode")
    overridden_at: Optional[datetime] = Field(None, description="Override timestamp")
    override_reason: Optional[str] = Field(None, description="Override reason")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True)


# =============================================================================
# Presence Check Schemas
# =============================================================================

class RequiredDocument(BaseModel):
    """Definition of a required document for a shipment."""
    document_type: str = Field(..., description="Required document type")
    mandatory: bool = Field(default=True, description="Is this document mandatory")
    description: Optional[str] = Field(None, description="Why this document is required")


class PresenceCheckResult(BaseModel):
    """Result of checking document presence for a shipment."""
    document_type: str = Field(..., description="Document type checked")
    status: str = Field(..., description="missing, draft, uploaded, validated")
    mandatory: bool = Field(..., description="Whether document is mandatory")
    count: int = Field(default=0, description="Number of documents of this type")
    has_duplicates: bool = Field(default=False, description="Multiple versions exist")
    primary_document_id: Optional[str] = Field(None, description="Primary version ID")

    @property
    def is_satisfied(self) -> bool:
        """Check if this requirement is satisfied."""
        if not self.mandatory:
            return True
        return self.status in ("uploaded", "validated")


class PresenceCheckSummary(BaseModel):
    """Summary of all presence checks for a shipment."""
    shipment_id: str
    results: List[PresenceCheckResult]
    all_mandatory_present: bool
    missing_mandatory: List[str] = Field(default_factory=list)
    has_duplicates: bool = False
    checked_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Cross-Document Validation Schemas
# =============================================================================

class CrossDocumentRule(BaseModel):
    """Rule for validating consistency across documents."""
    id: str = Field(..., description="Rule identifier (e.g., XD-001)")
    name: str = Field(..., description="Human-readable rule name")
    source_doc: str = Field(..., description="Source document type")
    source_field: str = Field(..., description="Field path in source document")
    target_doc: Optional[str] = Field(None, description="Target doc type (None for shipment)")
    target_field: str = Field(..., description="Field path in target")
    comparison: ComparisonType = Field(..., description="Type of comparison")
    tolerance: Optional[float] = Field(None, ge=0, le=1, description="Tolerance for numeric comparisons")
    severity: IssueSeverity = Field(..., description="Issue severity if rule fails")
    message: str = Field(..., description="Message when rule fails")

    model_config = ConfigDict(use_enum_values=True)


class CrossDocumentResult(BaseModel):
    """Result of a cross-document validation check."""
    rule_id: str
    rule_name: str
    passed: bool
    message: str
    severity: IssueSeverity
    source_document_id: str
    source_document_type: str
    source_value: Optional[str] = None
    target_document_id: Optional[str] = None
    target_document_type: Optional[str] = None
    target_value: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


# =============================================================================
# Validation Summary Schemas
# =============================================================================

class DocumentValidationResult(BaseModel):
    """Result of validating a single document."""
    document_id: str
    document_type: str
    document_name: str
    status: DocumentValidationStatus
    issues: List[DocumentIssue] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    validated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def decision(self) -> str:
        """Get validation decision based on issues."""
        if self.error_count > 0:
            return "REJECT"
        if self.warning_count > 0:
            return "HOLD"
        return "APPROVE"

    model_config = ConfigDict(use_enum_values=True)


class ShipmentValidationSummary(BaseModel):
    """Complete validation summary for a shipment."""
    shipment_id: str
    shipment_reference: Optional[str] = None

    # Overall status
    overall_decision: str = Field(..., description="APPROVE, HOLD, or REJECT")
    total_documents: int = 0
    validated_documents: int = 0

    # Issue counts
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    overridden_count: int = 0

    # Presence check
    presence_summary: Optional[PresenceCheckSummary] = None

    # Individual document results
    document_results: List[DocumentValidationResult] = Field(default_factory=list)

    # Cross-document results
    cross_document_issues: List[DocumentIssue] = Field(default_factory=list)

    # Metadata
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validation_version: int = Field(default=1, description="Rules version used")

    model_config = ConfigDict(use_enum_values=True)


# =============================================================================
# API Request/Response Schemas
# =============================================================================

class ValidateDocumentRequest(BaseModel):
    """Request to validate a specific document."""
    document_id: str
    force: bool = Field(default=False, description="Force re-validation")


class ValidateShipmentRequest(BaseModel):
    """Request to validate all documents for a shipment."""
    shipment_id: str
    force: bool = Field(default=False, description="Force re-validation of all docs")
    include_cross_document: bool = Field(default=True, description="Run cross-doc checks")


class OverrideIssueRequest(BaseModel):
    """Request to override a validation issue."""
    issue_id: str
    reason: str = Field(..., min_length=10, description="Reason for override (min 10 chars)")


class SelectPrimaryVersionRequest(BaseModel):
    """Request to select the primary version of a document."""
    document_id: str = Field(..., description="ID of document to make primary")
    reason: Optional[str] = Field(None, description="Reason for selection")


class ReclassifyDocumentRequest(BaseModel):
    """Request to manually reclassify a document type."""
    document_id: str
    new_document_type: str
    reason: Optional[str] = None
