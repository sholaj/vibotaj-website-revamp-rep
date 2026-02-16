"""Anthropic (Claude) LLM backend implementation (PRD-019).

Uses the Anthropic Python SDK for document classification
and general text completion. Reads config from pydantic-settings.
"""

import json
import logging
from typing import Dict, List, Optional

from ..config import get_settings
from ..models.document import DocumentType
from .llm import ClassificationResult

logger = logging.getLogger(__name__)

# Check if anthropic library is installed
try:
    import anthropic

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    anthropic = None  # type: ignore[assignment]


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
    "date": "document date if found"
  }},
  "reasoning": "Brief explanation of why this type was chosen",
  "alternatives": [
    {{"document_type": "other_possible_type", "confidence": 0.0 to 1.0}}
  ]
}}
"""

# Maximum text to send to the model
MAX_TEXT_LENGTH = 4000


class AnthropicBackend:
    """Claude LLM backend via Anthropic API.

    Reads API key and model name from pydantic-settings config.
    Falls back gracefully if the library or API key is missing.
    """

    def __init__(self) -> None:
        self._client: Optional[object] = None
        self._available = False
        self._last_error: Optional[str] = None

        settings = get_settings()
        api_key = settings.anthropic_api_key
        # SecretStr: get the underlying value
        raw_key = api_key.get_secret_value() if hasattr(api_key, "get_secret_value") else str(api_key)

        self._model = settings.llm_model

        if not _ANTHROPIC_AVAILABLE:
            self._last_error = "anthropic library not installed"
            logger.warning("Anthropic library not installed — LLM unavailable")
            return

        if not raw_key:
            self._last_error = "ANTHROPIC_API_KEY not set"
            logger.warning("ANTHROPIC_API_KEY not set — LLM unavailable")
            return

        try:
            self._client = anthropic.Anthropic(api_key=raw_key)
            self._available = True
            logger.info(
                "AnthropicBackend initialized (model=%s)", self._model
            )
        except Exception as exc:
            self._last_error = str(exc)
            logger.error("Failed to initialize Anthropic client: %s", exc)

    # --- LLMBackend Protocol ---

    def classify_document(self, text: str) -> Optional[ClassificationResult]:
        """Classify a document using Claude."""
        if not self._client:
            return None

        text_preview = text[:MAX_TEXT_LENGTH]
        prompt = CLASSIFICATION_PROMPT.format(text=text_preview)

        try:
            message = self._client.messages.create(  # type: ignore[union-attr]
                model=self._model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = self._extract_text(message)
            if not response_text:
                return None

            data = self._parse_json(response_text)
            if not data:
                return None

            return self._build_result(data)

        except Exception as exc:
            self._handle_error(exc)
            return None

    def complete(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """General text completion via Claude."""
        if not self._client:
            return None

        try:
            message = self._client.messages.create(  # type: ignore[union-attr]
                model=self._model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._extract_text(message)
        except Exception as exc:
            self._handle_error(exc)
            return None

    def is_available(self) -> bool:
        """Check if the Anthropic backend is operational."""
        return self._available

    def get_provider_name(self) -> str:
        """Return 'anthropic'."""
        return "anthropic"

    def get_status(self) -> Dict[str, object]:
        """Return detailed status."""
        return {
            "provider": "anthropic",
            "available": self._available,
            "model": self._model,
            "has_library": _ANTHROPIC_AVAILABLE,
            "last_error": self._last_error,
        }

    # --- Internal helpers ---

    @staticmethod
    def _extract_text(message: object) -> Optional[str]:
        """Extract text from an Anthropic message response."""
        content = getattr(message, "content", None)
        if not content:
            return None

        first_block = content[0]
        if hasattr(first_block, "text"):
            return first_block.text
        if isinstance(first_block, dict) and "text" in first_block:
            return first_block["text"]
        return str(first_block)

    @staticmethod
    def _parse_json(text: str) -> Optional[Dict]:
        """Extract JSON from model response text."""
        json_text = None

        # Strategy 1: markdown code blocks
        if "```json" in text:
            json_text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                json_text = parts[1]

        # Strategy 2: brace matching
        if not json_text:
            start = text.find("{")
            if start != -1:
                depth = 0
                for i, ch in enumerate(text[start:], start):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            json_text = text[start : i + 1]
                            break

        # Strategy 3: whole response
        if not json_text:
            json_text = text

        try:
            return json.loads(json_text.strip())
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse JSON from LLM response")
            return None

    def _build_result(self, data: Dict) -> ClassificationResult:
        """Build a ClassificationResult from parsed JSON."""
        type_str = data.get("document_type", "other")
        try:
            doc_type = DocumentType(type_str)
        except ValueError:
            doc_type = DocumentType.OTHER

        alternatives: List[Dict[str, object]] = []
        for alt in data.get("alternatives", []):
            if isinstance(alt, dict) and "document_type" in alt:
                alternatives.append({
                    "document_type": str(alt["document_type"]),
                    "confidence": float(alt.get("confidence", 0)),
                })

        self._available = True
        self._last_error = None

        return ClassificationResult(
            document_type=doc_type,
            confidence=float(data.get("confidence", 0.5)),
            method="ai",
            provider="anthropic",
            reference_number=data.get("reference_number"),
            key_fields=data.get("key_fields", {}),
            reasoning=data.get("reasoning", ""),
            alternatives=alternatives,
        )

    def _handle_error(self, exc: Exception) -> None:
        """Categorize and log API errors."""
        error_str = str(exc).lower()
        if "credit" in error_str or "insufficient" in error_str:
            self._last_error = "API credits exhausted"
        elif "rate limit" in error_str or "429" in error_str:
            self._last_error = "Rate limited"
        elif "authentication" in error_str or "401" in error_str:
            self._available = False
            self._last_error = "Invalid API key"
        else:
            self._last_error = str(exc)
        logger.error("Anthropic API error: %s", exc)
