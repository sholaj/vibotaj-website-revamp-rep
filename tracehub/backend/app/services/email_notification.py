"""Notification email service — orchestrates preferences, templates, and delivery (PRD-020).

Flow: check user preferences → render template → send via EmailBackend with retry.
"""

import logging
import time
from typing import Dict, List, Optional

from ..config import get_settings
from .email import EmailBackend, EmailMessage, EmailResult
from .email_factory import get_email_backend
from .email_templates import OrgBranding

logger = logging.getLogger(__name__)

# Retry config: 3 attempts with exponential backoff (1s, 4s, 16s)
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 1
RETRY_MULTIPLIER = 4


def _send_with_retry(
    backend: EmailBackend,
    message: EmailMessage,
    max_retries: int = MAX_RETRIES,
) -> EmailResult:
    """Send an email with exponential backoff retry.

    Args:
        backend: The email backend to use.
        message: The email to send.
        max_retries: Maximum number of attempts.

    Returns:
        The final EmailResult (success or last failure).
    """
    last_result: Optional[EmailResult] = None
    delay = RETRY_BASE_SECONDS

    for attempt in range(1, max_retries + 1):
        result = backend.send(message)
        if result.success:
            if attempt > 1:
                logger.info(
                    "Email sent on attempt %d to %s", attempt, message.to
                )
            return result

        last_result = result
        if attempt < max_retries:
            logger.warning(
                "Email send attempt %d/%d failed for %s: %s — retrying in %ds",
                attempt,
                max_retries,
                message.to,
                result.error,
                delay,
            )
            time.sleep(delay)
            delay *= RETRY_MULTIPLIER
        else:
            logger.error(
                "Email send failed after %d attempts for %s: %s",
                max_retries,
                message.to,
                result.error,
            )

    return last_result or EmailResult(
        success=False, provider="unknown", error="No attempts made"
    )


class NotificationEmailService:
    """Orchestrates email notifications: preferences → template → send.

    This service is stateless — preferences are checked via callback,
    and the email backend is injected or resolved from the factory.
    """

    def __init__(
        self,
        backend: Optional[EmailBackend] = None,
        branding: Optional[OrgBranding] = None,
    ) -> None:
        self._backend = backend
        self._branding = branding or OrgBranding()

    @property
    def backend(self) -> EmailBackend:
        if self._backend is None:
            self._backend = get_email_backend()
        return self._backend

    def is_enabled(self) -> bool:
        """Check if email sending is enabled globally."""
        settings = get_settings()
        return settings.email_enabled and self.backend.is_available()

    def send_notification(
        self,
        to: str,
        subject: str,
        html: str,
        event_type: str,
        tags: Optional[List[str]] = None,
    ) -> EmailResult:
        """Send a single notification email with retry.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            html: Rendered HTML content.
            event_type: The notification event type (for logging/tracking).
            tags: Optional tags for the email provider.

        Returns:
            EmailResult with delivery status.
        """
        if not self.is_enabled():
            logger.debug(
                "Email disabled — skipping %s notification to %s",
                event_type,
                to,
            )
            return EmailResult(
                success=False,
                provider="none",
                error="Email sending is disabled",
            )

        message = EmailMessage(
            to=to,
            subject=subject,
            html=html,
            tags=tags or [event_type],
        )

        result = _send_with_retry(self.backend, message)

        if result.success:
            logger.info(
                "Sent %s email to %s (provider=%s, id=%s)",
                event_type,
                to,
                result.provider,
                result.message_id,
            )
        else:
            logger.error(
                "Failed to send %s email to %s: %s",
                event_type,
                to,
                result.error,
            )

        return result

    def send_batch_notifications(
        self,
        recipients: List[str],
        subject: str,
        html: str,
        event_type: str,
    ) -> List[EmailResult]:
        """Send the same notification to multiple recipients."""
        return [
            self.send_notification(to, subject, html, event_type)
            for to in recipients
        ]
