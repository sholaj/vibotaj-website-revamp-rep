"""Webhooks router - receive tracking updates from Vizion."""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models import Shipment, ContainerEvent, EventType, ShipmentStatus

router = APIRouter()

# Map Vizion event types to our EventType enum
VIZION_EVENT_MAP = {
    "CONTAINER_LOADED": EventType.LOADED,
    "VESSEL_DEPARTED": EventType.DEPARTED,
    "VESSEL_ARRIVED": EventType.ARRIVED,
    "CONTAINER_DISCHARGED": EventType.DISCHARGED,
    "CONTAINER_DELIVERED": EventType.DELIVERED,
    "TRANSSHIPMENT": EventType.TRANSSHIPMENT,
    "GATE_IN": EventType.GATE_IN,
    "GATE_OUT": EventType.GATE_OUT,
}


@router.post("/vizion")
async def vizion_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive tracking webhook from Vizion API."""
    # TODO: Verify webhook signature in production
    payload = await request.json()

    container_number = payload.get("container_number") or payload.get("container_id")
    if not container_number:
        raise HTTPException(status_code=400, detail="Missing container number")

    # Find shipment
    shipment = db.query(Shipment).filter(
        Shipment.container_number == container_number
    ).first()

    if not shipment:
        # Log but don't fail - container might not be in our system yet
        return {"status": "ignored", "reason": "Container not found"}

    # Process events
    events_processed = 0
    for event_data in payload.get("events", [payload]):
        # Map event type
        vizion_type = event_data.get("event_type") or event_data.get("type")
        event_type = VIZION_EVENT_MAP.get(vizion_type)

        if not event_type:
            continue

        # Check for duplicate
        external_id = event_data.get("id") or f"{container_number}-{vizion_type}-{event_data.get('timestamp')}"
        existing = db.query(ContainerEvent).filter(
            ContainerEvent.external_id == external_id
        ).first()

        if existing:
            continue

        # Create event
        event = ContainerEvent(
            shipment_id=shipment.id,
            event_type=event_type,
            event_timestamp=datetime.fromisoformat(
                event_data.get("timestamp", "").replace("Z", "+00:00")
            ) if event_data.get("timestamp") else datetime.utcnow(),
            location_name=event_data.get("location", {}).get("name") or event_data.get("location"),
            location_code=event_data.get("location", {}).get("locode"),
            location_lat=event_data.get("location", {}).get("coordinates", {}).get("lat"),
            location_lng=event_data.get("location", {}).get("coordinates", {}).get("lng"),
            vessel_name=event_data.get("vessel", {}).get("name") or event_data.get("vessel"),
            voyage_number=event_data.get("vessel", {}).get("voyage") or event_data.get("voyage"),
            external_id=external_id,
            source="vizion",
            raw_payload=event_data
        )
        db.add(event)
        events_processed += 1

        # Update shipment status based on event
        if event_type == EventType.DEPARTED and shipment.status in [
            ShipmentStatus.CREATED, ShipmentStatus.DOCS_PENDING, ShipmentStatus.DOCS_COMPLETE
        ]:
            shipment.status = ShipmentStatus.IN_TRANSIT
            shipment.atd = event.event_timestamp

        elif event_type == EventType.ARRIVED and shipment.status == ShipmentStatus.IN_TRANSIT:
            shipment.status = ShipmentStatus.ARRIVED
            shipment.ata = event.event_timestamp

        elif event_type == EventType.DELIVERED and shipment.status in [
            ShipmentStatus.IN_TRANSIT, ShipmentStatus.ARRIVED
        ]:
            shipment.status = ShipmentStatus.DELIVERED

    # Update ETA if provided
    if payload.get("eta"):
        shipment.eta = datetime.fromisoformat(payload["eta"].replace("Z", "+00:00"))

    db.commit()

    return {
        "status": "processed",
        "container_number": container_number,
        "events_processed": events_processed
    }
