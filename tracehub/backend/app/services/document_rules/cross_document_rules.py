"""Cross-Document Validation Rules.

Rules that validate consistency across multiple documents in a shipment.
These rules ensure that information like container numbers, weights,
HS codes, and dates are consistent across all documents.

PRP: Document Validation & Compliance Enhancement
"""

import logging
from typing import List, Dict, Any, Optional, Set
from datetime import date

from .base import ValidationRule, RuleResult, RuleSeverity, RuleCategory
from .context import ValidationContext

logger = logging.getLogger(__name__)


class ContainerNumberConsistencyRule(ValidationRule):
    """Validates container numbers are consistent across documents.

    Checks that container numbers in B/L match those in packing list,
    fumigation certificate, and other container-related documents.
    """

    rule_id = "XD_001"
    name = "Container Number Consistency"
    description = "Container numbers must match across B/L, packing list, and certificates"
    severity = RuleSeverity.ERROR
    category = RuleCategory.CROSS_FIELD

    def validate(self, context: ValidationContext) -> List[RuleResult]:
        """Check container number consistency across documents."""
        from ...models.document import DocumentType

        results = []

        # Get container numbers from B/L
        bol_containers = self._get_containers_from_bol(context)

        # Compare with packing list
        packing_containers = self._get_containers_from_packing_list(context)
        if bol_containers and packing_containers:
            mismatches = self._find_mismatches(bol_containers, packing_containers)
            if mismatches:
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_PL",
                    rule_name=f"{self.name} (B/L vs Packing List)",
                    passed=False,
                    severity=self.severity,
                    message=f"Container mismatch between B/L and Packing List: {', '.join(mismatches)}",
                    category=self.category,
                    details={
                        "bol_containers": list(bol_containers),
                        "packing_containers": list(packing_containers),
                        "mismatches": list(mismatches),
                    },
                ))
            else:
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_PL",
                    rule_name=f"{self.name} (B/L vs Packing List)",
                    passed=True,
                    severity=self.severity,
                    message="Container numbers match between B/L and Packing List",
                    category=self.category,
                ))

        # Compare with fumigation certificate
        fumigation_containers = self._get_containers_from_fumigation(context)
        if bol_containers and fumigation_containers:
            # Fumigation containers should be a subset of B/L containers
            extra = fumigation_containers - bol_containers
            if extra:
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_FC",
                    rule_name=f"{self.name} (Fumigation Cert)",
                    passed=False,
                    severity=RuleSeverity.WARNING,
                    message=f"Fumigation cert references containers not in B/L: {', '.join(extra)}",
                    category=self.category,
                    details={"extra_containers": list(extra)},
                ))

        return results if results else [RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="Container numbers are consistent across documents",
            category=self.category,
        )]

    def _get_containers_from_bol(self, context: ValidationContext) -> Set[str]:
        """Extract container numbers from B/L."""
        from ...models.document import DocumentType

        containers = set()
        for doc in context.get_documents_of_type(DocumentType.BILL_OF_LADING):
            if doc.bol_parsed_data and "containers" in doc.bol_parsed_data:
                for container in doc.bol_parsed_data["containers"]:
                    if "number" in container:
                        containers.add(container["number"].upper().replace(" ", ""))
            if doc.extracted_container_number:
                containers.add(doc.extracted_container_number.upper().replace(" ", ""))
        return containers

    def _get_containers_from_packing_list(self, context: ValidationContext) -> Set[str]:
        """Extract container numbers from packing list."""
        from ...models.document import DocumentType

        containers = set()
        for doc in context.get_documents_of_type(DocumentType.PACKING_LIST):
            if doc.canonical_data and "fields" in doc.canonical_data:
                fields = doc.canonical_data["fields"]
                if "container_numbers" in fields:
                    for num in fields["container_numbers"]:
                        containers.add(num.upper().replace(" ", ""))
        return containers

    def _get_containers_from_fumigation(self, context: ValidationContext) -> Set[str]:
        """Extract container numbers from fumigation certificate."""
        from ...models.document import DocumentType

        containers = set()
        for doc in context.get_documents_of_type(DocumentType.FUMIGATION_CERTIFICATE):
            if doc.canonical_data and "fields" in doc.canonical_data:
                fields = doc.canonical_data["fields"]
                if "container_numbers" in fields:
                    for num in fields["container_numbers"]:
                        containers.add(num.upper().replace(" ", ""))
        return containers

    def _find_mismatches(self, set1: Set[str], set2: Set[str]) -> Set[str]:
        """Find elements that are in one set but not the other."""
        return (set1 - set2) | (set2 - set1)


