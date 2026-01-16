"""Bill of Lading Rules Engine Package.

This package provides a deterministic rules engine for evaluating
compliance rules against parsed Bill of Lading data.

Components:
- engine.py: Core rules engine with condition evaluators
- compliance_rules.py: Standard BoL compliance rule definitions
"""

from .engine import (
    RulesEngine,
    ConditionType,
    ComplianceRule,
    RuleResult,
)
from .compliance_rules import (
    STANDARD_BOL_RULES,
    get_compliance_decision,
    get_rules_for_product_type,
    format_compliance_report,
)

__all__ = [
    "RulesEngine",
    "ConditionType",
    "ComplianceRule",
    "RuleResult",
    "STANDARD_BOL_RULES",
    "get_compliance_decision",
    "get_rules_for_product_type",
    "format_compliance_report",
]
