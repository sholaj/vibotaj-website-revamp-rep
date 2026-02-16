"""BoL auto-parse pipeline (PRD-018).

Orchestrates: parse → compliance check → auto-sync for Bill of Lading
documents. Triggered automatically on upload when document_type is
bill_of_lading.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import Document, Shipment, ComplianceResult, Product
from ..models.document import DocumentType, DocumentStatus
from ..schemas.bol import CanonicalBoL
from ..schemas.bol_parse_result import (
    BolFieldResult,
    BolComplianceResult,
    BolParsedResponse,
    SyncChange,
    BolSyncPreviewResponse,
)
from .bol_parser import bol_parser
from .bol_shipment_sync import (
    get_sync_changes,
    apply_sync_changes,
    is_placeholder_container,
)
from .bol_rules import RulesEngine, STANDARD_BOL_RULES, get_compliance_decision
from .file_utils import get_full_path

logger = logging.getLogger(__name__)

# Confidence threshold for auto-sync
AUTO_SYNC_CONFIDENCE_THRESHOLD = 0.70


def auto_parse_bol(
    document: Document,
    db: Session,
    auto_sync: bool = True,
) -> BolParsedResponse:
    """Auto-parse a Bill of Lading document.

    Called automatically when a BoL is uploaded. Orchestrates:
    1. Extract text from PDF
    2. Parse BoL using regex parser
    3. Run compliance rules
    4. Auto-sync to shipment if confidence > threshold

    Args:
        document: The BoL document to parse
        db: Database session
        auto_sync: Whether to auto-sync if confidence meets threshold

    Returns:
        BolParsedResponse with parse results
    """
    doc_id = str(document.id)

    # Verify it's a BoL
    if document.document_type != DocumentType.BILL_OF_LADING:
        return BolParsedResponse(
            document_id=doc_id,
            parse_status="not_bol",
        )

    # Get PDF text
    text = _extract_text_from_document(document)
    if not text:
        logger.warning("No text extracted from BoL document %s", doc_id)
        return BolParsedResponse(
            document_id=doc_id,
            parse_status="failed",
        )

    # Parse
    try:
        parsed_bol = bol_parser.parse(text)
    except Exception:
        logger.exception("BoL parse failed for document %s", doc_id)
        return BolParsedResponse(
            document_id=doc_id,
            parse_status="failed",
        )

    # Store parsed data on document
    document.bol_parsed_data = parsed_bol.model_dump(mode="json")
    document.updated_at = datetime.utcnow()

    # Update document metadata
    if parsed_bol.bol_number and parsed_bol.bol_number != "UNKNOWN":
        document.reference_number = parsed_bol.bol_number
    if parsed_bol.date_of_issue:
        document.issue_date = parsed_bol.date_of_issue
    if parsed_bol.vessel_name:
        document.issuing_authority = parsed_bol.vessel_name

    # Run compliance
    compliance_result = _run_compliance(document, parsed_bol, db)

    # Build field-level confidence
    fields = _build_field_confidence(parsed_bol)

    # Auto-sync if confidence meets threshold
    auto_synced = False
    if auto_sync and parsed_bol.confidence_score >= AUTO_SYNC_CONFIDENCE_THRESHOLD:
        shipment = db.query(Shipment).filter(
            Shipment.id == document.shipment_id,
            Shipment.organization_id == document.organization_id,
        ).first()
        if shipment and compliance_result and compliance_result.decision != "REJECT":
            changes = apply_sync_changes(shipment, parsed_bol)
            if changes:
                auto_synced = True
                logger.info(
                    "Auto-synced BoL to shipment %s (confidence=%.2f): %s",
                    shipment.reference,
                    parsed_bol.confidence_score,
                    changes,
                )

    db.commit()

    return BolParsedResponse(
        document_id=doc_id,
        parse_status="parsed",
        parsed_at=datetime.utcnow().isoformat(),
        confidence_score=parsed_bol.confidence_score,
        fields=fields,
        compliance=compliance_result,
        auto_synced=auto_synced,
    )


def get_parsed_bol_data(document: Document, db: Session) -> BolParsedResponse:
    """Get parsed BoL data for a document.

    Args:
        document: The document to get parsed data for
        db: Database session

    Returns:
        BolParsedResponse with current parse state
    """
    doc_id = str(document.id)

    if document.document_type != DocumentType.BILL_OF_LADING:
        return BolParsedResponse(
            document_id=doc_id,
            parse_status="not_bol",
        )

    if not document.bol_parsed_data:
        return BolParsedResponse(
            document_id=doc_id,
            parse_status="pending",
        )

    try:
        parsed_bol = CanonicalBoL.model_validate(document.bol_parsed_data)
    except Exception:
        return BolParsedResponse(
            document_id=doc_id,
            parse_status="failed",
        )

    fields = _build_field_confidence(parsed_bol)

    # Get compliance status
    compliance = None
    if document.compliance_status:
        results = db.query(ComplianceResult).filter(
            ComplianceResult.document_id == document.id,
            ComplianceResult.organization_id == document.organization_id,
        ).all()
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        compliance = BolComplianceResult(
            decision=document.compliance_status,
            rules_passed=passed,
            rules_failed=failed,
            rules_total=len(results),
        )

    return BolParsedResponse(
        document_id=doc_id,
        parse_status="parsed",
        parsed_at=document.updated_at.isoformat() if document.updated_at else None,
        confidence_score=parsed_bol.confidence_score,
        fields=fields,
        compliance=compliance,
    )


def get_enhanced_sync_preview(
    document: Document, db: Session
) -> BolSyncPreviewResponse:
    """Enhanced sync preview with field-level change details.

    Args:
        document: The BoL document
        db: Database session

    Returns:
        BolSyncPreviewResponse with detailed changes
    """
    doc_id = str(document.id)

    if not document.bol_parsed_data:
        return BolSyncPreviewResponse(
            document_id=doc_id,
            shipment_id="",
            shipment_reference="",
            changes=[],
        )

    parsed_bol = CanonicalBoL.model_validate(document.bol_parsed_data)

    shipment = db.query(Shipment).filter(
        Shipment.id == document.shipment_id,
        Shipment.organization_id == document.organization_id,
    ).first()
    if not shipment:
        return BolSyncPreviewResponse(
            document_id=doc_id,
            shipment_id="",
            shipment_reference="",
            changes=[],
        )

    # Build change list with placeholder detection
    changes: List[SyncChange] = []
    field_map = [
        ("bl_number", shipment.bl_number, parsed_bol.bol_number),
        ("container_number", shipment.container_number, parsed_bol.get_primary_container()),
        ("vessel_name", shipment.vessel_name, parsed_bol.vessel_name),
        ("voyage_number", shipment.voyage_number, parsed_bol.voyage_number),
        ("pol_code", shipment.pol_code, parsed_bol.port_of_loading),
        ("pod_code", shipment.pod_code, parsed_bol.port_of_discharge),
    ]

    for field_name, current, new_val in field_map:
        if new_val and new_val != "UNKNOWN":
            is_placeholder = (
                field_name == "container_number"
                and is_placeholder_container(current)
            ) or not current
            will_update = is_placeholder or not current
            changes.append(SyncChange(
                field=field_name,
                current=current,
                new_value=new_val,
                is_placeholder=is_placeholder,
                will_update=will_update,
            ))

    return BolSyncPreviewResponse(
        document_id=doc_id,
        shipment_id=str(shipment.id),
        shipment_reference=shipment.reference,
        changes=changes,
    )


def cross_validate_weights(
    shipment: Shipment, db: Session
) -> List[Dict]:
    """Cross-validate BoL weight vs Packing List weight.

    Checks if gross weight from BoL cargo matches Packing List
    within 5% tolerance.

    Args:
        shipment: The shipment to validate
        db: Database session

    Returns:
        List of validation results (empty if no issues)
    """
    docs = db.query(Document).filter(
        Document.shipment_id == shipment.id,
        Document.organization_id == shipment.organization_id,
    ).all()

    bol_doc = None
    packing_list_doc = None
    for doc in docs:
        if doc.document_type == DocumentType.BILL_OF_LADING and doc.bol_parsed_data:
            bol_doc = doc
        elif doc.document_type == DocumentType.PACKING_LIST:
            packing_list_doc = doc

    if not bol_doc or not packing_list_doc:
        return []

    # Get BoL weight
    parsed_bol = CanonicalBoL.model_validate(bol_doc.bol_parsed_data)
    bol_weight = parsed_bol.get_total_weight_kg()
    if not bol_weight:
        return []

    # Get Packing List weight from products
    products = db.query(Product).filter(
        Product.shipment_id == shipment.id,
    ).all()
    pl_weight = sum(
        float(p.quantity_gross_kg) for p in products
        if p.quantity_gross_kg
    )
    if not pl_weight:
        return []

    # Check 5% tolerance
    tolerance = 0.05
    diff = abs(bol_weight - pl_weight)
    max_allowed = max(bol_weight, pl_weight) * tolerance

    issues = []
    if diff > max_allowed:
        pct_diff = (diff / max(bol_weight, pl_weight)) * 100
        issues.append({
            "rule_id": "CROSS-001",
            "rule_name": "BoL vs Packing List Weight",
            "passed": False,
            "severity": "WARNING",
            "message": (
                f"BoL gross weight ({bol_weight:,.2f} kg) differs from "
                f"Packing List ({pl_weight:,.2f} kg) by {pct_diff:.1f}% "
                f"(tolerance: {tolerance*100:.0f}%)"
            ),
        })

    return issues


def _extract_text_from_document(document: Document) -> Optional[str]:
    """Extract text from a document's PDF file."""
    if not document.file_path:
        return None

    # Resolve file path
    full_path = get_full_path(document.file_path)
    if not full_path or not os.path.exists(full_path):
        # Try direct path
        if os.path.exists(document.file_path):
            full_path = document.file_path
        else:
            return None

    try:
        from .pdf_processor import pdf_processor
        if not pdf_processor.is_available():
            return None
        pages = pdf_processor.extract_text(full_path)
        if not pages:
            return None
        return "\n".join(page.text for page in pages)
    except Exception:
        logger.debug("PDF text extraction failed", exc_info=True)
        return None