class WeightConsistencyRule(ValidationRule):
    """Validates weights are consistent across documents.

    Checks that gross/net weights in B/L match those in packing list
    and commercial invoice within a tolerance (default 5%).
    """

    rule_id = "XD_002"
    name = "Weight Consistency"
    description = "Weights must match across B/L, packing list, and invoice within tolerance"
    severity = RuleSeverity.WARNING
    category = RuleCategory.CROSS_FIELD
    tolerance = 0.05  # 5% tolerance

    def validate(self, context: ValidationContext) -> List[RuleResult]:
        """Check weight consistency across documents."""
        from ...models.document import DocumentType

        results = []

        # Get weights from B/L
        bol_weight = self._get_weight_from_bol(context)

        # Compare with packing list
        packing_weight = self._get_weight_from_packing_list(context)
        if bol_weight is not None and packing_weight is not None:
            diff_pct = abs(bol_weight - packing_weight) / max(bol_weight, packing_weight)
            if diff_pct > self.tolerance:
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_PL",
                    rule_name=f"{self.name} (B/L vs Packing List)",
                    passed=False,
                    severity=self.severity,
                    message=f"Weight differs by {diff_pct:.1%}: B/L={bol_weight:.1f}kg, PL={packing_weight:.1f}kg",
                    category=self.category,
                    details={
                        "bol_weight_kg": bol_weight,
                        "packing_weight_kg": packing_weight,
                        "difference_percent": diff_pct * 100,
                    },
                ))
            else:
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_PL",
                    rule_name=f"{self.name} (B/L vs Packing List)",
                    passed=True,
                    severity=self.severity,
                    message=f"Weights match within tolerance ({diff_pct:.1%})",
                    category=self.category,
                ))

        # Compare with invoice
        invoice_weight = self._get_weight_from_invoice(context)
        if packing_weight is not None and invoice_weight is not None:
            diff_pct = abs(packing_weight - invoice_weight) / max(packing_weight, invoice_weight)
            if diff_pct > self.tolerance:
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_INV",
                    rule_name=f"{self.name} (Packing List vs Invoice)",
                    passed=False,
                    severity=self.severity,
                    message=f"Weight differs by {diff_pct:.1%}: PL={packing_weight:.1f}kg, Invoice={invoice_weight:.1f}kg",
                    category=self.category,
                ))

        return results if results else [RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="Weights are consistent across documents",
            category=self.category,
        )]

    def _get_weight_from_bol(self, context: ValidationContext) -> Optional[float]:
        """Extract gross weight from B/L."""
        from ...models.document import DocumentType

        for doc in context.get_documents_of_type(DocumentType.BILL_OF_LADING):
            if doc.bol_parsed_data and "cargo" in doc.bol_parsed_data:
                total = 0.0
                for cargo in doc.bol_parsed_data["cargo"]:
                    if "gross_weight_kg" in cargo and cargo["gross_weight_kg"]:
                        total += cargo["gross_weight_kg"]
                if total > 0:
                    return total
        return None

    def _get_weight_from_packing_list(self, context: ValidationContext) -> Optional[float]:
        """Extract gross weight from packing list."""
        from ...models.document import DocumentType

        for doc in context.get_documents_of_type(DocumentType.PACKING_LIST):
            if doc.canonical_data and "fields" in doc.canonical_data:
                fields = doc.canonical_data["fields"]
                if "weight" in fields:
                    weight = fields["weight"]
                    if isinstance(weight, dict) and "gross_kg" in weight:
                        return weight["gross_kg"]
                    elif isinstance(weight, (int, float)):
                        return float(weight)
        return None

    def _get_weight_from_invoice(self, context: ValidationContext) -> Optional[float]:
        """Extract weight from commercial invoice."""
        from ...models.document import DocumentType

        for doc in context.get_documents_of_type(DocumentType.COMMERCIAL_INVOICE):
            if doc.canonical_data and "fields" in doc.canonical_data:
                fields = doc.canonical_data["fields"]
                if "weight" in fields:
                    weight = fields["weight"]
                    if isinstance(weight, dict) and "gross_kg" in weight:
                        return weight["gross_kg"]
        return None


