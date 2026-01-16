"""Compliance service - document requirements and validation.

This module implements the compliance rules defined in docs/COMPLIANCE_MATRIX.md.
It is the single source of truth for HS code classification and document requirements.

Key functions:
- is_eudr_required(hs_code) - Check if EUDR applies to a product
- get_required_documents_by_hs_code(hs_code, destination) - Get required documents
- get_required_documents(shipment) - Get required documents for a shipment
- check_document_completeness(documents, required_types) - Check completeness
"""

from typing import List, Dict, Any, Optional

from ..models import Shipment, Document, DocumentType, DocumentStatus
from ..models.shipment import ProductType
from ..schemas.shipment import DocumentSummary


# ============================================================================
# EUDR HS CODE CLASSIFICATION
# Based on EUDR Annex I - see docs/COMPLIANCE_MATRIX.md
# ============================================================================

# HS codes that require EUDR compliance (EU Deforestation Regulation)
# These are products covered by EUDR Annex I
EUDR_HS_CODES = ['1801', '0901', '1511', '4001', '1201']
"""
EUDR-applicable HS codes:
- 1801: Cocoa beans
- 0901: Coffee
- 1511: Palm oil
- 4001: Natural rubber
- 1201: Soybeans

NOT in EUDR:
- 0506/0507: Horn and hoof (animal by-products)
- 0714: Sweet potato pellets
- 0902: Hibiscus flowers
- 0910: Dried ginger
"""

# Horn and hoof HS codes - explicitly NOT covered by EUDR
HORN_HOOF_HS_CODES = ['0506', '0507']


# ============================================================================
# PRODUCT TYPE TO HS CODE MAPPING
# Maps ProductType enum to primary HS codes for document requirements
# ============================================================================

PRODUCT_TYPE_TO_HS_CODE: Dict[ProductType, str] = {
    ProductType.HORN_HOOF: "0506",      # Animal by-products
    ProductType.SWEET_POTATO: "0714",   # Sweet potato pellets
    ProductType.HIBISCUS: "0902",       # Hibiscus flowers
    ProductType.GINGER: "0910",         # Dried ginger
    ProductType.COCOA: "1801",          # Cocoa beans (EUDR)
    ProductType.OTHER: "default",       # Default requirements
}

# Human-readable product type labels
PRODUCT_TYPE_LABELS: Dict[ProductType, str] = {
    ProductType.HORN_HOOF: "Horn & Hoof",
    ProductType.SWEET_POTATO: "Sweet Potato Pellets",
    ProductType.HIBISCUS: "Hibiscus Flowers",
    ProductType.GINGER: "Dried Ginger",
    ProductType.COCOA: "Cocoa Beans",
    ProductType.OTHER: "Other",
}


def is_eudr_product_type(product_type: ProductType) -> bool:
    """Check if a product type requires EUDR compliance.

    Args:
        product_type: The ProductType enum value

    Returns:
        True if the product type requires EUDR compliance
    """
    return product_type == ProductType.COCOA


def get_required_documents_by_product_type(
    product_type: ProductType,
    destination: str = "DE"
) -> List[DocumentType]:
    """Get required documents based on product type.

    This is the primary function for determining document requirements
    when creating a shipment with a known product type.

    Args:
        product_type: The ProductType enum value
        destination: Destination country code (default: DE for Germany)

    Returns:
        List of required DocumentType enums
    """
    hs_code = PRODUCT_TYPE_TO_HS_CODE.get(product_type, "default")
    return get_required_documents_by_hs_code(hs_code, destination)


