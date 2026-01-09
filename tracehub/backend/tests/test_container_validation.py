"""
Container Number Validation Tests - ISO 6346 Format

TDD Red Phase: These tests define the expected behavior for container number
validation following the ISO 6346 standard.

ISO 6346 Container Number Format:
- 4 uppercase letters (owner code)
- 6 digits (serial number)
- 1 check digit
- Total: 11 characters

Example valid containers:
- MRSU3452572
- TCNU1234567
- MSKU9876543
- HLXU1234561

These tests are expected to FAIL until the validator is implemented
in app/schemas/shipment.py using Pydantic's field_validator.
"""
import pytest
from pydantic import ValidationError
import uuid

from app.schemas.shipment import ShipmentCreate


# =============================================================================
# Test Container Format Validation
# =============================================================================

class TestContainerFormatValidation:
    """
    Test ISO 6346 container number format validation.

    Expected format: 4 uppercase letters + 6 digits + 1 check digit = 11 chars
    Pattern: ^[A-Z]{4}[0-9]{7}$
    """

    def test_valid_container_format_accepted(self):
        """Valid ISO 6346 container numbers should be accepted."""
        # Arrange
        valid_containers = [
            "MRSU3452572",  # Standard format
            "TCNU1234567",  # Another valid container
            "MSKU9876543",  # Maersk-style
            "HLXU1234561",  # Hapag-Lloyd style
            "CSQU3054383",  # COSCO style
            "MSCU1234567",  # MSC style
        ]

        # Act & Assert - validator should accept these without raising
        for container in valid_containers:
            # This should NOT raise ValidationError
            shipment = ShipmentCreate(
                reference=f"TEST-{container}",
                container_number=container,
                organization_id=uuid.uuid4()
            )
            assert shipment.container_number == container

    def test_valid_container_lowercase_uppercased(self):
        """Lowercase container numbers should be auto-uppercased.

        User input 'mrsu3452572' should become 'MRSU3452572'.
        """
        # Arrange
        lowercase_container = "mrsu3452572"
        expected_upper = "MRSU3452572"

        # Act
        shipment = ShipmentCreate(
            reference="TEST-LOWERCASE",
            container_number=lowercase_container,
            organization_id=uuid.uuid4()
        )

        # Assert - should be normalized to uppercase
        assert shipment.container_number == expected_upper

    def test_invalid_container_too_short_rejected(self):
        """Container numbers that are too short should be rejected.

        'ABC123' is only 6 characters, should raise ValueError.
        """
        # Arrange
        short_container = "ABC123"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-SHORT",
                container_number=short_container,
                organization_id=uuid.uuid4()
            )

        # Verify the error message mentions container validation
        error_detail = str(exc_info.value)
        assert "container" in error_detail.lower() or "6 characters" in error_detail.lower()

    def test_invalid_container_too_long_rejected(self):
        """Container numbers that are too long should be rejected.

        'MRSU12345678' is 12 characters, should raise ValueError.
        """
        # Arrange
        long_container = "MRSU12345678"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-LONG",
                container_number=long_container,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_wrong_format_rejected(self):
        """Container numbers with wrong format should be rejected.

        '1234MRSU567' has digits before letters - invalid order.
        """
        # Arrange
        wrong_format = "1234MRSU567"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-WRONGFORMAT",
                container_number=wrong_format,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_with_dashes_rejected(self):
        """Container numbers with dashes should be rejected.

        'MRSU-123-4567' contains dashes which are not allowed.
        """
        # Arrange
        dashed_container = "MRSU-123-4567"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-DASHED",
                container_number=dashed_container,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_special_chars_rejected(self):
        """Container numbers with special characters should be rejected.

        'MRSU@#$%567' contains special characters - not valid.
        """
        # Arrange
        special_container = "MRSU@#$%567"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-SPECIAL",
                container_number=special_container,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_letters_in_digit_section(self):
        """Container numbers with letters in digit section should be rejected.

        'MRSU123456A' has a letter where only digits are allowed.
        """
        # Arrange
        mixed_container = "MRSU123456A"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-MIXED",
                container_number=mixed_container,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_only_digits_rejected(self):
        """Container numbers with only digits should be rejected.

        '12345678901' has no owner code letters.
        """
        # Arrange
        digits_only = "12345678901"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-DIGITSONLY",
                container_number=digits_only,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_only_letters_rejected(self):
        """Container numbers with only letters should be rejected.

        'ABCDEFGHIJK' has no serial number digits.
        """
        # Arrange
        letters_only = "ABCDEFGHIJK"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-LETTERSONLY",
                container_number=letters_only,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_empty_rejected(self):
        """Empty container numbers should be rejected."""
        # Arrange
        empty_container = ""

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-EMPTY",
                container_number=empty_container,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None

    def test_invalid_container_whitespace_rejected(self):
        """Container numbers with only whitespace should be rejected."""
        # Arrange
        whitespace_container = "   "

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-WHITESPACE",
                container_number=whitespace_container,
                organization_id=uuid.uuid4()
            )

        # Verify validation error is raised
        assert exc_info.value is not None


