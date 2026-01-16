"""Tests for Compliance Rules Definition.

TDD Phase: RED - Write failing tests first

These tests verify the compliance rules for BoL documents:
1. Required fields are validated
2. Format validations work correctly
3. Compliance decisions (APPROVE/HOLD/REJECT) are calculated correctly
4. Rules work for all product types
"""

import pytest
from datetime import date

from app.services.bol_rules.engine import RulesEngine, RuleResult
from app.services.bol_rules.compliance_rules import (
    STANDARD_BOL_RULES,
    get_compliance_decision,
)
from app.schemas.bol import (
    CanonicalBoL,
    BolParty,
    BolContainer,
    BolCargo,
)


# Test fixtures
@pytest.fixture
def complete_bol():
    """Create a complete, valid BoL."""
    return CanonicalBoL(
        bol_number="APU106546",
        shipper=BolParty(name="VIBOTAJ GLOBAL NIG LTD", country="Nigeria"),
        consignee=BolParty(name="HAGES GMBH", country="Germany"),
        containers=[
            BolContainer(number="MRSU4825686", type="40HC", seal_number="SL123456")
        ],
        cargo=[
            BolCargo(description="CATTLE HOOVES AND HORNS", hs_code="0506", gross_weight_kg=20000)
        ],
        vessel_name="MSC MARINA",
        voyage_number="VY2026001",
        port_of_loading="NGAPP",
        port_of_discharge="DEHAM",
        shipped_on_board_date=date(2026, 1, 12),
        date_of_issue=date(2026, 1, 10),
        freight_terms="PREPAID",
        confidence_score=0.95,
    )


@pytest.fixture
def bol_missing_shipper():
    """BoL with placeholder shipper name (parser couldn't extract)."""
    return CanonicalBoL(
        bol_number="PARTIAL-001",
        shipper=BolParty(name="Unknown Shipper"),  # Parser placeholder
        consignee=BolParty(name="HAGES GMBH"),
        containers=[BolContainer(number="MRSU4825686")],
        cargo=[BolCargo(description="CARGO")],
        confidence_score=0.5,
    )


@pytest.fixture
def bol_missing_consignee():
    """BoL with placeholder consignee name (parser couldn't extract)."""
    return CanonicalBoL(
        bol_number="PARTIAL-002",
        shipper=BolParty(name="VIBOTAJ"),
        consignee=BolParty(name="Unknown Consignee"),  # Parser placeholder
        containers=[BolContainer(number="MRSU4825686")],
        cargo=[BolCargo(description="CARGO")],
        confidence_score=0.5,
    )


@pytest.fixture
def bol_invalid_container():
    """BoL with invalid container number."""
    return CanonicalBoL(
        bol_number="CONTAINER-001",
        shipper=BolParty(name="VIBOTAJ"),
        consignee=BolParty(name="HAGES GMBH"),
        containers=[BolContainer(number="INVALID-123")],  # Not ISO 6346
        cargo=[BolCargo(description="CARGO")],
        confidence_score=0.5,
    )


@pytest.fixture
def bol_no_cargo():
    """BoL with no cargo description."""
    return CanonicalBoL(
        bol_number="NOCARGO-001",
        shipper=BolParty(name="VIBOTAJ"),
        consignee=BolParty(name="HAGES GMBH"),
        containers=[BolContainer(number="MRSU4825686")],
        cargo=[],  # No cargo
        confidence_score=0.5,
    )


@pytest.fixture
def bol_no_container():
    """BoL with no containers."""
    return CanonicalBoL(
        bol_number="NOCONT-001",
        shipper=BolParty(name="VIBOTAJ"),
        consignee=BolParty(name="HAGES GMBH"),
        containers=[],  # No containers
        cargo=[BolCargo(description="CARGO")],
        confidence_score=0.5,
    )


@pytest.fixture
def bol_missing_port_of_loading():
    """BoL with missing port of loading."""
    return CanonicalBoL(
        bol_number="NOPORT-001",
        shipper=BolParty(name="VIBOTAJ"),
        consignee=BolParty(name="HAGES GMBH"),
        containers=[BolContainer(number="MRSU4825686")],
        cargo=[BolCargo(description="CARGO")],
        port_of_loading=None,
        confidence_score=0.5,
    )


