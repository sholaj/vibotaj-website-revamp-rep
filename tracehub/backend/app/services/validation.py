"""Document validation rules engine.

Defines field-level validation requirements per document type
and provides validation logic for document compliance.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum

from ..models import Document, DocumentType, DocumentStatus


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Blocks approval
    WARNING = "warning"  # Flagged but can proceed
    INFO = "info"        # Informational only


@dataclass
class ValidationRule:
    """A single validation rule for a document field."""
    field: str
    description: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    required: bool = True

    def validate(self, document: Document) -> Optional[str]:
        """Override in subclasses to implement validation logic."""
        raise NotImplementedError


@dataclass
class RequiredFieldRule(ValidationRule):
    """Validates that a field is present and non-empty."""

    def validate(self, document: Document) -> Optional[str]:
        value = getattr(document, self.field, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            return f"{self.description} is required"
        return None


@dataclass
class DateNotExpiredRule(ValidationRule):
    """Validates that a date field is not in the past."""
    grace_days: int = 0  # Days after expiry still considered valid

    def validate(self, document: Document) -> Optional[str]:
        value = getattr(document, self.field, None)
        if value is None:
            return None  # Let RequiredFieldRule handle missing

        if isinstance(value, datetime):
            value = value.date()

        grace_date = date.today() - timedelta(days=self.grace_days)
        if value < grace_date:
            return f"{self.description} has expired"
        return None


@dataclass
class DateNotFutureRule(ValidationRule):
    """Validates that a date field is not in the future."""

    def validate(self, document: Document) -> Optional[str]:
        value = getattr(document, self.field, None)
        if value is None:
            return None

        if isinstance(value, datetime):
            value = value.date()

        if value > date.today():
            return f"{self.description} cannot be in the future"
        return None


@dataclass
class FileUploadedRule(ValidationRule):
    """Validates that a file has been uploaded."""
    field: str = "file_path"
    description: str = "Document file"

    def validate(self, document: Document) -> Optional[str]:
        if not document.file_path or not document.file_name:
            return "Document file must be uploaded"
        return None


@dataclass
class ExtraDataFieldRule(ValidationRule):
    """Validates a field within the extra_data JSONB column."""
    extra_field: str = ""

    def validate(self, document: Document) -> Optional[str]:
        extra_data = document.extra_data or {}
        value = extra_data.get(self.extra_field)
        if value is None or (isinstance(value, str) and not value.strip()):
            return f"{self.description} is required"
        return None


@dataclass
class ValidationResult:
    """Result of validating a document."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "total_issues": len(self.errors) + len(self.warnings)
        }


