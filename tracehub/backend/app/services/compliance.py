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

    This is a convenience wrapper around get_required_documents_by_hs_code
    that extracts HS code and destination from a Shipment object.

    Args:
        shipment: The shipment to check

    Returns:
        List of required DocumentType enums
    """
    # Get HS code prefix from first product if available
    hs_code = "default"
    if shipment.products and len(shipment.products) > 0:
        product_hs = shipment.products[0].hs_code
        if product_hs:
            hs_code = product_hs

    # Get destination country
    destination = shipment.pod_code[:2] if shipment.pod_code else "DE"

    return get_required_documents_by_hs_code(hs_code, destination)


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
    # Index documents by type
    doc_by_type: Dict[DocumentType, Document] = {}
    for doc in documents:
        # Keep the most recent/best status document of each type
        if doc.document_type not in doc_by_type:
            doc_by_type[doc.document_type] = doc
        elif doc.status.value > doc_by_type[doc.document_type].status.value:
            doc_by_type[doc.document_type] = doc

    # Check completeness
    complete_count = 0
    pending_count = 0
    missing_types = []

    for doc_type in required_types:
        if doc_type in doc_by_type:
            doc = doc_by_type[doc_type]
            if doc.status in [DocumentStatus.VALIDATED, DocumentStatus.COMPLIANCE_OK, DocumentStatus.LINKED]:
                complete_count += 1
            elif doc.status == DocumentStatus.UPLOADED:
                pending_count += 1
        else:
            missing_types.append(DOCUMENT_NAMES.get(doc_type, doc_type.value))

    return DocumentSummary(
        total_required=len(required_types),
        total_uploaded=len(documents),
        complete=complete_count,
        missing=missing_types,
        pending_validation=pending_count,
        is_complete=len(missing_types) == 0 and pending_count == 0
    )
