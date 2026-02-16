"""Tests for email templates and NotificationEmailService (PRD-020)."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.email import EmailMessage, EmailResult
from app.services.email_console import ConsoleBackend
from app.services.email_templates import (
    OrgBranding,
    render_document_uploaded,
    render_document_approved,
    render_document_rejected,
    render_shipment_status_change,
    render_compliance_alert,
    render_invitation_sent,
    render_invitation_accepted,
    render_expiry_warning,
)
from app.services.email_notification import (
    NotificationEmailService,
    _send_with_retry,
)


class TestOrgBranding:
    """Tests for OrgBranding defaults."""

    def test_default_branding(self):
        branding = OrgBranding()
        assert branding.org_name == "TraceHub"
        assert branding.logo_url is None
        assert branding.primary_color == "#2563EB"

    def test_custom_branding(self):
        branding = OrgBranding(
            org_name="VIBOTAJ",
            logo_url="https://example.com/logo.png",
            primary_color="#FF0000",
        )
        assert branding.org_name == "VIBOTAJ"
        assert branding.logo_url == "https://example.com/logo.png"


class TestDocumentTemplates:
    """Tests for document-related email templates."""

    def test_document_uploaded(self):
        subject, html = render_document_uploaded(
            doc_type="Bill of Lading",
            doc_name="bol.pdf",
            uploaded_by="Shola",
            shipment_ref="SHP-001",
            shipment_url="https://tracehub.com/shipments/1",
        )
        assert "[TraceHub]" in subject
        assert "Bill of Lading" in subject
        assert "SHP-001" in subject
        assert "bol.pdf" in html
        assert "Shola" in html
        assert "View Shipment" in html

    def test_document_approved(self):
        subject, html = render_document_approved(
            doc_type="Commercial Invoice",
            shipment_ref="SHP-002",
            approved_by="Bolaji",
            shipment_url="https://tracehub.com/shipments/2",
            notes="Looks good",
        )
        assert "approved" in subject.lower()
        assert "Bolaji" in html
        assert "Looks good" in html

    def test_document_approved_without_notes(self):
        subject, html = render_document_approved(
            doc_type="Packing List",
            shipment_ref="SHP-003",
            approved_by="Bolaji",
            shipment_url="https://tracehub.com/shipments/3",
        )
        assert "Notes" not in html

    def test_document_rejected(self):
        subject, html = render_document_rejected(
            doc_type="Certificate of Origin",
            shipment_ref="SHP-004",
            rejected_by="Admin",
            reason="Missing signature",
            shipment_url="https://tracehub.com/shipments/4",
        )
        assert "rejected" in subject.lower()
        assert "Missing signature" in html
        assert "Reason" in html


class TestShipmentTemplates:
    """Tests for shipment-related email templates."""

    def test_shipment_status_change(self):
        subject, html = render_shipment_status_change(
            shipment_ref="SHP-005",
            old_status="In Transit",
            new_status="Arrived",
            shipment_url="https://tracehub.com/shipments/5",
        )
        assert "SHP-005" in subject
        assert "Arrived" in subject
        assert "In Transit" in html
        assert "Arrived" in html


class TestComplianceTemplates:
    """Tests for compliance alert email template."""

    def test_compliance_alert(self):
        subject, html = render_compliance_alert(
            shipment_ref="SHP-006",
            alert_type="Missing Document",
            severity="error",
            message="Bill of Lading is required",
            shipment_url="https://tracehub.com/shipments/6",
        )
        assert "Compliance alert" in subject
        assert "Missing Document" in html
        assert "Bill of Lading is required" in html


class TestInvitationTemplates:
    """Tests for invitation email templates."""

    def test_invitation_sent(self):
        subject, html = render_invitation_sent(
            org_name="VIBOTAJ",
            inviter_name="Shola",
            role="compliance_officer",
            accept_url="https://tracehub.com/invite/abc123",
        )
        assert "invited" in subject.lower()
        assert "VIBOTAJ" in subject
        assert "Shola" in html
        assert "compliance_officer" in html
        assert "Accept Invitation" in html

    def test_invitation_accepted(self):
        subject, html = render_invitation_accepted(
            org_name="VIBOTAJ",
            accepted_by="Bolaji",
            role="admin",
        )
        assert "Bolaji" in subject
        assert "joined" in subject.lower()
        assert "admin" in html


class TestExpiryWarningTemplate:
    """Tests for document expiry warning template."""

    def test_expiry_warning_normal(self):
        subject, html = render_expiry_warning(
            doc_type="Veterinary Health Certificate",
            shipment_ref="SHP-007",
            expiry_date="2026-03-01",
            days_remaining=14,
            shipment_url="https://tracehub.com/shipments/7",
        )
        assert "expiring" in subject.lower()
        assert "14 days" in subject
        assert "URGENT" not in subject
        assert "2026-03-01" in html

    def test_expiry_warning_urgent(self):
        subject, html = render_expiry_warning(
            doc_type="Certificate of Origin",
            shipment_ref="SHP-008",
            expiry_date="2026-02-18",
            days_remaining=2,
            shipment_url="https://tracehub.com/shipments/8",
        )
        assert "URGENT" in subject
        assert "2 days" in subject


class TestBaseLayout:
    """Tests for base email layout."""

    def test_layout_contains_org_name(self):
        _, html = render_document_uploaded(
            doc_type="BoL",
            doc_name="bol.pdf",
            uploaded_by="X",
            shipment_ref="SHP-1",
            shipment_url="https://example.com",
            branding=OrgBranding(org_name="HAGES"),
        )
        assert "HAGES" in html
        assert "Sent by TraceHub on behalf of HAGES" in html

    def test_layout_with_custom_logo(self):
        branding = OrgBranding(
            org_name="Test",
            logo_url="https://example.com/logo.png",
        )
        _, html = render_document_uploaded(
            doc_type="BoL",
            doc_name="bol.pdf",
            uploaded_by="X",
            shipment_ref="SHP-1",
            shipment_url="https://example.com",
            branding=branding,
        )
        assert "https://example.com/logo.png" in html

    def test_layout_valid_html(self):
        _, html = render_document_uploaded(
            doc_type="BoL",
            doc_name="bol.pdf",
            uploaded_by="X",
            shipment_ref="SHP-1",
            shipment_url="https://example.com",
        )
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html


class TestSendWithRetry:
    """Tests for retry logic."""

    def test_success_on_first_attempt(self):
        backend = ConsoleBackend()
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")
        result = _send_with_retry(backend, msg, max_retries=3)
        assert result.success is True
        assert backend.call_count == 1

    def test_retries_on_failure(self):
        backend = ConsoleBackend(available=False)
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")
        result = _send_with_retry(backend, msg, max_retries=2)
        assert result.success is False
        assert backend.call_count == 2

    def test_succeeds_after_retry(self):
        """Backend fails first, then succeeds."""
        backend = ConsoleBackend(available=False)
        msg = EmailMessage(to="user@test.com", subject="Hi", html="<p>Hi</p>")

        original_send = backend.send

        call_count = 0

        def flaky_send(message):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return EmailResult(success=False, provider="console", error="Temp fail")
            backend.set_available(True)
            return original_send.__func__(backend, message)

        backend.send = flaky_send
        result = _send_with_retry(backend, msg, max_retries=3)
        assert result.success is True
        assert call_count == 2


class TestNotificationEmailService:
    """Tests for NotificationEmailService."""

    def _make_service(self, enabled: bool = True) -> NotificationEmailService:
        backend = ConsoleBackend()
        service = NotificationEmailService(backend=backend)
        return service

    @patch("app.services.email_notification.get_settings")
    def test_send_when_enabled(self, mock_settings):
        mock_settings.return_value = MagicMock(email_enabled=True)
        backend = ConsoleBackend()
        service = NotificationEmailService(backend=backend)
        result = service.send_notification(
            to="user@test.com",
            subject="Test",
            html="<p>Test</p>",
            event_type="document_uploaded",
        )
        assert result.success is True
        assert len(backend.sent_messages) == 1

    @patch("app.services.email_notification.get_settings")
    def test_skip_when_disabled(self, mock_settings):
        mock_settings.return_value = MagicMock(email_enabled=False)
        backend = ConsoleBackend()
        service = NotificationEmailService(backend=backend)
        result = service.send_notification(
            to="user@test.com",
            subject="Test",
            html="<p>Test</p>",
            event_type="document_uploaded",
        )
        assert result.success is False
        assert "disabled" in result.error
        assert len(backend.sent_messages) == 0

    @patch("app.services.email_notification.get_settings")
    def test_send_batch(self, mock_settings):
        mock_settings.return_value = MagicMock(email_enabled=True)
        backend = ConsoleBackend()
        service = NotificationEmailService(backend=backend)
        results = service.send_batch_notifications(
            recipients=["a@test.com", "b@test.com"],
            subject="Batch",
            html="<p>Batch</p>",
            event_type="shipment_status_change",
        )
        assert len(results) == 2
        assert all(r.success for r in results)
        assert len(backend.sent_messages) == 2

    @patch("app.services.email_notification.get_settings")
    def test_tags_default_to_event_type(self, mock_settings):
        mock_settings.return_value = MagicMock(email_enabled=True)
        backend = ConsoleBackend()
        service = NotificationEmailService(backend=backend)
        service.send_notification(
            to="user@test.com",
            subject="Test",
            html="<p>Test</p>",
            event_type="compliance_alert",
        )
        assert backend.last_message().tags == ["compliance_alert"]

    @patch("app.services.email_notification.get_settings")
    def test_custom_tags(self, mock_settings):
        mock_settings.return_value = MagicMock(email_enabled=True)
        backend = ConsoleBackend()
        service = NotificationEmailService(backend=backend)
        service.send_notification(
            to="user@test.com",
            subject="Test",
            html="<p>Test</p>",
            event_type="document_uploaded",
            tags=["document", "urgent"],
        )
        assert backend.last_message().tags == ["document", "urgent"]
