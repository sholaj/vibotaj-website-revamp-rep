"""Horn & Hoof specific validation rules.

Rules that only apply to Horn & Hoof shipments (HS 0506/0507).
These products require special veterinary documentation.
"""

from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext
from ...models.document import DocumentType


class VetCertIssueDateRule(ValidationRule):
    """Veterinary Health Certificate issue date must be on/before ship date.

    For Horn & Hoof exports, the vet cert must be issued before the
    shipment departs to ensure it's valid at time of export.
    """

    rule_id = "HORN_HOOF_002"
    name = "Vet Certificate Issue Date"
    description = "Veterinary Health Certificate must be issued on or before departure"
    severity = RuleSeverity.ERROR
    category = RuleCategory.DATE
    applies_to = ["horn_hoof"]

    def validate(self, context: ValidationContext) -> RuleResult:
        """Check vet cert issue date against ship date (ETD).

        Returns:
            RuleResult - pass if date is valid, fail if after ETD
        """
        vet_certs = context.get_documents_of_type(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE
        )

        if not vet_certs:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="No veterinary certificate to validate",
                category=self.category,
            )

        vet_cert = vet_certs[0]
        issue_date = vet_cert.document_date
        ship_date = context.shipment.etd

        if not issue_date:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message="Veterinary certificate missing issue date",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id),
            )

        # Convert datetime to date for comparison if needed
        if hasattr(issue_date, 'date'):
            issue_date = issue_date.date()
        if ship_date and hasattr(ship_date, 'date'):
            ship_date = ship_date.date()

        if ship_date and issue_date > ship_date:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Vet certificate issued ({issue_date}) after ship date ({ship_date})",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id),
                details={
                    "issue_date": str(issue_date),
                    "ship_date": str(ship_date),
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="Vet certificate issue date valid",
            category=self.category,
        )


class VetCertAuthorizedSignerRule(ValidationRule):
    """Veterinary Health Certificate must be from authorized Nigerian authority.

    For Horn & Hoof exports from Nigeria, the vet cert should be
    issued by recognized Nigerian veterinary authorities.
    """

    rule_id = "HORN_HOOF_003"
    name = "Vet Certificate Authorized Signer"
    description = "Certificate must be from Nigerian veterinary authority"
    severity = RuleSeverity.WARNING
    category = RuleCategory.CONTENT
    applies_to = ["horn_hoof"]

    # Keywords that indicate authorized Nigerian authority
    AUTHORIZED_TERMS = ["nigeria", "nigerian", "nvri", "federal"]

    def validate(self, context: ValidationContext) -> RuleResult:
        """Check vet cert issuing authority contains expected keywords.

        Returns:
            RuleResult - warning if authority doesn't match expected
        """
        vet_certs = context.get_documents_of_type(
            DocumentType.VETERINARY_HEALTH_CERTIFICATE
        )

        if not vet_certs:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="No veterinary certificate to validate",
                category=self.category,
            )

        vet_cert = vet_certs[0]
        issuer = vet_cert.issuer or ""

        if not issuer:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message="Veterinary certificate missing issuing authority",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id),
            )

        issuer_lower = issuer.lower()
        is_authorized = any(term in issuer_lower for term in self.AUTHORIZED_TERMS)

        if not is_authorized:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Issuing authority '{issuer}' may not be authorized Nigerian authority",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
                document_id=str(vet_cert.id),
                details={
                    "issuer": issuer,
                    "expected_terms": self.AUTHORIZED_TERMS,
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="Vet certificate from authorized Nigerian authority",
            category=self.category,
        )
