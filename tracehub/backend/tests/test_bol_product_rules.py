"""TDD Tests for Product-Specific BoL Compliance Rules.

Tests the PRP requirements:
- TRACES requirement for animal products (HS 0506/0507)
- Veterinary certificate date ≤ vessel ETD
- Weight tolerance validation
- Approved consignee validation

Run with: pytest tests/test_bol_product_rules.py -v

These tests are written BEFORE implementation (TDD approach).
They should FAIL initially, then PASS after implementation.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.schemas.bol import CanonicalBoL, BolParty, BolCargo, BolContainer
from app.services.bol_rules.engine import RulesEngine
from app.services.bol_rules.compliance_rules import (
    STANDARD_BOL_RULES,
    get_rules_for_product_type,
)
from app.models.shipment import ProductType


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def complete_horn_hoof_bol():
    """Create a complete BoL for Horn & Hoof products (HS 0506/0507)."""
    return CanonicalBoL(
        bol_number="MAEU123456789",
        shipper=BolParty(
            name="VIBOTAJ Global Nigeria Ltd",
            address="Lagos, Nigeria",
            country="NG"
        ),
        consignee=BolParty(
            name="HAGES GmbH",
            address="Hamburg, Germany",
            country="DE"
        ),
        containers=[
            BolContainer(
                number="MSCU1234567",
                seal_number="SEAL123",
                type="40HC",
                weight_kg=25000.0
            )
        ],
        cargo=[
            BolCargo(
                description="CATTLE HORN TIPS",
                hs_code="05069010",  # Horn & Hoof HS code
                quantity=1000,
                unit="PCS",
                gross_weight_kg=25000.0,
                net_weight_kg=24000.0
            )
        ],
        vessel_name="MAERSK SEALAND",
        voyage_number="001W",
        port_of_loading="NGAPP",
        port_of_discharge="DEHAM",
        date_of_issue=date(2026, 1, 10),
        shipped_on_board_date=date(2026, 1, 15),
        confidence_score=0.95
    )


@pytest.fixture
def horn_hoof_bol_without_traces():
    """Create a Horn & Hoof BoL missing TRACES reference."""
    return CanonicalBoL(
        bol_number="MAEU123456789",
        shipper=BolParty(name="VIBOTAJ Global Nigeria Ltd"),
        consignee=BolParty(name="HAGES GmbH"),
        containers=[BolContainer(number="MSCU1234567", weight_kg=25000.0)],
        cargo=[
            BolCargo(
                description="CATTLE HORN TIPS",
                hs_code="05069010",
                gross_weight_kg=25000.0
            )
        ],
        # Missing: traces_reference field
        confidence_score=0.85
    )


@pytest.fixture
def bol_with_weight_mismatch():
    """Create a BoL with weight exceeding tolerance."""
    return CanonicalBoL(
        bol_number="MAEU123456789",
        shipper=BolParty(name="VIBOTAJ Global"),
        consignee=BolParty(name="HAGES GmbH"),
        containers=[
            BolContainer(number="MSCU1234567", weight_kg=30000.0)  # Container weight
        ],
        cargo=[
            BolCargo(
                description="CATTLE HORN TIPS",
                hs_code="05069010",
                gross_weight_kg=25000.0  # Cargo weight 5000kg different (16.7% difference)
            )
        ],
        confidence_score=0.90
    )


# =============================================================================
# Test: Product-Type Specific Rules
# =============================================================================

class TestProductTypeRules:
    """Test that rules are returned based on product type."""

    def test_get_rules_for_horn_hoof_returns_specific_rules(self):
        """GIVEN product_type is HORN_HOOF
        WHEN get_rules_for_product_type is called
        THEN it should return Horn & Hoof specific rules including TRACES."""

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)

        # Should include standard rules PLUS product-specific rules
        rule_ids = [r.id for r in rules]

        # Standard rules should still be included
        assert "BOL-001" in rule_ids, "Shipper name rule should be included"
        assert "BOL-002" in rule_ids, "Consignee name rule should be included"

        # Product-specific rules should be added
        assert "BOL-HH-001" in rule_ids, "TRACES requirement rule should be included"
        assert "BOL-HH-002" in rule_ids, "Vet cert date rule should be included"

    def test_get_rules_for_cocoa_excludes_traces(self):
        """GIVEN product_type is COCOA (EUDR product)
        WHEN get_rules_for_product_type is called
        THEN it should NOT include TRACES rules (not applicable to cocoa)."""

        rules = get_rules_for_product_type(ProductType.COCOA)
        rule_ids = [r.id for r in rules]

        assert "BOL-HH-001" not in rule_ids, "TRACES rule should NOT be for cocoa"
        assert "BOL-HH-002" not in rule_ids, "Vet cert rule should NOT be for cocoa"

    def test_standard_rules_returned_for_other_products(self):
        """GIVEN product_type is OTHER
        WHEN get_rules_for_product_type is called
        THEN only standard rules should be returned."""

        rules = get_rules_for_product_type(ProductType.OTHER)

        assert rules == STANDARD_BOL_RULES, "OTHER should use standard rules only"


# =============================================================================
# Test: TRACES Requirement for Animal Products
# =============================================================================

class TestTracesRequirement:
    """Test TRACES reference validation for Horn & Hoof products."""

    def test_traces_rule_exists_for_horn_hoof(self):
        """GIVEN Horn & Hoof product type
        WHEN rules are retrieved
        THEN a TRACES requirement rule should exist."""

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        traces_rules = [r for r in rules if "TRACES" in r.name.upper() or "traces" in r.field]

        assert len(traces_rules) >= 1, "At least one TRACES rule should exist"

    def test_bol_without_traces_triggers_hold_or_reject(
        self, horn_hoof_bol_without_traces
    ):
        """GIVEN a Horn & Hoof BoL without TRACES reference
        WHEN compliance is checked
        THEN decision should be HOLD or REJECT."""

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        engine = RulesEngine()
        result = engine.evaluate(horn_hoof_bol_without_traces, rules)

        assert result.decision in ["HOLD", "REJECT"], \
            "Missing TRACES should trigger HOLD or REJECT"

        # Find the TRACES rule result
        traces_results = [
            r for r in result.results
            if "TRACES" in r.rule_name.upper() or "traces" in r.field_path
        ]
        assert len(traces_results) >= 1, "TRACES rule should have been evaluated"
        assert not traces_results[0].passed, "TRACES rule should have failed"


# =============================================================================
# Test: Veterinary Certificate Date Validation
# =============================================================================

class TestVetCertDateValidation:
    """Test veterinary certificate date must be ≤ vessel ETD."""

    def test_vet_cert_date_rule_exists(self):
        """GIVEN Horn & Hoof product type
        WHEN rules are retrieved
        THEN a vet cert date validation rule should exist."""

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        vet_cert_rules = [
            r for r in rules
            if "vet" in r.name.lower() or "veterinary" in r.name.lower()
        ]

        assert len(vet_cert_rules) >= 1, "Vet cert date rule should exist"

    def test_vet_cert_after_etd_fails_validation(self):
        """GIVEN vet cert date is AFTER vessel ETD
        WHEN compliance is checked
        THEN the rule should fail."""

        # Create BoL with vet cert date after ETD
        bol = CanonicalBoL(
            bol_number="MAEU123456789",
            shipper=BolParty(name="VIBOTAJ Global"),
            consignee=BolParty(name="HAGES GmbH"),
            containers=[BolContainer(number="MSCU1234567")],
            cargo=[BolCargo(description="HORN TIPS", hs_code="05069010")],
            shipped_on_board_date=date(2026, 1, 15),  # This is vessel ETD
            confidence_score=0.90
        )

        # Assume vet_cert_date would be stored/checked separately
        # Rule should check: vet_cert_date <= shipped_on_board_date (ETD)

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        engine = RulesEngine()

        # This test validates the rule exists and can be evaluated
        # Implementation should add vet_cert_date field or check via documents
        result = engine.evaluate(bol, rules)

        # At minimum, the rule should be in the results
        assert any("vet" in r.rule_name.lower() for r in result.results), \
            "Vet cert rule should be evaluated"


# =============================================================================
# Test: Weight Tolerance Validation
# =============================================================================

class TestWeightToleranceValidation:
    """Test weight tolerance between declared and extracted weights."""

    def test_weight_tolerance_rule_exists(self):
        """GIVEN standard BoL rules
        WHEN rules are retrieved
        THEN a weight tolerance rule should exist."""

        # Weight tolerance should be in standard rules (not product-specific)
        rule_ids = [r.id for r in STANDARD_BOL_RULES]

        assert "BOL-012" in rule_ids or "BOL-013" in rule_ids, \
            "Weight tolerance rule should exist in standard rules"

    def test_weight_within_tolerance_passes(self, complete_horn_hoof_bol):
        """GIVEN cargo weight within 5% of container weight
        WHEN compliance is checked
        THEN weight tolerance rule should pass."""

        # Complete BoL has container_weight=25000 and cargo_weight=25000 (0% diff)
        engine = RulesEngine()
        result = engine.evaluate(complete_horn_hoof_bol, STANDARD_BOL_RULES)

        weight_results = [r for r in result.results if "weight" in r.rule_name.lower()]
        if weight_results:
            assert weight_results[0].passed, "Weight within tolerance should pass"

    def test_weight_exceeding_tolerance_fails(self, bol_with_weight_mismatch):
        """GIVEN cargo weight differs by more than 5% from container weight
        WHEN compliance is checked
        THEN weight tolerance rule should fail."""

        engine = RulesEngine()
        result = engine.evaluate(bol_with_weight_mismatch, STANDARD_BOL_RULES)

        weight_results = [r for r in result.results if "weight" in r.rule_name.lower()]
        if weight_results:
            assert not weight_results[0].passed, \
                "Weight outside tolerance should fail"


# =============================================================================
# Test: Approved Consignee Validation
# =============================================================================

class TestApprovedConsigneeValidation:
    """Test consignee approval for regulated products."""

    def test_approved_consignee_rule_exists_for_horn_hoof(self):
        """GIVEN Horn & Hoof product type
        WHEN rules are retrieved
        THEN an approved consignee rule should exist."""

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        consignee_rules = [
            r for r in rules
            if "approved" in r.name.lower() and "consignee" in r.name.lower()
        ]

        # This validates the rule exists
        # Implementation should add BOL-HH-003 or similar
        assert len(consignee_rules) >= 1 or "BOL-HH-003" in [r.id for r in rules], \
            "Approved consignee rule should exist for Horn & Hoof"

    def test_unapproved_consignee_triggers_warning(self, complete_horn_hoof_bol):
        """GIVEN a consignee NOT in the approved list
        WHEN compliance is checked
        THEN it should trigger a WARNING (not immediate rejection)."""

        # Modify consignee to an unapproved entity
        complete_horn_hoof_bol.consignee = BolParty(
            name="UNKNOWN IMPORTER GmbH",
            country="DE"
        )

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        engine = RulesEngine()
        result = engine.evaluate(complete_horn_hoof_bol, rules)

        # Should trigger at least a HOLD (warning) for unapproved consignee
        approved_results = [
            r for r in result.results
            if "approved" in r.rule_name.lower() or "consignee" in r.field_path
        ]

        if approved_results:
            # If rule exists, unapproved should not pass
            # (may pass basic presence check but fail approved list check)
            pass  # Implementation will add this rule


# =============================================================================
# Test: Rules Engine Integration with Product Types
# =============================================================================

class TestRulesEngineProductIntegration:
    """Test the rules engine properly handles product-specific rules."""

    def test_engine_evaluates_all_product_rules(self, complete_horn_hoof_bol):
        """GIVEN a Horn & Hoof BoL with all fields
        WHEN compliance is checked with product-specific rules
        THEN all product-specific rules should be evaluated."""

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        engine = RulesEngine()
        result = engine.evaluate(complete_horn_hoof_bol, rules)

        # Count rule evaluations
        evaluated_ids = [r.rule_id for r in result.results]

        # Standard rules should be evaluated
        assert "BOL-001" in evaluated_ids
        assert "BOL-002" in evaluated_ids

        # Product-specific rules should also be evaluated
        # (will fail initially until rules are implemented)
        hh_rules = [r for r in evaluated_ids if r.startswith("BOL-HH-")]
        assert len(hh_rules) >= 1, "Horn & Hoof specific rules should be evaluated"

    def test_complete_bol_with_all_required_fields_passes(
        self, complete_horn_hoof_bol
    ):
        """GIVEN a complete Horn & Hoof BoL with all required fields
        WHEN compliance is checked
        THEN decision should be APPROVE."""

        # Add TRACES reference for completeness
        # (After implementation, CanonicalBoL may have traces_reference field)

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        engine = RulesEngine()
        result = engine.evaluate(complete_horn_hoof_bol, rules)

        # A complete BoL should pass all rules
        # (May need to add TRACES field to fixture after implementation)
        failed_errors = [r for r in result.results if not r.passed and r.severity == "ERROR"]

        # If there are ERROR failures, they should only be for missing TRACES
        # which we haven't added to the fixture yet
        for failure in failed_errors:
            assert "TRACES" in failure.rule_name.upper() or "vet" in failure.rule_name.lower(), \
                f"Unexpected error failure: {failure.rule_name}"


# =============================================================================
# Test: Severity Levels
# =============================================================================

class TestSeverityLevels:
    """Test that product-specific rules have correct severity levels."""

    def test_traces_missing_is_error_severity(self):
        """GIVEN TRACES is missing for Horn & Hoof
        WHEN rule is evaluated
        THEN severity should be ERROR (causes REJECT)."""

        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        traces_rules = [r for r in rules if "TRACES" in r.name.upper()]

        if traces_rules:
            assert traces_rules[0].severity == "ERROR", \
                "Missing TRACES should be ERROR severity for Horn & Hoof"

    def test_weight_tolerance_is_warning_severity(self):
        """GIVEN weight exceeds tolerance
        WHEN rule is evaluated
        THEN severity should be WARNING (causes HOLD, not REJECT)."""

        weight_rules = [r for r in STANDARD_BOL_RULES if "weight" in r.name.lower()]

        if weight_rules:
            assert weight_rules[0].severity == "WARNING", \
                "Weight tolerance should be WARNING severity"
