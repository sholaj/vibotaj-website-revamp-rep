"""Webhooks router - receive tracking updates from carriers."""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import hmac
import hashlib
import json

from ..database import get_db
from ..config import get_settings
from ..models import Shipment, ContainerEvent, EventType, ShipmentStatus
from ..services.notifications import (
    notify_shipment_status_change,
    notify_eta_changed
)

router = APIRouter()
settings = get_settings()

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

# Map carrier webhook event types to our EventType enum
CARRIER_EVENT_MAP = {
    # Standard event names
    "loaded": EventType.LOADED,
    "departed": EventType.DEPARTED,
    "arrived": EventType.ARRIVED,
    "discharged": EventType.DISCHARGED,
    "delivered": EventType.DELIVERED,
    "transshipment": EventType.TRANSSHIPMENT,
    "gate_in": EventType.GATE_IN,
    "gate_out": EventType.GATE_OUT,
    "customs_hold": EventType.CUSTOMS_HOLD,
    "customs_released": EventType.CUSTOMS_RELEASED,
    # Alternate names
    "LOADED": EventType.LOADED,
    "DEPARTED": EventType.DEPARTED,
    "ARRIVED": EventType.ARRIVED,
    "DISCHARGED": EventType.DISCHARGED,
    "DELIVERED": EventType.DELIVERED,
    "POD": EventType.ARRIVED,  # Proof of Delivery at port
    "PICKUP": EventType.GATE_OUT,
    "EMPTY_RETURN": EventType.EMPTY_RETURN,
}

# Events that trigger notifications
NOTIFICATION_EVENTS = {
    EventType.DEPARTED: True,
    EventType.ARRIVED: True,
    EventType.DELIVERED: True,
    EventType.CUSTOMS_HOLD: True,
}


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify webhook signature using HMAC.

    Args:
        payload: Raw request body bytes
        signature: Signature header value
        secret: Webhook secret key
        algorithm: Hash algorithm (default: sha256)

    Returns:
        True if signature is valid, False otherwise
    """
    if not secret:
        # No secret configured, skip verification (dev mode)
        return True

    # Handle different signature formats
    # Format: "sha256=xxx" or just "xxx"
    if "=" in signature:
        algo, sig = signature.split("=", 1)
    else:
        sig = signature

    # Compute expected signature
    expected = hmac.new(
        secret.encode(),
        payload,
        getattr(hashlib, algorithm)
    ).hexdigest()

    return hmac.compare_digest(sig, expected)


def get_users_to_notify(shipment: Shipment, db: Session) -> list[str]:
    """
    Get list of users to notify for a shipment.

    In production, this would query user roles and subscriptions.
    For POC, notify the demo user and any configured admins.
    """
    users = [settings.demo_username]

    # In future: Query buyer/supplier contacts from Party model
    # if shipment.buyer:
    #     users.extend(get_party_contacts(shipment.buyer_id))

    return list(set(users))  # Deduplicate


@router.post("/vizion")
async def vizion_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive tracking webhook from Vizion API."""
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

    # Store old ETA for comparison
    old_eta = shipment.eta
    old_status = shipment.status

    # Process events
    events_processed = 0
    status_changed = False

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
            status_changed = True

        elif event_type == EventType.ARRIVED and shipment.status == ShipmentStatus.IN_TRANSIT:
            shipment.status = ShipmentStatus.ARRIVED
            shipment.ata = event.event_timestamp
            status_changed = True

        elif event_type == EventType.DELIVERED and shipment.status in [
            ShipmentStatus.IN_TRANSIT, ShipmentStatus.ARRIVED
        ]:
            shipment.status = ShipmentStatus.DELIVERED
            status_changed = True

    # Update ETA if provided
    eta_changed = False
    if payload.get("eta"):
        new_eta = datetime.fromisoformat(payload["eta"].replace("Z", "+00:00"))
        if shipment.eta != new_eta:
            shipment.eta = new_eta
            eta_changed = True

    # Get users to notify
    notify_users = get_users_to_notify(shipment, db)

    # Create notifications for status changes
    if status_changed:
        notify_shipment_status_change(
            db=db,
            shipment=shipment,
            old_status=old_status.value,
            new_status=shipment.status.value,
            notify_users=notify_users
        )

    # Create notifications for ETA changes
    if eta_changed and old_eta:
        notify_eta_changed(
            db=db,
            shipment=shipment,
            old_eta=old_eta,
            new_eta=shipment.eta,
            notify_users=notify_users
        )

    db.commit()

    return {
        "status": "processed",
        "container_number": container_number,
        "events_processed": events_processed,
        "status_changed": status_changed,
        "eta_changed": eta_changed
    }


