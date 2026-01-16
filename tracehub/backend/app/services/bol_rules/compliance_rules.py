"""Standard Compliance Rules for Bill of Lading Documents.

This module defines the standard compliance rules used to validate
Bill of Lading documents. These rules are deterministic (no AI/ML).

Rules are organized by severity:
- ERROR: Critical issues that prevent processing (REJECT)
- WARNING: Issues that require review but can proceed (HOLD)
- INFO: Informational checks that don't affect processing

Works with ALL product types:
- Horn & Hoof (HS 0506/0507)
- Agricultural products
- General cargo
"""

from typing import List

from .engine import ComplianceRule, ConditionType, RuleResult


# Standard BoL compliance rules
STANDARD_BOL_RULES: List[ComplianceRule] = [
    # === ERROR Severity Rules (Rejection triggers) ===

    ComplianceRule(
        id="BOL-001",
        name="Shipper Name Required",
        field="shipper.name",
        condition=ConditionType.REGEX,
        value=r"^(?!Unknown Shipper$).+$",  # Not placeholder "Unknown Shipper"
        severity="ERROR",
        message="Valid shipper name is required (not placeholder)",
    ),

    ComplianceRule(
        id="BOL-002",
        name="Consignee Name Required",
        field="consignee.name",
        condition=ConditionType.REGEX,
        value=r"^(?!Unknown Consignee$).+$",  # Not placeholder "Unknown Consignee"
        severity="ERROR",
        message="Valid consignee name is required (not placeholder)",
    ),

    ComplianceRule(
        id="BOL-004",
        name="BoL Number Required",
        field="bol_number",
        condition=ConditionType.REGEX,
        value=r"^(?!UNKNOWN$).+$",  # Not placeholder "UNKNOWN"
        severity="ERROR",
        message="Valid Bill of Lading number is required",
    ),

    # === WARNING Severity Rules (Hold triggers) ===

    ComplianceRule(
        id="BOL-003",
        name="Container ISO 6346 Format",
        field="containers[0].number",
        condition=ConditionType.REGEX,
        value=r"^[A-Z]{4}\d{7}$",
        severity="WARNING",
        message="Container number should match ISO 6346 format (4 letters + 7 digits)",
    ),

    ComplianceRule(
        id="BOL-005",
        name="Port of Loading Required",
        field="port_of_loading",
        condition=ConditionType.NOT_NULL,
        severity="WARNING",
        message="Port of loading should be specified for routing",
    ),

    ComplianceRule(
        id="BOL-006",
        name="Cargo Description Required",
        field="cargo",
        condition=ConditionType.NOT_NULL,
        severity="WARNING",
        message="At least one cargo item should be specified",
    ),

    ComplianceRule(
        id="BOL-007",
        name="Container Required",
        field="containers",
        condition=ConditionType.NOT_NULL,
        severity="WARNING",
        message="At least one container should be specified",
    ),

    ComplianceRule(
        id="BOL-008",
        name="Port of Discharge Required",
        field="port_of_discharge",
        condition=ConditionType.NOT_NULL,
        severity="WARNING",
        message="Port of discharge should be specified for delivery",
    ),

    # === INFO Severity Rules (Informational) ===

    ComplianceRule(
        id="BOL-009",
        name="Vessel Name Present",
        field="vessel_name",
        condition=ConditionType.NOT_NULL,
        severity="INFO",
        message="Vessel name helps with shipment tracking",
    ),

    ComplianceRule(
        id="BOL-010",
        name="Voyage Number Present",
        field="voyage_number",
        condition=ConditionType.NOT_NULL,
        severity="INFO",
        message="Voyage number helps with shipment tracking",
    ),

    ComplianceRule(
        id="BOL-011",
        name="Confidence Score Threshold",
        field="confidence_score",
        condition=ConditionType.RANGE,
        value={"min": 0.5, "max": 1.0},
        severity="INFO",
        message="Low parser confidence - manual review recommended",
    ),
]


def get_compliance_decision(results: List[RuleResult]) -> str:
    """Determine overall compliance decision from rule results.

    Decision logic:
    - APPROVE: All rules passed OR only INFO failures
    - REJECT: At least one ERROR severity rule failed
    - HOLD: At least one WARNING severity rule failed (no ERROR failures)

    Args:
        results: List of rule evaluation results

    Returns:
        "APPROVE", "HOLD", or "REJECT"
    """
    if not results:
        return "APPROVE"

    error_failures = [
        r for r in results if not r.passed and r.severity == "ERROR"
    ]
    warning_failures = [
        r for r in results if not r.passed and r.severity == "WARNING"
    ]

    if error_failures:
        return "REJECT"
    if warning_failures:
        return "HOLD"
    return "APPROVE"


def get_rules_for_product_type(product_type: str = None) -> List[ComplianceRule]:
    """Get applicable rules for a specific product type.

    Currently all product types use the same standard rules.
    This function exists for future extensibility when product-specific
    rules may be needed.

    Args:
        product_type: Optional product type (e.g., "horn_hoof", "agricultural")

    Returns:
        List of applicable compliance rules
    """
    # For now, all products use the same rules
    # Future: Add product-specific rules for EUDR compliance, etc.
    return STANDARD_BOL_RULES


def format_compliance_report(results: List[RuleResult]) -> str:
    """Format rule results into a human-readable report.

    Args:
        results: List of rule evaluation results

    Returns:
        Formatted report string
    """
    if not results:
        return "No compliance rules evaluated."

    decision = get_compliance_decision(results)
    lines = [
        f"Compliance Decision: {decision}",
        "-" * 40,
    ]

    # Group by severity
    errors = [r for r in results if not r.passed and r.severity == "ERROR"]
    warnings = [r for r in results if not r.passed and r.severity == "WARNING"]
    info = [r for r in results if not r.passed and r.severity == "INFO"]
    passed = [r for r in results if r.passed]

    if errors:
        lines.append("\nERRORS (Must Fix):")
        for r in errors:
            lines.append(f"  - [{r.rule_id}] {r.rule_name}: {r.message}")

    if warnings:
        lines.append("\nWARNINGS (Review Required):")
        for r in warnings:
            lines.append(f"  - [{r.rule_id}] {r.rule_name}: {r.message}")

    if info:
        lines.append("\nINFO:")
        for r in info:
            lines.append(f"  - [{r.rule_id}] {r.rule_name}: {r.message}")

    lines.append(f"\nPassed: {len(passed)}/{len(results)} rules")

    return "\n".join(lines)
