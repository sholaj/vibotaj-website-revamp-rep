"""Pydantic schemas for notification preferences (PRD-020)."""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class NotificationPreference(BaseModel):
    """Single event type preference."""

    model_config = ConfigDict(from_attributes=True)

    event_type: str
    email_enabled: bool = True
    in_app_enabled: bool = True


class NotificationPreferencesResponse(BaseModel):
    """Full notification preferences for a user in an org."""

    preferences: List[NotificationPreference]


class NotificationPreferencesUpdate(BaseModel):
    """Update notification preferences (partial — only listed events are updated)."""

    preferences: List[NotificationPreference]


class EmailTestRequest(BaseModel):
    """Request to send a test email."""

    to: str


class EmailTestResponse(BaseModel):
    """Response from test email send."""

    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailStatusResponse(BaseModel):
    """Email system status."""

    enabled: bool
    provider: str
    available: bool
