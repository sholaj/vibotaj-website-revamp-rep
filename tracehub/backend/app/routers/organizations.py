"""Organizations router for TraceHub API.

Provides endpoints for organization management and listing.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.organization import Organization, OrganizationType, OrganizationStatus
from ..schemas.shipment import OrganizationInfo
from ..schemas.user import CurrentUser
from .auth import get_current_active_user

router = APIRouter()


@router.get("/buyers", response_model=List[OrganizationInfo])
async def list_buyer_organizations(
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all buyer organizations for dropdown selection.

    Returns organizations with type=BUYER, ordered by name.
    Used for the buyer organization dropdown in shipment creation form.
    """
    buyers = db.query(Organization).filter(
        Organization.type == OrganizationType.BUYER,
        Organization.status == OrganizationStatus.ACTIVE
    ).order_by(Organization.name).all()

    return buyers
