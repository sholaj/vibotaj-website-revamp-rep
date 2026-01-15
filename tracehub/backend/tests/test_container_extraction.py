"""Tests for container number extraction from BOL documents.

TDD Phase: RED - Write failing tests first
"""

import pytest
from typing import Tuple, Optional

# Import the service (will fail until implemented)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test data - sample BOL text excerpts
SAMPLE_BOL_TEXT_1 = """
BILL OF LADING
Shipper: VIBOTAJ Global Nigeria Ltd
Consignee: HAGES GmbH
Container No.: MRSU3452572
Port of Loading: NGAPP (Apapa, Lagos)
Port of Discharge: DEHAM (Hamburg)
"""

SAMPLE_BOL_TEXT_2 = """
OCEAN BILL OF LADING
Equipment No: TCNU 1234567
B/L Number: APU033525
Vessel: MSC AURORA
"""

SAMPLE_BOL_TEXT_3 = """
MULTIMODAL TRANSPORT DOCUMENT
Container: MSKU-987-6543
CNTR #: CAAU6541001
"""

SAMPLE_BOL_NO_CONTAINER = """
COMMERCIAL INVOICE
Invoice No: INV-2024-001
Date: 2024-06-15
Total: EUR 15,000.00
"""


class TestContainerExtraction:
    """Test container number extraction from text."""

    def test_extract_container_from_bol_text(self):
        """Extract MRSU3452572 from standard BOL text."""
        from app.services.shipment_data_extractor import ShipmentDataExtractor

        extractor = ShipmentDataExtractor()
        result = extractor.extract_container_with_confidence(SAMPLE_BOL_TEXT_1)

        assert result is not None
        container, confidence = result
        assert container == "MRSU3452572"
        assert confidence >= 0.8

    def test_extract_container_with_spaces(self):
        """Extract 'TCNU 1234567' and normalize to 'TCNU1234567'."""
        from app.services.shipment_data_extractor import ShipmentDataExtractor

        extractor = ShipmentDataExtractor()
        result = extractor.extract_container_with_confidence(SAMPLE_BOL_TEXT_2)

        assert result is not None
        container, confidence = result
        assert container == "TCNU1234567"  # Normalized - no spaces
        assert confidence >= 0.7

    def test_extract_container_with_dashes(self):
        """Extract 'MSKU-987-6543' and normalize correctly."""
        from app.services.shipment_data_extractor import ShipmentDataExtractor

        extractor = ShipmentDataExtractor()
        # Extract from text that has dashes
        text = "Container: MSKU-987-6543"
        result = extractor.extract_container_with_confidence(text)

        assert result is not None
        container, confidence = result
        assert container == "MSKU9876543"  # Normalized - no dashes
        assert confidence >= 0.6

    def test_extract_multiple_containers_returns_first_valid(self):
        """When multiple containers in text, return first valid one."""
        from app.services.shipment_data_extractor import ShipmentDataExtractor

        extractor = ShipmentDataExtractor()
        # Text with multiple containers
        result = extractor.extract_container_with_confidence(SAMPLE_BOL_TEXT_3)

        assert result is not None
        container, confidence = result
        # Should return first valid ISO 6346 container
        assert container in ["MSKU9876543", "CAAU6541001"]

    def test_no_container_returns_none(self):
        """Text without container should return None."""
        from app.services.shipment_data_extractor import ShipmentDataExtractor

        extractor = ShipmentDataExtractor()
        result = extractor.extract_container_with_confidence(SAMPLE_BOL_NO_CONTAINER)

        assert result is None or result[1] == 0.0


class TestPlaceholderDetection:
    """Test detection of placeholder container numbers."""

    def test_is_placeholder_container_with_cnt_pattern(self):
        """'BECKMANN-CNT-001' should be detected as placeholder."""
        from app.services.shipment_data_extractor import is_placeholder_container

        assert is_placeholder_container("BECKMANN-CNT-001") is True
        assert is_placeholder_container("WITATRADE-CNT-002") is True
        assert is_placeholder_container("FELIX-CNT-003") is True

    def test_is_placeholder_container_with_test_pattern(self):
        """'TEST1234567' should be detected as placeholder."""
        from app.services.shipment_data_extractor import is_placeholder_container

        assert is_placeholder_container("TEST1234567") is True
        assert is_placeholder_container("TESTCONTAINER") is True

    def test_real_container_not_placeholder(self):
        """Valid ISO 6346 containers should not be placeholders."""
        from app.services.shipment_data_extractor import is_placeholder_container

        assert is_placeholder_container("MRSU3452572") is False
        assert is_placeholder_container("TCNU1234567") is False
        assert is_placeholder_container("MSKU9876543") is False
        assert is_placeholder_container("CAAU6541001") is False


class TestContainerValidation:
    """Test ISO 6346 container format validation."""

    def test_valid_iso6346_formats(self):
        """Valid ISO 6346 formats should pass validation."""
        from app.services.shipment_data_extractor import is_valid_iso6346_container

        valid_containers = [
            "MRSU3452572",
            "TCNU1234567",
            "MSKU9876543",
            "CAAU6541001",
            "TGBU5396610",
        ]

        for container in valid_containers:
            assert is_valid_iso6346_container(container) is True, f"{container} should be valid"

    def test_invalid_iso6346_formats(self):
        """Invalid formats should fail validation."""
        from app.services.shipment_data_extractor import is_valid_iso6346_container

        invalid_containers = [
            "BECKMANN-CNT-001",  # Placeholder pattern
            "ABC123",            # Too short
            "MRSU12345678",      # Too long (8 digits)
            "1234567890A",       # Starts with numbers
            "ABCD123456",        # Only 6 digits
            "",                  # Empty
        ]

        for container in invalid_containers:
            assert is_valid_iso6346_container(container) is False, f"{container} should be invalid"


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def test_high_confidence_for_labeled_container(self):
        """Container with 'Container No.:' label should have high confidence."""
        from app.services.shipment_data_extractor import ShipmentDataExtractor

        extractor = ShipmentDataExtractor()
        text = "Container No.: MRSU3452572"
        result = extractor.extract_container_with_confidence(text)

        assert result is not None
        _, confidence = result
        assert confidence >= 0.9

    def test_medium_confidence_for_pattern_only(self):
        """Container without label should have medium confidence."""
        from app.services.shipment_data_extractor import ShipmentDataExtractor

        extractor = ShipmentDataExtractor()
        text = "MRSU3452572"  # Just the container, no label
        result = extractor.extract_container_with_confidence(text)

        assert result is not None
        _, confidence = result
        assert 0.5 <= confidence < 0.9
