"""Mock LLM backend for testing (PRD-019).

Returns deterministic results for unit tests without
requiring an API key or network access.
"""

from typing import Dict, List, Optional

from ..models.document import DocumentType
from .llm import ClassificationResult


class MockLLMBackend:
    """Mock LLM backend that returns configurable results.

    Use in tests to control classification output without
    hitting any external API.
    """

    def __init__(
        self,
        default_type: DocumentType = DocumentType.BILL_OF_LADING,
        default_confidence: float = 0.85,
        available: bool = True,
    ) -> None:
        self._default_type = default_type
        self._default_confidence = default_confidence
        self._available = available
        self._last_prompt: Optional[str] = None
        self._call_count = 0

    # --- LLMBackend Protocol ---

    def classify_document(self, text: str) -> Optional[ClassificationResult]:
        """Return a deterministic classification result."""
        if not self._available:
            return None

        self._last_prompt = text
        self._call_count += 1

        return ClassificationResult(
            document_type=self._default_type,
            confidence=self._default_confidence,
            method="ai",
            provider="mock",
            reference_number="MOCK-REF-001",
            key_fields={"issuer": "Mock Issuer", "date": "2026-02-16"},
            reasoning="Mock classification result",
            alternatives=[
                {"document_type": "commercial_invoice", "confidence": 0.10}
            ],
        )

    def complete(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """Return a mock completion."""
        if not self._available:
            return None

        self._last_prompt = prompt
        self._call_count += 1
        return "Mock LLM response"

    def is_available(self) -> bool:
        """Return configured availability."""
        return self._available

    def get_provider_name(self) -> str:
        """Return 'mock'."""
        return "mock"

    def get_status(self) -> Dict[str, object]:
        """Return mock status."""
        return {
            "provider": "mock",
            "available": self._available,
            "model": "mock-v1",
            "call_count": self._call_count,
        }

    # --- Test helpers ---

    @property
    def last_prompt(self) -> Optional[str]:
        """Get the last prompt sent to the mock."""
        return self._last_prompt

    @property
    def call_count(self) -> int:
        """Get the total number of calls."""
        return self._call_count

    def set_available(self, available: bool) -> None:
        """Toggle availability for testing fallback paths."""
        self._available = available

    def set_result(
        self, doc_type: DocumentType, confidence: float
    ) -> None:
        """Configure the result for the next call."""
        self._default_type = doc_type
        self._default_confidence = confidence
