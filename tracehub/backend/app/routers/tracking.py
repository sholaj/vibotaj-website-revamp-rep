"""Container tracking router - Vizion API integration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..models import Shipment, ContainerEvent
from ..routers.auth import get_current_user, User
from ..services.vizion import VizionClient

router = APIRouter()


@router.get("/status/{container_number}")
async def get_container_status(
    container_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current container tracking status from Vizion."""
    # Find shipment by container number
    shipment = db.query(Shipment).filter(
        Shipment.container_number == container_number
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Container not found in system")

    # Get latest event from database
    latest_event = (
        db.query(ContainerEvent)
        .filter(ContainerEvent.shipment_id == shipment.id)
        .order_by(ContainerEvent.event_timestamp.desc())
        .first()
    )

    return {
        "container_number": container_number,
        "shipment_reference": shipment.reference,
        "shipment_status": shipment.status.value,
        "vessel": shipment.vessel_name,
        "voyage": shipment.voyage_number,
        "etd": shipment.etd,
        "eta": shipment.eta,
        "pol": {"code": shipment.pol_code, "name": shipment.pol_name},
        "pod": {"code": shipment.pod_code, "name": shipment.pod_name},
        "latest_event": {
            "type": latest_event.event_type.value if latest_event else None,
            "timestamp": latest_event.event_timestamp if latest_event else None,
            "location": latest_event.location_name if latest_event else None,
        } if latest_event else None
    }


@router.post("/subscribe/{shipment_id}")
async def subscribe_container(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Subscribe a shipment's container to Vizion tracking."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    if not shipment.container_number:
        raise HTTPException(status_code=400, detail="Shipment has no container number")

    # Subscribe via Vizion
    client = VizionClient()
    result = await client.subscribe_container(
        container_number=shipment.container_number,
        bl_number=shipment.bl_number
    )

    return {
        "message": "Container subscribed for tracking",
        "container_number": shipment.container_number,
        "subscription": result
    }


@router.post("/refresh/{shipment_id}")
async def refresh_tracking(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually refresh tracking data for a shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Fetch latest status from Vizion
    client = VizionClient()
    tracking_data = await client.get_container_status(shipment.container_number)

    if tracking_data:
        # Update shipment ETA if available
        if tracking_data.get("eta"):
            shipment.eta = tracking_data["eta"]

        # Save any new events
        for event_data in tracking_data.get("events", []):
            # Check if event already exists
            existing = db.query(ContainerEvent).filter(
                ContainerEvent.shipment_id == shipment_id,
                ContainerEvent.external_id == event_data.get("id")
            ).first()

            if not existing:
                event = ContainerEvent(
                    shipment_id=shipment_id,
                    event_type=event_data["type"],
                    event_timestamp=event_data["timestamp"],
                    location_name=event_data.get("location"),
                    location_code=event_data.get("location_code"),
                    vessel_name=event_data.get("vessel"),
                    voyage_number=event_data.get("voyage"),
                    external_id=event_data.get("id"),
                    source="vizion",
                    raw_payload=event_data
                )
                db.add(event)

        db.commit()

    return {"message": "Tracking data refreshed", "shipment_id": shipment_id}
