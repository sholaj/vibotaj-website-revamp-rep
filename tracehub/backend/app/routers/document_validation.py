"""Document validation API endpoints.

Provides endpoints for validating shipment documents against
compliance rules, checking validation status, and overriding
AI rejections.

All endpoints enforce multi-tenancy by filtering on organization_id.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..routers.auth import get_current_active_user
from ..schemas.user import CurrentUser
from ..models import Shipment, Document
from ..models.shipment import ProductType
from ..services.document_rules import (
    ValidationRunner,
    ValidationReport,
    RuleRegistry,
    get_registry,
    RuleSeverity,
    RuleCategory,
)

router = APIRouter(prefix="/validation", tags=["Document Validation"])
logger = logging.getLogger(__name__)


@router.post("/shipments/{shipment_id}/validate")
async def validate_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Validate all documents for a shipment.

    Runs all applicable validation rules based on the shipment's product type
    and returns a comprehensive validation report.

    **Rules executed:**
    - PRESENCE_001: All required documents present
    - UNIQUE_001: No duplicate document types
    - RELEVANCE_001: AI-based content relevance (if AI available)
    - HORN_HOOF_002: Vet cert issue date (Horn & Hoof only)
    - HORN_HOOF_003: Vet cert authorized signer (Horn & Hoof only)

    **Returns:**
    - Validation report with pass/fail status for each rule
    - Summary statistics (passed, failed, warnings)
    - List of rejected documents (if any)

    **Requires:** Authenticated user with access to the shipment's organization
    """
    logger.info(f"Validation requested for shipment {shipment_id} by {current_user.email}")

    # Get shipment with multi-tenancy check
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get all documents for this shipment
    documents = db.query(Document).filter(
        Document.shipment_id == shipment_id
    ).all()

    logger.info(f"Found {len(documents)} documents for shipment {shipment.reference}")

    # Run validation
    runner = ValidationRunner()
    report = runner.validate_shipment(
        shipment=shipment,
        documents=documents,
        user=current_user.email,
        db=db,
    )

    logger.info(
        f"Validation complete for {shipment.reference}: "
        f"valid={report.is_valid}, failed={report.failed}, warnings={report.warnings}"
    )

    # Build response with override info
    result = report.to_dict()

    # Add override info if present
    if shipment.validation_override_reason:
        result["override"] = {
            "reason": shipment.validation_override_reason,
            "overridden_by": shipment.validation_override_by,
            "overridden_at": shipment.validation_override_at.isoformat() if shipment.validation_override_at else None,
        }
    else:
        result["override"] = None

    return result


