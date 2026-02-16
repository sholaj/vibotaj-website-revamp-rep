"""Console email backend for development and testing (PRD-020).

Logs emails to stdout instead of sending them. Tracks all calls
for test assertions.
"""

import logging
from typing import Dict, List, Optional

from .email import EmailBackend, EmailMessage, EmailResult

logger = logging.getLogger(__name__)


class ConsoleBackend:
    """Email backend that logs to console instead of sending.

    Useful for development and testing. Tracks sent messages
    for test assertions.
    """

    def __init__(self, available: bool = True) -> None:
        self._available = available
        self.sent_messages: List[EmailMessage] = []
        self.call_count: int = 0

    def send(self, message: EmailMessage) -> EmailResult:
        """Log the email to console and track it."""
        self.call_count += 1

        if not self._available:
            return EmailResult(
                success=False,
                provider="console",
                error="Console backend is disabled",
            )

        self.sent_messages.append(message)
        logger.info(
            "[EMAIL] To: %s | Subject: %s | Tags: %s",
            message.to,
            message.subject,
            ", ".join(message.tags) if message.tags else "none",
        )
        return EmailResult(
            success=True,
            provider="console",
            message_id=f"console-{self.call_count}",
        )

    def send_batch(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send each message individually."""
        return [self.send(m) for m in messages]

    def is_available(self) -> bool:
        """Console backend is always available unless explicitly disabled."""
        return self._available

    def get_provider_name(self) -> str:
        return "console"

    def get_status(self) -> Dict[str, object]:
        return {
            "provider": "console",
            "available": self._available,
            "sent_count": len(self.sent_messages),
        }

    # --- Test helpers ---

    def set_available(self, available: bool) -> None:
        """Toggle availability (for testing)."""
        self._available = available

    def reset(self) -> None:
        """Clear tracked messages and call count."""
        self.sent_messages.clear()
        self.call_count = 0

    def last_message(self) -> Optional[EmailMessage]:
        """Return the most recently sent message, or None."""
        return self.sent_messages[-1] if self.sent_messages else None
