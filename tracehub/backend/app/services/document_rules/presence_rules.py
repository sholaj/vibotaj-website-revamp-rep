"""Presence validation rules.

Rules that check for the existence of required documents.

Enhanced to distinguish between:
- MISSING: No document of this type exists
- DRAFT: Document exists but is in draft status (not yet validated)
- UPLOADED: Document uploaded but pending validation
- VALIDATED: Document has been validated

PRP: Document Validation & Compliance Enhancement
"""

from typing import List, Dict, Any

from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext


class RequiredDocumentsPresentRule(ValidationRule):
    """Validates all required documents are present for the shipment.

    Required documents are determined by the shipment's product_type
    using the compliance matrix from services/compliance.py.

    Enhanced: Documents in DRAFT status are not counted as 'missing'.
    They are reported separately as 'draft' with a WARNING severity.
    """

    rule_id = "PRESENCE_001"
    name = "Required Documents Present"
    description = "All required documents must be uploaded for the shipment"
    severity = RuleSeverity.CRITICAL
    category = RuleCategory.PRESENCE

    def validate(self, context: ValidationContext) -> List[RuleResult]:
        """Check that all required document types are present.

        Returns:
            List of RuleResult for each document type check
        """
        from ...models.document import DocumentStatus

        results = []
        missing = []
        drafts = []
        pending = []

        for doc_type in context.required_document_types:
            docs = context.get_documents_of_type(doc_type)

            if not docs:
                missing.append(doc_type.value)
            else:
                # Check status of documents
                has_validated = any(
                    d.status in (
                        DocumentStatus.VALIDATED,
                        DocumentStatus.COMPLIANCE_OK,
                        DocumentStatus.LINKED
                    ) for d in docs
                )
                all_draft = all(d.status == DocumentStatus.DRAFT for d in docs)
                has_uploaded = any(
                    d.status in (DocumentStatus.UPLOADED, DocumentStatus.PENDING_VALIDATION)
                    for d in docs
                )

                if all_draft:
                    drafts.append(doc_type.value)
                elif not has_validated and has_uploaded:
                    pending.append(doc_type.value)

        # Report truly missing documents (CRITICAL)
        if missing:
            results.append(RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=RuleSeverity.CRITICAL,
                message=f"Missing required documents: {', '.join(missing)}",
                category=self.category,
                details={"missing_types": missing, "count": len(missing)},
            ))

        # Report draft documents (WARNING - not missing but not validated)
        if drafts:
            results.append(RuleResult(
                rule_id=f"{self.rule_id}_DRAFT",
                rule_name=f"{self.name} (Drafts)",
                passed=True,  # Drafts are not failures, just notifications
                severity=RuleSeverity.WARNING,
                message=f"Documents in draft status (not yet validated): {', '.join(drafts)}",
                category=self.category,
                details={"draft_types": drafts, "count": len(drafts)},
            ))

        # Report pending validation documents (INFO)
        if pending:
            results.append(RuleResult(
                rule_id=f"{self.rule_id}_PENDING",
                rule_name=f"{self.name} (Pending Validation)",
                passed=True,
                severity=RuleSeverity.INFO,
                message=f"Documents awaiting validation: {', '.join(pending)}",
                category=self.category,
                details={"pending_types": pending, "count": len(pending)},
            ))

        # If nothing to report, return success
        if not results:
            results.append(RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=self.severity,
                message="All required documents present and validated",
                category=self.category,
            ))

        return results


class EnhancedPresenceCheckRule(ValidationRule):
    """Detailed presence check with status breakdown.

    Provides a comprehensive view of document presence including:
    - Which documents are present and validated
    - Which documents are in draft
    - Which documents are pending validation
    - Which documents are missing
    - Which documents have duplicates
    """

    rule_id = "PRESENCE_002"
    name = "Document Presence Summary"
    description = "Comprehensive document presence check with status breakdown"
    severity = RuleSeverity.INFO
    category = RuleCategory.PRESENCE

    def validate(self, context: ValidationContext) -> RuleResult:
        """Generate comprehensive presence check summary."""
        from ...models.document import DocumentStatus

        summary: Dict[str, Any] = {
            "validated": [],
            "draft": [],
            "uploaded": [],
            "missing": [],
            "duplicates": [],
        }

        for doc_type in context.required_document_types:
            docs = context.get_documents_of_type(doc_type)
            doc_type_name = doc_type.value

            if not docs:
                summary["missing"].append(doc_type_name)
            else:
                # Count by status
                validated_count = sum(
                    1 for d in docs if d.status in (
                        DocumentStatus.VALIDATED,
                        DocumentStatus.COMPLIANCE_OK,
                        DocumentStatus.LINKED
                    )
                )
                draft_count = sum(1 for d in docs if d.status == DocumentStatus.DRAFT)
                uploaded_count = sum(
                    1 for d in docs if d.status in (
                        DocumentStatus.UPLOADED,
                        DocumentStatus.PENDING_VALIDATION
                    )
                )

                if validated_count > 0:
                    summary["validated"].append(doc_type_name)
                elif draft_count > 0:
                    summary["draft"].append(doc_type_name)
                elif uploaded_count > 0:
                    summary["uploaded"].append(doc_type_name)

                # Check for duplicates
                if len(docs) > 1:
                    summary["duplicates"].append({
                        "type": doc_type_name,
                        "count": len(docs),
                    })

        # Determine overall status
        all_validated = len(summary["missing"]) == 0 and len(summary["draft"]) == 0
        has_issues = len(summary["missing"]) > 0

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=not has_issues,
            severity=RuleSeverity.CRITICAL if has_issues else RuleSeverity.INFO,
            message=self._format_summary(summary),
            category=self.category,
            details=summary,
        )

    def _format_summary(self, summary: Dict[str, Any]) -> str:
        """Format the summary into a human-readable message."""
        parts = []
        if summary["validated"]:
            parts.append(f"{len(summary['validated'])} validated")
        if summary["draft"]:
            parts.append(f"{len(summary['draft'])} draft")
        if summary["uploaded"]:
            parts.append(f"{len(summary['uploaded'])} pending")
        if summary["missing"]:
            parts.append(f"{len(summary['missing'])} missing")
        if summary["duplicates"]:
            parts.append(f"{len(summary['duplicates'])} with duplicates")

        return f"Document status: {', '.join(parts)}"