class TestStandardBolRules:
    """Test that standard BoL rules are properly defined."""

    def test_standard_rules_exist(self):
        """STANDARD_BOL_RULES should be defined."""
        assert STANDARD_BOL_RULES is not None
        assert len(STANDARD_BOL_RULES) > 0

    def test_shipper_name_rule_exists(self):
        """Rule for shipper name required should exist."""
        rule_ids = [r.id for r in STANDARD_BOL_RULES]
        assert "BOL-001" in rule_ids

    def test_consignee_name_rule_exists(self):
        """Rule for consignee name required should exist."""
        rule_ids = [r.id for r in STANDARD_BOL_RULES]
        assert "BOL-002" in rule_ids

    def test_container_format_rule_exists(self):
        """Rule for container ISO 6346 format should exist."""
        rule_ids = [r.id for r in STANDARD_BOL_RULES]
        assert "BOL-003" in rule_ids

    def test_bol_number_rule_exists(self):
        """Rule for BoL number required should exist."""
        rule_ids = [r.id for r in STANDARD_BOL_RULES]
        assert "BOL-004" in rule_ids


class TestShipperNameRequired:
    """Test shipper name required rule (BOL-001)."""

    def test_shipper_name_present_passes(self, complete_bol):
        """Should pass when shipper name is present."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(complete_bol)
        shipper_result = next(r for r in results if r.rule_id == "BOL-001")
        assert shipper_result.passed is True

    def test_shipper_name_missing_fails(self, bol_missing_shipper):
        """Should fail when shipper name is missing."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_missing_shipper)
        shipper_result = next(r for r in results if r.rule_id == "BOL-001")
        assert shipper_result.passed is False
        assert shipper_result.severity == "ERROR"


class TestConsigneeNameRequired:
    """Test consignee name required rule (BOL-002)."""

    def test_consignee_name_present_passes(self, complete_bol):
        """Should pass when consignee name is present."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(complete_bol)
        consignee_result = next(r for r in results if r.rule_id == "BOL-002")
        assert consignee_result.passed is True

    def test_consignee_name_missing_fails(self, bol_missing_consignee):
        """Should fail when consignee name is missing."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_missing_consignee)
        consignee_result = next(r for r in results if r.rule_id == "BOL-002")
        assert consignee_result.passed is False
        assert consignee_result.severity == "ERROR"


class TestContainerIso6346Format:
    """Test container ISO 6346 format rule (BOL-003)."""

    def test_valid_container_format_passes(self, complete_bol):
        """Should pass when container matches ISO 6346."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(complete_bol)
        container_result = next(r for r in results if r.rule_id == "BOL-003")
        assert container_result.passed is True

    def test_invalid_container_format_fails(self, bol_invalid_container):
        """Should fail when container doesn't match ISO 6346."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_invalid_container)
        container_result = next(r for r in results if r.rule_id == "BOL-003")
        assert container_result.passed is False
        # Container format is WARNING severity (can still process)
        assert container_result.severity == "WARNING"