def _run_compliance(
    document: Document,
    parsed_bol: CanonicalBoL,
    db: Session,
) -> Optional[BolComplianceResult]:
    """Run compliance rules and store results."""
    try:
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(parsed_bol)
        decision = get_compliance_decision(results)

        # Update document status
        document.compliance_status = decision
        document.compliance_checked_at = datetime.utcnow()

        if decision == "APPROVE":
            document.status = DocumentStatus.COMPLIANCE_OK
        elif decision == "REJECT":
            document.status = DocumentStatus.COMPLIANCE_FAILED

        # Store individual results
        db.query(ComplianceResult).filter(
            ComplianceResult.document_id == document.id
        ).delete()

        for result in results:
            cr = ComplianceResult(
                document_id=document.id,
                organization_id=document.organization_id,
                rule_id=result.rule_id,
                rule_name=result.rule_name,
                passed=result.passed,
                message=result.message,
                severity=result.severity,
                checked_at=datetime.utcnow(),
            )
            db.add(cr)

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        return BolComplianceResult(
            decision=decision,
            rules_passed=passed,
            rules_failed=failed,
            rules_total=len(results),
        )
    except Exception:
        logger.exception("Compliance check failed for document %s", document.id)
        return None


def _build_field_confidence(parsed_bol: CanonicalBoL) -> Dict[str, BolFieldResult]:
    """Build field-level confidence from parsed BoL data.

    Per-field confidence is derived from the overall weight system:
    if a field was extracted successfully, it gets full confidence
    for its weight tier; otherwise 0.
    """
    # Weight tiers (from bol_parser field_weights)
    high_conf = 0.95  # core fields found
    med_conf = 0.80   # optional fields found
    low_conf = 0.60   # inferred fields

    fields: Dict[str, BolFieldResult] = {}

    # BoL number
    bol_num = parsed_bol.bol_number
    has_bol = bol_num and bol_num != "UNKNOWN"
    fields["bol_number"] = BolFieldResult(
        value=bol_num if has_bol else None,
        confidence=high_conf if has_bol else 0.0,
    )

    # Shipper
    shipper_name = parsed_bol.shipper.name if parsed_bol.shipper else None
    has_shipper = shipper_name and shipper_name != "Unknown Shipper"
    fields["shipper"] = BolFieldResult(
        value=shipper_name if has_shipper else None,
        confidence=high_conf if has_shipper else 0.0,
    )

    # Consignee
    consignee_name = parsed_bol.consignee.name if parsed_bol.consignee else None
    has_consignee = consignee_name and consignee_name != "Unknown Consignee"
    fields["consignee"] = BolFieldResult(
        value=consignee_name if has_consignee else None,
        confidence=high_conf if has_consignee else 0.0,
    )

    # Container
    container = parsed_bol.get_primary_container()
    fields["container_number"] = BolFieldResult(
        value=container,
        confidence=high_conf if container else 0.0,
    )

    # Vessel
    fields["vessel_name"] = BolFieldResult(
        value=parsed_bol.vessel_name,
        confidence=med_conf if parsed_bol.vessel_name else 0.0,
    )

    # Voyage
    fields["voyage_number"] = BolFieldResult(
        value=parsed_bol.voyage_number,
        confidence=med_conf if parsed_bol.voyage_number else 0.0,
    )

    # Ports
    fields["port_of_loading"] = BolFieldResult(
        value=parsed_bol.port_of_loading,
        confidence=med_conf if parsed_bol.port_of_loading else 0.0,
    )
    fields["port_of_discharge"] = BolFieldResult(
        value=parsed_bol.port_of_discharge,
        confidence=med_conf if parsed_bol.port_of_discharge else 0.0,
    )

    return fields
