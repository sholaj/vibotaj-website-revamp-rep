"""Tests for Rules Engine Core.

TDD Phase: RED - Write failing tests first

These tests verify the rules engine can:
1. Evaluate different condition types (NOT_NULL, IN_LIST, EQUALS, etc.)
2. Get nested field values using dot notation
3. Calculate compliance decisions (APPROVE/HOLD/REJECT)
4. Handle edge cases gracefully
"""

import pytest
from datetime import date

from app.services.bol_rules.engine import (
    RulesEngine,
    ConditionType,
    ComplianceRule,
    RuleResult,
)
from app.schemas.bol import (
    CanonicalBoL,
    BolParty,
    BolContainer,
    BolCargo,
)


# Test fixtures
@pytest.fixture
def sample_bol():
    """Create a sample BoL for testing."""
    return CanonicalBoL(
        bol_number="APU106546",
        shipper=BolParty(name="VIBOTAJ GLOBAL NIG LTD", country="Nigeria"),
        consignee=BolParty(name="HAGES GMBH", country="Germany"),
        containers=[
            BolContainer(number="MRSU4825686", type="40HC", seal_number="SL123")
        ],
        cargo=[
            BolCargo(description="CATTLE HOOVES", hs_code="0506", gross_weight_kg=20000)
        ],
        vessel_name="MSC MARINA",
        voyage_number="VY2026001",
        port_of_loading="NGAPP",
        port_of_discharge="DEHAM",
        shipped_on_board_date=date(2026, 1, 12),
        confidence_score=0.95,
    )


@pytest.fixture
def incomplete_bol():
    """Create a BoL with missing fields."""
    return CanonicalBoL(
        bol_number="PARTIAL-001",
        shipper=BolParty(name="Test Shipper"),
        consignee=BolParty(name="Test Consignee"),
        containers=[],
        cargo=[],
        confidence_score=0.3,
    )


class TestConditionType:
    """Test condition type enumeration."""

    def test_condition_types_defined(self):
        """All condition types should be defined."""
        assert ConditionType.NOT_NULL
        assert ConditionType.IN_LIST
        assert ConditionType.EQUALS
        assert ConditionType.RANGE
        assert ConditionType.DATE_ORDER
        assert ConditionType.REGEX


class TestComplianceRule:
    """Test compliance rule model."""

    def test_rule_creation(self):
        """Should create rule with all fields."""
        rule = ComplianceRule(
            id="TEST-001",
            name="Test Rule",
            field="shipper.name",
            condition=ConditionType.NOT_NULL,
            severity="ERROR",
            message="Shipper name is required",
        )
        assert rule.id == "TEST-001"
        assert rule.name == "Test Rule"
        assert rule.field == "shipper.name"
        assert rule.severity == "ERROR"

    def test_rule_with_value(self):
        """Should create rule with condition value."""
        rule = ComplianceRule(
            id="TEST-002",
            name="Container Format",
            field="containers[0].number",
            condition=ConditionType.REGEX,
            value=r"^[A-Z]{4}\d{7}$",
            severity="WARNING",
            message="Container should match ISO 6346",
        )
        assert rule.value == r"^[A-Z]{4}\d{7}$"


class TestRuleResult:
    """Test rule result model."""

    def test_result_creation_passed(self):
        """Should create passed result."""
        result = RuleResult(
            rule_id="TEST-001",
            rule_name="Test Rule",
            passed=True,
            message="Rule passed",
            severity="ERROR",
        )
        assert result.passed is True

    def test_result_creation_failed(self):
        """Should create failed result."""
        result = RuleResult(
            rule_id="TEST-001",
            rule_name="Test Rule",
            passed=False,
            message="Value is missing",
            severity="ERROR",
        )
        assert result.passed is False


