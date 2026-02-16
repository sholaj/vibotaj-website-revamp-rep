"""Document Transition model for tracking state machine history.

Persists every document state change with actor, reason, and timestamp.
Part of PRD-016: Enhanced Compliance Engine.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database import Base


class DocumentTransition(Base):
    """Document transition entity - records every state change.

    Provides a full audit trail of document lifecycle transitions,
    including who performed the transition, when, and why.
    """

    __tablename__ = "document_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)
    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    reason = Column(Text, nullable=True)
    metadata = Column(JSONB, default=dict, server_default="{}")

    # Organization (multi-tenancy)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="transitions")

    def __repr__(self) -> str:
        return f"<DocumentTransition {self.from_state} -> {self.to_state}>"