@router.get("/shipments/{shipment_id}")
async def get_validation_report(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Get validation report for a shipment.

    Runs all applicable validation rules based on the shipment's product type
    and returns a comprehensive validation report. This is the same as the
    POST /validate endpoint but as a GET for retrieving the current state.

    **Returns:**
    - Validation report with pass/fail status for each rule
    - Summary statistics (passed, failed, warnings)
    - List of rejected documents (if any)

    **Requires:** Authenticated user with access to the shipment's organization
    """
    logger.info(f"Validation report requested for shipment {shipment_id} by {current_user.email}")

    # Get shipment with multi-tenancy check (owner or buyer can access)
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        (
            (Shipment.organization_id == current_user.organization_id) |
            (Shipment.buyer_organization_id == current_user.organization_id)
        )
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get all documents for this shipment
    documents = db.query(Document).filter(
        Document.shipment_id == shipment_id
    ).all()

    logger.info(f"Found {len(documents)} documents for shipment {shipment.reference}")

    # Run validation
    runner = ValidationRunner()
    report = runner.validate_shipment(
        shipment=shipment,
        documents=documents,
        user=current_user.email,
        db=db,
    )

    logger.info(
        f"Validation report for {shipment.reference}: "
        f"valid={report.is_valid}, failed={report.failed}, warnings={report.warnings}"
    )

    # Build response with override info
    result = report.to_dict()

    # Add override info if present
    if shipment.validation_override_reason:
        result["override"] = {
            "reason": shipment.validation_override_reason,
            "overridden_by": shipment.validation_override_by,
            "overridden_at": shipment.validation_override_at.isoformat() if shipment.validation_override_at else None,
        }
    else:
        result["override"] = None

    return result


@router.get("/shipments/{shipment_id}/status")
async def get_validation_status(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Get quick validation status for a shipment.

    Returns a simplified status without running full validation.
    Useful for dashboard displays and quick checks.

    **Returns:**
    - has_all_required: Whether all required documents are present
    - has_duplicates: Whether duplicate documents exist
    - document_count: Number of documents attached
    - required_count: Number of required document types
    """
    # Get shipment with multi-tenancy check
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get documents
    documents = db.query(Document).filter(
        Document.shipment_id == shipment_id
    ).all()

    # Get required document types
    from ..services.compliance import get_required_documents_by_product_type
    required_types = []
    if shipment.product_type:
        try:
            required_types = get_required_documents_by_product_type(shipment.product_type)
        except Exception:
            pass

    # Check what we have
    doc_types_present = set(doc.document_type for doc in documents)
    required_set = set(required_types)
    missing = required_set - doc_types_present

    # Check for duplicates
    type_counts = {}
    for doc in documents:
        type_counts[doc.document_type] = type_counts.get(doc.document_type, 0) + 1
    duplicates = [dt.value for dt, count in type_counts.items() if count > 1]

    return {
        "shipment_id": str(shipment_id),
        "shipment_reference": shipment.reference,
        "product_type": shipment.product_type.value if shipment.product_type else None,
        "document_count": len(documents),
        "required_count": len(required_types),
        "has_all_required": len(missing) == 0,
        "missing_documents": [dt.value for dt in missing],
        "has_duplicates": len(duplicates) > 0,
        "duplicate_types": duplicates,
    }


@router.get("/rules")
async def list_validation_rules(
    product_type: Optional[str] = Query(
        None,
        description="Filter rules by product type (e.g., 'horn_hoof', 'sweet_potato')"
    ),
    category: Optional[str] = Query(
        None,
        description="Filter rules by category (presence, uniqueness, relevance, content, date)"
    ),
):
    """
    List all available validation rules.

    Returns information about each rule including:
    - Rule ID and name
    - Description of what the rule validates
    - Severity level (critical, error, warning, info)
    - Category (presence, uniqueness, relevance, etc.)
    - Which product types the rule applies to

    **Query Parameters:**
    - product_type: Filter to rules that apply to this product type
    - category: Filter to rules in this category
    """
    registry = get_registry()

    # Get rules, optionally filtered by product type
    if product_type:
        try:
            pt = ProductType(product_type)
            rules = registry.get_rules_for_product_type(pt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product_type: {product_type}"
            )
    else:
        rules = registry.get_all_rules()

    # Filter by category if specified
    if category:
        try:
            cat = RuleCategory(category)
            rules = [r for r in rules if r.category == cat]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Valid: {[c.value for c in RuleCategory]}"
            )

    return [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "severity": r.severity.value,
            "category": r.category.value,
            "applies_to": r.applies_to,
        }
        for r in rules
    ]


@router.get("/rules/{rule_id}")
async def get_rule_details(rule_id: str):
    """
    Get detailed information about a specific validation rule.

    **Path Parameters:**
    - rule_id: The unique rule identifier (e.g., "PRESENCE_001")
    """
    registry = get_registry()
    rule = registry.get_rule(rule_id)

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"Rule not found: {rule_id}"
        )

    return {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "description": rule.description,
        "severity": rule.severity.value,
        "category": rule.category.value,
        "applies_to": rule.applies_to,
    }


