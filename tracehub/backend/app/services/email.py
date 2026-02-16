"""Email backend protocol for transactional emails (PRD-020).

Provider-agnostic interface for email delivery.
Same pattern as LLMBackend (PRD-019) and StorageBackend (PRD-005).

Implementations:
- ResendBackend: Resend API (default for production)
- ConsoleBackend: Dev/test (logs to stdout)
- Future: SendGridBackend, SMTPBackend, etc.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol


@dataclass
class EmailMessage:
    """A single email message."""

    to: str
    subject: str
    html: str
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class EmailResult:
    """Result of sending an email."""

    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailBackend(Protocol):
    """Protocol for email delivery.

    Implementations must provide single and batch sending.
    Provider-specific details (API key, domain, etc.) are
    handled internally.
    """

    def send(self, message: EmailMessage) -> EmailResult:
        """Send a single email.

        Args:
            message: The email to send.

        Returns:
            EmailResult with success status and provider message ID.
        """
        ...

    def send_batch(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send multiple emails.

        Args:
            messages: List of emails to send.

        Returns:
            List of EmailResult, one per message.
        """
        ...

    def is_available(self) -> bool:
        """Check if the email backend is operational."""
        ...

    def get_provider_name(self) -> str:
        """Return the provider identifier (e.g. 'resend', 'sendgrid')."""
        ...

    def get_status(self) -> Dict[str, object]:
        """Return detailed status information."""
        ...