# Define validation rules per document type
DOCUMENT_VALIDATION_RULES: Dict[DocumentType, List[ValidationRule]] = {
    DocumentType.BILL_OF_LADING: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "BL Number"),
        RequiredFieldRule("issue_date", "Issue Date"),
        DateNotFutureRule("issue_date", "Issue Date"),
        RequiredFieldRule("issuing_authority", "Shipping Line/Carrier"),
    ],

    DocumentType.COMMERCIAL_INVOICE: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Invoice Number"),
        RequiredFieldRule("issue_date", "Invoice Date"),
        DateNotFutureRule("issue_date", "Invoice Date"),
    ],

    DocumentType.PACKING_LIST: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Packing List Reference"),
        RequiredFieldRule("issue_date", "Issue Date"),
    ],

    DocumentType.CERTIFICATE_OF_ORIGIN: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Certificate Number"),
        RequiredFieldRule("issue_date", "Issue Date"),
        RequiredFieldRule("issuing_authority", "Issuing Chamber/Authority"),
        DateNotFutureRule("issue_date", "Issue Date"),
    ],

    DocumentType.PHYTOSANITARY_CERTIFICATE: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Certificate Number"),
        RequiredFieldRule("issue_date", "Issue Date"),
        RequiredFieldRule("issuing_authority", "Plant Quarantine Authority"),
        RequiredFieldRule("expiry_date", "Expiry Date"),
        DateNotExpiredRule("expiry_date", "Certificate", grace_days=0),
        DateNotFutureRule("issue_date", "Issue Date"),
    ],

    DocumentType.FUMIGATION_CERTIFICATE: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Certificate Number"),
        RequiredFieldRule("issue_date", "Treatment Date"),
        RequiredFieldRule("issuing_authority", "Fumigation Company"),
        RequiredFieldRule("expiry_date", "Validity Date"),
        DateNotExpiredRule("expiry_date", "Certificate", grace_days=0),
    ],

    DocumentType.SANITARY_CERTIFICATE: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Certificate Number"),
        RequiredFieldRule("issue_date", "Issue Date"),
        RequiredFieldRule("issuing_authority", "Health Authority"),
        RequiredFieldRule("expiry_date", "Expiry Date"),
        DateNotExpiredRule("expiry_date", "Certificate", grace_days=0),
    ],

    DocumentType.INSURANCE_CERTIFICATE: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Policy/Certificate Number"),
        RequiredFieldRule("issue_date", "Issue Date"),
        RequiredFieldRule("issuing_authority", "Insurance Company"),
        RequiredFieldRule("expiry_date", "Coverage End Date"),
        DateNotExpiredRule("expiry_date", "Insurance Coverage", grace_days=0),
    ],

    DocumentType.EUDR_DUE_DILIGENCE: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "DDS Reference Number"),
        RequiredFieldRule("issue_date", "Statement Date"),
        DateNotFutureRule("issue_date", "Statement Date"),
        # EUDR-specific fields stored in extra_data
        ExtraDataFieldRule(
            field="extra_data",
            extra_field="operator_name",
            description="Operator Name",
            severity=ValidationSeverity.ERROR
        ),
        ExtraDataFieldRule(
            field="extra_data",
            extra_field="country_of_production",
            description="Country of Production",
            severity=ValidationSeverity.ERROR
        ),
        ExtraDataFieldRule(
            field="extra_data",
            extra_field="geolocation_coordinates",
            description="Geolocation Coordinates",
            severity=ValidationSeverity.ERROR
        ),
        ExtraDataFieldRule(
            field="extra_data",
            extra_field="commodity_description",
            description="Commodity Description",
            severity=ValidationSeverity.ERROR
        ),
        ExtraDataFieldRule(
            field="extra_data",
            extra_field="risk_assessment_conclusion",
            description="Risk Assessment Conclusion",
            severity=ValidationSeverity.WARNING
        ),
    ],

    DocumentType.QUALITY_CERTIFICATE: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Certificate Number"),
        RequiredFieldRule("issue_date", "Test Date"),
        RequiredFieldRule("issuing_authority", "Testing Laboratory"),
    ],

    DocumentType.CUSTOMS_DECLARATION: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Declaration Number"),
        RequiredFieldRule("issue_date", "Declaration Date"),
    ],

    DocumentType.CONTRACT: [
        FileUploadedRule(),
        RequiredFieldRule("reference_number", "Contract Number"),
        RequiredFieldRule("issue_date", "Contract Date"),
    ],

    DocumentType.OTHER: [
        FileUploadedRule(),
        RequiredFieldRule("name", "Document Name"),
    ],
}


def validate_document(document: Document) -> ValidationResult:
    """Validate a document against its type-specific rules.

    Args:
        document: The document to validate

    Returns:
        ValidationResult with all issues found
    """
    rules = DOCUMENT_VALIDATION_RULES.get(document.document_type, [])

    errors = []
    warnings = []
    info = []

    for rule in rules:
        message = rule.validate(document)
        if message:
            if rule.severity == ValidationSeverity.ERROR:
                errors.append(message)
            elif rule.severity == ValidationSeverity.WARNING:
                warnings.append(message)
            else:
                info.append(message)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info=info
    )


def get_required_fields(doc_type: DocumentType) -> List[Dict[str, Any]]:
    """Get list of required fields for a document type.

    Args:
        doc_type: The document type

    Returns:
        List of field definitions with name, description, and requirements
    """
    rules = DOCUMENT_VALIDATION_RULES.get(doc_type, [])
    fields = []

    for rule in rules:
        if isinstance(rule, ExtraDataFieldRule):
            fields.append({
                "field": f"extra_data.{rule.extra_field}",
                "description": rule.description,
                "required": rule.required,
                "severity": rule.severity.value
            })
        else:
            fields.append({
                "field": rule.field,
                "description": rule.description,
                "required": rule.required,
                "severity": rule.severity.value
            })

    return fields


def check_expiring_documents(documents: List[Document], days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Check for documents expiring within the specified timeframe.

    Args:
        documents: List of documents to check
        days_ahead: Number of days to look ahead for expiry

    Returns:
        List of expiring document info
    """
    expiring = []
    threshold = date.today() + timedelta(days=days_ahead)

    for doc in documents:
        if doc.expiry_date:
            expiry = doc.expiry_date
            if isinstance(expiry, datetime):
                expiry = expiry.date()

            if expiry <= threshold:
                days_until = (expiry - date.today()).days
                expiring.append({
                    "document_id": str(doc.id),
                    "document_type": doc.document_type.value,
                    "name": doc.name,
                    "expiry_date": expiry.isoformat(),
                    "days_until_expiry": days_until,
                    "is_expired": days_until < 0,
                    "urgency": "expired" if days_until < 0 else (
                        "critical" if days_until <= 7 else (
                            "warning" if days_until <= 14 else "info"
                        )
                    )
                })

    # Sort by days until expiry (most urgent first)
    expiring.sort(key=lambda x: x["days_until_expiry"])
    return expiring