def is_eudr_required(hs_code: str) -> bool:
    """Check if EUDR (EU Deforestation Regulation) applies to an HS code.

    This is the centralized function for determining EUDR applicability.
    Horn/hoof products (HS 0506/0507) are explicitly NOT covered by EUDR.

    Args:
        hs_code: The HS (Harmonized System) code to check.
                 Can be 4-digit prefix or full code (e.g., "1801" or "1801.00.00")

    Returns:
        True if the product requires EUDR compliance documentation,
        False otherwise.

    Examples:
        >>> is_eudr_required("0506")  # Horn
        False
        >>> is_eudr_required("0507.90")  # Hoof
        False
        >>> is_eudr_required("1801")  # Cocoa
        True
        >>> is_eudr_required("0714.20")  # Sweet potato
        False
    """
    if not hs_code or not hs_code.strip():
        return False

    # Get the first 4 characters (HS chapter + heading)
    prefix = hs_code.strip()[:4]

    # Check if the prefix starts with any EUDR code
    return any(prefix.startswith(code) for code in EUDR_HS_CODES)


def is_horn_hoof_product(hs_code: str) -> bool:
    """Check if the HS code is for horn or hoof products.

    Horn and hoof products (HS 0506/0507) require special documentation
    (EU TRACES, Veterinary Health Certificate) but NOT EUDR documents.

    Args:
        hs_code: The HS code to check.

    Returns:
        True if the product is horn or hoof.
    """
    if not hs_code or not hs_code.strip():
        return False

    prefix = hs_code.strip()[:4]
    return any(prefix.startswith(code) for code in HORN_HOOF_HS_CODES)


# EU member state country codes (ISO 3166-1 alpha-2)
EU_COUNTRY_CODES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE"
}

# ============================================================================
# REQUIRED DOCUMENTS BY PRODUCT TYPE AND DESTINATION
# Based on docs/COMPLIANCE_MATRIX.md
# ============================================================================

REQUIRED_DOCUMENTS = {
    # -------------------------------------------------------------------------
    # HORN & HOOF (HS 0506, 0507) - Animal products, NO EUDR
    # Requires: EU TRACES (RC1479592), Vet Health Cert, CoO, BOL, Invoice, Packing
    # -------------------------------------------------------------------------
    ("0506", "DE"): [
        DocumentType.EU_TRACES_CERTIFICATE,  # Must show RC1479592
        DocumentType.VETERINARY_HEALTH_CERTIFICATE,  # From Nigerian authority
        DocumentType.CERTIFICATE_OF_ORIGIN,  # Must specify Nigeria
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.EXPORT_DECLARATION,
    ],
    ("0507", "DE"): [
        DocumentType.EU_TRACES_CERTIFICATE,
        DocumentType.VETERINARY_HEALTH_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.EXPORT_DECLARATION,
    ],
    ("0506", "EU"): [
        DocumentType.EU_TRACES_CERTIFICATE,
        DocumentType.VETERINARY_HEALTH_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.EXPORT_DECLARATION,
    ],
    ("0507", "EU"): [
        DocumentType.EU_TRACES_CERTIFICATE,
        DocumentType.VETERINARY_HEALTH_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.EXPORT_DECLARATION,
    ],

    # -------------------------------------------------------------------------
    # SWEET POTATO PELLETS (HS 0714.20) - Plant products, NO EUDR
    # Requires: Phyto, CoO, Quality, BOL, Invoice
    # -------------------------------------------------------------------------
    ("0714", "DE"): [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
    ],
    ("0714", "EU"): [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
    ],

    # -------------------------------------------------------------------------
    # HIBISCUS FLOWERS (HS 0902.10) - Plant products, NO EUDR
    # Requires: Phyto, CoO, Quality (grade spec), BOL, Invoice
    # -------------------------------------------------------------------------
    ("0902", "DE"): [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
    ],
    ("0902", "EU"): [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
    ],

    # -------------------------------------------------------------------------
    # DRIED GINGER (HS 0910.11) - Plant products, NO EUDR
    # Requires: Phyto, CoO, Quality (moisture & grade), BOL, Invoice
    # -------------------------------------------------------------------------
    ("0910", "DE"): [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
    ],
    ("0910", "EU"): [
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
    ],

    # -------------------------------------------------------------------------
    # COCOA BEANS (HS 1801) - EUDR APPLICABLE (future use)
    # Requires: All standard docs + EUDR package (geolocation, deforestation stmt)
    # -------------------------------------------------------------------------
    ("1801", "DE"): [
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.EUDR_DUE_DILIGENCE,  # EUDR required
    ],
    ("1801", "EU"): [
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.EUDR_DUE_DILIGENCE,  # EUDR required
    ],

    # -------------------------------------------------------------------------
    # COFFEE (HS 0901) - EUDR APPLICABLE
    # -------------------------------------------------------------------------
    ("0901", "DE"): [
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.EUDR_DUE_DILIGENCE,
    ],
    ("0901", "EU"): [
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.EUDR_DUE_DILIGENCE,
    ],

    # -------------------------------------------------------------------------
    # PELLETS (HS 2302) - Agricultural by-products
    # -------------------------------------------------------------------------
    ("2302", "DE"): [
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.QUALITY_CERTIFICATE,
    ],

    # -------------------------------------------------------------------------
    # DEFAULT REQUIREMENTS
    # -------------------------------------------------------------------------
    ("default", "default"): [
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.CERTIFICATE_OF_ORIGIN,
    ],
}

