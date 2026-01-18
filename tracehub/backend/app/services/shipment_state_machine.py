"""Shipment Status State Machine.

Sprint 12 - FEAT-003: Shipment status transition validation.

Prevents invalid state transitions like DELIVERED -> DRAFT.
"""
from typing import List, Optional
from ..models.shipment import ShipmentStatus


# Valid state transitions
# Key: current state, Value: list of valid next states
# Issue #35, #42: Added DOCS_PENDING -> IN_TRANSIT for logistics flexibility
VALID_TRANSITIONS: dict[ShipmentStatus, List[ShipmentStatus]] = {
    ShipmentStatus.DRAFT: [
        ShipmentStatus.DOCS_PENDING,
        ShipmentStatus.ARCHIVED,  # Can archive drafts
    ],
    ShipmentStatus.DOCS_PENDING: [
        ShipmentStatus.DOCS_COMPLETE,
        ShipmentStatus.IN_TRANSIT,  # Issue #35: Allow direct transition for logistics flexibility
        ShipmentStatus.DRAFT,  # Can revert to draft
        ShipmentStatus.ARCHIVED,
    ],
    ShipmentStatus.DOCS_COMPLETE: [
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.DOCS_PENDING,  # If docs rejected
        ShipmentStatus.ARCHIVED,
    ],
    ShipmentStatus.IN_TRANSIT: [
        ShipmentStatus.ARRIVED,
        ShipmentStatus.CUSTOMS,  # Direct to customs possible
    ],
    ShipmentStatus.ARRIVED: [
        ShipmentStatus.CUSTOMS,
        ShipmentStatus.DELIVERED,  # Quick clearance
    ],
    ShipmentStatus.CUSTOMS: [
        ShipmentStatus.DELIVERED,
        ShipmentStatus.ARRIVED,  # Back to arrived if issues
    ],
    ShipmentStatus.DELIVERED: [
        ShipmentStatus.ARCHIVED,  # Only archive after delivery
    ],
    ShipmentStatus.ARCHIVED: [],  # Terminal state - no transitions
}


def validate_transition(current: ShipmentStatus, target: ShipmentStatus) -> bool:
    """Check if a status transition is valid.

    Args:
        current: Current shipment status
        target: Target status to transition to

    Returns:
        True if transition is valid, False otherwise
    """
    if current == target:
        return True  # No-op is always valid

    valid_targets = VALID_TRANSITIONS.get(current, [])
    return target in valid_targets


def get_allowed_transitions(current: ShipmentStatus) -> List[ShipmentStatus]:
    """Get list of valid next states from current state.

    Args:
        current: Current shipment status

    Returns:
        List of valid next statuses
    """
    return VALID_TRANSITIONS.get(current, [])


def get_transition_error_message(
    current: ShipmentStatus,
    target: ShipmentStatus
) -> Optional[str]:
    """Get error message for invalid transition.

    Args:
        current: Current shipment status
        target: Target status attempted

    Returns:
        Error message if invalid, None if valid
    """
    if validate_transition(current, target):
        return None

    allowed = get_allowed_transitions(current)
    if not allowed:
        return f"Cannot transition from {current.value}: this is a terminal state"

    allowed_str = ", ".join(s.value for s in allowed)
    return (
        f"Invalid status transition from '{current.value}' to '{target.value}'. "
        f"Allowed transitions: {allowed_str}"
    )


# State descriptions for UI
STATE_DESCRIPTIONS = {
    ShipmentStatus.DRAFT: "Shipment created, awaiting documentation",
    ShipmentStatus.DOCS_PENDING: "Documents being collected",
    ShipmentStatus.DOCS_COMPLETE: "All required documents uploaded",
    ShipmentStatus.IN_TRANSIT: "Container in transit to destination",
    ShipmentStatus.ARRIVED: "Container arrived at destination port",
    ShipmentStatus.CUSTOMS: "Undergoing customs clearance",
    ShipmentStatus.DELIVERED: "Shipment delivered to consignee",
    ShipmentStatus.ARCHIVED: "Shipment completed and archived",
}