class HSCodeConsistencyRule(ValidationRule):
    """Validates HS codes are consistent across documents.

    Checks that HS codes in B/L match those in Certificate of Origin
    and Commercial Invoice.
    """

    rule_id = "XD_003"
    name = "HS Code Consistency"
    description = "HS codes must match across B/L, Certificate of Origin, and Invoice"
    severity = RuleSeverity.ERROR
    category = RuleCategory.CROSS_FIELD

    def validate(self, context: ValidationContext) -> List[RuleResult]:
        """Check HS code consistency across documents."""
        from ...models.document import DocumentType

        results = []

        # Get HS codes from B/L
        bol_hs_codes = self._get_hs_codes_from_bol(context)

        # Compare with Certificate of Origin
        coo_hs_codes = self._get_hs_codes_from_coo(context)
        if bol_hs_codes and coo_hs_codes:
            # HS codes should have common prefixes (first 4-6 digits)
            if not self._hs_codes_compatible(bol_hs_codes, coo_hs_codes):
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_COO",
                    rule_name=f"{self.name} (B/L vs Certificate of Origin)",
                    passed=False,
                    severity=self.severity,
                    message=f"HS code mismatch: B/L has {bol_hs_codes}, CoO has {coo_hs_codes}",
                    category=self.category,
                    details={
                        "bol_hs_codes": list(bol_hs_codes),
                        "coo_hs_codes": list(coo_hs_codes),
                    },
                ))
            else:
                results.append(RuleResult(
                    rule_id=f"{self.rule_id}_COO",
                    rule_name=f"{self.name} (B/L vs Certificate of Origin)",
                    passed=True,
                    severity=self.severity,
                    message="HS codes are compatible between B/L and Certificate of Origin",
                    category=self.category,
                ))

        return results if results else [RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="HS codes are consistent across documents",
            category=self.category,
        )]

    def _get_hs_codes_from_bol(self, context: ValidationContext) -> Set[str]:
        """Extract HS codes from B/L."""
        from ...models.document import DocumentType

        hs_codes = set()
        for doc in context.get_documents_of_type(DocumentType.BILL_OF_LADING):
            if doc.bol_parsed_data and "cargo" in doc.bol_parsed_data:
                for cargo in doc.bol_parsed_data["cargo"]:
                    if "hs_code" in cargo and cargo["hs_code"]:
                        hs_codes.add(cargo["hs_code"].replace(".", "").replace(" ", ""))
        return hs_codes

    def _get_hs_codes_from_coo(self, context: ValidationContext) -> Set[str]:
        """Extract HS codes from Certificate of Origin."""
        from ...models.document import DocumentType

        hs_codes = set()
        for doc in context.get_documents_of_type(DocumentType.CERTIFICATE_OF_ORIGIN):
            if doc.canonical_data and "fields" in doc.canonical_data:
                fields = doc.canonical_data["fields"]
                if "hs_codes" in fields:
                    for code in fields["hs_codes"]:
                        hs_codes.add(code.replace(".", "").replace(" ", ""))
        return hs_codes

    def _hs_codes_compatible(self, set1: Set[str], set2: Set[str]) -> bool:
        """Check if HS codes are compatible (share first 4 digits)."""
        prefixes1 = {code[:4] for code in set1 if len(code) >= 4}
        prefixes2 = {code[:4] for code in set2 if len(code) >= 4}
        return bool(prefixes1 & prefixes2)