# =============================================================================
# Test ShipmentCreate Schema Validation
# =============================================================================

class TestShipmentCreateSchemaValidation:
    """
    Test ShipmentCreate schema validation for container numbers.

    These tests verify that the Pydantic schema correctly validates
    container numbers during shipment creation.
    """

    def test_shipment_create_with_valid_container(self):
        """ShipmentCreate should accept valid container numbers."""
        # Arrange
        valid_container = "TCNU1234567"
        org_id = uuid.uuid4()

        # Act
        shipment = ShipmentCreate(
            reference="VIB-2026-001",
            container_number=valid_container,
            organization_id=org_id,
            vessel_name="Ever Given",
            pol_code="NGLOS",
            pod_code="DEHAM"
        )

        # Assert
        assert shipment.container_number == valid_container
        assert shipment.reference == "VIB-2026-001"
        assert shipment.organization_id == org_id

    def test_shipment_create_with_invalid_container_raises(self):
        """ShipmentCreate should raise ValidationError for invalid containers."""
        # Arrange
        invalid_container = "INVALID123"  # Only 3 letters, wrong format

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="VIB-2026-002",
                container_number=invalid_container,
                organization_id=uuid.uuid4()
            )

        # Verify the error is about container_number field
        errors = exc_info.value.errors()
        container_errors = [e for e in errors if "container" in str(e.get("loc", []))]
        assert len(container_errors) > 0

    def test_shipment_create_normalizes_lowercase_container(self):
        """ShipmentCreate should normalize lowercase to uppercase."""
        # Arrange
        lowercase_container = "msku9876543"
        expected_upper = "MSKU9876543"

        # Act
        shipment = ShipmentCreate(
            reference="VIB-2026-003",
            container_number=lowercase_container,
            organization_id=uuid.uuid4()
        )

        # Assert - container should be uppercased
        assert shipment.container_number == expected_upper

    def test_shipment_create_with_mixed_case_container(self):
        """ShipmentCreate should handle mixed case containers."""
        # Arrange
        mixed_case = "MrSu3452572"
        expected_upper = "MRSU3452572"

        # Act
        shipment = ShipmentCreate(
            reference="VIB-2026-004",
            container_number=mixed_case,
            organization_id=uuid.uuid4()
        )

        # Assert
        assert shipment.container_number == expected_upper

    def test_shipment_create_strips_whitespace(self):
        """ShipmentCreate should strip leading/trailing whitespace."""
        # Arrange
        padded_container = "  HLXU1234561  "
        expected_clean = "HLXU1234561"

        # Act
        shipment = ShipmentCreate(
            reference="VIB-2026-005",
            container_number=padded_container,
            organization_id=uuid.uuid4()
        )

        # Assert
        assert shipment.container_number == expected_clean


# =============================================================================
# Test Error Messages
# =============================================================================

class TestContainerValidationErrorMessages:
    """
    Test that validation errors provide helpful error messages.
    """

    def test_error_message_mentions_iso_6346(self):
        """Error message should reference ISO 6346 format."""
        # Arrange
        invalid_container = "BAD"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-MSG",
                container_number=invalid_container,
                organization_id=uuid.uuid4()
            )

        # Verify error message is helpful
        error_str = str(exc_info.value)
        # Should mention the expected format or ISO standard
        assert any(term in error_str.lower() for term in [
            "iso 6346",
            "4 letters",
            "7 digits",
            "format",
            "pattern"
        ])

    def test_error_message_shows_expected_pattern(self):
        """Error message should show the expected pattern."""
        # Arrange
        invalid_container = "WRONG"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ShipmentCreate(
                reference="TEST-PATTERN",
                container_number=invalid_container,
                organization_id=uuid.uuid4()
            )

        # Verify the error includes pattern info or example
        errors = exc_info.value.errors()
        assert len(errors) > 0
        # The error should be from container_number field
        field_names = [str(e.get("loc", [])) for e in errors]
        assert any("container" in name.lower() for name in field_names)