@router.post("/documents/{document_id}/override-rejection")
async def override_document_rejection(
    document_id: UUID,
    reason: str = Query(..., min_length=10, description="Reason for override (min 10 chars)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Override an AI-rejected document with manual approval.

    Use this endpoint when a document was incorrectly flagged by the
    AI relevance check and needs manual approval.

    **Requirements:**
    - User must have 'admin' or 'owner' role
    - Reason must be at least 10 characters

    **Audit:**
    - Override is logged to the audit trail with user and reason
    """
    # Check role
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Override requires admin or owner role"
        )

    # Find the document with org check
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Log the override to audit trail
    from ..models.audit_log import AuditLog

    audit_entry = AuditLog(
        action="document.validation_override",
        resource_type="document",
        resource_id=str(document_id),
        user_id=str(current_user.id),
        username=current_user.email,
        organization_id=current_user.organization_id,
        details={
            "action": "validation_override",
            "override_reason": reason,
            "overridden_by": current_user.email,
            "document_type": document.document_type.value,
            "document_name": document.name,
        },
    )
    db.add(audit_entry)
    db.commit()

    logger.info(
        f"Validation override for document {document_id} by {current_user.email}: {reason}"
    )

    return {
        "success": True,
        "message": "Document rejection overridden",
        "document_id": str(document_id),
        "overridden_by": current_user.email,
        "reason": reason,
    }


@router.post("/shipments/{shipment_id}/validate-document/{document_id}")
async def validate_single_document(
    shipment_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Validate a single document against relevance rules.

    Useful during upload to get immediate feedback on whether
    a document matches its declared type.

    **Returns:**
    - Relevance check results only (not full shipment validation)
    """
    # Get shipment with multi-tenancy check
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get the specific document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.shipment_id == shipment_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Run relevance validation only
    runner = ValidationRunner()
    results = runner.validate_document(document, shipment, db=db)

    return {
        "document_id": str(document_id),
        "document_type": document.document_type.value,
        "results": [r.to_dict() for r in results],
        "is_valid": all(r.passed or r.severity == RuleSeverity.INFO for r in results),
    }


@router.post("/shipments/{shipment_id}/override")
async def override_shipment_validation(
    shipment_id: UUID,
    reason: str = Query(..., min_length=5, description="Reason for override (min 5 chars)"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Override the validation status for a shipment.

    Allows admin users to mark a shipment as valid despite failing validation rules.
    This is useful when documents are correct but automated checks fail.

    **Requirements:**
    - User must have 'admin' or 'owner' role
    - Reason must be at least 5 characters

    **Audit:**
    - Override is logged to the audit trail with user and reason
    """
    # Check role
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Override requires admin or owner role"
        )

    # Get shipment with multi-tenancy check
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Set override fields
    shipment.validation_override_reason = reason
    shipment.validation_override_by = current_user.email
    shipment.validation_override_at = datetime.utcnow()

    # Log to audit trail
    from ..models.audit_log import AuditLog

    audit_entry = AuditLog(
        action="shipment.validation_override",
        resource_type="shipment",
        resource_id=str(shipment_id),
        user_id=str(current_user.id),
        username=current_user.email,
        organization_id=current_user.organization_id,
        details={
            "action": "validation_override",
            "override_reason": reason,
            "overridden_by": current_user.email,
            "shipment_reference": shipment.reference,
        },
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(shipment)

    logger.info(
        f"Validation override for shipment {shipment.reference} by {current_user.email}: {reason}"
    )

    # Return updated validation report
    documents = db.query(Document).filter(Document.shipment_id == shipment_id).all()
    runner = ValidationRunner()
    report = runner.validate_shipment(
        shipment=shipment,
        documents=documents,
        user=current_user.email,
        db=db,
    )

    result = report.to_dict()
    result["override"] = {
        "reason": shipment.validation_override_reason,
        "overridden_by": shipment.validation_override_by,
        "overridden_at": shipment.validation_override_at.isoformat() if shipment.validation_override_at else None,
    }

    return result


@router.delete("/shipments/{shipment_id}/override")
async def clear_shipment_validation_override(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Clear the validation override for a shipment.

    Removes any admin override, returning the shipment to normal validation status.

    **Requirements:**
    - User must have 'admin' or 'owner' role
    """
    # Check role
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Clearing override requires admin or owner role"
        )

    # Get shipment with multi-tenancy check
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Check if there's an override to clear
    if not shipment.validation_override_reason:
        raise HTTPException(status_code=400, detail="No override to clear")

    # Log to audit trail before clearing
    from ..models.audit_log import AuditLog

    audit_entry = AuditLog(
        action="shipment.validation_override_cleared",
        resource_type="shipment",
        resource_id=str(shipment_id),
        user_id=str(current_user.id),
        username=current_user.email,
        organization_id=current_user.organization_id,
        details={
            "action": "validation_override_cleared",
            "cleared_by": current_user.email,
            "previous_reason": shipment.validation_override_reason,
            "previous_override_by": shipment.validation_override_by,
            "shipment_reference": shipment.reference,
        },
    )
    db.add(audit_entry)

    # Clear override fields
    shipment.validation_override_reason = None
    shipment.validation_override_by = None
    shipment.validation_override_at = None

    db.commit()
    db.refresh(shipment)

    logger.info(
        f"Validation override cleared for shipment {shipment.reference} by {current_user.email}"
    )

    # Return updated validation report
    documents = db.query(Document).filter(Document.shipment_id == shipment_id).all()
    runner = ValidationRunner()
    report = runner.validate_shipment(
        shipment=shipment,
        documents=documents,
        user=current_user.email,
        db=db,
    )

    result = report.to_dict()
    result["override"] = None

    return result
