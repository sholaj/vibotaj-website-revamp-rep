"""Container tracking router - JSONCargo API integration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import Optional

from ..database import get_db
from ..models import Shipment, ShipmentStatus, ContainerEvent, EventStatus
from ..routers.auth import get_current_active_user
from ..schemas.user import CurrentUser
from ..services.jsoncargo import get_jsoncargo_client

router = APIRouter()


@router.get("/status/{container_number}")
async def get_container_status(
    container_number: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get current container tracking status.

    Returns both database status and live tracking data from JSONCargo.
    """
    # Find shipment by container number (filtered by organization)
    shipment = db.query(Shipment).filter(
        Shipment.container_number == container_number,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Container not found in system")

    # Get latest event from database
    latest_event = (
        db.query(ContainerEvent)
        .filter(ContainerEvent.shipment_id == shipment.id)
        .order_by(ContainerEvent.event_time.desc())
        .first()
    )

    # Get live status from JSONCargo
    client = get_jsoncargo_client()
    live_status = await client.get_container_status(container_number)

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
            "status": latest_event.event_status.value if latest_event else None,
            "timestamp": latest_event.event_time if latest_event else None,
            "location": latest_event.location_name if latest_event else None,
        } if latest_event else None,
        "live_tracking": live_status
    }


@router.get("/live/{container_number}")
async def get_live_tracking(
    container_number: str,
    shipping_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get live container tracking directly from JSONCargo.

    This endpoint fetches real-time tracking data for containers
    belonging to the user's organization.
    """
    # Security: Verify container belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.container_number == container_number,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail=f"Container {container_number} not found in your organization"
        )

    client = get_jsoncargo_client()
    tracking_data = await client.get_container_status(
        container_number,
        shipping_line=shipping_line
    )

    if not tracking_data:
        raise HTTPException(
            status_code=404,
            detail=f"Container {container_number} not found or carrier not detected"
        )

    return tracking_data


@router.get("/bol/{bl_number}")
async def get_tracking_by_bol(
    bl_number: str,
    shipping_line: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get container tracking by Bill of Lading number.

    Requires shipping_line parameter (e.g., 'maersk', 'msc', 'hapag-lloyd').
    Only returns tracking for B/L numbers linked to shipments in your organization.
    """
    # Security: Verify B/L belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.bl_number == bl_number,
        Shipment.organization_id == current_user.organization_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail=f"B/L {bl_number} not found in your organization"
        )

    client = get_jsoncargo_client()
    tracking_data = await client.get_container_by_bol(
        bl_number,
        shipping_line=shipping_line
    )

    if not tracking_data:
        raise HTTPException(
            status_code=404,
            detail=f"B/L {bl_number} not found for {shipping_line}"
        )

    return tracking_data


