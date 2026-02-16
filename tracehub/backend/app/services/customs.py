"""Customs backend protocol for trade compliance operations (PRD-021).

Provider-agnostic interface for customs API interactions.
Same pattern as EmailBackend (PRD-020), LLMBackend (PRD-019), StorageBackend (PRD-005).

Implementations:
- MockCustomsBackend: Dev/test (simulates NCS responses)
- Future: NCSCustomsBackend, SONCustomsBackend
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol
from enum import StrEnum


class ClearanceStatus(StrEnum):
    """Pre-clearance check result status."""

    CLEARED = "cleared"
    PENDING_DOCS = "pending_docs"
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"


class DeclarationStatus(StrEnum):
    """Export declaration status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    AMENDED = "amended"


@dataclass
class PreClearanceResult:
    """Result of a pre-clearance check."""

    hs_code: str
    origin_country: str
    status: ClearanceStatus
    required_documents: List[str] = field(default_factory=list)
    restrictions: List[str] = field(default_factory=list)
    notes: str = ""
    provider: str = ""


@dataclass
class DutyCalculation:
    """Result of a duty calculation."""

    hs_code: str
    cif_value: float
    currency: str
    import_duty_rate: float
    import_duty_amount: float
    vat_rate: float
    vat_amount: float
    surcharges: List[Dict[str, object]] = field(default_factory=list)
    total_duty: float = 0.0
    provider: str = ""


@dataclass
class DeclarationResult:
    """Result of submitting an export declaration."""

    reference_number: str
    status: DeclarationStatus
    submitted_at: Optional[str] = None
    provider: str = ""
    error: Optional[str] = None


class CustomsBackend(Protocol):
    """Protocol for customs API operations.

    Implementations must provide pre-clearance checks,
    duty calculations, and declaration submission.
    Provider-specific details (API key, base URL) are
    handled internally.
    """

    def check_pre_clearance(
        self, hs_code: str, origin_country: str, destination_country: str = "DE"
    ) -> PreClearanceResult:
        """Check pre-clearance status for a product.

        Args:
            hs_code: Harmonized System code (e.g., '0506', '1801').
            origin_country: ISO 3166-1 alpha-2 (e.g., 'NG').
            destination_country: ISO 3166-1 alpha-2 (default 'DE').

        Returns:
            PreClearanceResult with status and required documents.
        """
        ...

    def calculate_duty(
        self,
        hs_code: str,
        cif_value: float,
        currency: str = "EUR",
        quantity: float = 1.0,
    ) -> DutyCalculation:
        """Calculate import duties for a product.

        Args:
            hs_code: Harmonized System code.
            cif_value: Cost, Insurance, and Freight value.
            currency: Currency code (default EUR).
            quantity: Quantity in standard units.

        Returns:
            DutyCalculation with duty breakdown.
        """
        ...

    def submit_declaration(
        self,
        shipment_reference: str,
        hs_code: str,
        exporter_name: str,
        consignee_name: str,
        cif_value: float,
        currency: str = "EUR",
        extra_data: Optional[Dict[str, object]] = None,
    ) -> DeclarationResult:
        """Submit an export declaration.

        Args:
            shipment_reference: TraceHub shipment reference.
            hs_code: Harmonized System code.
            exporter_name: Name of the exporting organization.
            consignee_name: Name of the buyer/consignee.
            cif_value: Cost, Insurance, and Freight value.
            currency: Currency code.
            extra_data: Additional provider-specific fields.

        Returns:
            DeclarationResult with reference number and status.
        """
        ...

    def get_declaration_status(self, reference_number: str) -> DeclarationResult:
        """Get the current status of a submitted declaration.

        Args:
            reference_number: Declaration reference from submit_declaration().

        Returns:
            DeclarationResult with current status.
        """
        ...

    def is_available(self) -> bool:
        """Check if the customs backend is operational."""
        ...

    def get_provider_name(self) -> str:
        """Return the provider identifier (e.g. 'ncs', 'son', 'mock')."""
        ...

    def get_status(self) -> Dict[str, object]:
        """Return detailed status information."""
        ...
