"""Validation runner for executing rules against shipments.

The ValidationRunner orchestrates rule execution and produces
a comprehensive ValidationReport with all results.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext
from .registry import RuleRegistry, get_registry

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ...models import Shipment, Document

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Complete validation report for a shipment.

    Contains summary statistics and detailed results for all rules executed.
    """
    shipment_id: str
    shipment_reference: str
    product_type: str
    validated_at: datetime
    validated_by: str

    # Summary statistics
    total_rules: int
    passed: int
    failed: int
    warnings: int
    rejected_documents: int  # Count of AI-rejected documents

    # Status flags
    is_valid: bool           # No critical/error failures
    needs_review: bool       # Has warnings
    has_rejections: bool     # Has AI-rejected documents

    # Detailed results
    results: List[RuleResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "shipment_id": self.shipment_id,
            "shipment_reference": self.shipment_reference,
            "product_type": self.product_type,
            "validated_at": self.validated_at.isoformat(),
            "validated_by": self.validated_by,
            "summary": {
                "total_rules": self.total_rules,
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "rejected_documents": self.rejected_documents,
                "is_valid": self.is_valid,
                "needs_review": self.needs_review,
                "has_rejections": self.has_rejections,
            },
            "results": [r.to_dict() for r in self.results],
        }

    def get_failures(self) -> List[RuleResult]:
        """Get only failed results (CRITICAL or ERROR severity)."""
        return [
            r for r in self.results
            if not r.passed and r.severity in [RuleSeverity.CRITICAL, RuleSeverity.ERROR]
        ]

    def get_warnings(self) -> List[RuleResult]:
        """Get only warning results."""
        return [
            r for r in self.results
            if not r.passed and r.severity == RuleSeverity.WARNING
        ]

    def get_rejections(self) -> List[RuleResult]:
        """Get AI-rejected document results."""
        return [
            r for r in self.results
            if not r.passed
            and r.category == RuleCategory.RELEVANCE
            and r.severity == RuleSeverity.CRITICAL
        ]


class ValidationRunner:
    """Executes validation rules against shipments.

    The runner:
    1. Gets applicable rules from the registry
    2. Builds a ValidationContext from the shipment
    3. Executes each rule
    4. Aggregates results into a ValidationReport
    5. Optionally logs to audit trail

    Example:
        runner = ValidationRunner()
        report = runner.validate_shipment(
            shipment=shipment,
            documents=documents,
            user="admin@example.com",
            db=db,
        )

        if not report.is_valid:
            print(f"Validation failed with {report.failed} errors")
    """

    def __init__(
        self,
        registry: Optional[RuleRegistry] = None,
        audit_logger: Optional[Any] = None,
    ):
        """Initialize the validation runner.

        Args:
            registry: Rule registry to use. If None, uses default.
            audit_logger: Optional audit logger for logging validation runs.
        """
        self.registry = registry or get_registry()
        self.audit_logger = audit_logger

    def validate_shipment(
        self,
        shipment: "Shipment",
        documents: List["Document"],
        user: str = "system",
        db: Optional["Session"] = None,
    ) -> ValidationReport:
        """Run all applicable validation rules on a shipment.

        Args:
            shipment: The shipment to validate
            documents: Documents attached to the shipment
            user: Username of who triggered validation
            db: Database session for loading related data and logging

        Returns:
            ValidationReport with all rule results
        """
        logger.info(f"Starting validation for shipment {shipment.reference}")

        # Build context with AI classification data
        context = ValidationContext.from_shipment(shipment, documents, db=db)

        # Get applicable rules for this product type
        rules = self.registry.get_rules_for_product_type(context.product_type)
        logger.info(f"Running {len(rules)} rules for product type {context.product_type}")

        # Execute rules and collect results
        results: List[RuleResult] = []
        for rule in rules:
            try:
                result = rule.validate(context)
                # Handle rules that return multiple results (like relevance)
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
            except Exception as e:
                logger.error(f"Rule {rule.rule_id} failed with error: {e}")
                results.append(RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message=f"Rule execution failed: {str(e)}",
                    category=rule.category,
                    details={"error": str(e)},
                ))

        # Calculate summary statistics
        passed = sum(1 for r in results if r.passed)
        failed = sum(
            1 for r in results
            if not r.passed and r.severity in [RuleSeverity.CRITICAL, RuleSeverity.ERROR]
        )
        warnings = sum(
            1 for r in results
            if not r.passed and r.severity == RuleSeverity.WARNING
        )
        rejected_documents = sum(
            1 for r in results
            if not r.passed
            and r.category == RuleCategory.RELEVANCE
            and r.severity == RuleSeverity.CRITICAL
        )

        # Build report
        report = ValidationReport(
            shipment_id=str(shipment.id),
            shipment_reference=shipment.reference,
            product_type=context.product_type.value if context.product_type else "unknown",
            validated_at=datetime.utcnow(),
            validated_by=user,
            total_rules=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            rejected_documents=rejected_documents,
            is_valid=(failed == 0),
            needs_review=(warnings > 0),
            has_rejections=(rejected_documents > 0),
            results=results,
        )

        logger.info(
            f"Validation complete for {shipment.reference}: "
            f"{passed} passed, {failed} failed, {warnings} warnings"
        )

        # Log to audit trail if configured
        if db and self.audit_logger:
            try:
                self.audit_logger.log(
                    action="document.validation.run",
                    resource_type="shipment",
                    resource_id=str(shipment.id),
                    username=user,
                    organization_id=str(shipment.organization_id),
                    success=report.is_valid,
                    details=report.to_dict(),
                    db=db,
                )
            except Exception as e:
                logger.warning(f"Failed to log validation to audit trail: {e}")

        return report

    def validate_document(
        self,
        document: "Document",
        shipment: "Shipment",
        db: Optional["Session"] = None,
    ) -> List[RuleResult]:
        """Validate a single document against relevance rules.

        This is a convenience method for validating just one document,
        useful during upload. Only runs relevance-related rules.

        Args:
            document: The document to validate
            shipment: The parent shipment
            db: Database session

        Returns:
            List of RuleResult for relevance checks only
        """
        context = ValidationContext.from_shipment(shipment, [document], db=db)

        # Only run relevance rules
        relevance_rules = self.registry.get_rules_by_category(RuleCategory.RELEVANCE)

        results: List[RuleResult] = []
        for rule in relevance_rules:
            try:
                result = rule.validate(context)
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
            except Exception as e:
                logger.error(f"Relevance rule {rule.rule_id} failed: {e}")

        return results
