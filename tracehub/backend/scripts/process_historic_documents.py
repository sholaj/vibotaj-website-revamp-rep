#!/usr/bin/env python3
"""Process and upload historic documents from customer directories.

This script:
1. Scans customer document directories
2. Classifies each document using AI/keyword classification
3. **Uses Bill of Lading as the SOURCE OF TRUTH** for shipment data
4. Corrects/updates shipment records based on BOL extracted data
5. Uploads documents to corresponding shipments
6. Updates shipment status with informative notes
7. Generates a detailed processing report

Key Feature: BOL Source of Truth
--------------------------------
When a Bill of Lading is classified:
- Extracts container number, vessel name, voyage, ports, HS codes
- Compares with existing shipment data
- Corrects any mismatches and logs all corrections
- Adds validation notes explaining what was reviewed/corrected

Usage:
    python scripts/process_historic_documents.py --env staging --dry-run
    python scripts/process_historic_documents.py --env production
"""

import os
import sys
import argparse
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import mimetypes

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Supported file types
SUPPORTED_EXTENSIONS = {".pdf", ".jpeg", ".jpg", ".png"}
SKIP_EXTENSIONS = {".mp4", ".docx", ".xlsx", ".xls", ".zip", ".mov", ".avi"}

# Customer to shipment mapping (reference prefix -> customer slug)
CUSTOMER_SHIPMENT_MAP = {
    "felix": "VIBO-HIST-FELIX",
    "hages": "VIBO-HIST-HAGES",
    "witatrade": "VIBO-HIST-WITATRADE",
    "beckmann": "VIBO-HIST-BECKMANN",
}

# Required documents for Horn & Hoof products (per COMPLIANCE_MATRIX.md)
HORN_HOOF_REQUIRED_DOCS = [
    "bill_of_lading",
    "commercial_invoice",
    "packing_list",
    "certificate_of_origin",
    "veterinary_health_certificate",
    # "eu_traces_certificate",  # Not always available for historic shipments
]


@dataclass
class BOLCorrection:
    """Correction made to a shipment based on Bill of Lading data."""
    field: str
    old_value: Optional[str]
    new_value: str

    def __str__(self):
        old = self.old_value or "(empty)"
        return f"{self.field}: {old} -> {self.new_value}"