# Validation rules for Horn & Hoof documents
HORN_HOOF_VALIDATION_RULES = {
    DocumentType.EU_TRACES_CERTIFICATE: {
        "required_field": "reference_number",
        "expected_value": "RC1479592",
        "description": "EU TRACES must show RC1479592",
    },
    DocumentType.VETERINARY_HEALTH_CERTIFICATE: {
        "required_field": "issuing_authority",
        "expected_contains": ["Nigeria", "Nigerian", "NVRI", "Federal"],
        "description": "Must be from Nigerian veterinary authority",
    },
    DocumentType.CERTIFICATE_OF_ORIGIN: {
        "required_field": "extra_data.country_of_origin",
        "expected_value": "Nigeria",
        "description": "Must specify Nigeria as country of origin",
    },
}

# Human-readable document names
DOCUMENT_NAMES = {
    DocumentType.BILL_OF_LADING: "Bill of Lading",
    DocumentType.COMMERCIAL_INVOICE: "Commercial Invoice",
    DocumentType.PACKING_LIST: "Packing List",
    DocumentType.CERTIFICATE_OF_ORIGIN: "Certificate of Origin",
    DocumentType.PHYTOSANITARY_CERTIFICATE: "Phytosanitary Certificate",
    DocumentType.FUMIGATION_CERTIFICATE: "Fumigation Certificate",
    DocumentType.SANITARY_CERTIFICATE: "Sanitary Certificate",
    DocumentType.INSURANCE_CERTIFICATE: "Insurance Certificate",
    DocumentType.CUSTOMS_DECLARATION: "Customs Declaration",
    DocumentType.CONTRACT: "Contract",
    DocumentType.EUDR_DUE_DILIGENCE: "EUDR Due Diligence Statement",
    DocumentType.QUALITY_CERTIFICATE: "Quality Certificate",
    # Horn & Hoof specific documents
    DocumentType.EU_TRACES_CERTIFICATE: "EU TRACES Certificate",
    DocumentType.VETERINARY_HEALTH_CERTIFICATE: "Veterinary Health Certificate",
    DocumentType.EXPORT_DECLARATION: "Export Declaration",
    DocumentType.OTHER: "Other Document",
}


