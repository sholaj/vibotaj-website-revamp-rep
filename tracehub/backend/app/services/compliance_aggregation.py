"""Shipment-level compliance aggregation service.

Derives aggregate compliance status from individual document compliance
states and validation results. Part of PRD-016.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..models import Document, DocumentStatus, Shipment, ComplianceResult
from ..models.document import DocumentIssue

logger = logging.getLogger(__name__)


def get_compliance_decision(
    shipment: Shipment,
    documents: List[Document],
    db: Session,
) -> str:
    """Derive aggregate compliance decision for a shipment.

    Logic:
    - REJECT: Any document has COMPLIANCE_FAILED and unresolved issues with ERROR severity
    - HOLD: Any document still in UPLOADED/VALIDATED (not yet compliance-checked),
            or has WARNING-level unresolved issues
    - APPROVE: All documents are COMPLIANCE_OK or LINKED

    Args:
        shipment: The shipment to evaluate
        documents: All documents for this shipment
        db: Database session

    Returns:
        "APPROVE", "HOLD", or "REJECT"
    """
    if not documents:
        return "HOLD"

    # Check for overrides
    if shipment.validation_override_reason:
        return "APPROVE"

    has_failed = False
    has_pending = False

    for doc in documents:
        if doc.status == DocumentStatus.COMPLIANCE_FAILED:
            # Check if all issues are overridden
            unresolved = [
                issue for issue in (doc.issues or [])
                if not issue.is_overridden and issue.severity == "ERROR"
            ]
            if unresolved:
                has_failed = True
            else:
                has_pending = True
        elif doc.status in (
            DocumentStatus.DRAFT,
            DocumentStatus.UPLOADED,
            DocumentStatus.VALIDATED,
        ):
            has_pending = True

    if has_failed:
        return "REJECT"
    if has_pending:
        return "HOLD"
    return "APPROVE"


def get_compliance_summary(
    shipment: Shipment,
    documents: List[Document],
    db: Session,
) -> Dict[str, Any]:
    """Get full compliance summary for a shipment.

    Args:
        shipment: The shipment
        documents: All shipment documents
        db: Database session

    Returns:
        Compliance summary dict with decision, counts, and rule results
    """
    decision = get_compliance_decision(shipment, documents, db)

    # Gather all compliance results for this shipment's documents
    doc_ids = [doc.id for doc in documents]
    results: List[ComplianceResult] = []
    if doc_ids:
        results = (
            db.query(ComplianceResult)
            .filter(
                ComplianceResult.document_id.in_(doc_ids),
                ComplianceResult.organization_id == shipment.organization_id,
            )
            .all()
        )

    # Also gather document issues
    issues: List[DocumentIssue] = []
    if doc_ids:
        issues = (
            db.query(DocumentIssue)
            .filter(
                DocumentIssue.document_id.in_(doc_ids),
                DocumentIssue.organization_id == shipment.organization_id,
            )
            .all()
        )

    # Compute counts
    total_rules = len(results) + len(issues)
    passed = sum(1 for r in results if r.passed)
    failed_results = sum(1 for r in results if not r.passed)
    failed_issues = sum(1 for i in issues if not i.is_overridden)
    warnings = sum(
        1 for r in results if not r.passed and r.severity == "WARNING"
    ) + sum(
        1 for i in issues if not i.is_overridden and i.severity == "WARNING"
    )

    # Build rule results list
    rule_results = []
    for r in results:
        rule_results.append({
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "passed": r.passed,
            "severity": r.severity,
            "message": r.message,
            "field_path": r.field_path,
            "document_type": r.document_type,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
        })

    for i in issues:
        rule_results.append({
            "rule_id": i.rule_id,
            "rule_name": i.rule_name,
            "passed": i.is_overridden,
            "severity": i.severity,
            "message": i.message,
            "field_path": i.field,
            "document_type": i.source_document_type,
            "checked_at": i.created_at.isoformat() if i.created_at else None,
            "is_overridden": i.is_overridden,
            "override_reason": i.override_reason,
        })

    # Override info
    override = None
    if shipment.validation_override_reason:
        override = {
            "reason": shipment.validation_override_reason,
            "overridden_by": shipment.validation_override_by,
            "overridden_at": (
                shipment.validation_override_at.isoformat()
                if shipment.validation_override_at
                else None
            ),
        }

    return {
        "shipment_id": str(shipment.id),
        "decision": decision,
        "summary": {
            "total_rules": total_rules,
            "passed": passed,
            "failed": failed_results + failed_issues,
            "warnings": warnings,
        },
        "results": rule_results,
        "override": override,
    }
