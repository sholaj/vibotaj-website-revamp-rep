"""
Centralized entity creation with required fields.

This module provides factory functions that ensure all required fields
(especially organization_id) are always set when creating entities.

ALWAYS use these functions instead of direct Model() instantiation to
prevent multi-tenancy bugs where organization_id is forgotten.

Usage:
    from app.services.entity_factory import create_product, create_document

    # Product creation - organization_id inherited from shipment
    product = create_product(
        shipment=shipment,
        name="Buffalo Horns",
        hs_code="050610"
    )

    # Document creation - organization_id inherited from shipment
    document = create_document(
        shipment=shipment,
        document_type=DocumentType.BILL_OF_LADING,
        name="BOL-12345.pdf",
        file_path="/uploads/bol.pdf"
    )

See: PRP-017 Phase 3 for rationale.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from ..models.product import Product
from ..models.document import Document, DocumentType, DocumentStatus
from ..models.shipment import Shipment


def create_product(
    shipment: Shipment,
    name: str,
    *,
    hs_code: Optional[str] = None,
    description: Optional[str] = None,
    quantity_net_kg: Optional[float] = None,
    quantity_gross_kg: Optional[float] = None,
    quantity_units: Optional[int] = None,
    packaging: Optional[str] = None,
    batch_number: Optional[str] = None,
    lot_number: Optional[str] = None,
    moisture_content: Optional[float] = None,
    quality_grade: Optional[str] = None,
) -> Product:
    """
    Create a Product with all required fields.

    The organization_id is automatically inherited from the shipment,
    ensuring proper multi-tenancy isolation.

    Args:
        shipment: Parent shipment (required - provides organization_id)
        name: Product name (required)
        hs_code: Harmonized System code (e.g., "050610")
        description: Product description
        quantity_net_kg: Net weight in kg
        quantity_gross_kg: Gross weight in kg
        quantity_units: Number of units
        packaging: Packaging type (e.g., "bags", "cartons")
        batch_number: Batch identifier
        lot_number: Lot identifier
        moisture_content: Moisture percentage
        quality_grade: Quality grade (e.g., "A", "B", "Premium")

    Returns:
        Product instance ready to be added to database session

    Raises:
        ValueError: If shipment has no organization_id
    """
    if not shipment.organization_id:
        raise ValueError(
            f"Cannot create product: shipment {shipment.id} has no organization_id. "
            "This indicates a data integrity issue."
        )

    return Product(
        shipment_id=shipment.id,
        organization_id=shipment.organization_id,
        name=name,
        hs_code=hs_code,
        description=description,
        quantity_net_kg=quantity_net_kg,
        quantity_gross_kg=quantity_gross_kg,
        quantity_units=quantity_units,
        packaging=packaging,
        batch_number=batch_number,
        lot_number=lot_number,
        moisture_content=moisture_content,
        quality_grade=quality_grade,
    )


def create_document(
    shipment: Shipment,
    document_type: DocumentType,
    name: str,
    *,
    file_path: Optional[str] = None,
    status: DocumentStatus = DocumentStatus.UPLOADED,
    file_name: Optional[str] = None,
    file_size: Optional[int] = None,
    mime_type: Optional[str] = None,
    document_date: Optional[datetime] = None,
    expiry_date: Optional[datetime] = None,
    issuer: Optional[str] = None,
    reference_number: Optional[str] = None,
    uploaded_by: Optional[UUID] = None,
    validation_notes: Optional[str] = None,
) -> Document:
    """
    Create a Document with all required fields.

    The organization_id is automatically inherited from the shipment,
    ensuring proper multi-tenancy isolation.

    Args:
        shipment: Parent shipment (required - provides organization_id)
        document_type: Type of document (e.g., DocumentType.BILL_OF_LADING)
        name: Document name/title (required)
        file_path: Path to stored file
        status: Initial status (default: UPLOADED)
        file_name: Original filename
        file_size: File size in bytes
        mime_type: MIME type (e.g., "application/pdf")
        document_date: Date on the document
        expiry_date: Document expiry date
        issuer: Issuing authority/organization
        reference_number: Document reference number
        uploaded_by: User ID who uploaded the document
        validation_notes: Notes from validation process

    Returns:
        Document instance ready to be added to database session

    Raises:
        ValueError: If shipment has no organization_id
    """
    if not shipment.organization_id:
        raise ValueError(
            f"Cannot create document: shipment {shipment.id} has no organization_id. "
            "This indicates a data integrity issue."
        )

    return Document(
        shipment_id=shipment.id,
        organization_id=shipment.organization_id,
        document_type=document_type,
        name=name,
        status=status,
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        document_date=document_date,
        expiry_date=expiry_date,
        issuer=issuer,
        reference_number=reference_number,
        uploaded_by=uploaded_by,
        validation_notes=validation_notes,
    )
