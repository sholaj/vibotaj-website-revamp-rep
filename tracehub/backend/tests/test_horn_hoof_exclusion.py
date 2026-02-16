"""Tests for Horn & Hoof EUDR exclusion (PRD-016).

CRITICAL: HS 0506/0507 (horn & hoof) are NOT covered by EUDR.
This test ensures PRD-016 compliance engine changes preserve this behavior.
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.compliance import is_eudr_required
from app.services.bol_rules.compliance_rules import get_rules_for_product_type
from app.models.shipment import ProductType


class TestHornHoofExclusion:
    """Verify EUDR rules are NOT applied to horn/hoof products."""

    def test_horn_not_eudr_0506(self):
        """HS 0506 (horn) is NOT EUDR-covered."""
        assert is_eudr_required("0506") is False

    def test_hoof_not_eudr_0507(self):
        """HS 0507 (hoof) is NOT EUDR-covered."""
        assert is_eudr_required("0507") is False

    def test_horn_hoof_subcodes_not_eudr(self):
        """Horn/hoof subcodes are NOT EUDR-covered."""
        for code in ["0506.10", "0506.90", "0507.10", "0507.90.00"]:
            assert is_eudr_required(code) is False, f"HS {code} should NOT be EUDR"

    def test_horn_hoof_product_type_rules(self):
        """Horn/hoof product type gets horn/hoof specific rules, not EUDR."""
        rules = get_rules_for_product_type(ProductType.HORN_HOOF)
        rule_ids = [r.id for r in rules]

        # Should have horn/hoof rules
        assert "BOL-HH-001" in rule_ids
        assert "BOL-HH-002" in rule_ids
        assert "BOL-HH-003" in rule_ids

    def test_cocoa_is_eudr_required(self):
        """HS 1801 (cocoa) IS EUDR-covered — control test."""
        assert is_eudr_required("1801") is True
