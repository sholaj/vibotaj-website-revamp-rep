"""Tests for DocumentClassifierV2 with LLM abstraction (PRD-019).

Tests: AI classification via mock LLM, keyword fallback,
confidence threshold, provider-agnostic behavior.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.models.document import DocumentType
from app.services.llm import ClassificationResult
from app.services.llm_mock import MockLLMBackend
from app.services.document_classifier_v2 import DocumentClassifierV2


class TestClassifierWithMockLLM:
    """Tests for classifier using MockLLMBackend."""

    def test_classify_uses_llm_when_available(self):
        mock_llm = MockLLMBackend(
            default_type=DocumentType.BILL_OF_LADING,
            default_confidence=0.92,
        )
        classifier = DocumentClassifierV2(llm=mock_llm)
        result = classifier.classify("B/L No.: MSC1234567")
        assert result.document_type == DocumentType.BILL_OF_LADING
        assert result.confidence == 0.92
        assert result.method == "ai"
        assert result.provider == "mock"

    def test_falls_back_to_keywords_when_llm_unavailable(self):
        mock_llm = MockLLMBackend(available=False)
        classifier = DocumentClassifierV2(llm=mock_llm)
        result = classifier.classify("bill of lading shipper consignee vessel")
        assert result.method == "keyword"
        assert result.provider == "keyword"

    def test_falls_back_when_prefer_ai_false(self):
        mock_llm = MockLLMBackend()
        classifier = DocumentClassifierV2(llm=mock_llm)
        result = classifier.classify("bill of lading", prefer_ai=False)
        assert result.method == "keyword"
        assert mock_llm.call_count == 0

    def test_keyword_fallback_returns_result(self):
        mock_llm = MockLLMBackend(available=False)
        classifier = DocumentClassifierV2(llm=mock_llm)
        result = classifier.classify("some random text")
        assert result is not None
        assert isinstance(result.document_type, DocumentType)

    def test_is_ai_available_delegates_to_llm(self):
        mock_llm = MockLLMBackend(available=True)
        classifier = DocumentClassifierV2(llm=mock_llm)
        assert classifier.is_ai_available() is True

        mock_llm.set_available(False)
        assert classifier.is_ai_available() is False

    def test_get_ai_status_delegates_to_llm(self):
        mock_llm = MockLLMBackend()
        classifier = DocumentClassifierV2(llm=mock_llm)
        status = classifier.get_ai_status()
        assert status["provider"] == "mock"
        assert status["available"] is True


class TestClassifierKeywordOnly:
    """Tests for keyword-only classification."""

    def test_bol_keywords_detected(self):
        mock_llm = MockLLMBackend(available=False)
        classifier = DocumentClassifierV2(llm=mock_llm)
        text = "BILL OF LADING shipper consignee port vessel voyage container"
        result = classifier.classify_with_keywords(text)
        assert result.document_type == DocumentType.BILL_OF_LADING
        assert result.confidence > 0

    def test_invoice_keywords_detected(self):
        mock_llm = MockLLMBackend(available=False)
        classifier = DocumentClassifierV2(llm=mock_llm)
        text = "COMMERCIAL INVOICE total amount payment terms unit price quantity"
        result = classifier.classify_with_keywords(text)
        assert result.document_type == DocumentType.COMMERCIAL_INVOICE

    def test_unknown_text_returns_other(self):
        mock_llm = MockLLMBackend(available=False)
        classifier = DocumentClassifierV2(llm=mock_llm)
        result = classifier.classify_with_keywords("xyzzy foobar baz")
        assert result.document_type == DocumentType.OTHER
        assert result.confidence == 0.0

    def test_keyword_result_has_correct_method(self):
        mock_llm = MockLLMBackend(available=False)
        classifier = DocumentClassifierV2(llm=mock_llm)
        result = classifier.classify_with_keywords("packing list gross weight")
        assert result.method == "keyword"
        assert result.provider == "keyword"


class TestClassifierProviderAgnostic:
    """Tests verifying the classifier is provider-agnostic."""

    def test_classifier_accepts_any_llm_backend(self):
        """Verify that any object satisfying LLMBackend works."""

        class CustomBackend:
            def classify_document(self, text):
                return ClassificationResult(
                    document_type=DocumentType.CONTRACT,
                    confidence=0.99,
                    method="ai",
                    provider="custom",
                )

            def complete(self, prompt, max_tokens=1024):
                return "custom response"

            def is_available(self):
                return True

            def get_provider_name(self):
                return "custom"

            def get_status(self):
                return {"provider": "custom", "available": True}

        classifier = DocumentClassifierV2(llm=CustomBackend())
        result = classifier.classify("some contract text")
        assert result.document_type == DocumentType.CONTRACT
        assert result.provider == "custom"
        assert result.confidence == 0.99

    def test_classifier_never_imports_anthropic(self):
        """Ensure DocumentClassifierV2 has no direct anthropic dependency."""
        import inspect
        source = inspect.getsource(DocumentClassifierV2)
        assert "import anthropic" not in source
        assert "from anthropic" not in source


class TestClassificationSchemas:
    """Tests for classification Pydantic schemas."""

    def test_classification_response_creation(self):
        from app.schemas.classification import ClassificationResponse

        resp = ClassificationResponse(
            document_type="bill_of_lading",
            confidence=0.92,
            method="ai",
            provider="anthropic",
            reasoning="Matched BoL patterns",
        )
        assert resp.document_type == "bill_of_lading"
        assert resp.confidence == 0.92

    def test_classification_in_upload(self):
        from app.schemas.classification import ClassificationInUpload

        info = ClassificationInUpload(
            suggested_type="commercial_invoice",
            confidence=0.85,
            method="ai",
            auto_applied=True,
        )
        assert info.auto_applied is True
        data = info.model_dump()
        assert data["suggested_type"] == "commercial_invoice"

    def test_reclassify_response(self):
        from app.schemas.classification import (
            ReclassifyResponse,
            ClassificationResponse,
        )

        classification = ClassificationResponse(
            document_type="packing_list",
            confidence=0.78,
            method="keyword",
            provider="keyword",
        )
        resp = ReclassifyResponse(
            document_id="doc-123",
            previous_type="other",
            new_type="packing_list",
            classification=classification,
            auto_applied=True,
        )
        assert resp.previous_type == "other"
        assert resp.new_type == "packing_list"
