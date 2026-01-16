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
    """

    rule_id: str = Field(..., description="Rule identifier")
    rule_name: str = Field(..., description="Rule name")
    passed: bool = Field(..., description="Whether the rule passed")
    message: str = Field(..., description="Result message")
    severity: str = Field(..., description="Rule severity level")


class RulesEngine:
    """Deterministic rules engine for BoL compliance.

    This engine evaluates a list of compliance rules against a
    parsed Bill of Lading and returns individual rule results
    plus an overall compliance decision.

    Usage:
        engine = RulesEngine(rules)
        results = engine.evaluate(bol)
        decision = engine.get_compliance_decision(results)
    """

    def __init__(self, rules: List[ComplianceRule]):
        """Initialize the rules engine.

        Args:
            rules: List of compliance rules to evaluate
        """
        self.rules = rules

    def evaluate(self, bol: CanonicalBoL) -> List[RuleResult]:
        """Evaluate all rules against BoL data.

        Args:
            bol: Parsed Bill of Lading data

        Returns:
            List of RuleResult for each rule evaluated
        """
        results = []
        for rule in self.rules:
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
                    )
                )
        return results

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
        }

        evaluator = evaluators.get(rule.condition)
        if not evaluator:
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=False,
                message=f"Unknown condition type: {rule.condition}",
                severity=rule.severity,
            )

        passed, message = evaluator(field_value, rule.value, bol)

        return RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=passed,
            message=message if not passed else f"{rule.name}: OK",
            severity=rule.severity,
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
