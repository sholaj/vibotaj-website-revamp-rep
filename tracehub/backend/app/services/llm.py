"""LLM backend protocol for AI operations (PRD-019).

Provider-agnostic interface for language model interactions.
Same pattern as StorageBackend (PRD-005).

Implementations:
- AnthropicBackend: Claude (default)
- MockLLMBackend: Tests
- Future: OpenAIBackend, etc.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol

from ..models.document import DocumentType


@dataclass
class ClassificationResult:
    """Result of AI document classification."""

    document_type: DocumentType
    confidence: float
    method: str  # "ai", "keyword"
    provider: str  # "anthropic", "openai", "keyword", "mock"
    reference_number: Optional[str] = None
    key_fields: Dict[str, str] = field(default_factory=dict)
    reasoning: str = ""
    alternatives: List[Dict[str, object]] = field(default_factory=list)


class LLMBackend(Protocol):
    """Protocol for LLM operations.

    Implementations must provide document classification
    and general text completion. Provider-specific details
    (model name, API key, etc.) are handled internally.
    """

    def classify_document(self, text: str) -> Optional[ClassificationResult]:
        """Classify a document from its text content.

        Args:
            text: Extracted text from the document (truncated to model limits).

        Returns:
            ClassificationResult or None if classification fails.
        """
        ...

    def complete(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """General-purpose text completion.

        Args:
            prompt: The prompt to send to the LLM.
            max_tokens: Maximum tokens in the response.

        Returns:
            Response text or None if the call fails.
        """
        ...

    def is_available(self) -> bool:
        """Check if the LLM backend is operational."""
        ...

    def get_provider_name(self) -> str:
        """Return the provider identifier (e.g. 'anthropic', 'openai')."""
        ...

    def get_status(self) -> Dict[str, object]:
        """Return detailed status information."""
        ...