@router.post("/refresh/{shipment_id}")
async def refresh_tracking(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Refresh tracking data for a shipment from JSONCargo.

    Fetches latest tracking data and syncs new events to the database.
    """
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    if not shipment.container_number:
        raise HTTPException(status_code=400, detail="Shipment has no container number")

    # Fetch latest status from JSONCargo
    client = get_jsoncargo_client()
    tracking_data = await client.get_container_status(shipment.container_number)

    if not tracking_data:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch tracking data for {shipment.container_number}"
        )

    events_added = 0
    # Map JSONCargo / carrier event types to our enum
    event_type_map = {
        "CONTAINER_LOADED": EventStatus.LOADED,
        "VESSEL_DEPARTED": EventStatus.DEPARTED,
        "VESSEL_ARRIVED": EventStatus.ARRIVED,
        "CONTAINER_DISCHARGED": EventStatus.DISCHARGED,
        "CONTAINER_DELIVERED": EventStatus.DELIVERED,
        "DELIVERED": EventStatus.DELIVERED,
        "DISCHARGED": EventStatus.DISCHARGED,
        "DEPARTED": EventStatus.DEPARTED,
        "ARRIVED": EventStatus.ARRIVED,
        "TRANSSHIPMENT": EventStatus.TRANSSHIPMENT,
        "GATE_IN": EventStatus.GATE_IN,
        "GATE_OUT": EventStatus.GATE_OUT,
        "BOOKED": EventStatus.BOOKED,
        "IN_TRANSIT": EventStatus.IN_TRANSIT,
        "LOADED": EventStatus.LOADED,
    }

    status_priority = {
        EventStatus.DELIVERED: 5,
        EventStatus.GATE_OUT: 4,
        EventStatus.ARRIVED: 4,
        EventStatus.DISCHARGED: 4,
        EventStatus.DEPARTED: 3,
        EventStatus.IN_TRANSIT: 2,
        EventStatus.LOADED: 2,
        EventStatus.GATE_IN: 1,
        EventStatus.BOOKED: 1,
    }

    def normalize_event_status(raw_status: str) -> EventStatus:
        key = (raw_status or "").upper()
        if key in event_type_map:
            return event_type_map[key]
        try:
            return EventStatus(key)
        except ValueError:
            return EventStatus.OTHER

    def consider_status(best_status, candidate):
        if not candidate:
            return best_status
        if best_status is None:
            return candidate
        if status_priority.get(candidate, 0) > status_priority.get(best_status, 0):
            return candidate
        return best_status

    highest_status = None
    highest_status_time: Optional[datetime] = None

    # Update shipment ETA if available
    if tracking_data.get("eta"):
        try:
            eta_str = tracking_data["eta"]
            if isinstance(eta_str, str):
                shipment.eta = datetime.fromisoformat(eta_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass  # Keep existing ETA if parse fails

    # Sync events to database
    for event_data in tracking_data.get("events", []):
        # Map event type to EventStatus
        event_type_str = event_data.get("type", "OTHER")
        event_status = normalize_event_status(event_type_str)

        # Parse timestamp
        timestamp = event_data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.utcnow()
        if not timestamp:
            timestamp = datetime.utcnow()

        # Helper to truncate strings to max length
        def truncate(value, max_len):
            if value and len(value) > max_len:
                return value[:max_len]
            return value

        # Avoid duplicate events with same status and timestamp
        duplicate = (
            db.query(ContainerEvent)
            .filter_by(
                shipment_id=shipment_id,
                event_status=event_status,
                event_time=timestamp
            )
            .first()
        )

        if not duplicate:
            event = ContainerEvent(
                shipment_id=shipment_id,
                organization_id=shipment.organization_id,
                event_status=event_status,
                event_time=timestamp,
                location_name=truncate(event_data.get("location"), 255),
                location_code=truncate(event_data.get("location_code"), 20),
                vessel_name=truncate(event_data.get("vessel"), 100),
                voyage_number=truncate(event_data.get("voyage"), 50),
                description=event_data.get("description"),
                source="jsoncargo",
                raw_data=event_data
            )
            db.add(event)
            events_added += 1

        # Track most advanced status for shipment lifecycle updates
        highest_status = consider_status(highest_status, event_status)
        if event_status in {EventStatus.ARRIVED, EventStatus.DELIVERED, EventStatus.DEPARTED}:
            if not highest_status_time or (timestamp and timestamp > highest_status_time):
                highest_status_time = timestamp

    # Consider live container status to fill gaps
    live_status_raw = tracking_data.get("status", "")
    # Map common status strings to event statuses
    status_to_event_map = {
        "DISCHARGED FROM VESSEL": EventStatus.DISCHARGED,
        "DISCHARGED": EventStatus.DISCHARGED,
        "DELIVERED": EventStatus.DELIVERED,
        "ARRIVED": EventStatus.ARRIVED,
        "DEPARTED": EventStatus.DEPARTED,
        "IN TRANSIT": EventStatus.IN_TRANSIT,
        "LOADED": EventStatus.LOADED,
    }
    live_status_upper = live_status_raw.upper().strip()
    live_status_event = status_to_event_map.get(live_status_upper)
    if not live_status_event:
        live_status_event = normalize_event_status(live_status_raw)
    highest_status = consider_status(highest_status, live_status_event)

    # Update shipment status based on the most advanced event/status
    if highest_status:
        previous_status = shipment.status
        if highest_status == EventStatus.DELIVERED:
            shipment.status = ShipmentStatus.DELIVERED
            if highest_status_time and shipment.ata is None:
                shipment.ata = highest_status_time
        elif highest_status in {EventStatus.ARRIVED, EventStatus.DISCHARGED}:
            shipment.status = ShipmentStatus.ARRIVED
            if highest_status_time and shipment.ata is None:
                shipment.ata = highest_status_time
        elif highest_status in {EventStatus.DEPARTED, EventStatus.IN_TRANSIT, EventStatus.GATE_OUT, EventStatus.LOADED}:
            shipment.status = ShipmentStatus.IN_TRANSIT
            if highest_status_time and shipment.atd is None:
                shipment.atd = highest_status_time

        if shipment.status != previous_status:
            shipment.updated_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Tracking data refreshed",
        "shipment_id": str(shipment_id),
        "container_number": shipment.container_number,
        "events_added": events_added,
        "live_status": tracking_data.get("status")
    }


@router.get("/usage")
async def get_api_usage(
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get JSONCargo API usage statistics.

    Shows how many API calls have been used this month.
    """
    client = get_jsoncargo_client()
    usage = await client.get_api_usage()

    if not usage:
        return {"message": "Could not fetch API usage stats"}

    return usage