@router.post("/carrier")
async def carrier_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: Optional[str] = Header(default=None),
    x_webhook_secret: Optional[str] = Header(default=None)
):
    """
    Generic carrier webhook endpoint.

    Accepts webhooks from various carriers with a standardized payload format:
    {
        "container_number": "MSCU1234567",
        "event_type": "departed" | "arrived" | "delivered" | etc,
        "timestamp": "2024-01-15T10:30:00Z",
        "location": {
            "name": "Port of Rotterdam",
            "code": "NLRTM",
            "lat": 51.9,
            "lng": 4.5
        },
        "vessel": {
            "name": "MSC Oscar",
            "voyage": "12W"
        },
        "eta": "2024-02-01T08:00:00Z",  // optional
        "carrier": "MSC"  // optional
    }
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature if configured
    webhook_secret = getattr(settings, 'webhook_secret', None)
    if webhook_secret and x_webhook_signature:
        if not verify_webhook_signature(body, x_webhook_signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Extract container number
    container_number = payload.get("container_number") or payload.get("container_id")
    if not container_number:
        raise HTTPException(status_code=400, detail="Missing container_number in payload")

    # Find shipment
    shipment = db.query(Shipment).filter(
        Shipment.container_number == container_number
    ).first()

    if not shipment:
        return {
            "status": "ignored",
            "reason": "Container not found in system",
            "container_number": container_number
        }

    # Store old values for comparison
    old_eta = shipment.eta
    old_status = shipment.status.value

    # Map event type
    event_type_str = payload.get("event_type") or payload.get("type")
    event_type = CARRIER_EVENT_MAP.get(event_type_str, EventType.UNKNOWN)

    # Parse timestamp
    timestamp_str = payload.get("timestamp")
    if timestamp_str:
        try:
            event_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            event_timestamp = datetime.utcnow()
    else:
        event_timestamp = datetime.utcnow()

    # Generate external ID for deduplication
    external_id = payload.get("id") or f"{container_number}-{event_type_str}-{timestamp_str}"

    # Check for duplicate event
    existing = db.query(ContainerEvent).filter(
        ContainerEvent.external_id == external_id
    ).first()

    if existing:
        return {
            "status": "duplicate",
            "message": "Event already processed",
            "event_id": external_id
        }

    # Extract location info
    location = payload.get("location", {})
    if isinstance(location, str):
        location = {"name": location}

    # Extract vessel info
    vessel = payload.get("vessel", {})
    if isinstance(vessel, str):
        vessel = {"name": vessel}

    # Create container event
    event = ContainerEvent(
        shipment_id=shipment.id,
        event_type=event_type,
        event_timestamp=event_timestamp,
        location_name=location.get("name"),
        location_code=location.get("code") or location.get("locode"),
        location_lat=location.get("lat") or location.get("latitude"),
        location_lng=location.get("lng") or location.get("longitude"),
        vessel_name=vessel.get("name"),
        voyage_number=vessel.get("voyage") or vessel.get("voyage_number"),
        external_id=external_id,
        source=payload.get("carrier", "carrier_webhook"),
        raw_payload=payload
    )
    db.add(event)

    # Update shipment status based on event
    status_changed = False
    if event_type == EventType.DEPARTED and shipment.status in [
        ShipmentStatus.CREATED, ShipmentStatus.DOCS_PENDING, ShipmentStatus.DOCS_COMPLETE
    ]:
        shipment.status = ShipmentStatus.IN_TRANSIT
        shipment.atd = event_timestamp
        status_changed = True

    elif event_type == EventType.ARRIVED and shipment.status == ShipmentStatus.IN_TRANSIT:
        shipment.status = ShipmentStatus.ARRIVED
        shipment.ata = event_timestamp
        status_changed = True

    elif event_type == EventType.DELIVERED and shipment.status in [
        ShipmentStatus.IN_TRANSIT, ShipmentStatus.ARRIVED
    ]:
        shipment.status = ShipmentStatus.DELIVERED
        status_changed = True

    # Update ETA if provided
    eta_changed = False
    if payload.get("eta"):
        try:
            new_eta = datetime.fromisoformat(payload["eta"].replace("Z", "+00:00"))
            if shipment.eta != new_eta:
                shipment.eta = new_eta
                eta_changed = True
        except ValueError:
            pass  # Invalid ETA format, ignore

    # Get users to notify
    notify_users = get_users_to_notify(shipment, db)

    # Create notifications for significant events
    if status_changed:
        notify_shipment_status_change(
            db=db,
            shipment=shipment,
            old_status=old_status,
            new_status=shipment.status.value,
            notify_users=notify_users,
            event_details={
                "location": location.get("name"),
                "vessel": vessel.get("name"),
                "timestamp": event_timestamp.isoformat()
            }
        )

    if eta_changed and old_eta:
        notify_eta_changed(
            db=db,
            shipment=shipment,
            old_eta=old_eta,
            new_eta=shipment.eta,
            notify_users=notify_users
        )

    db.commit()

    return {
        "status": "processed",
        "container_number": container_number,
        "event_type": event_type.value,
        "event_id": external_id,
        "status_changed": status_changed,
        "eta_changed": eta_changed,
        "new_status": shipment.status.value if status_changed else None
    }


@router.post("/test")
async def test_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Test webhook endpoint for development.

    Accepts any payload and logs it for debugging.
    """
    payload = await request.json()
    headers = dict(request.headers)

    return {
        "status": "received",
        "message": "Test webhook received successfully",
        "payload_preview": str(payload)[:500],
        "headers": {k: v for k, v in headers.items() if k.lower().startswith("x-")}
    }
