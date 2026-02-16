"""Resend email backend for production use (PRD-020).

Uses the Resend Python SDK for transactional email delivery.
Configuration via pydantic-settings (resend_api_key, email_from_address).
"""

import logging
from typing import Dict, List, Optional

from ..config import get_settings
from .email import EmailBackend, EmailMessage, EmailResult

logger = logging.getLogger(__name__)


class ResendBackend:
    """Email backend using Resend API.

    Requires `resend_api_key` in Settings. Falls back to unavailable
    state if the key is empty or the SDK is not installed.
    """

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.resend_api_key
        # Handle SecretStr
        self._api_key: str = (
            api_key.get_secret_value()
            if hasattr(api_key, "get_secret_value")
            else str(api_key)
        )
        self._from_email = settings.email_from_address
        self._from_name = settings.email_from_name
        self._client: Optional[object] = None

        if self._api_key:
            try:
                import resend

                resend.api_key = self._api_key
                self._client = resend
                logger.info("Resend email backend initialized")
            except ImportError:
                logger.warning(
                    "resend package not installed — email sending disabled"
                )

    def send(self, message: EmailMessage) -> EmailResult:
        """Send a single email via Resend."""
        if not self._client:
            return EmailResult(
                success=False,
                provider="resend",
                error="Resend client not available (missing API key or SDK)",
            )

        from_addr = message.from_email or self._from_email
        from_name = message.from_name or self._from_name
        sender = f"{from_name} <{from_addr}>" if from_name else from_addr

        try:
            import resend

            params: resend.Emails.SendParams = {
                "from": sender,
                "to": [message.to],
                "subject": message.subject,
                "html": message.html,
            }
            if message.reply_to:
                params["reply_to"] = message.reply_to
            if message.tags:
                params["tags"] = [
                    {"name": tag, "value": "true"} for tag in message.tags
                ]

            result = resend.Emails.send(params)
            message_id = result.get("id", "") if isinstance(result, dict) else ""

            return EmailResult(
                success=True,
                provider="resend",
                message_id=message_id,
            )
        except Exception as e:
            error_msg = str(e)
            logger.error("Resend send failed: %s", error_msg)
            return EmailResult(
                success=False,
                provider="resend",
                error=error_msg,
            )

    def send_batch(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send each message individually via Resend."""
        return [self.send(m) for m in messages]

    def is_available(self) -> bool:
        return self._client is not None

    def get_provider_name(self) -> str:
        return "resend"

    def get_status(self) -> Dict[str, object]:
        return {
            "provider": "resend",
            "available": self.is_available(),
            "from_email": self._from_email,
        }
