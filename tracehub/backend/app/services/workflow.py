"""Document workflow state machine.

Manages document lifecycle transitions with validation
and audit trail support.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..models import Document, DocumentStatus
from .validation import validate_document, ValidationResult


class TransitionError(Exception):
    """Raised when a state transition is not allowed."""
    pass


@dataclass
class StateTransition:
    """Defines an allowed state transition."""
    from_state: DocumentStatus
    to_state: DocumentStatus
    requires_validation: bool = False
    requires_approval: bool = False
    allowed_roles: List[str] = None  # None means any role

    def __post_init__(self):
        if self.allowed_roles is None:
            self.allowed_roles = ["admin", "compliance", "supplier", "buyer"]


# Define allowed state transitions
ALLOWED_TRANSITIONS: List[StateTransition] = [
    # Draft -> Uploaded (when file is attached)
    StateTransition(
        DocumentStatus.DRAFT,
        DocumentStatus.UPLOADED,
        requires_validation=False,
        allowed_roles=["admin", "compliance", "supplier"]
    ),

    # Uploaded -> Validated (after field validation passes)
    StateTransition(
        DocumentStatus.UPLOADED,
        DocumentStatus.VALIDATED,
        requires_validation=True,
        requires_approval=True,
        allowed_roles=["admin", "compliance"]
    ),

    # Uploaded -> Draft (rejected, needs re-upload)
    StateTransition(
        DocumentStatus.UPLOADED,
        DocumentStatus.DRAFT,
        requires_validation=False,
        allowed_roles=["admin", "compliance"]
    ),

    # Validated -> Compliance OK (after compliance review)
    StateTransition(
        DocumentStatus.VALIDATED,
        DocumentStatus.COMPLIANCE_OK,
        requires_validation=False,
        requires_approval=True,
        allowed_roles=["admin", "compliance"]
    ),

    # Validated -> Compliance Failed (compliance issues found)
    StateTransition(
        DocumentStatus.VALIDATED,
        DocumentStatus.COMPLIANCE_FAILED,
        requires_validation=False,
        requires_approval=True,
        allowed_roles=["admin", "compliance"]
    ),

    # Compliance Failed -> Uploaded (re-submitted after fixes)
    StateTransition(
        DocumentStatus.COMPLIANCE_FAILED,
        DocumentStatus.UPLOADED,
        requires_validation=False,
        allowed_roles=["admin", "compliance", "supplier"]
    ),

    # Compliance OK -> Linked (linked to shipment for export)
    StateTransition(
        DocumentStatus.COMPLIANCE_OK,
        DocumentStatus.LINKED,
        requires_validation=False,
        allowed_roles=["admin", "compliance"]
    ),

    # Linked -> Archived (after shipment complete)
    StateTransition(
        DocumentStatus.LINKED,
        DocumentStatus.ARCHIVED,
        requires_validation=False,
        allowed_roles=["admin"]
    ),

    # Any validated+ state -> Archived (manual archive)
    StateTransition(
        DocumentStatus.VALIDATED,
        DocumentStatus.ARCHIVED,
        requires_validation=False,
        allowed_roles=["admin"]
    ),
    StateTransition(
        DocumentStatus.COMPLIANCE_OK,
        DocumentStatus.ARCHIVED,
        requires_validation=False,
        allowed_roles=["admin"]
    ),
    StateTransition(
        DocumentStatus.COMPLIANCE_FAILED,
        DocumentStatus.ARCHIVED,
        requires_validation=False,
        allowed_roles=["admin"]
    ),
]

# Build lookup for quick access
_TRANSITION_MAP: Dict[Tuple[DocumentStatus, DocumentStatus], StateTransition] = {
    (t.from_state, t.to_state): t for t in ALLOWED_TRANSITIONS
}


def get_allowed_transitions(
    current_status: DocumentStatus,
    user_role: str = "admin"
) -> List[DocumentStatus]:
    """Get list of states a document can transition to.

    Args:
        current_status: Current document status
        user_role: Role of the user attempting transition

    Returns:
        List of allowed target states
    """
    allowed = []
    for transition in ALLOWED_TRANSITIONS:
        if transition.from_state == current_status:
            if user_role in transition.allowed_roles:
                allowed.append(transition.to_state)
    return allowed


def can_transition(
    document: Document,
    target_status: DocumentStatus,
    user_role: str = "admin"
) -> Tuple[bool, Optional[str]]:
    """Check if a document can transition to target status.

    Args:
        document: The document to check
        target_status: The desired target status
        user_role: Role of the user attempting transition

    Returns:
        Tuple of (can_transition, error_message)
    """
    key = (document.status, target_status)
    transition = _TRANSITION_MAP.get(key)

    if not transition:
        return False, f"Transition from {document.status.value} to {target_status.value} is not allowed"

    if user_role not in transition.allowed_roles:
        return False, f"Role '{user_role}' is not authorized for this transition"

    if transition.requires_validation:
        result = validate_document(document)
        if not result.is_valid:
            errors = "; ".join(result.errors)
            return False, f"Document validation failed: {errors}"

    return True, None


@dataclass
class TransitionResult:
    """Result of a state transition attempt."""
    success: bool
    previous_status: DocumentStatus
    new_status: DocumentStatus
    validation_result: Optional[ValidationResult] = None
    error_message: Optional[str] = None
    transitioned_at: datetime = None
    transitioned_by: str = None

    def __post_init__(self):
        if self.transitioned_at is None:
            self.transitioned_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "previous_status": self.previous_status.value,
            "new_status": self.new_status.value,
            "transitioned_at": self.transitioned_at.isoformat() if self.transitioned_at else None,
            "transitioned_by": self.transitioned_by
        }
        if self.validation_result:
            result["validation"] = self.validation_result.to_dict()
        if self.error_message:
            result["error"] = self.error_message
        return result


def transition_document(
    document: Document,
    target_status: DocumentStatus,
    user: str = "system",
    user_role: str = "admin",
    notes: Optional[str] = None
) -> TransitionResult:
    """Attempt to transition a document to a new status.

    Args:
        document: The document to transition
        target_status: The desired target status
        user: Username performing the transition
        user_role: Role of the user
        notes: Optional notes for the transition

    Returns:
        TransitionResult with outcome details

    Note: This does not persist the change - caller must save to database
    """
    previous_status = document.status
    validation_result = None

    # Check if transition is allowed
    can, error = can_transition(document, target_status, user_role)

    if not can:
        return TransitionResult(
            success=False,
            previous_status=previous_status,
            new_status=previous_status,
            error_message=error,
            transitioned_by=user
        )

    # Run validation if required
    key = (document.status, target_status)
    transition = _TRANSITION_MAP.get(key)

    if transition and transition.requires_validation:
        validation_result = validate_document(document)
        if not validation_result.is_valid:
            return TransitionResult(
                success=False,
                previous_status=previous_status,
                new_status=previous_status,
                validation_result=validation_result,
                error_message="Document validation failed",
                transitioned_by=user
            )

    # Perform the transition
    document.status = target_status
    document.updated_at = datetime.utcnow()

    # Update validation tracking fields
    if target_status == DocumentStatus.VALIDATED:
        document.validated_at = datetime.utcnow()
        document.validated_by = user
        if notes:
            document.validation_notes = notes

    return TransitionResult(
        success=True,
        previous_status=previous_status,
        new_status=target_status,
        validation_result=validation_result,
        transitioned_by=user
    )


# Workflow action definitions for UI
WORKFLOW_ACTIONS = {
    DocumentStatus.DRAFT: {
        "display": "Draft",
        "color": "gray",
        "actions": ["upload"]
    },
    DocumentStatus.UPLOADED: {
        "display": "Pending Review",
        "color": "yellow",
        "actions": ["validate", "reject"]
    },
    DocumentStatus.VALIDATED: {
        "display": "Validated",
        "color": "blue",
        "actions": ["approve_compliance", "fail_compliance"]
    },
    DocumentStatus.COMPLIANCE_OK: {
        "display": "Compliance Approved",
        "color": "green",
        "actions": ["link_to_shipment", "archive"]
    },
    DocumentStatus.COMPLIANCE_FAILED: {
        "display": "Compliance Failed",
        "color": "red",
        "actions": ["resubmit", "archive"]
    },
    DocumentStatus.LINKED: {
        "display": "Linked to Shipment",
        "color": "green",
        "actions": ["archive"]
    },
    DocumentStatus.ARCHIVED: {
        "display": "Archived",
        "color": "gray",
        "actions": []
    }
}


def get_status_info(status: DocumentStatus) -> Dict[str, Any]:
    """Get display information for a document status.

    Args:
        status: The document status

    Returns:
        Dict with display name, color, and available actions
    """
    info = WORKFLOW_ACTIONS.get(status, {
        "display": status.value,
        "color": "gray",
        "actions": []
    })
    return {
        "status": status.value,
        **info
    }


def get_workflow_summary(documents: List[Document]) -> Dict[str, Any]:
    """Get a summary of documents by workflow status.

    Args:
        documents: List of documents to summarize

    Returns:
        Summary with counts per status and overall progress
    """
    by_status = {}
    for status in DocumentStatus:
        by_status[status.value] = 0

    for doc in documents:
        by_status[doc.status.value] += 1

    total = len(documents)
    complete = by_status.get(DocumentStatus.LINKED.value, 0) + \
               by_status.get(DocumentStatus.COMPLIANCE_OK.value, 0)
    pending = by_status.get(DocumentStatus.UPLOADED.value, 0) + \
              by_status.get(DocumentStatus.VALIDATED.value, 0)
    failed = by_status.get(DocumentStatus.COMPLIANCE_FAILED.value, 0)

    return {
        "total": total,
        "by_status": by_status,
        "complete": complete,
        "pending_review": pending,
        "failed": failed,
        "draft": by_status.get(DocumentStatus.DRAFT.value, 0),
        "progress_percent": round((complete / total) * 100) if total > 0 else 0
    }
