"""Presence validation rules.

Rules that check for the existence of required documents.
"""

from typing import List, Union

from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext


class RequiredDocumentsPresentRule(ValidationRule):
    """Validates all required documents are present for the shipment.

    Required documents are determined by the shipment's product_type
    using the compliance matrix from services/compliance.py.
    """

    rule_id = "PRESENCE_001"
    name = "Required Documents Present"
    description = "All required documents must be uploaded for the shipment"
    severity = RuleSeverity.CRITICAL
    category = RuleCategory.PRESENCE

    def validate(self, context: ValidationContext) -> RuleResult:
        """Check that all required document types are present.

        Returns:
            RuleResult with list of missing document types if any
        """
        missing = []
        for doc_type in context.required_document_types:
            if not context.has_document_type(doc_type):
                missing.append(doc_type.value)

        if missing:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Missing required documents: {', '.join(missing)}",
                category=self.category,
                details={"missing_types": missing},
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="All required documents present",
            category=self.category,
        )
