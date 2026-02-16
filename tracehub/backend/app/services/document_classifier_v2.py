"""Document classifier v2 — uses LLMBackend abstraction (PRD-019).

Provider-agnostic classifier that routes AI calls through
the LLMBackend Protocol. Keyword fallback always available.
Replaces direct Anthropic usage from v1 document_classifier.py.
"""

import logging
from typing import Dict, List, Optional

from ..models.document import DocumentType
from .llm import ClassificationResult, LLMBackend
from .llm_factory import get_llm
from .pdf_processor import DocumentSection, pdf_processor

logger = logging.getLogger(__name__)


class DocumentClassifierV2:
    """Document classifier using LLMBackend for AI and keywords for fallback.

    The classifier never imports a specific LLM provider — it only
    talks through the LLMBackend Protocol, making the provider swappable.
    """

    def __init__(self, llm: Optional[LLMBackend] = None) -> None:
        self._llm = llm

    @property
    def llm(self) -> LLMBackend:
        """Lazy-load the LLM backend."""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def is_ai_available(self) -> bool:
        """Check if AI classification is available."""
        return self.llm.is_available()

    def get_ai_status(self) -> Dict[str, object]:
        """Get detailed AI availability status."""
        return self.llm.get_status()

    def classify(self, text: str, prefer_ai: bool = True) -> ClassificationResult:
        """Classify document with automatic AI/keyword fallback.

        1. Tries AI classification via LLMBackend if available
        2. Falls back to keyword matching on failure
        3. Always returns a result

        Args:
            text: Text content from the document.
            prefer_ai: Whether to try AI first (default True).

        Returns:
            ClassificationResult (always returns, never None).
        """
        result = None

        if prefer_ai and self.llm.is_available():
            result = self.llm.classify_document(text)

        if result is None:
            result = self.classify_with_keywords(text)

        return result

    def classify_with_keywords(self, text: str) -> ClassificationResult:
        """Classify document using keyword matching (always available).

        Args:
            text: Text content from the document.

        Returns:
            ClassificationResult with keyword-based detection.
        """
        type_scores = pdf_processor.detect_document_type_by_keywords(text)

        if type_scores:
            doc_type, confidence = type_scores[0]
            alternatives = [
                {"document_type": t.value, "confidence": c}
                for t, c in type_scores[1:4]
            ]
        else:
            doc_type = DocumentType.OTHER
            confidence = 0.0
            alternatives = []

        ref_number = pdf_processor.extract_reference_number(text, doc_type)

        return ClassificationResult(
            document_type=doc_type,
            confidence=confidence,
            method="keyword",
            provider="keyword",
            reference_number=ref_number,
            key_fields={},
            reasoning=(
                f"Matched keywords for {doc_type.value}"
                if doc_type != DocumentType.OTHER
                else "No keywords matched"
            ),
            alternatives=alternatives,
        )

    def classify_section(self, section: DocumentSection) -> DocumentSection:
        """Enhance a document section with AI classification.

        Falls back to keyword-based results if AI is unavailable.
        """
        if not self.llm.is_available():
            return section

        result = self.llm.classify_document(section.text_preview)
        if result:
            if result.confidence > section.confidence:
                section.document_type = result.document_type
                section.confidence = result.confidence
                section.detection_method = "ai"

            if result.reference_number and not section.reference_number:
                section.reference_number = result.reference_number

            section.detected_fields.update({
                "ai_reasoning": result.reasoning,
                "ai_fields": result.key_fields,
            })

        return section

    def analyze_pdf(
        self, file_path: str, use_ai: bool = True
    ) -> List[DocumentSection]:
        """Analyze a PDF and classify all documents within it.

        Args:
            file_path: Path to the PDF file.
            use_ai: Whether to use AI classification.

        Returns:
            List of DocumentSection with classification results.
        """
        sections = pdf_processor.analyze_pdf(file_path)

        if use_ai and self.llm.is_available():
            sections = [self.classify_section(s) for s in sections]

        return sections


# Global instance — uses get_llm() lazily
document_classifier_v2 = DocumentClassifierV2()
