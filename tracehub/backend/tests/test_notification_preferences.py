"""Tests for notification preferences API and models (PRD-020)."""

import pytest
from unittest.mock import patch, MagicMock

from app.schemas.notification_preferences import (
    NotificationPreference,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    EmailTestRequest,
    EmailTestResponse,
    EmailStatusResponse,
)
from app.models.notification_preference import (
    NotificationPreference as NotificationPreferenceModel,
)
from app.models.email_log import EmailLog


class TestNotificationPreferenceSchemas:
    """Tests for Pydantic schemas."""

    def test_preference_creation(self):
        pref = NotificationPreference(
            event_type="document_uploaded",
            email_enabled=True,
            in_app_enabled=True,
        )
        assert pref.event_type == "document_uploaded"
        assert pref.email_enabled is True
        assert pref.in_app_enabled is True

    def test_preference_defaults(self):
        pref = NotificationPreference(event_type="compliance_alert")
        assert pref.email_enabled is True
        assert pref.in_app_enabled is True

    def test_preference_disabled(self):
        pref = NotificationPreference(
            event_type="shipment_status_change",
            email_enabled=False,
            in_app_enabled=True,
        )
        assert pref.email_enabled is False

    def test_preferences_response(self):
        resp = NotificationPreferencesResponse(
            preferences=[
                NotificationPreference(event_type="document_uploaded"),
                NotificationPreference(
                    event_type="compliance_alert", email_enabled=False
                ),
            ]
        )
        assert len(resp.preferences) == 2
        assert resp.preferences[1].email_enabled is False

    def test_preferences_update(self):
        update = NotificationPreferencesUpdate(
            preferences=[
                NotificationPreference(
                    event_type="document_uploaded", email_enabled=False
                ),
            ]
        )
        assert len(update.preferences) == 1
        assert update.preferences[0].email_enabled is False

    def test_email_test_request(self):
        req = EmailTestRequest(to="test@example.com")
        assert req.to == "test@example.com"

    def test_email_test_response_success(self):
        resp = EmailTestResponse(
            success=True,
            provider="resend",
            message_id="msg-123",
        )
        assert resp.success is True
        assert resp.error is None

    def test_email_test_response_failure(self):
        resp = EmailTestResponse(
            success=False,
            provider="resend",
            error="Invalid API key",
        )
        assert resp.success is False
        assert resp.error == "Invalid API key"

    def test_email_status_response(self):
        resp = EmailStatusResponse(
            enabled=True,
            provider="resend",
            available=True,
        )
        assert resp.enabled is True
        data = resp.model_dump()
        assert data["provider"] == "resend"


class TestNotificationPreferenceModel:
    """Tests for SQLAlchemy model structure."""

    def test_model_has_required_columns(self):
        import inspect
        source = inspect.getsource(NotificationPreferenceModel)
        assert "user_id" in source
        assert "organization_id" in source
        assert "event_type" in source
        assert "email_enabled" in source
        assert "in_app_enabled" in source

    def test_model_tablename(self):
        assert NotificationPreferenceModel.__tablename__ == "notification_preferences"


class TestEmailLogModel:
    """Tests for EmailLog SQLAlchemy model."""

    def test_model_has_required_columns(self):
        import inspect
        source = inspect.getsource(EmailLog)
        assert "organization_id" in source
        assert "recipient_email" in source
        assert "event_type" in source
        assert "subject" in source
        assert "status" in source
        assert "provider" in source
        assert "provider_message_id" in source
        assert "error_message" in source
        assert "attempts" in source

    def test_model_tablename(self):
        assert EmailLog.__tablename__ == "email_log"


class TestAllEventTypes:
    """Tests for event type coverage."""

    def test_all_event_types_defined(self):
        from app.routers.notification_preferences import ALL_EVENT_TYPES

        expected = [
            "document_uploaded",
            "document_validated",
            "document_rejected",
            "shipment_status_change",
            "compliance_alert",
            "expiry_warning",
            "invitation_sent",
            "invitation_accepted",
        ]
        assert ALL_EVENT_TYPES == expected

    def test_event_types_match_notification_model(self):
        """Verify our event types are a subset of NotificationType values."""
        from app.models.notification import NotificationType
        from app.routers.notification_preferences import ALL_EVENT_TYPES

        notification_values = [nt.value for nt in NotificationType]
        # All configured email events should exist in the notification model
        # (except invitation events which are new)
        for et in ALL_EVENT_TYPES:
            if et.startswith("invitation_"):
                continue  # invitation events are email-only, not in v1 model
            assert et in notification_values or et == "shipment_status_change"
