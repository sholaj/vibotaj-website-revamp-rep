"""Access control service for multi-tenancy and buyer organization access.

Sprint 11 - FEAT-001: Buyer Organization Access Control

This service provides functions to check if a user can access resources
based on organization ownership OR buyer assignment.

Shipments can have both:
- organization_id: The exporter/owner organization
- buyer_organization_id: The buyer organization that should also have access

Users from either organization should be able to access the shipment.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_

from ..models.shipment import Shipment
from ..schemas.user import CurrentUser


def can_access_shipment(shipment: Shipment, user: CurrentUser) -> bool:
    """
    Check if user can access a shipment.

    Access is granted if user's organization is either:
    - The shipment owner (organization_id)
    - The assigned buyer (buyer_organization_id)

    Args:
        shipment: The shipment to check access for
        user: The current authenticated user

    Returns:
        True if user can access the shipment, False otherwise
    """
    if not shipment or not user or not user.organization_id:
        return False

    # Owner access
    if shipment.organization_id == user.organization_id:
        return True

    # Buyer access
    if shipment.buyer_organization_id and shipment.buyer_organization_id == user.organization_id:
        return True

    return False


def get_accessible_shipments_filter(user: CurrentUser):
    """
    Get SQLAlchemy filter for shipments the user can access.

    Returns a filter condition that matches shipments where:
    - The user's org is the owner (organization_id), OR
    - The user's org is the buyer (buyer_organization_id)

    Args:
        user: The current authenticated user

    Returns:
        SQLAlchemy filter condition

    Usage:
        query = db.query(Shipment).filter(get_accessible_shipments_filter(user))
    """
    return or_(
        Shipment.organization_id == user.organization_id,
        Shipment.buyer_organization_id == user.organization_id
    )


def get_accessible_shipment(
    db: Session,
    shipment_id: UUID,
    user: CurrentUser
) -> Optional[Shipment]:
    """
    Get a shipment by ID if the user has access to it.

    Args:
        db: Database session
        shipment_id: UUID of the shipment
        user: The current authenticated user

    Returns:
        Shipment if found and accessible, None otherwise
    """
    return db.query(Shipment).filter(
        Shipment.id == shipment_id,
        get_accessible_shipments_filter(user)
    ).first()


def user_is_shipment_owner(shipment: Shipment, user: CurrentUser) -> bool:
    """
    Check if user is the owner of a shipment (not just a buyer).

    Some operations (like editing/deleting) may be restricted to owners only.

    Args:
        shipment: The shipment to check
        user: The current authenticated user

    Returns:
        True if user's org owns the shipment
    """
    if not shipment or not user or not user.organization_id:
        return False

    return shipment.organization_id == user.organization_id


def user_is_shipment_buyer(shipment: Shipment, user: CurrentUser) -> bool:
    """
    Check if user is the buyer of a shipment.

    Args:
        shipment: The shipment to check
        user: The current authenticated user

    Returns:
        True if user's org is the assigned buyer
    """
    if not shipment or not user or not user.organization_id:
        return False

    return (
        shipment.buyer_organization_id is not None and
        shipment.buyer_organization_id == user.organization_id
    )
