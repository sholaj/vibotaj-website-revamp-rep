"""Relevance validation rules.

AI-based rules that check document content matches declared type.
"""

from typing import List

from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext


class DocumentRelevanceRule(ValidationRule):
    """Validates that uploaded document content matches declared document type.

    Uses AI classification to detect and reject:
    1. Unrelated documents (random PDFs, photos, etc.)
    2. Mismatched documents (declared as BOL but is actually an Invoice)

    Confidence Thresholds:
    - < 0.3: REJECT as unrelated (CRITICAL)
    - 0.3 - 0.5: FLAG for review if type matches, REJECT if mismatch
    - >= 0.5: ACCEPT if type matches, REJECT if mismatch
    """

    rule_id = "RELEVANCE_001"
    name = "Document Content Relevance"
    description = "Document content must match the declared document type"
    severity = RuleSeverity.CRITICAL
    category = RuleCategory.RELEVANCE

    # Configurable thresholds
    REJECT_THRESHOLD = 0.3      # Below this = definitely unrelated
    REVIEW_THRESHOLD = 0.5      # Below this but above reject = needs review

    def validate(self, context: ValidationContext) -> List[RuleResult]:
        """Validate all documents for relevance.

        Returns:
            List of RuleResult - one per problematic document,
            or a single success result if all pass.
        """
        results: List[RuleResult] = []

        # Skip if AI is not available
        if not context.ai_available:
            results.append(RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="AI classification unavailable - relevance check skipped",
                category=self.category,
                details={"reason": "ai_unavailable"},
            ))
            return results

        for doc_id, doc_with_class in context.classifications.items():
            doc = doc_with_class.document
            confidence = doc_with_class.confidence_score
            classification = doc_with_class.classification

            # Case 1: Very low confidence - document appears unrelated
            if confidence < self.REJECT_THRESHOLD:
                results.append(RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.CRITICAL,
                    message=f"Document appears unrelated. AI confidence: {confidence:.0%}. "
                            f"Expected: {doc.document_type.value}",
                    category=self.category,
                    document_type=doc.document_type.value,
                    document_id=doc_id,
                    details={
                        "confidence": confidence,
                        "declared_type": doc.document_type.value,
                        "rejection_reason": "unrelated_document",
                        "threshold": self.REJECT_THRESHOLD,
                    },
                ))
                continue

            # Case 2: Check type match if we have classification
            if classification and classification.document_type:
                ai_detected_type = classification.document_type
                declared_type = doc.document_type

                types_match = ai_detected_type == declared_type

                if not types_match:
                    # Type mismatch - reject regardless of confidence
                    results.append(RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        passed=False,
                        severity=RuleSeverity.CRITICAL,
                        message=f"Document type mismatch. Declared: {declared_type.value}, "
                                f"AI detected: {ai_detected_type.value} ({confidence:.0%} confidence)",
                        category=self.category,
                        document_type=doc.document_type.value,
                        document_id=doc_id,
                        details={
                            "confidence": confidence,
                            "declared_type": declared_type.value,
                            "detected_type": ai_detected_type.value,
                            "rejection_reason": "type_mismatch",
                            "ai_reasoning": classification.reasoning,
                        },
                    ))
                    continue

                # Types match but low confidence - flag for review
                if confidence < self.REVIEW_THRESHOLD:
                    results.append(RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        passed=False,
                        severity=RuleSeverity.WARNING,
                        message=f"Document type uncertain. Please verify manually. "
                                f"AI confidence: {confidence:.0%}",
                        category=self.category,
                        document_type=doc.document_type.value,
                        document_id=doc_id,
                        details={
                            "confidence": confidence,
                            "declared_type": declared_type.value,
                            "detected_type": ai_detected_type.value,
                            "flag_reason": "low_confidence",
                            "threshold": self.REVIEW_THRESHOLD,
                        },
                    ))
                    continue

        # If no issues found, return success
        if not results:
            results.append(RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="All documents match their declared types",
                category=self.category,
            ))

        return results
