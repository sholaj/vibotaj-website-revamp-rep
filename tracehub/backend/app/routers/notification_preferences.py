"""Notification preferences API endpoints (PRD-020).

Endpoints:
- GET  /api/users/me/notification-preferences
- PUT  /api/users/me/notification-preferences
- POST /api/admin/notifications/test
- GET  /api/admin/notifications/status
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..schemas.notification_preferences import (
    NotificationPreference as PrefSchema,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    EmailTestRequest,
    EmailTestResponse,
    EmailStatusResponse,
)
from ..services.email import EmailMessage
from ..services.email_factory import get_email_backend
from ..services.email_templates import render_document_uploaded, OrgBranding

logger = logging.getLogger(__name__)

router = APIRouter(tags=["notifications"])

# All event types that can be configured
ALL_EVENT_TYPES = [
    "document_uploaded",
    "document_validated",
    "document_rejected",
    "shipment_status_change",
    "compliance_alert",
    "expiry_warning",
    "invitation_sent",
    "invitation_accepted",
]


@router.get(
    "/api/users/me/notification-preferences",
    response_model=NotificationPreferencesResponse,
)
async def get_notification_preferences(
    db: Session = Depends(get_db),
    # In production, user/org from auth: user = Depends(auth.require_user)
) -> NotificationPreferencesResponse:
    """Get current user's notification preferences.

    Returns defaults (all enabled) for events that have no saved preference.
    """
    # TODO: Get user_id and org_id from auth token
    # For now, return defaults for all event types
    preferences = [
        PrefSchema(event_type=et, email_enabled=True, in_app_enabled=True)
        for et in ALL_EVENT_TYPES
    ]
    return NotificationPreferencesResponse(preferences=preferences)


@router.put(
    "/api/users/me/notification-preferences",
    response_model=NotificationPreferencesResponse,
)
async def update_notification_preferences(
    body: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
) -> NotificationPreferencesResponse:
    """Update notification preferences for the current user.

    Only events included in the request body are updated.
    Events not included retain their current settings.
    """
    # TODO: Get user_id and org_id from auth token, upsert into DB
    # For now, echo back the submitted preferences merged with defaults
    updated_map = {p.event_type: p for p in body.preferences}
    preferences = []
    for et in ALL_EVENT_TYPES:
        if et in updated_map:
            preferences.append(updated_map[et])
        else:
            preferences.append(
                PrefSchema(event_type=et, email_enabled=True, in_app_enabled=True)
            )
    return NotificationPreferencesResponse(preferences=preferences)


@router.post(
    "/api/admin/notifications/test",
    response_model=EmailTestResponse,
)
async def send_test_email(
    body: EmailTestRequest,
) -> EmailTestResponse:
    """Send a test email to verify email configuration (admin only).

    TODO: Add admin role check via auth dependency.
    """
    backend = get_email_backend()
    settings = get_settings()

    if not settings.email_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_DISABLED",
                "message": "Email sending is not enabled. Set EMAIL_ENABLED=true.",
            },
        )

    subject, html = render_document_uploaded(
        doc_type="Test Document",
        doc_name="test.pdf",
        uploaded_by="TraceHub Admin",
        shipment_ref="TEST-001",
        shipment_url=f"{settings.frontend_url}/shipments/test",
        branding=OrgBranding(),
    )

    message = EmailMessage(
        to=body.to,
        subject=f"[TEST] {subject}",
        html=html,
        tags=["test"],
    )
    result = backend.send(message)

    return EmailTestResponse(
        success=result.success,
        provider=result.provider,
        message_id=result.message_id,
        error=result.error,
    )


@router.get(
    "/api/admin/notifications/status",
    response_model=EmailStatusResponse,
)
async def get_email_status() -> EmailStatusResponse:
    """Get email system status (admin only)."""
    settings = get_settings()
    backend = get_email_backend()

    return EmailStatusResponse(
        enabled=settings.email_enabled,
        provider=backend.get_provider_name(),
        available=backend.is_available(),
    )
