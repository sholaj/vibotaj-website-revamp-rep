"""Rule registry for managing validation rules.

The RuleRegistry is a singleton that holds all registered validation rules.
It supports:
- Registering rules at startup
- Filtering rules by product type
- Resetting for testing
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from collections import defaultdict

from .base import ValidationRule, RuleCategory

if TYPE_CHECKING:
    from ...models.shipment import ProductType


class RuleRegistry:
    """Central registry of all validation rules.

    This is a singleton that holds all registered validation rules.
    Rules can be registered at startup and retrieved by category
    or product type.

    For testing, use reset() to clear the registry and register
    custom rules:

        RuleRegistry.reset()
        registry = RuleRegistry()
        registry.register(MyTestRule())
    """

    _instance: Optional["RuleRegistry"] = None
    _rules: Dict[str, ValidationRule]
    _rules_by_category: Dict[RuleCategory, List[ValidationRule]]

    def __new__(cls) -> "RuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._rules = {}
            cls._instance._rules_by_category = defaultdict(list)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance.

        Use this in tests to start with a fresh registry.
        """
        cls._instance = None

    def register(self, rule: ValidationRule) -> None:
        """Register a validation rule.

        Args:
            rule: The rule instance to register

        Raises:
            ValueError: If a rule with the same ID is already registered
        """
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule {rule.rule_id} is already registered")

        self._rules[rule.rule_id] = rule
        self._rules_by_category[rule.category].append(rule)

    def unregister(self, rule_id: str) -> None:
        """Unregister a rule by ID.

        Args:
            rule_id: The ID of the rule to remove
        """
        if rule_id in self._rules:
            rule = self._rules[rule_id]
            del self._rules[rule_id]
            self._rules_by_category[rule.category].remove(rule)

    def get_all_rules(self) -> List[ValidationRule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def get_rules_by_category(self, category: RuleCategory) -> List[ValidationRule]:
        """Get all rules in a specific category."""
        return self._rules_by_category.get(category, [])

    def get_rules_for_product_type(
        self, product_type: Optional["ProductType"]
    ) -> List[ValidationRule]:
        """Get rules applicable to a specific product type.

        Args:
            product_type: The product type to filter by

        Returns:
            List of rules that apply to this product type
        """
        product_type_value = product_type.value if product_type else None
        return [
            rule for rule in self._rules.values()
            if rule.should_apply(product_type_value)
        ]

    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get a specific rule by ID."""
        return self._rules.get(rule_id)

    def __len__(self) -> int:
        """Return the number of registered rules."""
        return len(self._rules)


# Default registry instance - populated by register_default_rules()
_default_registry: Optional[RuleRegistry] = None


def get_registry() -> RuleRegistry:
    """Get the default rule registry.

    Returns the singleton registry with all default rules registered.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = register_default_rules()
    return _default_registry


def register_default_rules(registry: Optional[RuleRegistry] = None) -> RuleRegistry:
    """Register all built-in validation rules.

    Args:
        registry: Optional registry to use. If None, creates new singleton.

    Returns:
        The registry with all default rules registered.
    """
    if registry is None:
        RuleRegistry.reset()
        registry = RuleRegistry()

    # Import and register all rule modules
    from .presence_rules import RequiredDocumentsPresentRule
    from .uniqueness_rules import NoDuplicateDocumentsRule
    from .relevance_rules import DocumentRelevanceRule
    from .horn_hoof_rules import (
        VetCertIssueDateRule,
        VetCertAuthorizedSignerRule,
    )

    rules = [
        RequiredDocumentsPresentRule(),
        NoDuplicateDocumentsRule(),
        DocumentRelevanceRule(),
        VetCertIssueDateRule(),
        VetCertAuthorizedSignerRule(),
    ]

    for rule in rules:
        registry.register(rule)

    return registry
