"""Shipment enrichment service.

Applies extracted document data to enrich shipment records:
- Updates port information from Bill of Lading
- Creates products from HS codes
- Updates vessel/voyage information
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Shipment, Product, Document
from ..models.document import DocumentType
from .shipment_data_extractor import ExtractedShipmentData, shipment_data_extractor

logger = logging.getLogger(__name__)


# Standard product descriptions by HS code
HS_CODE_DESCRIPTIONS = {
    "0506": "Bones, horn-cores, hooves, nails and claws",
    "0507": "Ivory, tortoise-shell, whalebone, horns and antlers",
    "2302": "Bran, sharps and other residues (pellets)",
    "1207": "Oil seeds and oleaginous fruits (sesame)",
    "0901": "Coffee",
    "0902": "Tea",
    "1801": "Cocoa beans",
    "4001": "Natural rubber",
    "4403": "Wood in the rough",
}


@dataclass
class EnrichmentResult:
    """Result of shipment enrichment operation."""
    success: bool
    shipment_id: str
    updates_applied: List[str] = field(default_factory=list)
    products_created: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    extracted_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "shipment_id": self.shipment_id,
            "updates_applied": self.updates_applied,
            "products_created": self.products_created,
            "warnings": self.warnings,
            "errors": self.errors,
            "extracted_data": self.extracted_data,
        }


class ShipmentEnrichmentService:
    """Service for enriching shipments with data extracted from documents."""

    def enrich_from_document(
        self,
        shipment: Shipment,
        document: Document,
        db: Session,
        auto_create_products: bool = True,
        overwrite_existing: bool = False
    ) -> EnrichmentResult:
        """Enrich a shipment with data extracted from a document.

        Args:
            shipment: The shipment to enrich
            document: The document to extract data from
            db: Database session
            auto_create_products: Whether to auto-create products from HS codes
            overwrite_existing: Whether to overwrite existing shipment fields

        Returns:
            EnrichmentResult with details of updates applied
        """
        result = EnrichmentResult(
            success=True,
            shipment_id=str(shipment.id)
        )

        # Extract data from document
        if not document.file_path:
            result.warnings.append("Document has no file path")
            return result

        try:
            extracted = shipment_data_extractor.extract_from_document(
                document.file_path,
                document.document_type
            )
        except Exception as e:
            result.errors.append(f"Extraction failed: {str(e)}")
            result.success = False
            return result

        # Store raw extracted data
        result.extracted_data = extracted.raw_fields

        # Apply updates based on document type
        if document.document_type == DocumentType.BILL_OF_LADING:
            self._apply_bill_of_lading_data(
                shipment, extracted, result, overwrite_existing
            )
        elif document.document_type in [
            DocumentType.COMMERCIAL_INVOICE,
            DocumentType.PACKING_LIST
        ]:
            self._apply_invoice_data(
                shipment, extracted, result, overwrite_existing, auto_create_products, db
            )
        else:
            # Generic extraction for any document
            self._apply_generic_data(
                shipment, extracted, result, overwrite_existing, auto_create_products, db
            )

        # Update shipment timestamp
        if result.updates_applied:
            shipment.updated_at = datetime.utcnow()

        return result

    def _apply_bill_of_lading_data(
        self,
        shipment: Shipment,
        extracted: ExtractedShipmentData,
        result: EnrichmentResult,
        overwrite: bool
    ):
        """Apply Bill of Lading extracted data to shipment."""

        # Update B/L number
        if extracted.bl_number:
            if not shipment.bl_number or overwrite:
                shipment.bl_number = extracted.bl_number
                result.updates_applied.append(f"bl_number: {extracted.bl_number}")
            elif shipment.bl_number != extracted.bl_number:
                result.warnings.append(
                    f"B/L number mismatch: shipment has '{shipment.bl_number}', "
                    f"document has '{extracted.bl_number}'"
                )

        # Update Port of Loading
        if extracted.port_of_loading_code:
            if not shipment.pol_code or overwrite:
                shipment.pol_code = extracted.port_of_loading_code
                result.updates_applied.append(f"pol_code: {extracted.port_of_loading_code}")
            if not shipment.pol_name or overwrite:
                shipment.pol_name = extracted.port_of_loading_name
                result.updates_applied.append(f"pol_name: {extracted.port_of_loading_name}")

        # Update Port of Discharge (CRITICAL for compliance routing)
        if extracted.port_of_discharge_code:
            if not shipment.pod_code or overwrite:
                shipment.pod_code = extracted.port_of_discharge_code
                result.updates_applied.append(f"pod_code: {extracted.port_of_discharge_code}")
            if not shipment.pod_name or overwrite:
                shipment.pod_name = extracted.port_of_discharge_name
                result.updates_applied.append(f"pod_name: {extracted.port_of_discharge_name}")
        elif extracted.port_of_discharge_name:
            # Name found but couldn't resolve to code
            if not shipment.pod_name or overwrite:
                shipment.pod_name = extracted.port_of_discharge_name
                result.updates_applied.append(f"pod_name: {extracted.port_of_discharge_name}")
            result.warnings.append(
                f"Could not resolve port '{extracted.port_of_discharge_name}' to UN/LOCODE"
            )

        # Note: final_destination field removed from Shipment model in Sprint 8
        # The POD (port of discharge) fields serve this purpose now

        # Update Vessel
        if extracted.vessel_name:
            if not shipment.vessel_name or overwrite:
                shipment.vessel_name = extracted.vessel_name
                result.updates_applied.append(f"vessel_name: {extracted.vessel_name}")

        # Update Voyage
        if extracted.voyage_number:
            if not shipment.voyage_number or overwrite:
                shipment.voyage_number = extracted.voyage_number
                result.updates_applied.append(f"voyage_number: {extracted.voyage_number}")

        # Update Container Number (verify or add)
        if extracted.container_number:
            if not shipment.container_number:
                shipment.container_number = extracted.container_number
                result.updates_applied.append(f"container_number: {extracted.container_number}")
            elif shipment.container_number != extracted.container_number:
                result.warnings.append(
                    f"Container mismatch: shipment has '{shipment.container_number}', "
                    f"document has '{extracted.container_number}'"
                )

    def _apply_invoice_data(
        self,
        shipment: Shipment,
        extracted: ExtractedShipmentData,
        result: EnrichmentResult,
        overwrite: bool,
        auto_create_products: bool,
        db: Session
    ):
        """Apply Commercial Invoice/Packing List data to shipment."""

        # Create products from HS codes
        if auto_create_products and extracted.hs_codes:
            self._create_products_from_hs_codes(
                shipment, extracted, result, db
            )

        # Also apply any port data found
        self._apply_generic_port_data(shipment, extracted, result, overwrite)

    def _apply_generic_data(
        self,
        shipment: Shipment,
        extracted: ExtractedShipmentData,
        result: EnrichmentResult,
        overwrite: bool,
        auto_create_products: bool,
        db: Session
    ):
        """Apply generic extracted data from any document type."""

        # Apply port data
        self._apply_generic_port_data(shipment, extracted, result, overwrite)

        # Create products if HS codes found
        if auto_create_products and extracted.hs_codes:
            self._create_products_from_hs_codes(
                shipment, extracted, result, db
            )

    def _apply_generic_port_data(
        self,
        shipment: Shipment,
        extracted: ExtractedShipmentData,
        result: EnrichmentResult,
        overwrite: bool
    ):
        """Apply port data from any document type."""

        # Update POD if found and shipment doesn't have it
        if extracted.port_of_discharge_code:
            if not shipment.pod_code or overwrite:
                shipment.pod_code = extracted.port_of_discharge_code
                result.updates_applied.append(f"pod_code: {extracted.port_of_discharge_code}")
            if not shipment.pod_name or overwrite:
                shipment.pod_name = extracted.port_of_discharge_name
                result.updates_applied.append(f"pod_name: {extracted.port_of_discharge_name}")

        # Update POL if found and shipment doesn't have it
        if extracted.port_of_loading_code:
            if not shipment.pol_code or overwrite:
                shipment.pol_code = extracted.port_of_loading_code
                result.updates_applied.append(f"pol_code: {extracted.port_of_loading_code}")

        # Container number
        if extracted.container_number and not shipment.container_number:
            shipment.container_number = extracted.container_number
            result.updates_applied.append(f"container_number: {extracted.container_number}")

    def _create_products_from_hs_codes(
        self,
        shipment: Shipment,
        extracted: ExtractedShipmentData,
        result: EnrichmentResult,
        db: Session
    ):
        """Create product records from extracted HS codes."""

        # Get existing HS codes for this shipment
        existing_codes = {p.hs_code for p in shipment.products}

        for hs_code in extracted.hs_codes:
            # Skip if product with this HS code already exists
            if hs_code in existing_codes:
                result.warnings.append(
                    f"Product with HS code {hs_code} already exists"
                )
                continue

            # Get description from our mapping or extracted products
            description = HS_CODE_DESCRIPTIONS.get(hs_code)

            if not description:
                # Check extracted product descriptions
                for prod in extracted.product_descriptions:
                    if prod.get("hs_code") == hs_code:
                        description = prod.get("name")
                        break

            if not description:
                description = f"Product (HS {hs_code})"

            # Create product (must include organization_id for multi-tenancy)
            product = Product(
                shipment_id=shipment.id,
                organization_id=shipment.organization_id,
                hs_code=hs_code,
                description=description,
                quantity_net_kg=extracted.total_net_weight_kg,
                quantity_gross_kg=extracted.total_gross_weight_kg,
            )

            db.add(product)
            result.products_created.append({
                "hs_code": hs_code,
                "description": description
            })

            logger.info(
                f"Created product {hs_code} for shipment {shipment.reference}"
            )

    def enrich_from_text(
        self,
        shipment: Shipment,
        text: str,
        document_type: Optional[DocumentType],
        db: Session,
        auto_create_products: bool = True,
        overwrite_existing: bool = False
    ) -> EnrichmentResult:
        """Enrich a shipment from raw text content.

        Useful for manual text input or non-PDF documents.

        Args:
            shipment: The shipment to enrich
            text: Text content to extract data from
            document_type: Type of document the text is from
            db: Database session
            auto_create_products: Whether to auto-create products
            overwrite_existing: Whether to overwrite existing fields

        Returns:
            EnrichmentResult with details of updates applied
        """
        result = EnrichmentResult(
            success=True,
            shipment_id=str(shipment.id)
        )

        # Extract data from text
        extracted = shipment_data_extractor.extract_from_text(text, document_type)
        result.extracted_data = extracted.raw_fields

        # Apply based on document type
        if document_type == DocumentType.BILL_OF_LADING:
            self._apply_bill_of_lading_data(
                shipment, extracted, result, overwrite_existing
            )
        elif document_type in [DocumentType.COMMERCIAL_INVOICE, DocumentType.PACKING_LIST]:
            self._apply_invoice_data(
                shipment, extracted, result, overwrite_existing,
                auto_create_products, db
            )
        else:
            self._apply_generic_data(
                shipment, extracted, result, overwrite_existing,
                auto_create_products, db
            )

        if result.updates_applied:
            shipment.updated_at = datetime.utcnow()

        return result


# Global instance
shipment_enrichment_service = ShipmentEnrichmentService()
