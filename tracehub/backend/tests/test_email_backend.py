"""Tests for email abstraction layer (PRD-020).

Tests: EmailBackend Protocol, ConsoleBackend, factory, ResendBackend init.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.email import EmailMessage, EmailResult
from app.services.email_console import ConsoleBackend
from app.services.email_factory import _create_backend, reset_email_backend


class TestEmailMessage:
    """Tests for EmailMessage dataclass."""

    def test_basic_creation(self):
        msg = EmailMessage(
            to="user@example.com",
            subject="Test Subject",
            html="<p>Hello</p>",
        )
        assert msg.to == "user@example.com"
        assert msg.subject == "Test Subject"
        assert msg.html == "<p>Hello</p>"
        assert msg.from_email is None
        assert msg.from_name is None
        assert msg.reply_to is None
        assert msg.tags == []

    def test_full_creation(self):
        msg = EmailMessage(
            to="user@example.com",
            subject="Test",
            html="<p>Hello</p>",
            from_email="sender@tracehub.com",
            from_name="TraceHub",
            reply_to="support@tracehub.com",
            tags=["document", "notification"],
        )
        assert msg.from_email == "sender@tracehub.com"
        assert msg.from_name == "TraceHub"
        assert msg.reply_to == "support@tracehub.com"
        assert len(msg.tags) == 2


class TestEmailResult:
    """Tests for EmailResult dataclass."""

    def test_success_result(self):
        result = EmailResult(
            success=True,
            provider="resend",
            message_id="msg-123",
        )
        assert result.success is True
        assert result.provider == "resend"
        assert result.message_id == "msg-123"
        assert result.error is None

    def test_failure_result(self):
        result = EmailResult(
            success=False,
            provider="resend",
            error="Rate limit exceeded",
        )
        assert result.success is False
        assert result.error == "Rate limit exceeded"
        assert result.message_id is None


class TestConsoleBackend:
    """Tests for ConsoleBackend."""

    def test_send_returns_success(self):
        backend = ConsoleBackend()
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")
        result = backend.send(msg)
        assert result.success is True
        assert result.provider == "console"
        assert result.message_id == "console-1"

    def test_send_tracks_messages(self):
        backend = ConsoleBackend()
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")
        backend.send(msg)
        assert len(backend.sent_messages) == 1
        assert backend.sent_messages[0].to == "user@test.com"

    def test_send_increments_call_count(self):
        backend = ConsoleBackend()
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")
        assert backend.call_count == 0
        backend.send(msg)
        assert backend.call_count == 1
        backend.send(msg)
        assert backend.call_count == 2

    def test_send_fails_when_unavailable(self):
        backend = ConsoleBackend(available=False)
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")
        result = backend.send(msg)
        assert result.success is False
        assert "disabled" in result.error

    def test_send_batch(self):
        backend = ConsoleBackend()
        messages = [
            EmailMessage(to="a@test.com", subject="A", html="<p>A</p>"),
            EmailMessage(to="b@test.com", subject="B", html="<p>B</p>"),
        ]
        results = backend.send_batch(messages)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert len(backend.sent_messages) == 2

    def test_is_available(self):
        assert ConsoleBackend(available=True).is_available() is True
        assert ConsoleBackend(available=False).is_available() is False

    def test_get_provider_name(self):
        assert ConsoleBackend().get_provider_name() == "console"

    def test_get_status(self):
        backend = ConsoleBackend()
        status = backend.get_status()
        assert status["provider"] == "console"
        assert status["available"] is True
        assert status["sent_count"] == 0

    def test_set_available(self):
        backend = ConsoleBackend(available=True)
        assert backend.is_available() is True
        backend.set_available(False)
        assert backend.is_available() is False

    def test_reset(self):
        backend = ConsoleBackend()
        backend.send(EmailMessage(to="a@t.com", subject="X", html="<p>X</p>"))
        assert backend.call_count == 1
        assert len(backend.sent_messages) == 1
        backend.reset()
        assert backend.call_count == 0
        assert len(backend.sent_messages) == 0

    def test_last_message(self):
        backend = ConsoleBackend()
        assert backend.last_message() is None
        backend.send(EmailMessage(to="a@t.com", subject="First", html="<p>1</p>"))
        backend.send(EmailMessage(to="b@t.com", subject="Second", html="<p>2</p>"))
        assert backend.last_message() is not None
        assert backend.last_message().subject == "Second"

    def test_tags_in_message(self):
        backend = ConsoleBackend()
        msg = EmailMessage(
            to="user@test.com",
            subject="Tagged",
            html="<p>Tag test</p>",
            tags=["document", "uploaded"],
        )
        result = backend.send(msg)
        assert result.success is True
        assert backend.last_message().tags == ["document", "uploaded"]


class TestEmailFactory:
    """Tests for email factory function."""

    def setup_method(self):
        reset_email_backend()

    def teardown_method(self):
        reset_email_backend()

    @patch("app.services.email_factory.get_settings")
    def test_creates_console_backend(self, mock_settings):
        mock_settings.return_value = MagicMock(email_provider="console")
        backend = _create_backend()
        assert backend.get_provider_name() == "console"

    @patch("app.services.email_factory.get_settings")
    def test_creates_resend_backend(self, mock_settings):
        mock_settings.return_value = MagicMock(
            email_provider="resend",
            resend_api_key="",
            email_from_address="test@tracehub.com",
            email_from_name="TraceHub",
        )
        backend = _create_backend()
        assert backend.get_provider_name() == "resend"
        # Without a real API key, it should not be available
        assert backend.is_available() is False

    @patch("app.services.email_factory.get_settings")
    def test_unknown_provider_falls_back_to_console(self, mock_settings):
        mock_settings.return_value = MagicMock(email_provider="unknown_provider")
        backend = _create_backend()
        assert backend.get_provider_name() == "console"
        assert backend.is_available() is False


class TestEmailBackendProviderAgnostic:
    """Tests verifying the email system is provider-agnostic."""

    def test_backend_accepts_any_implementation(self):
        """Verify that any object satisfying EmailBackend works."""

        class CustomEmailBackend:
            def send(self, message):
                return EmailResult(
                    success=True,
                    provider="custom",
                    message_id="custom-1",
                )

            def send_batch(self, messages):
                return [self.send(m) for m in messages]

            def is_available(self):
                return True

            def get_provider_name(self):
                return "custom"

            def get_status(self):
                return {"provider": "custom", "available": True}

        backend = CustomEmailBackend()
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")
        result = backend.send(msg)
        assert result.success is True
        assert result.provider == "custom"

    def test_console_backend_never_imports_resend(self):
        """Ensure ConsoleBackend has no resend dependency."""
        import inspect

        source = inspect.getsource(ConsoleBackend)
        assert "import resend" not in source
        assert "from resend" not in source