class VetCertDateValidationRule(ValidationRule):
    """Validates veterinary certificate date against vessel ETD.

    For Horn & Hoof products, the vet cert issue date must be
    on or before the vessel departure date (ETD).
    """

    rule_id = "XD_004"
    name = "Veterinary Certificate Date Validation"
    description = "Vet cert must be issued before vessel departure (ETD)"
    severity = RuleSeverity.ERROR
    category = RuleCategory.CROSS_FIELD
    applies_to = ["horn_hoof"]

    def validate(self, context: ValidationContext) -> RuleResult:
        """Check vet cert date is before ETD."""
        from ...models.document import DocumentType

        # Get ETD from B/L or shipment
        etd = self._get_etd(context)
        if not etd:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=RuleSeverity.INFO,
                message="No ETD available for comparison",
                category=self.category,
            )

        # Get vet cert issue date
        vet_cert_date = self._get_vet_cert_date(context)
        if not vet_cert_date:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message="Veterinary certificate missing issue date",
                category=self.category,
                document_type=DocumentType.VETERINARY_HEALTH_CERTIFICATE.value,
            )

        # Compare dates
        if vet_cert_date <= etd:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=True,
                severity=self.severity,
                message=f"Vet cert date ({vet_cert_date}) is valid (before ETD {etd})",
                category=self.category,
            )
        else:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Vet cert date ({vet_cert_date}) is AFTER vessel ETD ({etd})",
                category=self.category,
                details={"vet_cert_date": str(vet_cert_date), "etd": str(etd)},
            )

    def _get_etd(self, context: ValidationContext) -> Optional[date]:
        """Get ETD from B/L or shipment."""
        from ...models.document import DocumentType

        # Try B/L first
        for doc in context.get_documents_of_type(DocumentType.BILL_OF_LADING):
            if doc.bol_parsed_data and "shipped_on_board_date" in doc.bol_parsed_data:
                date_str = doc.bol_parsed_data["shipped_on_board_date"]
                if date_str:
                    try:
                        return date.fromisoformat(date_str[:10])
                    except (ValueError, TypeError):
                        pass

        # Fall back to shipment ETD
        if context.shipment.etd:
            if isinstance(context.shipment.etd, date):
                return context.shipment.etd
            try:
                return context.shipment.etd.date()
            except AttributeError:
                pass

        return None

    def _get_vet_cert_date(self, context: ValidationContext) -> Optional[date]:
        """Get vet cert issue date."""
        from ...models.document import DocumentType

        for doc in context.get_documents_of_type(DocumentType.VETERINARY_HEALTH_CERTIFICATE):
            # Try canonical data first
            if doc.canonical_data and "fields" in doc.canonical_data:
                fields = doc.canonical_data["fields"]
                if "issue_date" in fields and fields["issue_date"]:
                    try:
                        return date.fromisoformat(str(fields["issue_date"])[:10])
                    except (ValueError, TypeError):
                        pass

            # Fall back to document_date
            if doc.document_date:
                if isinstance(doc.document_date, date):
                    return doc.document_date
                try:
                    return doc.document_date.date()
                except AttributeError:
                    pass

        return None


class AuthorizedSignerPresentRule(ValidationRule):
    """Validates that certificates have authorized signers.

    Checks that veterinary and fumigation certificates have
    an authorized signer identified.
    """

    rule_id = "XD_005"
    name = "Authorized Signer Present"
    description = "Certificates must have an authorized signer"
    severity = RuleSeverity.WARNING
    category = RuleCategory.CROSS_FIELD

    def validate(self, context: ValidationContext) -> List[RuleResult]:
        """Check for authorized signers on certificates."""
        from ...models.document import DocumentType

        results = []
        cert_types = [
            DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            DocumentType.FUMIGATION_CERTIFICATE,
            DocumentType.CERTIFICATE_OF_ORIGIN,
        ]

        for cert_type in cert_types:
            docs = context.get_documents_of_type(cert_type)
            for doc in docs:
                has_signer = False
                signer_name = None

                if doc.canonical_data and "fields" in doc.canonical_data:
                    fields = doc.canonical_data["fields"]
                    signer_name = fields.get("authorized_signer") or fields.get("signer_name")
                    has_signer = bool(signer_name)

                if not has_signer and doc.issuer:
                    has_signer = True
                    signer_name = doc.issuer

                if not has_signer:
                    results.append(RuleResult(
                        rule_id=f"{self.rule_id}_{cert_type.value}",
                        rule_name=f"{self.name} ({cert_type.value})",
                        passed=False,
                        severity=self.severity,
                        message=f"Missing authorized signer on {cert_type.value}",
                        category=self.category,
                        document_type=cert_type.value,
                        document_id=str(doc.id),
                    ))

        return results if results else [RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=self.severity,
            message="All certificates have authorized signers",
            category=self.category,
        )]


# List of all cross-document rules
CROSS_DOCUMENT_RULES = [
    ContainerNumberConsistencyRule(),
    WeightConsistencyRule(),
    HSCodeConsistencyRule(),
    VetCertDateValidationRule(),
    AuthorizedSignerPresentRule(),
]


def get_cross_document_rules(product_type: Optional[str] = None) -> List[ValidationRule]:
    """Get applicable cross-document rules for a product type.

    Args:
        product_type: Optional product type to filter rules

    Returns:
        List of applicable validation rules
    """
    return [
        rule for rule in CROSS_DOCUMENT_RULES
        if rule.should_apply(product_type)
    ]