class TestBolNumberRequired:
    """Test BoL number required rule (BOL-004)."""

    def test_bol_number_present_passes(self, complete_bol):
        """Should pass when BoL number is present."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(complete_bol)
        bol_result = next(r for r in results if r.rule_id == "BOL-004")
        assert bol_result.passed is True

    def test_bol_number_missing_fails(self):
        """Should fail when BoL number is placeholder."""
        bol = CanonicalBoL(
            bol_number="UNKNOWN",  # Placeholder from parser
            shipper=BolParty(name="VIBOTAJ"),
            consignee=BolParty(name="HAGES"),
            containers=[],
            cargo=[],
        )
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        bol_result = next(r for r in results if r.rule_id == "BOL-004")
        assert bol_result.passed is False
        assert bol_result.severity == "ERROR"


class TestPortOfLoadingRequired:
    """Test port of loading required rule (BOL-005)."""

    def test_pol_present_passes(self, complete_bol):
        """Should pass when port of loading is present."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(complete_bol)
        pol_result = next(r for r in results if r.rule_id == "BOL-005")
        assert pol_result.passed is True

    def test_pol_missing_fails(self, bol_missing_port_of_loading):
        """Should fail when port of loading is missing."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_missing_port_of_loading)
        pol_result = next(r for r in results if r.rule_id == "BOL-005")
        assert pol_result.passed is False
        # POL is WARNING severity (document may still be processable)
        assert pol_result.severity == "WARNING"


class TestCargoDescriptionRequired:
    """Test cargo description required rule (BOL-006)."""

    def test_cargo_present_passes(self, complete_bol):
        """Should pass when cargo is present."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(complete_bol)
        cargo_result = next(r for r in results if r.rule_id == "BOL-006")
        assert cargo_result.passed is True

    def test_cargo_missing_fails(self, bol_no_cargo):
        """Should fail when cargo is missing."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_no_cargo)
        cargo_result = next(r for r in results if r.rule_id == "BOL-006")
        assert cargo_result.passed is False
        assert cargo_result.severity == "WARNING"


class TestComplianceDecision:
    """Test compliance decision calculation."""

    def test_complete_bol_approved(self, complete_bol):
        """Complete valid BoL should be APPROVED."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(complete_bol)
        decision = get_compliance_decision(results)
        assert decision == "APPROVE"

    def test_missing_shipper_rejected(self, bol_missing_shipper):
        """Missing shipper (ERROR) should result in REJECT."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_missing_shipper)
        decision = get_compliance_decision(results)
        assert decision == "REJECT"

    def test_missing_consignee_rejected(self, bol_missing_consignee):
        """Missing consignee (ERROR) should result in REJECT."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_missing_consignee)
        decision = get_compliance_decision(results)
        assert decision == "REJECT"

    def test_invalid_container_hold(self, bol_invalid_container):
        """Invalid container format (WARNING) should result in HOLD."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_invalid_container)
        decision = get_compliance_decision(results)
        assert decision == "HOLD"

    def test_no_cargo_hold(self, bol_no_cargo):
        """No cargo (WARNING) should result in HOLD."""
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol_no_cargo)
        decision = get_compliance_decision(results)
        assert decision == "HOLD"


class TestComplianceRulesProductTypes:
    """Test compliance rules work for all product types."""

    def test_horn_and_hoof_bol(self):
        """Rules should work for Horn & Hoof products (HS 0506/0507)."""
        bol = CanonicalBoL(
            bol_number="HORN-BOL-001",
            shipper=BolParty(name="VIBOTAJ GLOBAL"),
            consignee=BolParty(name="HAGES GMBH"),
            containers=[BolContainer(number="MRSU4825686")],
            cargo=[
                BolCargo(description="CATTLE HOOVES", hs_code="0506"),
                BolCargo(description="CATTLE HORNS", hs_code="0507"),
            ],
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            vessel_name="MSC MARINA",
            voyage_number="VY2026001",
            confidence_score=0.9,
        )
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)
        assert decision == "APPROVE"

    def test_agricultural_bol(self):
        """Rules should work for agricultural products."""
        bol = CanonicalBoL(
            bol_number="AGR-BOL-001",
            shipper=BolParty(name="FARM EXPORT CO"),
            consignee=BolParty(name="FOOD IMPORT GMBH"),
            containers=[BolContainer(number="MSKU9876543")],
            cargo=[
                BolCargo(description="COCOA BEANS", hs_code="1801"),
            ],
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            vessel_name="CMA CARGO",
            voyage_number="V2026002",
            confidence_score=0.9,
        )
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)
        assert decision == "APPROVE"

    def test_general_cargo_bol(self):
        """Rules should work for general cargo."""
        bol = CanonicalBoL(
            bol_number="GEN-BOL-001",
            shipper=BolParty(name="EXPORT CO LTD"),
            consignee=BolParty(name="IMPORT GMBH"),
            containers=[BolContainer(number="TCNU1234567")],
            cargo=[
                BolCargo(description="GENERAL MERCHANDISE", hs_code="9999"),
            ],
            port_of_loading="NGAPP",
            port_of_discharge="DEHAM",
            vessel_name="EVER GREEN",
            voyage_number="EG2026003",
            confidence_score=0.9,
        )
        engine = RulesEngine(STANDARD_BOL_RULES)
        results = engine.evaluate(bol)
        decision = get_compliance_decision(results)
        assert decision == "APPROVE"


class TestGetComplianceDecisionFunction:
    """Test the standalone get_compliance_decision function."""

    def test_empty_results_approve(self):
        """Empty results should return APPROVE."""
        decision = get_compliance_decision([])
        assert decision == "APPROVE"

    def test_all_passed_approve(self):
        """All passed results should return APPROVE."""
        results = [
            RuleResult(rule_id="1", rule_name="Test", passed=True, message="OK", severity="ERROR"),
            RuleResult(rule_id="2", rule_name="Test", passed=True, message="OK", severity="WARNING"),
        ]
        decision = get_compliance_decision(results)
        assert decision == "APPROVE"

    def test_error_failure_reject(self):
        """ERROR failure should return REJECT."""
        results = [
            RuleResult(rule_id="1", rule_name="Test", passed=False, message="Fail", severity="ERROR"),
        ]
        decision = get_compliance_decision(results)
        assert decision == "REJECT"

    def test_warning_failure_hold(self):
        """WARNING failure should return HOLD."""
        results = [
            RuleResult(rule_id="1", rule_name="Test", passed=False, message="Fail", severity="WARNING"),
        ]
        decision = get_compliance_decision(results)
        assert decision == "HOLD"

    def test_info_failure_approve(self):
        """INFO failure should still return APPROVE."""
        results = [
            RuleResult(rule_id="1", rule_name="Test", passed=False, message="Fail", severity="INFO"),
        ]
        decision = get_compliance_decision(results)
        assert decision == "APPROVE"
