"""Shipments router - core shipment CRUD and operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import io

from ..database import get_db
from ..models import Shipment, Document, ContainerEvent, Product, Party
from ..schemas.shipment import ShipmentResponse, ShipmentDetailResponse
from ..routers.auth import get_current_user, User
from ..services.compliance import get_required_documents, check_document_completeness
from ..services.audit_pack import generate_audit_pack

router = APIRouter()


@router.get("/{shipment_id}", response_model=ShipmentDetailResponse)
async def get_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shipment details with documents and tracking status."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get latest container event
    latest_event = (
        db.query(ContainerEvent)
        .filter(ContainerEvent.shipment_id == shipment_id)
        .order_by(ContainerEvent.event_timestamp.desc())
        .first()
    )

    # Get document summary
    documents = db.query(Document).filter(Document.shipment_id == shipment_id).all()
    required_docs = get_required_documents(shipment)
    doc_completeness = check_document_completeness(documents, required_docs)

    return ShipmentDetailResponse(
        shipment=shipment,
        latest_event=latest_event,
        documents=documents,
        document_summary=doc_completeness
    )


@router.get("/{shipment_id}/documents")
async def get_shipment_documents(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents for a shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    documents = db.query(Document).filter(Document.shipment_id == shipment_id).all()
    required_docs = get_required_documents(shipment)
    completeness = check_document_completeness(documents, required_docs)

    return {
        "documents": documents,
        "required_types": required_docs,
        "summary": completeness
    }


@router.get("/{shipment_id}/events")
async def get_shipment_events(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get container event history for a shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    events = (
        db.query(ContainerEvent)
        .filter(ContainerEvent.shipment_id == shipment_id)
        .order_by(ContainerEvent.event_timestamp.asc())
        .all()
    )

    return {"events": events}


@router.get("/{shipment_id}/audit-pack")
async def download_audit_pack(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download audit pack ZIP for a shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Generate audit pack
    zip_buffer = generate_audit_pack(shipment, db)

    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={shipment.reference}-audit-pack.zip"
        }
    )
