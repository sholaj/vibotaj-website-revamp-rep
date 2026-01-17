"""Base classes and interfaces for the document validation rules engine.

This module defines the core abstractions:
- RuleSeverity: How critical a rule failure is
- RuleCategory: What type of validation the rule performs
- RuleResult: The outcome of executing a single rule
- ValidationRule: Abstract base class for all validation rules
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .context import ValidationContext


class RuleSeverity(str, Enum):
    """Severity levels for validation rules.

    Determines how the system responds to rule failures:
    - CRITICAL: Blocks shipment, must be fixed immediately
    - ERROR: Blocks shipment, must be fixed
    - WARNING: Flagged for review, shipment can proceed
    - INFO: Informational only, no action required
    """
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleCategory(str, Enum):
    """Categories of validation rules.

    Used for organizing rules and filtering results:
    - PRESENCE: Checks that required documents exist
    - UNIQUENESS: Checks for duplicate documents
    - RELEVANCE: AI-based content relevance validation
    - CONTENT: Field-level content validation
    - CROSS_FIELD: Cross-document validation
    - DATE: Date-based rules (expiry, issue dates)
    """
    PRESENCE = "presence"
    UNIQUENESS = "uniqueness"
    RELEVANCE = "relevance"
    CONTENT = "content"
    CROSS_FIELD = "cross_field"
    DATE = "date"


@dataclass
class RuleResult:
    """Result of executing a single validation rule.

    Attributes:
        rule_id: Unique identifier for the rule (e.g., "PRESENCE_001")
        rule_name: Human-readable name of the rule
        passed: Whether the rule passed (True) or failed (False)
        severity: How critical the failure is
        message: Human-readable description of the result
        category: What type of validation this is
        document_type: Type of document this result relates to (if applicable)
        document_id: UUID of the specific document (if applicable)
        details: Additional structured data about the result
    """
    rule_id: str
    rule_name: str
    passed: bool
    severity: RuleSeverity
    message: str
    category: RuleCategory
    document_type: Optional[str] = None
    document_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
            "category": self.category.value,
            "document_type": self.document_type,
            "document_id": self.document_id,
            "details": self.details,
        }


class ValidationRule(ABC):
    """Abstract base class for all validation rules.

    All validation rules must inherit from this class and implement:
    - rule_id: Unique identifier (e.g., "PRESENCE_001")
    - name: Human-readable name
    - description: What the rule validates
    - category: The type of validation
    - validate(): The validation logic

    Optional attributes:
    - severity: Default severity level (default: ERROR)
    - applies_to: List of product types this rule applies to (None = all)

    Example:
        class MyCustomRule(ValidationRule):
            rule_id = "CUSTOM_001"
            name = "My Custom Rule"
            description = "Validates something custom"
            category = RuleCategory.CONTENT

            def validate(self, context: ValidationContext) -> RuleResult:
                # Validation logic here
                return RuleResult(...)
    """

    rule_id: str
    name: str
    description: str
    severity: RuleSeverity = RuleSeverity.ERROR
    category: RuleCategory

    # Product types this rule applies to. None means all product types.
    applies_to: Optional[List[str]] = None

    @abstractmethod
    def validate(self, context: "ValidationContext") -> RuleResult:
        """Execute the validation rule.

        Args:
            context: ValidationContext containing shipment, documents, and metadata

        Returns:
            RuleResult indicating pass/fail with details

        Note:
            Some rules may return a List[RuleResult] if they validate
            multiple items (e.g., relevance checks each document).
            The runner handles both single and list returns.
        """
        pass

    def should_apply(self, product_type: Optional[str]) -> bool:
        """Check if this rule applies to the given product type.

        Args:
            product_type: The product type value (e.g., "horn_hoof")

        Returns:
            True if the rule should be executed for this product type
        """
        if self.applies_to is None:
            return True
        if product_type is None:
            return True  # Apply to unknown types by default
        return product_type in self.applies_to

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.rule_id}: {self.name}>"
