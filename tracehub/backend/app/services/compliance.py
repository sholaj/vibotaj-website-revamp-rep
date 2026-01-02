"""Compliance service - document requirements and validation."""

from typing import List, Dict, Any

from ..models import Shipment, Document, DocumentType, DocumentStatus
from ..schemas.shipment import DocumentSummary


# Required documents by product type and destination
REQUIRED_DOCUMENTS = {
    # Hooves to Germany/EU
    ("0506", "DE"): [
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.FUMIGATION_CERTIFICATE,
        DocumentType.SANITARY_CERTIFICATE,
        DocumentType.INSURANCE_CERTIFICATE,
        DocumentType.EUDR_DUE_DILIGENCE,
    ],
    # Pellets to Germany/EU
    ("2302", "DE"): [
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.PHYTOSANITARY_CERTIFICATE,
        DocumentType.INSURANCE_CERTIFICATE,
        DocumentType.QUALITY_CERTIFICATE,
        DocumentType.EUDR_DUE_DILIGENCE,
    ],
    # Default requirements
    ("default", "default"): [
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.CERTIFICATE_OF_ORIGIN,
        DocumentType.INSURANCE_CERTIFICATE,
    ],
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
    DocumentType.OTHER: "Other Document",
}


def get_required_documents(shipment: Shipment) -> List[DocumentType]:
    """Get list of required document types for a shipment.

    Args:
        shipment: The shipment to check

    Returns:
        List of required DocumentType enums
    """
    # Get HS code prefix from first product if available
    hs_prefix = "default"
    if shipment.products and len(shipment.products) > 0:
        hs_code = shipment.products[0].hs_code
        if hs_code:
            hs_prefix = hs_code[:4]  # First 4 digits

    # Get destination country
    destination = shipment.pod_code[:2] if shipment.pod_code else "default"

    # Look up requirements
    key = (hs_prefix, destination)
    if key in REQUIRED_DOCUMENTS:
        return REQUIRED_DOCUMENTS[key]

    # Try with just destination
    for (hs, dest), docs in REQUIRED_DOCUMENTS.items():
        if dest == destination:
            return docs

    # Fall back to default
    return REQUIRED_DOCUMENTS[("default", "default")]


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
