"""Document validation rules engine.

Provides a modular, extensible system for validating shipment documents.
Includes AI-powered relevance validation to detect and reject unrelated documents.

TDD Implementation - tests written first, implementation follows.

Usage:
    from app.services.document_rules import ValidationRunner, get_registry

    runner = ValidationRunner()
    report = runner.validate_shipment(shipment, documents, user="admin@example.com", db=db)

    if not report.is_valid:
        print(f"Validation failed: {report.failed} errors, {report.warnings} warnings")
        for result in report.results:
            if not result.passed:
                print(f"  - {result.rule_name}: {result.message}")

See PRP-document-validation-rules-engine.md for full specification.
"""

from .base import (
    ValidationRule,
    RuleResult,
    RuleSeverity,
    RuleCategory,
)
from .context import ValidationContext
from .registry import RuleRegistry, get_registry, register_default_rules
from .runner import ValidationRunner, ValidationReport

__all__ = [
    # Base classes
    "ValidationRule",
    "RuleResult",
    "RuleSeverity",
    "RuleCategory",
    # Context
    "ValidationContext",
    # Registry
    "RuleRegistry",
    "get_registry",
    "register_default_rules",
    # Runner
    "ValidationRunner",
    "ValidationReport",
]