def get_required_documents_by_hs_code(
    hs_code: str,
    destination: str = "DE"
) -> List[DocumentType]:
    """Get list of required document types based on HS code and destination.

    This is the primary function for determining document requirements.
    Use this when you have an HS code but not a full shipment object.

    Args:
        hs_code: The HS code (e.g., "0506", "0714.20", "1801.00.00")
        destination: The destination country code (default: "DE" for Germany)

    Returns:
        List of required DocumentType enums

    Examples:
        >>> get_required_documents_by_hs_code("0506", "DE")
        [EU_TRACES_CERTIFICATE, VETERINARY_HEALTH_CERTIFICATE, ...]
        >>> get_required_documents_by_hs_code("0714", "DE")
        [PHYTOSANITARY_CERTIFICATE, CERTIFICATE_OF_ORIGIN, ...]
    """
    if not hs_code:
        return REQUIRED_DOCUMENTS[("default", "default")]

    # Get 4-digit prefix
    hs_prefix = hs_code.strip()[:4]
    dest = destination.upper() if destination else "DE"

    # Look up requirements with specific destination
    key = (hs_prefix, dest)
    if key in REQUIRED_DOCUMENTS:
        return REQUIRED_DOCUMENTS[key]

    # For EU countries, try the "EU" fallback
    if dest in EU_COUNTRY_CODES:
        eu_key = (hs_prefix, "EU")
        if eu_key in REQUIRED_DOCUMENTS:
            return REQUIRED_DOCUMENTS[eu_key]

    # Try to find any matching HS code
    for (hs, d), docs in REQUIRED_DOCUMENTS.items():
        if hs == hs_prefix:
            return docs

    # Fall back to default
    return REQUIRED_DOCUMENTS[("default", "default")]


def get_required_documents(shipment: Shipment) -> List[DocumentType]:
    """Get list of required document types for a shipment.

    Uses product_type (primary) or products array HS code (fallback)
    to determine document requirements.

    Args:
        shipment: The shipment to check

    Returns:
        List of required DocumentType enums
    """
    # Get destination country
    destination = shipment.pod_code[:2] if shipment.pod_code else "DE"

    # Primary: Check product_type field (set during shipment creation)
    if shipment.product_type:
        return get_required_documents_by_product_type(shipment.product_type, destination)

    # Fallback: Get HS code prefix from first product if available
    hs_code = "default"
    if shipment.products and len(shipment.products) > 0:
        product_hs = shipment.products[0].hs_code
        if product_hs:
            hs_code = product_hs

    return get_required_documents_by_hs_code(hs_code, destination)


def _get_status_value(status) -> str:
    """Get status value as string, handling both enum and string types."""
    if hasattr(status, 'value'):
        return status.value
    return str(status) if status else ''


def _get_doc_type_value(doc_type) -> str:
    """Get document type value as string, handling both enum and string types."""
    if hasattr(doc_type, 'value'):
        return doc_type.value
    return str(doc_type) if doc_type else ''


def check_document_completeness(
    documents: List[Document],
    required_types: List[DocumentType]
) -> DocumentSummary:
    """Check document completeness for a shipment.

    Args:
        documents: List of documents attached to shipment
        required_types: List of required document types

    Returns:
        DocumentSummary with completeness information
    """
    # Index documents by type (use string values for comparison)
    doc_by_type: Dict[str, Document] = {}
    for doc in documents:
        doc_type_str = _get_doc_type_value(doc.document_type)
        status_str = _get_status_value(doc.status)
        # Keep the most recent/best status document of each type
        if doc_type_str not in doc_by_type:
            doc_by_type[doc_type_str] = doc
        else:
            existing_status = _get_status_value(doc_by_type[doc_type_str].status)
            if status_str > existing_status:
                doc_by_type[doc_type_str] = doc

    # Check completeness
    complete_count = 0
    pending_count = 0
    missing_types = []

    # Statuses that indicate completion
    complete_statuses = {'VALIDATED', 'COMPLIANCE_OK', 'LINKED'}
    pending_statuses = {'UPLOADED'}

    for doc_type in required_types:
        doc_type_str = _get_doc_type_value(doc_type)
        if doc_type_str in doc_by_type:
            doc = doc_by_type[doc_type_str]
            status_str = _get_status_value(doc.status)
            if status_str in complete_statuses:
                complete_count += 1
            elif status_str in pending_statuses:
                pending_count += 1
        else:
            missing_types.append(DOCUMENT_NAMES.get(doc_type, _get_doc_type_value(doc_type)))

    return DocumentSummary(
        total_required=len(required_types),
        total_uploaded=len(documents),
        complete=complete_count,
        missing=missing_types,
        pending_validation=pending_count,
        is_complete=len(missing_types) == 0 and pending_count == 0
    )


