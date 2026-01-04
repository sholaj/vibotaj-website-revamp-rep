"""Document classifier service using AI for document type detection.

Provides automatic document type detection with:
1. AI-based classification (when credits available)
2. Keyword-based fallback (always available)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..models.document import DocumentType
from .pdf_processor import DocumentSection, pdf_processor

logger = logging.getLogger(__name__)


class AIStatus(str, Enum):
    """Status of AI availability."""
    AVAILABLE = "available"
    NO_LIBRARY = "no_library"
    NO_API_KEY = "no_api_key"
    NO_CREDITS = "no_credits"
    API_ERROR = "api_error"
    RATE_LIMITED = "rate_limited"


# Check if AI is available
try:
    import anthropic
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    anthropic = None


@dataclass
class ClassificationResult:
    """Result of AI document classification."""
    document_type: DocumentType
    confidence: float
    reference_number: Optional[str]
    detected_fields: Dict[str, Any]
    reasoning: str


CLASSIFICATION_PROMPT = """You are analyzing a document extract from a shipping/export PDF.
Identify what type of document this is based on the content.

Document types to choose from:
- bill_of_lading: Ocean bill of lading, transport document
- commercial_invoice: Commercial invoice, sales invoice
- packing_list: Packing list, cargo details
- certificate_of_origin: Certificate of origin, COO
- phytosanitary_certificate: Plant health certificate
- fumigation_certificate: Fumigation/pest treatment certificate
- sanitary_certificate: Veterinary/health certificate for animal products
- insurance_certificate: Cargo insurance
- customs_declaration: Export/import customs declaration
- contract: Sales contract, purchase agreement
- eudr_due_diligence: EU deforestation regulation statement
- quality_certificate: Quality/inspection certificate
- eu_traces_certificate: EU TRACES (CHED) animal health certificate for EU imports
- veterinary_health_certificate: Veterinary health certificate from origin country
- export_declaration: Export declaration / NXP form
- other: Unknown or cannot determine

Extract from document:
---
{text}
---

