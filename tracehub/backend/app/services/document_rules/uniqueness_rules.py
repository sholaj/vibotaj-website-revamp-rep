"""Uniqueness validation rules.

Rules that check for duplicate documents.
"""

from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext


class NoDuplicateDocumentsRule(ValidationRule):
    """Validates no duplicate document types exist.

    Each document type should appear only once per shipment
    unless explicitly allowed (e.g., multiple packing lists
    for multi-container shipments).
    """

    rule_id = "UNIQUE_001"
    name = "No Duplicate Documents"
    description = "Each document type should appear only once per shipment"
    severity = RuleSeverity.ERROR
    category = RuleCategory.UNIQUENESS

    def validate(self, context: ValidationContext) -> RuleResult:
        """Check for duplicate document types.

        Returns:
            RuleResult with list of duplicates if any
        """
        duplicates = []
        for doc_type, count in context.document_count_by_type.items():
            if count > 1:
                duplicates.append(f"{doc_type.value} ({count} copies)")

        if duplicates:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Duplicate documents found: {', '.join(duplicates)}",
                category=self.category,
                details={"duplicates": duplicates},
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="No duplicate documents",
            category=self.category,
        )