# ============================================================================
# DOCUMENT CONTENT VALIDATION - Sprint 14
# ============================================================================

class DocumentValidationResult:
    """Result of document content validation."""

    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str):
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


def validate_document_content(
    document: Document,
    shipment: Optional[Shipment] = None
) -> DocumentValidationResult:
    """Validate document content against compliance rules.

    Sprint 14: Implements enforcement of HORN_HOOF_VALIDATION_RULES.

    Args:
        document: The document to validate
        shipment: Optional shipment for context (to determine product type)

    Returns:
        DocumentValidationResult with validation status and any errors/warnings

    Examples:
        >>> result = validate_document_content(eu_traces_doc, shipment)
        >>> if not result.is_valid:
        ...     raise HTTPException(400, result.errors[0])
    """
    result = DocumentValidationResult()

    # Determine if this is a Horn & Hoof shipment
    is_horn_hoof = False
    if shipment:
        is_horn_hoof = shipment.product_type == ProductType.HORN_HOOF

    # Get document type as string for lookup
    doc_type_str = _get_doc_type_value(document.document_type)

    # Check Horn & Hoof validation rules
    if is_horn_hoof and document.document_type in HORN_HOOF_VALIDATION_RULES:
        rule = HORN_HOOF_VALIDATION_RULES[document.document_type]

        # EU TRACES must have RC1479592
        if document.document_type == DocumentType.EU_TRACES_CERTIFICATE:
            ref_num = getattr(document, 'reference_number', None)
            if not ref_num:
                # Check extra_data if available
                if document.extra_data:
                    ref_num = document.extra_data.get('reference_number')

            expected = rule.get("expected_value", "RC1479592")
            if ref_num and expected not in ref_num:
                result.add_error(
                    f"EU TRACES Certificate must reference {expected}. "
                    f"VIBOTAJ Global Nigeria Ltd registration is required for Horn & Hoof exports."
                )
            elif not ref_num:
                result.add_warning(
                    f"EU TRACES Certificate should show reference {expected}. "
                    "Please verify the document includes VIBOTAJ registration."
                )

        # Veterinary Health Certificate must be from Nigerian authority
        elif document.document_type == DocumentType.VETERINARY_HEALTH_CERTIFICATE:
            issuing_auth = None
            if document.extra_data:
                issuing_auth = document.extra_data.get('issuing_authority', '')

            expected_contains = rule.get("expected_contains", [])
            if issuing_auth:
                if not any(term.lower() in issuing_auth.lower() for term in expected_contains):
                    result.add_warning(
                        f"Veterinary Health Certificate should be from Nigerian authority. "
                        f"Found: {issuing_auth}"
                    )

        # Certificate of Origin must specify Nigeria
        elif document.document_type == DocumentType.CERTIFICATE_OF_ORIGIN:
            country_origin = None
            if document.extra_data:
                country_origin = document.extra_data.get('country_of_origin', '')

            expected = rule.get("expected_value", "Nigeria")
            if country_origin and expected.lower() not in country_origin.lower():
                result.add_warning(
                    f"Certificate of Origin should specify {expected} as country of origin. "
                    f"Found: {country_origin}"
                )

    return result


def validate_traces_reference(reference_number: str) -> bool:
    """Validate that a TRACES reference includes VIBOTAJ registration.

    Args:
        reference_number: The TRACES certificate reference number

    Returns:
        True if the reference includes RC1479592

    Example:
        >>> validate_traces_reference("TRACES-EU/RC1479592/2026/001")
        True
        >>> validate_traces_reference("TRACES-EU/XX999999/2026/001")
        False
    """
    return "RC1479592" in reference_number if reference_number else False