class TestRulesEngineNotNull:
    """Test NOT_NULL condition type."""

    def test_not_null_passes_with_value(self, sample_bol):
        """NOT_NULL should pass when value is present."""
        rule = ComplianceRule(
            id="BOL-001",
            name="Shipper Name Required",
            field="shipper.name",
            condition=ConditionType.NOT_NULL,
            severity="ERROR",
            message="Shipper name is required",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert len(results) == 1
        assert results[0].passed is True

    def test_not_null_fails_when_missing(self, sample_bol):
        """NOT_NULL should fail when value is missing."""
        # Set shipper name to None/empty
        sample_bol.shipper.name = ""
        rule = ComplianceRule(
            id="BOL-001",
            name="Shipper Name Required",
            field="shipper.name",
            condition=ConditionType.NOT_NULL,
            severity="ERROR",
            message="Shipper name is required",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert len(results) == 1
        assert results[0].passed is False

    def test_not_null_fails_with_none(self, incomplete_bol):
        """NOT_NULL should fail when value is None."""
        rule = ComplianceRule(
            id="BOL-002",
            name="Vessel Required",
            field="vessel_name",
            condition=ConditionType.NOT_NULL,
            severity="WARNING",
            message="Vessel name is required",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(incomplete_bol)

        assert len(results) == 1
        assert results[0].passed is False


class TestRulesEngineInList:
    """Test IN_LIST condition type."""

    def test_in_list_passes_with_matching_value(self, sample_bol):
        """IN_LIST should pass when value is in list."""
        rule = ComplianceRule(
            id="BOL-003",
            name="Valid Port of Loading",
            field="port_of_loading",
            condition=ConditionType.IN_LIST,
            value=["NGAPP", "NGTIN", "NGLAG"],
            severity="WARNING",
            message="Port of loading must be a valid Nigerian port",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is True

    def test_in_list_fails_with_non_matching_value(self, sample_bol):
        """IN_LIST should fail when value is not in list."""
        sample_bol.port_of_loading = "INVALID"
        rule = ComplianceRule(
            id="BOL-003",
            name="Valid Port of Loading",
            field="port_of_loading",
            condition=ConditionType.IN_LIST,
            value=["NGAPP", "NGTIN", "NGLAG"],
            severity="WARNING",
            message="Port of loading must be a valid Nigerian port",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is False


class TestRulesEngineEquals:
    """Test EQUALS condition type."""

    def test_equals_passes_with_matching_value(self, sample_bol):
        """EQUALS should pass when values match."""
        rule = ComplianceRule(
            id="BOL-004",
            name="Shipper Country",
            field="shipper.country",
            condition=ConditionType.EQUALS,
            value="Nigeria",
            severity="ERROR",
            message="Shipper must be from Nigeria",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is True

    def test_equals_fails_with_non_matching_value(self, sample_bol):
        """EQUALS should fail when values don't match."""
        sample_bol.shipper.country = "Ghana"
        rule = ComplianceRule(
            id="BOL-004",
            name="Shipper Country",
            field="shipper.country",
            condition=ConditionType.EQUALS,
            value="Nigeria",
            severity="ERROR",
            message="Shipper must be from Nigeria",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is False


class TestRulesEngineRange:
    """Test RANGE condition type."""

    def test_range_passes_within_bounds(self, sample_bol):
        """RANGE should pass when value is within bounds."""
        rule = ComplianceRule(
            id="BOL-005",
            name="Confidence Score Valid",
            field="confidence_score",
            condition=ConditionType.RANGE,
            value={"min": 0.7, "max": 1.0},
            severity="WARNING",
            message="Confidence score should be above 70%",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is True

    def test_range_fails_below_min(self, incomplete_bol):
        """RANGE should fail when value is below minimum."""
        rule = ComplianceRule(
            id="BOL-005",
            name="Confidence Score Valid",
            field="confidence_score",
            condition=ConditionType.RANGE,
            value={"min": 0.7, "max": 1.0},
            severity="WARNING",
            message="Confidence score should be above 70%",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(incomplete_bol)

        assert results[0].passed is False

    def test_range_cargo_weight(self, sample_bol):
        """RANGE should work with cargo weight."""
        rule = ComplianceRule(
            id="BOL-006",
            name="Cargo Weight Range",
            field="cargo[0].gross_weight_kg",
            condition=ConditionType.RANGE,
            value={"min": 1000, "max": 30000},
            severity="INFO",
            message="Cargo weight should be reasonable",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is True


class TestRulesEngineRegex:
    """Test REGEX condition type."""

    def test_regex_passes_with_matching_pattern(self, sample_bol):
        """REGEX should pass when pattern matches."""
        rule = ComplianceRule(
            id="BOL-007",
            name="Container ISO 6346",
            field="containers[0].number",
            condition=ConditionType.REGEX,
            value=r"^[A-Z]{4}\d{7}$",
            severity="ERROR",
            message="Container must match ISO 6346 format",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is True

    def test_regex_fails_with_non_matching_pattern(self, sample_bol):
        """REGEX should fail when pattern doesn't match."""
        sample_bol.containers[0].number = "INVALID123"
        rule = ComplianceRule(
            id="BOL-007",
            name="Container ISO 6346",
            field="containers[0].number",
            condition=ConditionType.REGEX,
            value=r"^[A-Z]{4}\d{7}$",
            severity="ERROR",
            message="Container must match ISO 6346 format",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is False

    def test_regex_bol_number_format(self, sample_bol):
        """REGEX should validate BoL number format."""
        rule = ComplianceRule(
            id="BOL-008",
            name="BoL Number Format",
            field="bol_number",
            condition=ConditionType.REGEX,
            value=r"^[A-Z0-9-]+$",
            severity="WARNING",
            message="BoL number should be alphanumeric",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        assert results[0].passed is True


class TestRulesEngineDateOrder:
    """Test DATE_ORDER condition type."""

    def test_date_order_passes_chronological(self):
        """DATE_ORDER should pass when dates are in order."""
        bol = CanonicalBoL(
            bol_number="DATE-001",
            shipper=BolParty(name="Shipper"),
            consignee=BolParty(name="Consignee"),
            containers=[],
            cargo=[],
            shipped_on_board_date=date(2026, 1, 12),
            date_of_issue=date(2026, 1, 10),  # Issue date before shipped date
        )
        rule = ComplianceRule(
            id="BOL-009",
            name="Date Order",
            field="date_of_issue",
            condition=ConditionType.DATE_ORDER,
            value="shipped_on_board_date",
            severity="WARNING",
            message="Issue date should be before shipped date",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(bol)

        assert results[0].passed is True

    def test_date_order_fails_reverse_chronological(self):
        """DATE_ORDER should fail when dates are out of order."""
        bol = CanonicalBoL(
            bol_number="DATE-002",
            shipper=BolParty(name="Shipper"),
            consignee=BolParty(name="Consignee"),
            containers=[],
            cargo=[],
            shipped_on_board_date=date(2026, 1, 10),  # Shipped BEFORE issue?
            date_of_issue=date(2026, 1, 15),
        )
        rule = ComplianceRule(
            id="BOL-009",
            name="Date Order",
            field="date_of_issue",
            condition=ConditionType.DATE_ORDER,
            value="shipped_on_board_date",
            severity="WARNING",
            message="Issue date should be before shipped date",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(bol)

        assert results[0].passed is False


class TestRulesEngineNestedFields:
    """Test nested field value extraction."""

    def test_get_nested_field_shipper_name(self, sample_bol):
        """Should get shipper.name correctly."""
        engine = RulesEngine([])
        value = engine._get_field_value(sample_bol, "shipper.name")
        assert value == "VIBOTAJ GLOBAL NIG LTD"

    def test_get_nested_field_container_number(self, sample_bol):
        """Should get containers[0].number correctly."""
        engine = RulesEngine([])
        value = engine._get_field_value(sample_bol, "containers[0].number")
        assert value == "MRSU4825686"

    def test_get_nested_field_cargo_hs_code(self, sample_bol):
        """Should get cargo[0].hs_code correctly."""
        engine = RulesEngine([])
        value = engine._get_field_value(sample_bol, "cargo[0].hs_code")
        assert value == "0506"

    def test_get_nested_field_missing_returns_none(self, incomplete_bol):
        """Should return None for missing fields."""
        engine = RulesEngine([])
        value = engine._get_field_value(incomplete_bol, "containers[0].number")
        assert value is None


class TestRulesEngineMultipleRules:
    """Test evaluating multiple rules together."""

    def test_evaluate_all_rules(self, sample_bol):
        """Should evaluate all rules and return results."""
        rules = [
            ComplianceRule(
                id="BOL-001",
                name="Shipper Required",
                field="shipper.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Shipper required",
            ),
            ComplianceRule(
                id="BOL-002",
                name="Consignee Required",
                field="consignee.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Consignee required",
            ),
            ComplianceRule(
                id="BOL-003",
                name="Container Format",
                field="containers[0].number",
                condition=ConditionType.REGEX,
                value=r"^[A-Z]{4}\d{7}$",
                severity="WARNING",
                message="Container format invalid",
            ),
        ]
        engine = RulesEngine(rules)
        results = engine.evaluate(sample_bol)

        assert len(results) == 3
        assert all(r.passed for r in results)

    def test_evaluate_mixed_results(self, sample_bol):
        """Should return mixed pass/fail results."""
        sample_bol.vessel_name = None  # Make vessel check fail
        rules = [
            ComplianceRule(
                id="BOL-001",
                name="Shipper Required",
                field="shipper.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Shipper required",
            ),
            ComplianceRule(
                id="BOL-002",
                name="Vessel Required",
                field="vessel_name",
                condition=ConditionType.NOT_NULL,
                severity="WARNING",
                message="Vessel required",
            ),
        ]
        engine = RulesEngine(rules)
        results = engine.evaluate(sample_bol)

        assert len(results) == 2
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        assert len(passed) == 1
        assert len(failed) == 1


class TestRulesEngineComplianceDecision:
    """Test compliance decision calculation."""

    def test_all_pass_returns_approve(self, sample_bol):
        """All rules passing should return APPROVE."""
        rules = [
            ComplianceRule(
                id="BOL-001",
                name="Shipper Required",
                field="shipper.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Shipper required",
            ),
            ComplianceRule(
                id="BOL-002",
                name="Consignee Required",
                field="consignee.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Consignee required",
            ),
        ]
        engine = RulesEngine(rules)
        results = engine.evaluate(sample_bol)
        decision = engine.get_compliance_decision(results)

        assert decision == "APPROVE"

    def test_error_failure_returns_reject(self, sample_bol):
        """ERROR severity failure should return REJECT."""
        sample_bol.shipper.name = ""  # Make it fail
        rules = [
            ComplianceRule(
                id="BOL-001",
                name="Shipper Required",
                field="shipper.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Shipper required",
            ),
        ]
        engine = RulesEngine(rules)
        results = engine.evaluate(sample_bol)
        decision = engine.get_compliance_decision(results)

        assert decision == "REJECT"

    def test_warning_failure_returns_hold(self, sample_bol):
        """WARNING severity failure should return HOLD."""
        sample_bol.vessel_name = None  # Make it fail
        rules = [
            ComplianceRule(
                id="BOL-001",
                name="Shipper Required",
                field="shipper.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Shipper required",
            ),
            ComplianceRule(
                id="BOL-002",
                name="Vessel Required",
                field="vessel_name",
                condition=ConditionType.NOT_NULL,
                severity="WARNING",
                message="Vessel required",
            ),
        ]
        engine = RulesEngine(rules)
        results = engine.evaluate(sample_bol)
        decision = engine.get_compliance_decision(results)

        assert decision == "HOLD"

    def test_error_overrides_warning(self, sample_bol):
        """ERROR failure should override WARNING to return REJECT."""
        sample_bol.shipper.name = ""  # ERROR failure
        sample_bol.vessel_name = None  # WARNING failure
        rules = [
            ComplianceRule(
                id="BOL-001",
                name="Shipper Required",
                field="shipper.name",
                condition=ConditionType.NOT_NULL,
                severity="ERROR",
                message="Shipper required",
            ),
            ComplianceRule(
                id="BOL-002",
                name="Vessel Required",
                field="vessel_name",
                condition=ConditionType.NOT_NULL,
                severity="WARNING",
                message="Vessel required",
            ),
        ]
        engine = RulesEngine(rules)
        results = engine.evaluate(sample_bol)
        decision = engine.get_compliance_decision(results)

        assert decision == "REJECT"


class TestRulesEngineEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_rules_list(self, sample_bol):
        """Empty rules list should return empty results and APPROVE."""
        engine = RulesEngine([])
        results = engine.evaluate(sample_bol)
        decision = engine.get_compliance_decision(results)

        assert results == []
        assert decision == "APPROVE"

    def test_invalid_field_path_handled(self, sample_bol):
        """Invalid field path should be handled gracefully."""
        rule = ComplianceRule(
            id="BOL-999",
            name="Invalid Field",
            field="nonexistent.field.path",
            condition=ConditionType.NOT_NULL,
            severity="WARNING",
            message="This field doesn't exist",
        )
        engine = RulesEngine([rule])
        results = engine.evaluate(sample_bol)

        # Should fail NOT_NULL since field doesn't exist
        assert len(results) == 1
        assert results[0].passed is False