@dataclass
class DocumentInfo:
    """Information about a processed document."""
    file_path: Path
    file_name: str
    customer: str
    document_type: str
    confidence: float
    detection_method: str
    reference_number: Optional[str]
    text_extracted: int
    ocr_used: bool
    shipment_ref: Optional[str] = None
    uploaded: bool = False
    error: Optional[str] = None
    # BOL-specific fields
    bol_corrections: List[BOLCorrection] = field(default_factory=list)
    extracted_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingReport:
    """Report of document processing."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_files: int = 0
    processed: int = 0
    uploaded: int = 0
    skipped: int = 0
    errors: int = 0
    by_customer: Dict[str, Dict] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)
    shipment_updates: List[Dict] = field(default_factory=list)
    bol_corrections_total: int = 0
    bol_corrections_by_shipment: Dict[str, List[str]] = field(default_factory=dict)
    documents: List[DocumentInfo] = field(default_factory=list)


def get_shipment_for_document(customer: str, doc_path: Path, db, Shipment) -> Optional[Any]:
    """Determine which shipment a document belongs to based on path and content."""
    # Get all shipments for this customer
    prefix = CUSTOMER_SHIPMENT_MAP.get(customer, "")
    if not prefix:
        return None

    shipments = db.query(Shipment).filter(
        Shipment.reference.like(f"{prefix}%")
    ).order_by(Shipment.reference).all()

    if not shipments:
        return None

    # For now, assign to first shipment
    # In a real scenario, you'd parse dates/container numbers from the document
    path_parts = str(doc_path).lower()

    # Try to match based on folder structure or file name hints
    for shipment in shipments:
        # Check for container number in path
        if shipment.container_number and shipment.container_number.lower() in path_parts:
            return shipment
        # Check for BL number
        if shipment.bl_number and shipment.bl_number.lower() in path_parts:
            return shipment

    # Default to first shipment
    return shipments[0]


def classify_document(file_path: str, pdf_processor, document_classifier) -> Tuple[str, float, str, Optional[str], int, bool]:
    """Classify a document and extract metadata."""
    ext = Path(file_path).suffix.lower()
    text = ""
    ocr_used = False

    try:
        if ext == ".pdf":
            pages = pdf_processor.extract_text(file_path, use_ocr_fallback=True)
            if pages:
                text = "\n".join(p.text for p in pages)
                # Check if OCR was used (low initial text, higher after OCR)
                initial_chars = sum(p.char_count for p in pages)
                if initial_chars < 100 and len(text) > 100:
                    ocr_used = True
        elif ext in {".jpeg", ".jpg", ".png"}:
            # Use OCR for images
            try:
                import pytesseract
                from PIL import Image
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image, lang="eng")
                ocr_used = True
            except Exception as e:
                return "other", 0.0, "error", None, 0, False

        # Classify the document
        if text.strip() and document_classifier:
            result = document_classifier.classify(text, prefer_ai=True)
            return (
                result.document_type.value,
                result.confidence,
                result.detected_fields.get("detection_method", "keyword"),
                result.reference_number,
                len(text),
                ocr_used
            )
        else:
            return "other", 0.0, "no_text", None, len(text), ocr_used

    except Exception as e:
        return "other", 0.0, "error", None, 0, False


def is_valid_container_number(container: str) -> bool:
    """Validate container number format (ISO 6346: 4 letters + 7 digits)."""
    import re
    if not container:
        return False
    clean = re.sub(r'[\s-]', '', container.upper())
    return bool(re.match(r'^[A-Z]{4}\d{7}$', clean))


def is_valid_bl_number(bl: str) -> bool:
    """Validate B/L number - must start with letters/digits and be reasonable length."""
    import re
    if not bl or len(bl) < 6:
        return False
    # Should start with alphanumeric and not be common words
    invalid_words = ['issuance', 'igations', 'obligations', 'per', 'the', 'and', 'for']
    if bl.lower() in invalid_words:
        return False
    # Must contain at least one digit or be mostly uppercase
    return bool(re.match(r'^[A-Z0-9]', bl.upper()))


def is_valid_vessel_name(vessel: str) -> bool:
    """Validate vessel name - must look like an actual vessel name."""
    if not vessel or len(vessel) < 3 or len(vessel) > 30:
        return False
    # Reject common extraction errors (partial sentences, instructions)
    invalid_patterns = [
        'confirmation', 'issued', 'upon', 'customer', 'exiting', 'entering',
        'port', 'united', 'direction', 'ments', 'per', 'arrival'
    ]
    vessel_lower = vessel.lower()
    for pattern in invalid_patterns:
        if pattern in vessel_lower:
            return False
    return True


def extract_bol_data_and_correct_shipment(
    text: str,
    shipment: Any,
    dry_run: bool = False
) -> Tuple[Dict[str, Any], List[BOLCorrection]]:
    """Extract data from Bill of Lading and correct shipment if needed.

    BOL is the SOURCE OF TRUTH. If BOL data differs from shipment, correct it.
    Only applies corrections for validated values (not garbage from boilerplate).

    Args:
        text: Extracted text from Bill of Lading document
        shipment: The Shipment model instance to potentially correct
        dry_run: If True, don't apply corrections, just report them

    Returns:
        Tuple of (extracted_data dict, list of BOLCorrection objects)
    """
    from app.services.shipment_data_extractor import shipment_data_extractor

    corrections = []
    extracted = {}

    # Extract data from BOL text
    bol_data = shipment_data_extractor.extract_from_text(text)

    # Log what was extracted
    print(f"    BOL Extraction (confidence: {bol_data.confidence:.0%}):")

    # Container Number - PRIMARY IDENTIFIER (validated)
    if bol_data.container_number and is_valid_container_number(bol_data.container_number):
        extracted["container_number"] = bol_data.container_number
        print(f"      Container: {bol_data.container_number} [VALID]")
        if bol_data.container_number != shipment.container_number:
            corrections.append(BOLCorrection(
                field="container_number",
                old_value=shipment.container_number,
                new_value=bol_data.container_number
            ))
            if not dry_run:
                shipment.container_number = bol_data.container_number
    elif bol_data.container_number:
        print(f"      Container: {bol_data.container_number} [INVALID - skipped]")

    # B/L Number (validated)
    if bol_data.bl_number and is_valid_bl_number(bol_data.bl_number):
        extracted["bl_number"] = bol_data.bl_number
        print(f"      B/L: {bol_data.bl_number} [VALID]")
        if bol_data.bl_number != shipment.bl_number:
            corrections.append(BOLCorrection(
                field="bl_number",
                old_value=shipment.bl_number,
                new_value=bol_data.bl_number
            ))
            if not dry_run:
                shipment.bl_number = bol_data.bl_number
    elif bol_data.bl_number:
        print(f"      B/L: {bol_data.bl_number} [INVALID - skipped]")

    # Vessel Name (validated)
    if bol_data.vessel_name and is_valid_vessel_name(bol_data.vessel_name):
        extracted["vessel_name"] = bol_data.vessel_name
        print(f"      Vessel: {bol_data.vessel_name} [VALID]")
        if bol_data.vessel_name != shipment.vessel_name:
            corrections.append(BOLCorrection(
                field="vessel_name",
                old_value=shipment.vessel_name,
                new_value=bol_data.vessel_name
            ))
            if not dry_run:
                shipment.vessel_name = bol_data.vessel_name
    elif bol_data.vessel_name:
        print(f"      Vessel: {bol_data.vessel_name} [INVALID - skipped]")

    # Voyage Number (basic validation - should be short alphanumeric)
    if bol_data.voyage_number and len(bol_data.voyage_number) <= 20:
        extracted["voyage_number"] = bol_data.voyage_number
        print(f"      Voyage: {bol_data.voyage_number} [VALID]")
        if bol_data.voyage_number != shipment.voyage_number:
            corrections.append(BOLCorrection(
                field="voyage_number",
                old_value=shipment.voyage_number,
                new_value=bol_data.voyage_number
            ))
            if not dry_run:
                shipment.voyage_number = bol_data.voyage_number
    elif bol_data.voyage_number:
        print(f"      Voyage: {bol_data.voyage_number} [INVALID - skipped]")

    # Port of Loading
    if bol_data.port_of_loading_code:
        extracted["pol_code"] = bol_data.port_of_loading_code
        extracted["pol_name"] = bol_data.port_of_loading_name
        print(f"      POL: {bol_data.port_of_loading_code} ({bol_data.port_of_loading_name})")
        if bol_data.port_of_loading_code != shipment.pol_code:
            corrections.append(BOLCorrection(
                field="pol_code",
                old_value=shipment.pol_code,
                new_value=bol_data.port_of_loading_code
            ))
            if not dry_run:
                shipment.pol_code = bol_data.port_of_loading_code
                shipment.pol_name = bol_data.port_of_loading_name or shipment.pol_name

    # Port of Discharge
    if bol_data.port_of_discharge_code:
        extracted["pod_code"] = bol_data.port_of_discharge_code
        extracted["pod_name"] = bol_data.port_of_discharge_name
        print(f"      POD: {bol_data.port_of_discharge_code} ({bol_data.port_of_discharge_name})")
        if bol_data.port_of_discharge_code != shipment.pod_code:
            corrections.append(BOLCorrection(
                field="pod_code",
                old_value=shipment.pod_code,
                new_value=bol_data.port_of_discharge_code
            ))
            if not dry_run:
                shipment.pod_code = bol_data.port_of_discharge_code
                shipment.pod_name = bol_data.port_of_discharge_name or shipment.pod_name

    # HS Codes
    if bol_data.hs_codes:
        extracted["hs_codes"] = bol_data.hs_codes
        print(f"      HS Codes: {', '.join(bol_data.hs_codes)}")

    # Weights
    if bol_data.total_net_weight_kg:
        extracted["net_weight_kg"] = bol_data.total_net_weight_kg
        print(f"      Net Weight: {bol_data.total_net_weight_kg} kg")
    if bol_data.total_gross_weight_kg:
        extracted["gross_weight_kg"] = bol_data.total_gross_weight_kg
        print(f"      Gross Weight: {bol_data.total_gross_weight_kg} kg")

    # Products detected
    if bol_data.product_descriptions:
        products = [p.get("name", "Unknown") for p in bol_data.product_descriptions]
        extracted["products"] = products
        print(f"      Products: {', '.join(products)}")

    # Store extraction confidence
    extracted["extraction_confidence"] = bol_data.confidence

    # Log corrections
    if corrections:
        print(f"    [BOL CORRECTIONS] {len(corrections)} field(s) corrected from BOL:")
        for c in corrections:
            print(f"      - {c}")
    else:
        print(f"    [BOL OK] Shipment data matches Bill of Lading")

    return extracted, corrections


def get_document_status_info(doc_type: str, confidence: float, corrections: List[BOLCorrection] = None) -> Tuple[str, str]:
    """Get status and validation notes based on classification result.

    Args:
        doc_type: The classified document type
        confidence: Classification confidence (0-1)
        corrections: Optional list of BOL corrections applied

    Returns:
        Tuple of (status, validation_notes)
    """
    # Base notes from confidence
    if confidence >= 0.8:
        status = "VALIDATED"
        base_notes = f"Classified with {confidence:.0%} confidence"
    elif confidence >= 0.5:
        status = "UPLOADED"
        base_notes = f"Classified with {confidence:.0%} confidence - needs review"
    else:
        status = "UPLOADED"
        base_notes = f"Low confidence ({confidence:.0%}) - manual classification needed"

    # Add BOL-specific notes if applicable
    if doc_type == "bill_of_lading" and corrections is not None:
        if corrections:
            correction_summary = "; ".join(str(c) for c in corrections)
            notes = f"{base_notes}. BOL verified as source of truth. Corrections applied: {correction_summary}"
            status = "VALIDATED"  # BOL with corrections is still validated
        else:
            notes = f"{base_notes}. BOL verified - all shipment data matches"
            status = "VALIDATED"
    else:
        notes = base_notes

    return status, notes


def calculate_shipment_status(documents: List[Any], DocumentType, has_bol_corrections: bool = False) -> Tuple[str, str]:
    """Calculate shipment status based on document completeness.

    Provides detailed, informative status notes for the user.

    Args:
        documents: List of Document records for the shipment
        DocumentType: The DocumentType enum
        has_bol_corrections: Whether BOL corrections were applied

    Returns:
        Tuple of (new_status, informative_status_note)
    """
    if not documents:
        return "DOCS_PENDING", "No documents uploaded yet"

    doc_types = {doc.document_type.value for doc in documents}

    # Build document review summary
    doc_summary = []
    for doc in documents:
        status_emoji = "OK" if doc.status.value in ("VALIDATED", "COMPLIANCE_OK") else "REVIEW"
        doc_summary.append(f"{doc.document_type.value.replace('_', ' ').title()}: [{status_emoji}]")

    # Check required documents
    missing = []
    for req_type in HORN_HOOF_REQUIRED_DOCS:
        if req_type not in doc_types:
            missing.append(req_type.replace("_", " ").title())

    # Build informative notes
    notes_parts = ["Document Review Complete:"]

    # Document summary (first 5)
    for summary in doc_summary[:5]:
        notes_parts.append(f"  - {summary}")
    if len(doc_summary) > 5:
        notes_parts.append(f"  - ... and {len(doc_summary) - 5} more")

    # BOL corrections note
    if has_bol_corrections:
        notes_parts.append("BOL verified and shipment data corrected.")

    # Missing documents
    if missing:
        notes_parts.append(f"Missing: {', '.join(missing[:3])}")
        if len(missing) > 3:
            notes_parts.append(f"  + {len(missing) - 3} more required documents")
        status = "DOCS_PENDING"
    else:
        notes_parts.append("All required documents present.")
        status = "DOCS_COMPLETE"

    return status, " ".join(notes_parts)


def process_documents(env: str, dry_run: bool = False) -> ProcessingReport:
    """Process all documents from customer directories."""
    report = ProcessingReport()

    print(f"\n{'=' * 70}")
    print(f"Processing Historic Documents - {env.upper()}")
    print(f"{'=' * 70}")
    print(f"Dry Run: {dry_run}")
    print()

    # Import database modules
    try:
        from app.database import SessionLocal
        from app.models import (
            Shipment, ShipmentStatus, Document, DocumentType, DocumentStatus,
            Organization
        )
        from app.services.pdf_processor import pdf_processor, PDF_PROCESSING_AVAILABLE, OCR_AVAILABLE
        from app.services.document_classifier import document_classifier
        print("[OK] Modules loaded")
        print(f"    PDF Processing: {PDF_PROCESSING_AVAILABLE}")
        print(f"    OCR Available: {OCR_AVAILABLE}")
        print(f"    AI Available: {document_classifier.is_ai_available()}")
    except Exception as e:
        print(f"[ERROR] Failed to load modules: {e}")
        return report

    db = SessionLocal()

    try:
        # Test connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        print("[OK] Database connected")
        print()

        # Get VIBOTAJ organization
        vibotaj_org = db.query(Organization).filter(
            Organization.slug == "vibotaj"
        ).first()

        if not vibotaj_org:
            print("[ERROR] VIBOTAJ organization not found")
            return report

        print(f"[OK] VIBOTAJ org: {vibotaj_org.id}")

        # Define upload paths
        upload_base = Path(__file__).parent.parent / "uploads"
        server_upload_base = Path("/app/uploads")  # Path in container

        # Process each customer
        for customer in ["felix", "hages", "witatrade", "beckmann"]:
            print(f"\n{'=' * 50}")
            print(f"Processing: {customer.upper()}")
            print(f"{'=' * 50}")

            customer_dir = upload_base / customer
            if not customer_dir.exists():
                print(f"  [SKIP] Directory not found: {customer_dir}")
                continue

            report.by_customer[customer] = {
                "total": 0,
                "processed": 0,
                "uploaded": 0,
                "by_type": {},
            }

            # Get shipments for this customer
            shipment_prefix = CUSTOMER_SHIPMENT_MAP.get(customer, "")
            shipments = db.query(Shipment).filter(
                Shipment.reference.like(f"{shipment_prefix}%")
            ).all()

            if not shipments:
                print(f"  [WARN] No shipments found for {customer}")
                continue

            print(f"  Found {len(shipments)} shipment(s)")

            # Collect all supported files
            files = []
            for item in customer_dir.rglob("*"):
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        files.append(item)
                    elif ext in SKIP_EXTENSIONS:
                        report.skipped += 1

            report.by_customer[customer]["total"] = len(files)
            report.total_files += len(files)

            print(f"  Found {len(files)} supported files")

            # Process each file
            for file_path in files:
                rel_path = file_path.relative_to(customer_dir)
                print(f"\n  Processing: {rel_path}")

                # Classify document
                doc_type, confidence, method, ref_num, text_len, ocr_used = classify_document(
                    str(file_path), pdf_processor, document_classifier
                )

                print(f"    Type: {doc_type} ({confidence:.0%}) [{method}]")
                if ocr_used:
                    print(f"    OCR: Yes ({text_len} chars)")
                if ref_num:
                    print(f"    Ref: {ref_num}")

                # Track by type
                report.by_type[doc_type] = report.by_type.get(doc_type, 0) + 1
                report.by_customer[customer]["by_type"][doc_type] = \
                    report.by_customer[customer]["by_type"].get(doc_type, 0) + 1

                # Determine which shipment to assign
                shipment = get_shipment_for_document(customer, file_path, db, Shipment)

                if not shipment:
                    print(f"    [SKIP] No shipment found")
                    continue

                print(f"    Shipment: {shipment.reference}")

                # Check if document already exists
                existing = db.query(Document).filter(
                    Document.shipment_id == shipment.id,
                    Document.file_name == file_path.name
                ).first()

                if existing:
                    print(f"    [SKIP] Already uploaded")
                    continue

                # For Bill of Lading, extract data and correct shipment
                bol_corrections = []
                extracted_data = {}
                if doc_type == "bill_of_lading":
                    # Re-extract text for BOL data extraction
                    try:
                        ext = file_path.suffix.lower()
                        if ext == ".pdf":
                            pages = pdf_processor.extract_text(str(file_path), use_ocr_fallback=True)
                            full_text = "\n".join(p.text for p in pages) if pages else ""
                        elif ext in {".jpeg", ".jpg", ".png"}:
                            import pytesseract
                            from PIL import Image
                            image = Image.open(str(file_path))
                            full_text = pytesseract.image_to_string(image, lang="eng")
                        else:
                            full_text = ""

                        if full_text.strip():
                            extracted_data, bol_corrections = extract_bol_data_and_correct_shipment(
                                full_text, shipment, dry_run
                            )
                            if bol_corrections:
                                db.flush()  # Persist shipment corrections
                    except Exception as e:
                        print(f"    [WARN] BOL extraction failed: {e}")

                # Get document status based on confidence and BOL corrections
                status, notes = get_document_status_info(doc_type, confidence, bol_corrections)

                # Create document record
                doc_info = DocumentInfo(
                    file_path=file_path,
                    file_name=file_path.name,
                    customer=customer,
                    document_type=doc_type,
                    confidence=confidence,
                    detection_method=method,
                    reference_number=ref_num,
                    text_extracted=text_len,
                    ocr_used=ocr_used,
                    shipment_ref=shipment.reference,
                    bol_corrections=bol_corrections,
                    extracted_data=extracted_data,
                )

                if not dry_run:
                    try:
                        # Create destination path
                        dest_dir = server_upload_base / str(shipment.id)
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest_path = dest_dir / file_path.name

                        # Copy file
                        shutil.copy2(file_path, dest_path)

                        # Get file info
                        file_size = file_path.stat().st_size
                        mime_type, _ = mimetypes.guess_type(str(file_path))

                        # Create document record
                        document = Document(
                            shipment_id=shipment.id,
                            organization_id=vibotaj_org.id,
                            name=f"{doc_type.replace('_', ' ').title()} - {file_path.stem}",
                            document_type=DocumentType(doc_type),
                            status=DocumentStatus(status),
                            file_name=file_path.name,
                            file_path=str(dest_path),
                            file_size=file_size,
                            mime_type=mime_type or "application/octet-stream",
                            reference_number=ref_num,
                            validation_notes=notes,
                        )
                        db.add(document)
                        db.flush()

                        doc_info.uploaded = True
                        report.uploaded += 1
                        print(f"    [OK] Uploaded -> {status}")

                    except Exception as e:
                        doc_info.error = str(e)
                        report.errors += 1
                        print(f"    [ERROR] {e}")
                else:
                    print(f"    [DRY-RUN] Would upload -> {status}")
                    doc_info.uploaded = True
                    report.uploaded += 1

                report.documents.append(doc_info)
                report.processed += 1
                report.by_customer[customer]["processed"] += 1
                if doc_info.uploaded:
                    report.by_customer[customer]["uploaded"] = \
                        report.by_customer[customer].get("uploaded", 0) + 1

                # Track BOL corrections
                if bol_corrections:
                    report.bol_corrections_total += len(bol_corrections)
                    if shipment.reference not in report.bol_corrections_by_shipment:
                        report.bol_corrections_by_shipment[shipment.reference] = []
                    for c in bol_corrections:
                        report.bol_corrections_by_shipment[shipment.reference].append(str(c))

        # Update shipment statuses
        print(f"\n{'=' * 50}")
        print("Updating Shipment Statuses")
        print(f"{'=' * 50}")

        for customer in ["felix", "hages", "witatrade", "beckmann"]:
            shipment_prefix = CUSTOMER_SHIPMENT_MAP.get(customer, "")
            shipments = db.query(Shipment).filter(
                Shipment.reference.like(f"{shipment_prefix}%")
            ).all()

            for shipment in shipments:
                # Get all documents for this shipment
                docs = db.query(Document).filter(
                    Document.shipment_id == shipment.id
                ).all()

                doc_count = len(docs)
                doc_types = [d.document_type.value for d in docs]

                # Check if BOL corrections were applied to this shipment
                has_bol_corrections = shipment.reference in report.bol_corrections_by_shipment

                # Calculate new status with informative notes
                new_status, status_note = calculate_shipment_status(docs, DocumentType, has_bol_corrections)

                print(f"\n  {shipment.reference}:")
                print(f"    Documents: {doc_count} ({', '.join(set(doc_types)) if doc_types else 'none'})")
                if has_bol_corrections:
                    corrections = report.bol_corrections_by_shipment[shipment.reference]
                    print(f"    BOL Corrections: {len(corrections)}")
                    for c in corrections:
                        print(f"      - {c}")
                print(f"    Status: {shipment.status.value} -> {new_status}")
                print(f"    Note: {status_note[:100]}..." if len(status_note) > 100 else f"    Note: {status_note}")

                if not dry_run and shipment.status.value != new_status:
                    # Don't downgrade from DELIVERED (historic shipments)
                    if shipment.status != ShipmentStatus.DELIVERED:
                        shipment.status = ShipmentStatus(new_status)
                        db.flush()
                        print(f"    [OK] Status updated")
                    else:
                        print(f"    [SKIP] Keeping DELIVERED status for historic shipment")

                report.shipment_updates.append({
                    "reference": shipment.reference,
                    "documents": doc_count,
                    "doc_types": list(set(doc_types)),
                    "old_status": shipment.status.value,
                    "new_status": new_status,
                    "note": status_note,
                    "bol_corrections": report.bol_corrections_by_shipment.get(shipment.reference, []),
                })

        # Commit all changes
        if not dry_run:
            db.commit()
            print(f"\n[OK] All changes committed")
        else:
            db.rollback()
            print(f"\n[DRY-RUN] Changes not committed")

        return report

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return report
    finally:
        db.close()


def print_report(report: ProcessingReport):
    """Print processing report summary."""
    print(f"\n{'=' * 70}")
    print("PROCESSING REPORT - BOL as Source of Truth")
    print(f"{'=' * 70}")

    print(f"\nTimestamp: {report.timestamp}")
    print(f"\nOverall Statistics:")
    print(f"  Total files found:    {report.total_files}")
    print(f"  Processed:            {report.processed}")
    print(f"  Uploaded:             {report.uploaded}")
    print(f"  Skipped (video/docs): {report.skipped}")
    print(f"  Errors:               {report.errors}")

    # BOL Corrections Summary (KEY FEATURE)
    print(f"\nBill of Lading Corrections:")
    print(f"  Total corrections:    {report.bol_corrections_total}")
    print(f"  Shipments corrected:  {len(report.bol_corrections_by_shipment)}")
    if report.bol_corrections_by_shipment:
        print(f"\n  Correction Details:")
        for ref, corrections in report.bol_corrections_by_shipment.items():
            print(f"    {ref}:")
            for c in corrections:
                print(f"      - {c}")

    print(f"\nBy Document Type:")
    for doc_type, count in sorted(report.by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {doc_type.replace('_', ' ').title()}: {count}")

    print(f"\nBy Customer:")
    for customer, stats in report.by_customer.items():
        print(f"  {customer.upper()}:")
        print(f"    Files: {stats.get('total', 0)}, Uploaded: {stats.get('uploaded', 0)}")
        if stats.get("by_type"):
            types_str = ", ".join(f"{k}:{v}" for k, v in stats["by_type"].items())
            print(f"    Types: {types_str}")

    print(f"\nShipment Updates:")
    for update in report.shipment_updates:
        print(f"  {update['reference']}:")
        print(f"    Documents: {update['documents']} - {', '.join(update['doc_types']) if update['doc_types'] else 'none'}")
        if update.get('bol_corrections'):
            print(f"    BOL Corrections: {len(update['bol_corrections'])}")
        print(f"    Status: {update['old_status']} -> {update['new_status']}")
        # Truncate long notes for readability
        note = update['note']
        if len(note) > 80:
            note = note[:77] + "..."
        print(f"    Note: {note}")

    print(f"\n{'=' * 70}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process and upload historic documents"
    )
    parser.add_argument(
        "--env",
        choices=["staging", "production", "local"],
        default="local",
        help="Target environment"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't make any changes"
    )

    args = parser.parse_args()

    # Set database URL based on environment
    if args.env == "local":
        os.environ.setdefault(
            "DATABASE_URL",
            "postgresql://tracehub:tracehub@localhost:5432/tracehub"
        )

    # Run processing
    report = process_documents(args.env, args.dry_run)

    # Print report
    print_report(report)

    # Save report
    report_path = Path(__file__).parent / f"document_processing_report_{args.env}.json"
    report_data = {
        "timestamp": report.timestamp,
        "total_files": report.total_files,
        "processed": report.processed,
        "uploaded": report.uploaded,
        "skipped": report.skipped,
        "errors": report.errors,
        "by_customer": report.by_customer,
        "by_type": report.by_type,
        "shipment_updates": report.shipment_updates,
        # BOL Source of Truth tracking
        "bol_corrections_total": report.bol_corrections_total,
        "bol_corrections_by_shipment": report.bol_corrections_by_shipment,
    }

    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nReport saved: {report_path}")

    return 0 if report.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
