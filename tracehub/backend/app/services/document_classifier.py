"""Document classifier service using AI for document type detection."""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..models.document import DocumentType
from .pdf_processor import DocumentSection, pdf_processor

logger = logging.getLogger(__name__)

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
    """Service for classifying document types using AI."""

    def __init__(self):
        self.client = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        if AI_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("AI document classifier initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize AI client: {e}")
        else:
            if not AI_AVAILABLE:
                logger.info("Anthropic library not installed. Using keyword-based classification.")
            elif not self.api_key:
                logger.info("ANTHROPIC_API_KEY not set. Using keyword-based classification.")

    def is_ai_available(self) -> bool:
        """Check if AI classification is available."""
        return self.client is not None

    def classify_with_ai(self, text: str) -> Optional[ClassificationResult]:
        """Classify document type using AI.

        Args:
            text: Text content from the document (first 2000 chars recommended)

        Returns:
            ClassificationResult or None if AI is unavailable
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
