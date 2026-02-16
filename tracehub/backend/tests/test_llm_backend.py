"""Tests for LLM abstraction layer (PRD-019).

Tests: LLMBackend Protocol, MockLLMBackend, factory, AnthropicBackend init.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.models.document import DocumentType
from app.services.llm import ClassificationResult, LLMBackend
from app.services.llm_mock import MockLLMBackend
from app.services.llm_factory import _create_backend, reset_llm


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""

    def test_basic_creation(self):
        result = ClassificationResult(
            document_type=DocumentType.BILL_OF_LADING,
            confidence=0.92,
            method="ai",
            provider="anthropic",
        )
        assert result.document_type == DocumentType.BILL_OF_LADING
        assert result.confidence == 0.92
        assert result.method == "ai"
        assert result.provider == "anthropic"
        assert result.reference_number is None
        assert result.key_fields == {}
        assert result.reasoning == ""
        assert result.alternatives == []

    def test_full_creation(self):
        result = ClassificationResult(
            document_type=DocumentType.COMMERCIAL_INVOICE,
            confidence=0.88,
            method="ai",
            provider="anthropic",
            reference_number="INV-2026-001",
            key_fields={"issuer": "VIBOTAJ", "date": "2026-02-16"},
            reasoning="Matched invoice patterns",
            alternatives=[
                {"document_type": "packing_list", "confidence": 0.10}
            ],
        )
        assert result.reference_number == "INV-2026-001"
        assert result.key_fields["issuer"] == "VIBOTAJ"
        assert len(result.alternatives) == 1


class TestMockLLMBackend:
    """Tests for MockLLMBackend."""

    def test_classify_returns_result(self):
        mock = MockLLMBackend()
        result = mock.classify_document("Sample BoL text")
        assert result is not None
        assert result.document_type == DocumentType.BILL_OF_LADING
        assert result.confidence == 0.85
        assert result.provider == "mock"

    def test_classify_returns_none_when_unavailable(self):
        mock = MockLLMBackend(available=False)
        result = mock.classify_document("Sample text")
        assert result is None

    def test_complete_returns_string(self):
        mock = MockLLMBackend()
        result = mock.complete("Hello")
        assert result == "Mock LLM response"

    def test_complete_returns_none_when_unavailable(self):
        mock = MockLLMBackend(available=False)
        result = mock.complete("Hello")
        assert result is None

    def test_is_available(self):
        mock = MockLLMBackend(available=True)
        assert mock.is_available() is True

        mock2 = MockLLMBackend(available=False)
        assert mock2.is_available() is False

    def test_get_provider_name(self):
        mock = MockLLMBackend()
        assert mock.get_provider_name() == "mock"

    def test_get_status(self):
        mock = MockLLMBackend()
        status = mock.get_status()
        assert status["provider"] == "mock"
        assert status["available"] is True

    def test_call_count_tracks(self):
        mock = MockLLMBackend()
        assert mock.call_count == 0
        mock.classify_document("text")
        assert mock.call_count == 1
        mock.complete("text")
        assert mock.call_count == 2

    def test_last_prompt_stored(self):
        mock = MockLLMBackend()
        mock.classify_document("BoL text")
        assert mock.last_prompt == "BoL text"

    def test_set_result(self):
        mock = MockLLMBackend()
        mock.set_result(DocumentType.PACKING_LIST, 0.75)
        result = mock.classify_document("text")
        assert result is not None
        assert result.document_type == DocumentType.PACKING_LIST
        assert result.confidence == 0.75

    def test_set_available(self):
        mock = MockLLMBackend(available=True)
        assert mock.is_available() is True
        mock.set_available(False)
        assert mock.is_available() is False

    def test_configurable_defaults(self):
        mock = MockLLMBackend(
            default_type=DocumentType.CUSTOMS_DECLARATION,
            default_confidence=0.60,
        )
        result = mock.classify_document("text")
        assert result is not None
        assert result.document_type == DocumentType.CUSTOMS_DECLARATION
        assert result.confidence == 0.60


class TestLLMFactory:
    """Tests for LLM factory function."""

    def setup_method(self):
        reset_llm()

    def teardown_method(self):
        reset_llm()

    @patch("app.services.llm_factory.get_settings")
    def test_creates_mock_backend(self, mock_settings):
        mock_settings.return_value = MagicMock(llm_provider="mock")
        backend = _create_backend()
        assert backend.get_provider_name() == "mock"

    @patch("app.services.llm_factory.get_settings")
    def test_unknown_provider_falls_back_to_mock(self, mock_settings):
        mock_settings.return_value = MagicMock(llm_provider="unknown_provider")
        backend = _create_backend()
        assert backend.get_provider_name() == "mock"
        assert backend.is_available() is False

    @patch("app.services.llm_factory.get_settings")
    def test_anthropic_provider_creates_anthropic_backend(self, mock_settings):
        mock_settings.return_value = MagicMock(
            llm_provider="anthropic",
            anthropic_api_key="",
            llm_model="claude-haiku-4-5-20251001",
        )
        backend = _create_backend()
        assert backend.get_provider_name() == "anthropic"
        # Without a real API key, it should not be available
        assert backend.is_available() is False
