"""Rules Engine Core for Bill of Lading Compliance.

This module provides a deterministic rules engine that evaluates
compliance rules against parsed Bill of Lading data.

The engine supports the following condition types:
- NOT_NULL: Field must have a non-empty value
- IN_LIST: Field value must be in a specified list
- EQUALS: Field value must equal a specified value
- RANGE: Field value must be within min/max bounds
- DATE_ORDER: Date field must be before another date field
- REGEX: Field value must match a regex pattern

Works with ALL product types:
- Horn & Hoof (HS 0506/0507)
- Agricultural products
- General cargo
"""

import re
import logging
from enum import Enum
from datetime import date
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ...schemas.bol import CanonicalBoL

logger = logging.getLogger(__name__)


class ConditionType(str, Enum):
    """Types of conditions that can be evaluated."""

    NOT_NULL = "NOT_NULL"  # Field must have a value
    IN_LIST = "IN_LIST"  # Field value must be in list
    EQUALS = "EQUALS"  # Field value must equal specified value
    RANGE = "RANGE"  # Field value must be within range
    DATE_ORDER = "DATE_ORDER"  # Date must be before another date
    REGEX = "REGEX"  # Field must match regex pattern
    CUSTOM = "CUSTOM"  # Custom validator function (value = validator name)


class ComplianceRule(BaseModel):
    """Definition of a compliance rule.

    Attributes:
        id: Unique rule identifier (e.g., "BOL-001")
        name: Human-readable rule name
        field: Dot-notation path to field (e.g., "shipper.name")
        condition: Type of condition to evaluate
        value: Value for comparison (depends on condition type)
        severity: ERROR, WARNING, or INFO
        message: Message to display when rule fails
    """

    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    field: str = Field(..., description="Dot-notation path to field")
    condition: ConditionType = Field(..., description="Condition type to evaluate")
    value: Optional[Any] = Field(None, description="Value for comparison")
    severity: str = Field(default="WARNING", description="ERROR, WARNING, or INFO")
    message: str = Field(..., description="Message when rule fails")


class RuleResult(BaseModel):
    """Result of evaluating a single rule.

    Attributes:
        rule_id: ID of the rule that was evaluated
        rule_name: Name of the rule
        passed: Whether the rule passed
        message: Explanation message
        severity: Severity level of the rule
        field_path: The field that was evaluated
    """

    rule_id: str = Field(..., description="Rule identifier")
    rule_name: str = Field(..., description="Rule name")
    passed: bool = Field(..., description="Whether the rule passed")
    message: str = Field(..., description="Result message")
    severity: str = Field(..., description="Rule severity level")
    field_path: str = Field(default="", description="Field path evaluated")


class ComplianceEvaluationResult(BaseModel):
    """Result of evaluating all compliance rules.

    Attributes:
        decision: Overall compliance decision (APPROVE, HOLD, REJECT)
        results: Individual rule results

    Note:
        This class implements list-like behavior for backward compatibility
        with code that expects evaluate() to return a list of RuleResult.
    """

    decision: str = Field(..., description="APPROVE, HOLD, or REJECT")
    results: List[RuleResult] = Field(..., description="Individual rule results")

    def __iter__(self):
        """Allow iterating over results for backward compatibility."""
        return iter(self.results)

    def __len__(self):
        """Return number of results for backward compatibility."""
        return len(self.results)

    def __getitem__(self, index):
        """Allow indexing results for backward compatibility."""
        return self.results[index]

    def __eq__(self, other):
        """Allow comparison with list for backward compatibility."""
        if isinstance(other, list):
            return self.results == other
        return super().__eq__(other)


