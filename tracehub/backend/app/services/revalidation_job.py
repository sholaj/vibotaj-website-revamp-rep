"""Historic Shipment Revalidation Background Job.

Provides functionality to revalidate existing shipments against
new or updated validation rules.

PRP: Document Validation & Compliance Enhancement (Phase 3)

Usage:
    from app.services.revalidation_job import RevalidationService

    service = RevalidationService(db)
    report = service.revalidate_shipment(shipment_id)

    # Or batch revalidation
    summary = service.revalidate_all_shipments(
        product_type="horn_hoof",
        limit=100
    )
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import Shipment, Document, ShipmentStatus
from ..models.document import DocumentIssue
from .document_rules import ValidationRunner, ValidationReport, get_registry

logger = logging.getLogger(__name__)


@dataclass
class RevalidationResult:
    """Result of revalidating a single shipment."""
    shipment_id: str
    shipment_reference: str
    success: bool
    previous_issue_count: int
    new_issue_count: int
    issues_resolved: int
    new_issues_created: int
    validation_version: int
    revalidated_at: datetime
    error_message: Optional[str] = None
    report: Optional[ValidationReport] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shipment_id": self.shipment_id,
            "shipment_reference": self.shipment_reference,
            "success": self.success,
            "previous_issue_count": self.previous_issue_count,
            "new_issue_count": self.new_issue_count,
            "issues_resolved": self.issues_resolved,
            "new_issues_created": self.new_issues_created,
            "validation_version": self.validation_version,
            "revalidated_at": self.revalidated_at.isoformat(),
            "error_message": self.error_message,
        }


@dataclass
class BatchRevalidationSummary:
    """Summary of batch revalidation run."""
    total_shipments: int
    successful: int
    failed: int
    total_new_issues: int
    total_resolved_issues: int
    validation_version: int
    started_at: datetime
    completed_at: datetime
    results: List[RevalidationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_shipments": self.total_shipments,
            "successful": self.successful,
            "failed": self.failed,
            "total_new_issues": self.total_new_issues,
            "total_resolved_issues": self.total_resolved_issues,
            "validation_version": self.validation_version,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "results": [r.to_dict() for r in self.results],
        }


class RevalidationService:
    """Service for revalidating shipments against validation rules.

    This service:
    1. Runs the validation pipeline against existing shipments
    2. Creates new DocumentIssue records for failures
    3. Resolves issues that are no longer failing
    4. Updates validation_version on documents
    5. Provides batch processing for historic data
    """

    # Current validation rules version - increment when rules change
    VALIDATION_VERSION = 1

    def __init__(self, db: Session):
        self.db = db
        self.runner = ValidationRunner(registry=get_registry())

    def revalidate_shipment(
        self,
        shipment_id: UUID,
        user: str = "system",
        force: bool = False,
    ) -> RevalidationResult:
        """Revalidate a single shipment.

        Args:
            shipment_id: ID of the shipment to revalidate
            user: Username triggering the revalidation
            force: If True, revalidate even if version hasn't changed

        Returns:
            RevalidationResult with details of the revalidation
        """
        now = datetime.utcnow()

        try:
            # Get shipment with documents
            shipment = self.db.query(Shipment).filter(
                Shipment.id == shipment_id
            ).first()

            if not shipment:
                return RevalidationResult(
                    shipment_id=str(shipment_id),
                    shipment_reference="UNKNOWN",
                    success=False,
                    previous_issue_count=0,
                    new_issue_count=0,
                    issues_resolved=0,
                    new_issues_created=0,
                    validation_version=self.VALIDATION_VERSION,
                    revalidated_at=now,
                    error_message=f"Shipment {shipment_id} not found",
                )

            # Get documents for this shipment
            documents = self.db.query(Document).filter(
                Document.shipment_id == shipment_id
            ).all()

            # Count existing unresolved issues
            previous_issue_count = self.db.query(DocumentIssue).filter(
                DocumentIssue.shipment_id == shipment_id,
                DocumentIssue.is_overridden == False,
            ).count()

            # Check if any document needs revalidation
            if not force:
                needs_revalidation = any(
                    (doc.validation_version or 0) < self.VALIDATION_VERSION
                    for doc in documents
                )
                if not needs_revalidation and previous_issue_count == 0:
                    return RevalidationResult(
                        shipment_id=str(shipment_id),
                        shipment_reference=shipment.reference,
                        success=True,
                        previous_issue_count=0,
                        new_issue_count=0,
                        issues_resolved=0,
                        new_issues_created=0,
                        validation_version=self.VALIDATION_VERSION,
                        revalidated_at=now,
                        error_message="Already at current validation version",
                    )

            # Run validation
            report = self.runner.validate_shipment(
                shipment=shipment,
                documents=documents,
                user=user,
                db=self.db,
            )

            # Process validation results and create/update issues
            issues_created, issues_resolved = self._process_validation_results(
                shipment_id=shipment_id,
                report=report,
            )

            # Update validation_version on all documents
            for doc in documents:
                doc.validation_version = self.VALIDATION_VERSION
                doc.last_validated_at = now

            self.db.commit()

            # Count new issue count after processing
            new_issue_count = self.db.query(DocumentIssue).filter(
                DocumentIssue.shipment_id == shipment_id,
                DocumentIssue.is_overridden == False,
            ).count()

            return RevalidationResult(
                shipment_id=str(shipment_id),
                shipment_reference=shipment.reference,
                success=True,
                previous_issue_count=previous_issue_count,
                new_issue_count=new_issue_count,
                issues_resolved=issues_resolved,
                new_issues_created=issues_created,
                validation_version=self.VALIDATION_VERSION,
                revalidated_at=now,
                report=report,
            )

        except Exception as e:
            logger.error(f"Error revalidating shipment {shipment_id}: {e}")
            self.db.rollback()
            return RevalidationResult(
                shipment_id=str(shipment_id),
                shipment_reference=shipment.reference if shipment else "UNKNOWN",
                success=False,
                previous_issue_count=0,
                new_issue_count=0,
                issues_resolved=0,
                new_issues_created=0,
                validation_version=self.VALIDATION_VERSION,
                revalidated_at=now,
                error_message=str(e),
            )

    def _process_validation_results(
        self,
        shipment_id: UUID,
        report: ValidationReport,
    ) -> tuple[int, int]:
        """Process validation results and update DocumentIssue records.

        Returns:
            Tuple of (issues_created, issues_resolved)
        """
        issues_created = 0
        issues_resolved = 0

        # Get existing unresolved issues for this shipment
        existing_issues = {
            issue.rule_id: issue
            for issue in self.db.query(DocumentIssue).filter(
                DocumentIssue.shipment_id == shipment_id,
                DocumentIssue.is_overridden == False,
            ).all()
        }

        # Process each validation result
        new_rule_ids = set()
        for result in report.results:
            if not result.passed:
                new_rule_ids.add(result.rule_id)

                if result.rule_id not in existing_issues:
                    # Create new issue
                    issue = DocumentIssue(
                        shipment_id=shipment_id,
                        document_id=UUID(result.document_id) if result.document_id else None,
                        rule_id=result.rule_id,
                        rule_name=result.rule_name,
                        severity=result.severity.value if hasattr(result.severity, 'value') else str(result.severity),
                        message=result.message,
                        field=result.details.get("field") if result.details else None,
                        expected_value=str(result.details.get("expected")) if result.details and result.details.get("expected") else None,
                        actual_value=str(result.details.get("actual")) if result.details and result.details.get("actual") else None,
                        source_document_type=result.details.get("source_doc") if result.details else None,
                        target_document_type=result.details.get("target_doc") if result.details else None,
                        is_overridden=False,
                    )
                    self.db.add(issue)
                    issues_created += 1

        # Resolve issues that no longer fail
        for rule_id, existing_issue in existing_issues.items():
            if rule_id not in new_rule_ids:
                # Issue is resolved - delete it
                self.db.delete(existing_issue)
                issues_resolved += 1

        return issues_created, issues_resolved

    def revalidate_all_shipments(
        self,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        force: bool = False,
    ) -> BatchRevalidationSummary:
        """Batch revalidate multiple shipments.

        Args:
            product_type: Filter to specific product type
            status: Filter to specific shipment status
            organization_id: Filter to specific organization
            limit: Maximum number of shipments to process
            force: If True, revalidate all regardless of version

        Returns:
            BatchRevalidationSummary with results
        """
        started_at = datetime.utcnow()

        # Build query
        query = self.db.query(Shipment)

        if product_type:
            query = query.filter(Shipment.product_type == product_type)

        if status:
            query = query.filter(Shipment.status == status)

        if organization_id:
            query = query.filter(Shipment.organization_id == organization_id)

        # Exclude archived shipments by default
        query = query.filter(Shipment.status != ShipmentStatus.ARCHIVED)

        if limit:
            query = query.limit(limit)

        shipments = query.all()

        results: List[RevalidationResult] = []
        total_new_issues = 0
        total_resolved_issues = 0
        successful = 0
        failed = 0

        for shipment in shipments:
            result = self.revalidate_shipment(
                shipment_id=shipment.id,
                user="batch_revalidation",
                force=force,
            )
            results.append(result)

            if result.success:
                successful += 1
                total_new_issues += result.new_issues_created
                total_resolved_issues += result.issues_resolved
            else:
                failed += 1

        completed_at = datetime.utcnow()

        return BatchRevalidationSummary(
            total_shipments=len(shipments),
            successful=successful,
            failed=failed,
            total_new_issues=total_new_issues,
            total_resolved_issues=total_resolved_issues,
            validation_version=self.VALIDATION_VERSION,
            started_at=started_at,
            completed_at=completed_at,
            results=results,
        )

    def get_shipments_needing_revalidation(
        self,
        limit: int = 100,
    ) -> List[Shipment]:
        """Get shipments that have documents below current validation version.

        Returns:
            List of shipments that need revalidation
        """
        # Find shipments with documents that have old validation_version
        subquery = self.db.query(Document.shipment_id).filter(
            (Document.validation_version == None) |
            (Document.validation_version < self.VALIDATION_VERSION)
        ).distinct().subquery()

        return self.db.query(Shipment).filter(
            Shipment.id.in_(subquery),
            Shipment.status != ShipmentStatus.ARCHIVED,
        ).limit(limit).all()
