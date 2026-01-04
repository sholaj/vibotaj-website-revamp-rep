"""Document classifier service using AI for document type detection.

Provides automatic document type detection with:
1. AI-based classification (when credits available)
2. Keyword-based fallback (always available)
"""

import os
import re
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
{{
  "document_type": "type_name",
  "confidence": 0.0 to 1.0,
  "reference_number": "extracted reference number or null",
  "key_fields": {{
    "issuer": "issuing authority/company",
    "date": "document date if found",
    "other_relevant_fields": "..."
  }},
  "reasoning": "Brief explanation of why this type was chosen"
}}
"""


class DocumentClassifier:
    """Service for classifying document types using AI with keyword fallback."""

    def __init__(self):
        self.client = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self._ai_status = AIStatus.AVAILABLE
        self._last_error: Optional[str] = None

        # Log initialization details
        logger.info(f"Initializing document classifier. AI library available: {AI_AVAILABLE}")
        api_key_present = bool(self.api_key)
        api_key_prefix = self.api_key[:15] + "..." if self.api_key else "None"
        logger.info(f"ANTHROPIC_API_KEY present: {api_key_present}, prefix: {api_key_prefix}")

        if not AI_AVAILABLE:
            self._ai_status = AIStatus.NO_LIBRARY
            logger.warning("Anthropic library not installed. Using keyword-based classification.")
        elif not self.api_key:
            self._ai_status = AIStatus.NO_API_KEY
            logger.warning("ANTHROPIC_API_KEY not set. Using keyword-based classification.")
        else:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self._ai_status = AIStatus.AVAILABLE
                logger.info("AI document classifier initialized successfully with Claude Haiku")
            except Exception as e:
                self._ai_status = AIStatus.API_ERROR
                self._last_error = str(e)
                logger.error(f"Failed to initialize AI client: {e}")

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
            logger.info("Calling Claude API for classification...")

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast, cost-effective model
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": CLASSIFICATION_PROMPT.format(text=text_preview)
                }]
            )

            # Log message structure for debugging
            logger.info(f"Message type: {type(message)}")
            logger.info(f"Message content type: {type(message.content)}")
            logger.info(f"Message content length: {len(message.content) if message.content else 0}")

            if message.content:
                first_block = message.content[0]
                logger.info(f"First content block type: {type(first_block)}")
                logger.info(f"First content block dir: {[attr for attr in dir(first_block) if not attr.startswith('_')]}")

                # Handle different content block types
                if hasattr(first_block, 'text'):
                    response_text = first_block.text
                elif isinstance(first_block, dict) and 'text' in first_block:
                    response_text = first_block['text']
                else:
                    response_text = str(first_block)
                    logger.warning(f"Unexpected content block format, using str(): {response_text[:100]}")
            else:
                logger.error("Empty message content from Claude API")
                return None

            logger.info(f"Raw AI response (first 300 chars): {response_text[:300]}")

            # Extract JSON from response using multiple strategies
            json_text = None

            # Strategy 1: Handle markdown code blocks
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                parts = response_text.split("```")
                if len(parts) >= 2:
                    json_text = parts[1]

            # Strategy 2: Find JSON object by matching braces
            if not json_text:
                # Find the first { and match to its closing }
                start_idx = response_text.find('{')
                if start_idx != -1:
                    brace_count = 0
                    end_idx = start_idx
                    for i, char in enumerate(response_text[start_idx:], start_idx):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    if end_idx > start_idx:
                        json_text = response_text[start_idx:end_idx]

            # Strategy 3: Try the whole response as last resort
            if not json_text:
                json_text = response_text

            logger.info(f"Extracted JSON (first 200 chars): {json_text[:200] if json_text else 'None'}")

            if not json_text:
                logger.error(f"Could not extract JSON from response: {response_text[:200]}")
                return None

            data = json.loads(json_text.strip())

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