Respond in JSON format:
{
  "document_type": "type_name",
  "confidence": 0.0 to 1.0,
  "reference_number": "extracted reference number or null",
  "key_fields": {
    "issuer": "issuing authority/company",
    "date": "document date if found",
    "other_relevant_fields": "..."
  },
  "reasoning": "Brief explanation of why this type was chosen"
}
"""


class DocumentClassifier:
    """Service for classifying document types using AI with keyword fallback."""

    def __init__(self):
        self.client = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self._ai_status = AIStatus.AVAILABLE
        self._last_error: Optional[str] = None

        if not AI_AVAILABLE:
            self._ai_status = AIStatus.NO_LIBRARY
            logger.info("Anthropic library not installed. Using keyword-based classification.")
        elif not self.api_key:
            self._ai_status = AIStatus.NO_API_KEY
            logger.info("ANTHROPIC_API_KEY not set. Using keyword-based classification.")
        else:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("AI document classifier initialized successfully")
            except Exception as e:
                self._ai_status = AIStatus.API_ERROR
                self._last_error = str(e)
                logger.warning(f"Failed to initialize AI client: {e}")

    def is_ai_available(self) -> bool:
        """Check if AI classification is available."""
        return self.client is not None and self._ai_status == AIStatus.AVAILABLE

    def get_ai_status(self) -> Dict[str, Any]:
        """Get detailed AI availability status."""
        return {
            "available": self.is_ai_available(),
            "status": self._ai_status.value,
            "has_api_key": bool(self.api_key),
            "has_library": AI_AVAILABLE,
            "last_error": self._last_error,
            "fallback_active": not self.is_ai_available(),
        }

    def classify_with_ai(self, text: str) -> Optional[ClassificationResult]:
        """Classify document type using AI.

        Args:
            text: Text content from the document (first 2000 chars recommended)

        Returns:
            ClassificationResult or None if AI is unavailable or fails
        """
        if not self.client:
            return None

        try:
            # Limit text to avoid token limits
            text_preview = text[:3000]

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast, cost-effective model
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": CLASSIFICATION_PROMPT.format(text=text_preview)
                }]
            )

            # Parse JSON response
            response_text = message.content[0].text
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            data = json.loads(response_text.strip())

            # Map to DocumentType enum
            type_str = data.get("document_type", "other")
            try:
                doc_type = DocumentType(type_str)
            except ValueError:
                doc_type = DocumentType.OTHER

            # Reset error status on success
            self._ai_status = AIStatus.AVAILABLE
            self._last_error = None

            return ClassificationResult(
                document_type=doc_type,
                confidence=float(data.get("confidence", 0.5)),
                reference_number=data.get("reference_number"),
                detected_fields=data.get("key_fields", {}),
                reasoning=data.get("reasoning", "")
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return None
        except Exception as e:
            error_str = str(e).lower()

            # Check for specific error types and update status
            if "credit balance" in error_str or "insufficient" in error_str:
                self._ai_status = AIStatus.NO_CREDITS
                self._last_error = "API credits exhausted. Using keyword-based classification."
                logger.warning(f"AI credits exhausted: {e}")
            elif "rate limit" in error_str or "429" in error_str:
                self._ai_status = AIStatus.RATE_LIMITED
                self._last_error = "API rate limited. Using keyword-based classification."
                logger.warning(f"AI rate limited: {e}")
            elif "authentication" in error_str or "401" in error_str or "invalid" in error_str:
                self._ai_status = AIStatus.NO_API_KEY
                self._last_error = "Invalid API key. Using keyword-based classification."
                logger.error(f"AI authentication error: {e}")
            else:
                self._ai_status = AIStatus.API_ERROR
                self._last_error = str(e)
                logger.error(f"AI classification error: {e}")

            return None

    def classify_section(self, section: DocumentSection) -> DocumentSection:
        """Enhance a document section with AI classification.

        Falls back to keyword-based results if AI is unavailable.
        """
        if not self.is_ai_available():
            return section

        result = self.classify_with_ai(section.text_preview)
        if result:
            # Update section with AI results if confidence is higher
            if result.confidence > section.confidence:
                section.document_type = result.document_type
                section.confidence = result.confidence
                section.detection_method = "ai"

            # Always update with AI-detected fields
            if result.reference_number and not section.reference_number:
                section.reference_number = result.reference_number

            section.detected_fields.update({
                "ai_reasoning": result.reasoning,
                "ai_fields": result.detected_fields
            })

        return section

    def analyze_pdf(self, file_path: str, use_ai: bool = True) -> List[DocumentSection]:
        """Analyze a PDF and classify all documents within it.

        Args:
            file_path: Path to the PDF file
            use_ai: Whether to use AI classification (if available)

        Returns:
            List of DocumentSection with classification results
        """
        # First, use keyword-based analysis
        sections = pdf_processor.analyze_pdf(file_path)

        # Enhance with AI if requested and available
        if use_ai and self.is_ai_available():
            sections = [self.classify_section(s) for s in sections]

        return sections

    def classify_with_keywords(self, text: str) -> ClassificationResult:
        """Classify document using keyword matching (always available).

        Args:
            text: Text content from the document

        Returns:
            ClassificationResult with keyword-based detection
        """
        type_scores = pdf_processor.detect_document_type_by_keywords(text)

        if type_scores:
            doc_type, confidence = type_scores[0]
            alternatives = [{"type": t.value, "confidence": c} for t, c in type_scores[1:4]]
        else:
            doc_type = DocumentType.OTHER
            confidence = 0.0
            alternatives = []

        # Try to extract reference number
        ref_number = pdf_processor.extract_reference_number(text, doc_type)

        return ClassificationResult(
            document_type=doc_type,
            confidence=confidence,
            reference_number=ref_number,
            detected_fields={
                "detection_method": "keyword",
                "alternatives": alternatives,
            },
            reasoning=f"Matched keywords for {doc_type.value}" if doc_type != DocumentType.OTHER else "No keywords matched"
        )

    def classify(self, text: str, prefer_ai: bool = True) -> ClassificationResult:
        """Classify document with automatic AI/keyword fallback.

        This is the main classification method that:
        1. Tries AI classification if available and requested
        2. Falls back to keyword matching on any failure
        3. Always returns a result

        Args:
            text: Text content from the document
            prefer_ai: Whether to try AI first (default True)

        Returns:
            ClassificationResult (always returns, never None)
        """
        result = None

        # Try AI first if requested and available
        if prefer_ai and self.client:
            result = self.classify_with_ai(text)
            if result:
                result.detected_fields["detection_method"] = "ai"

        # Fall back to keywords if AI failed or unavailable
        if result is None:
            result = self.classify_with_keywords(text)
            # Add AI status info to fallback result
            result.detected_fields["ai_status"] = self._ai_status.value
            if self._last_error:
                result.detected_fields["ai_error"] = self._last_error

        return result

    def quick_classify(self, text: str) -> DocumentType:
        """Quick classification using keywords only.

        Useful for real-time feedback during upload.
        """
        type_scores = pdf_processor.detect_document_type_by_keywords(text)
        if type_scores:
            return type_scores[0][0]
        return DocumentType.OTHER


# Global instance
document_classifier = DocumentClassifier()