class RulesEngine:
    """Deterministic rules engine for BoL compliance.

    This engine evaluates a list of compliance rules against a
    parsed Bill of Lading and returns individual rule results
    plus an overall compliance decision.

    Usage:
        # Option 1: Rules at construction
        engine = RulesEngine(rules)
        results = engine.evaluate(bol)

        # Option 2: Rules at evaluation
        engine = RulesEngine()
        results = engine.evaluate(bol, rules)

        # Get decision
        decision = engine.get_compliance_decision(results)
    """

    def __init__(self, rules: Optional[List[ComplianceRule]] = None):
        """Initialize the rules engine.

        Args:
            rules: Optional list of compliance rules (can also be passed to evaluate)
        """
        self.rules = rules or []

    def evaluate(
        self, bol: CanonicalBoL, rules: Optional[List[ComplianceRule]] = None
    ) -> "ComplianceEvaluationResult":
        """Evaluate all rules against BoL data.

        Args:
            bol: Parsed Bill of Lading data
            rules: Optional rules to use (overrides constructor rules)

        Returns:
            ComplianceEvaluationResult with results and decision
        """
        rules_to_use = rules if rules is not None else self.rules
        results = []
        for rule in rules_to_use:
            try:
                result = self._evaluate_rule(rule, bol)
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
                results.append(
                    RuleResult(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        passed=False,
                        message=f"Rule evaluation error: {str(e)}",
                        severity=rule.severity,
                        field_path=rule.field,
                    )
                )

        # Calculate decision
        decision = self.get_compliance_decision(results)

        return ComplianceEvaluationResult(decision=decision, results=results)

    def _evaluate_rule(self, rule: ComplianceRule, bol: CanonicalBoL) -> RuleResult:
        """Evaluate a single rule against BoL data.

        Args:
            rule: The compliance rule to evaluate
            bol: Parsed Bill of Lading data

        Returns:
            RuleResult indicating pass/fail
        """
        field_value = self._get_field_value(bol, rule.field)

        evaluators = {
            ConditionType.NOT_NULL: self._eval_not_null,
            ConditionType.IN_LIST: self._eval_in_list,
            ConditionType.EQUALS: self._eval_equals,
            ConditionType.RANGE: self._eval_range,
            ConditionType.DATE_ORDER: self._eval_date_order,
            ConditionType.REGEX: self._eval_regex,
            ConditionType.CUSTOM: self._eval_custom,
        }

        evaluator = evaluators.get(rule.condition)
        if not evaluator:
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=False,
                message=f"Unknown condition type: {rule.condition}",
                severity=rule.severity,
                field_path=rule.field,
            )

        passed, message = evaluator(field_value, rule.value, bol)

        return RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=passed,
            message=message if not passed else f"{rule.name}: OK",
            severity=rule.severity,
            field_path=rule.field,
        )

    def _get_field_value(self, bol: CanonicalBoL, field_path: str) -> Any:
        """Get nested field value using dot notation.

        Supports array access with [index] notation.
        e.g., "shipper.name", "containers[0].number", "cargo[0].hs_code"

        Args:
            bol: The BoL to extract from
            field_path: Dot-notation path (e.g., "shipper.name")

        Returns:
            The field value or None if not found
        """
        try:
            # Parse the field path
            parts = self._parse_field_path(field_path)
            current = bol

            for part in parts:
                if current is None:
                    return None

                if isinstance(part, tuple):
                    # Array access: (field_name, index)
                    field_name, index = part
                    current = getattr(current, field_name, None)
                    if current is None or not isinstance(current, list):
                        return None
                    if index >= len(current):
                        return None
                    current = current[index]
                else:
                    # Simple field access
                    current = getattr(current, part, None)

            return current
        except Exception as e:
            logger.debug(f"Error getting field {field_path}: {e}")
            return None

    def _parse_field_path(self, path: str) -> List[Union[str, tuple]]:
        """Parse field path into parts.

        Args:
            path: Dot-notation path like "containers[0].number"

        Returns:
            List of parts, with array access as tuples
        """
        parts = []
        # Split by dots
        segments = path.split(".")

        for segment in segments:
            # Check for array access
            match = re.match(r"(\w+)\[(\d+)\]", segment)
            if match:
                field_name = match.group(1)
                index = int(match.group(2))
                parts.append((field_name, index))
            else:
                parts.append(segment)

        return parts

    def _eval_not_null(
        self, value: Any, rule_value: Any, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Evaluate NOT_NULL condition."""
        if value is None:
            return False, "Value is missing"
        if isinstance(value, str) and not value.strip():
            return False, "Value is empty"
        if isinstance(value, list) and len(value) == 0:
            return False, "List is empty"
        return True, "Value present"

    def _eval_in_list(
        self, value: Any, allowed_values: List[Any], bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Evaluate IN_LIST condition."""
        if value is None:
            return False, "Value is missing"
        if not isinstance(allowed_values, list):
            return False, "Invalid rule: allowed_values must be a list"
        if value in allowed_values:
            return True, "Value in allowed list"
        return False, f"Value '{value}' not in allowed list"

    def _eval_equals(
        self, value: Any, expected: Any, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Evaluate EQUALS condition."""
        if value is None:
            return False, "Value is missing"
        if value == expected:
            return True, f"Value equals '{expected}'"
        return False, f"Value '{value}' does not equal '{expected}'"

    def _eval_range(
        self, value: Any, range_def: Dict[str, float], bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Evaluate RANGE condition."""
        if value is None:
            return False, "Value is missing"
        if not isinstance(range_def, dict):
            return False, "Invalid rule: range must be a dict with min/max"

        try:
            num_value = float(value)
        except (TypeError, ValueError):
            return False, f"Value '{value}' is not numeric"

        min_val = range_def.get("min")
        max_val = range_def.get("max")

        if min_val is not None and num_value < min_val:
            return False, f"Value {num_value} is below minimum {min_val}"
        if max_val is not None and num_value > max_val:
            return False, f"Value {num_value} is above maximum {max_val}"

        return True, f"Value {num_value} is within range"

    def _eval_regex(
        self, value: Any, pattern: str, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Evaluate REGEX condition."""
        if value is None:
            return False, "Value is missing"
        if not isinstance(value, str):
            value = str(value)

        try:
            if re.match(pattern, value):
                return True, "Pattern matches"
            return False, f"Value '{value}' does not match pattern '{pattern}'"
        except re.error as e:
            return False, f"Invalid regex pattern: {e}"

    def _eval_date_order(
        self, value: Any, other_field: str, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Evaluate DATE_ORDER condition.

        Checks that the field value (date) is before another date field.

        Args:
            value: The date value of the primary field
            other_field: Name of the field to compare against
            bol: The BoL containing both fields
        """
        if value is None:
            return False, "Primary date is missing"

        other_value = self._get_field_value(bol, other_field)
        if other_value is None:
            return False, f"Comparison date '{other_field}' is missing"

        # Ensure both are date objects
        if not isinstance(value, date):
            return False, f"Primary value is not a date: {type(value)}"
        if not isinstance(other_value, date):
            return False, f"Comparison value is not a date: {type(other_value)}"

        if value <= other_value:
            return True, f"Date {value} is before or equal to {other_value}"
        return False, f"Date {value} is after {other_value}"

    def get_compliance_decision(self, results: List[RuleResult]) -> str:
        """Determine overall compliance decision from rule results.

        Decision logic:
        - APPROVE: All rules passed
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

    def _eval_custom(
        self, value: Any, validator_name: str, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Evaluate CUSTOM condition using named validators.

        Args:
            value: The field value
            validator_name: Name of the custom validator to use
            bol: The full BoL for cross-field validation
        """
        validators = {
            "weight_tolerance": self._validate_weight_tolerance,
            "vet_cert_before_etd": self._validate_vet_cert_before_etd,
            "approved_consignee": self._validate_approved_consignee,
        }

        validator = validators.get(validator_name)
        if not validator:
            return False, f"Unknown custom validator: {validator_name}"

        return validator(value, bol)

    def _validate_weight_tolerance(
        self, container_weight: Any, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Validate weight tolerance between container and cargo.

        Weight difference should be within 5% tolerance.
        """
        if container_weight is None:
            return True, "No container weight to validate"

        # Get total cargo weight
        cargo_weight = bol.get_total_weight_kg()
        if cargo_weight is None:
            return True, "No cargo weight to compare"

        try:
            container_wt = float(container_weight)
            cargo_wt = float(cargo_weight)
        except (TypeError, ValueError):
            return False, "Invalid weight values"

        if cargo_wt == 0:
            return True, "No cargo weight declared"

        # Calculate percentage difference
        diff_percent = abs(container_wt - cargo_wt) / cargo_wt * 100

        if diff_percent <= 5.0:
            return True, f"Weight within tolerance ({diff_percent:.1f}%)"
        return False, f"Weight difference {diff_percent:.1f}% exceeds 5% tolerance"

    def _validate_vet_cert_before_etd(
        self, vet_cert_date: Any, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Validate veterinary certificate date is before vessel departure.

        For animal products, vet cert must be issued before vessel ETD.
        """
        if vet_cert_date is None:
            return False, "Veterinary certificate date is missing"

        # ETD is typically shipped_on_board_date
        etd = bol.shipped_on_board_date
        if etd is None:
            # Can't validate without ETD
            return True, "No ETD to validate against"

        if not isinstance(vet_cert_date, date):
            return False, f"Vet cert date is not a date: {type(vet_cert_date)}"

        if vet_cert_date <= etd:
            return True, f"Vet cert date {vet_cert_date} is valid (before ETD {etd})"
        return False, f"Vet cert date {vet_cert_date} is after vessel ETD {etd}"

    def _validate_approved_consignee(
        self, consignee_name: Any, bol: CanonicalBoL
    ) -> tuple[bool, str]:
        """Validate consignee is in approved list for Horn & Hoof products."""
        if consignee_name is None:
            return False, "Consignee name is missing"

        # Import the approved list (avoid circular import)
        from .compliance_rules import APPROVED_HORN_HOOF_CONSIGNEES

        # Normalize for comparison
        name_upper = str(consignee_name).upper().strip()

        for approved in APPROVED_HORN_HOOF_CONSIGNEES:
            if approved.upper() in name_upper or name_upper in approved.upper():
                return True, f"Consignee '{consignee_name}' is approved"

        return False, f"Consignee '{consignee_name}' not in approved list"
