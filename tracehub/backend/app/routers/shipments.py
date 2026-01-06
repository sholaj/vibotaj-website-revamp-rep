"""Shipments router - core shipment CRUD and operations."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import io

from ..database import get_db
from ..models import Shipment, Document, ContainerEvent, Product, Organization
from ..models.shipment import ShipmentStatus
from ..schemas.shipment import ShipmentResponse, ShipmentDetailResponse, ShipmentListResponse, ShipmentCreate, ShipmentUpdate
from ..schemas.user import CurrentUser
from ..routers.auth import get_current_active_user
from ..services.compliance import get_required_documents, check_document_completeness
from ..services.audit_pack import generate_audit_pack
from ..services.permissions import Permission, has_permission

router = APIRouter()


def check_permission(user: CurrentUser, permission: Permission) -> None:
    """Check if user has the required permission, raise 403 if not."""
    if not has_permission(user.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: {permission.value}"
        )


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Create a new shipment.

    Requires: shipments:create permission (admin, logistics_agent roles)

    For historical/completed shipments, set is_historical=True and status accordingly.
    This allows uploading documentation for past trades.
    """
    # Check permission
    check_permission(current_user, Permission.SHIPMENTS_CREATE)

    # Check for duplicate reference
    existing = db.query(Shipment).filter(Shipment.reference == shipment_data.reference).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A shipment with reference '{shipment_data.reference}' already exists"
        )

    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == shipment_data.organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with id '{shipment_data.organization_id}' not found"
        )

    # Create the shipment (updated for Sprint 8 schema)
    shipment = Shipment(
        reference=shipment_data.reference,
        container_number=shipment_data.container_number,
        bl_number=shipment_data.bl_number,
        booking_ref=shipment_data.booking_ref,  # Renamed from booking_reference
        vessel_name=shipment_data.vessel_name,
        voyage_number=shipment_data.voyage_number,
        carrier_code=shipment_data.carrier_code,  # New field
        carrier_name=shipment_data.carrier_name,  # New field
        etd=shipment_data.etd,
        eta=shipment_data.eta,
        atd=shipment_data.atd,
        ata=shipment_data.ata,
        pol_code=shipment_data.pol_code,
        pol_name=shipment_data.pol_name,
        pod_code=shipment_data.pod_code,
        pod_name=shipment_data.pod_name,
        incoterms=shipment_data.incoterms,
        status=shipment_data.status or ShipmentStatus.DRAFT,  # Changed default
        exporter_name=shipment_data.exporter_name,  # New field
        importer_name=shipment_data.importer_name,  # New field
        eudr_compliant=shipment_data.eudr_compliant,  # New field
        eudr_statement_id=shipment_data.eudr_statement_id,  # New field
        organization_id=shipment_data.organization_id,  # Required for multi-tenancy
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    return shipment


@router.get("", response_model=List[ShipmentResponse])
async def list_shipments(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """List all shipments with optional filtering.

    Returns a list of shipments sorted by creation date (newest first).
    Filtered by user's organization for multi-tenancy.
    """
    # Filter by organization for multi-tenancy
    query = db.query(Shipment).filter(
        Shipment.organization_id == current_user.organization_id
    )

    # Apply status filter if provided
    if status:
        from ..models.shipment import ShipmentStatus
        try:
            status_enum = ShipmentStatus(status)
            query = query.filter(Shipment.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid values are: {[s.value for s in ShipmentStatus]}"
            )

    # Order by creation date descending and apply pagination
    shipments = (
        query
        .order_by(Shipment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return shipments


@router.get("/{shipment_id}", response_model=ShipmentDetailResponse)
async def get_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get shipment details with documents and tracking status."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Eagerly load products to ensure HS code lookup works for compliance
        # Filter by organization for multi-tenancy security
        shipment = (
            db.query(Shipment)
            .options(joinedload(Shipment.products))
            .filter(
                Shipment.id == shipment_id,
                Shipment.organization_id == current_user.organization_id
            )
            .first()
        )
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        logger.info(f"Shipment loaded: {shipment.reference}")

        # Get latest container event
        latest_event = (
            db.query(ContainerEvent)
            .filter(ContainerEvent.shipment_id == shipment_id)
            .order_by(ContainerEvent.event_time.desc())
            .first()
        )
        logger.info(f"Latest event: {latest_event}")

        # Get document summary
        documents = db.query(Document).filter(Document.shipment_id == shipment_id).all()
        logger.info(f"Documents count: {len(documents)}")

        required_docs = get_required_documents(shipment)
        logger.info(f"Required docs: {required_docs}")

        doc_completeness = check_document_completeness(documents, required_docs)
        logger.info(f"Doc completeness: {doc_completeness}")

        # Explicitly build response to catch serialization errors
        from ..schemas.shipment import ShipmentResponse, EventInfo, DocumentInfo

        # Serialize shipment
        try:
            shipment_data = ShipmentResponse.model_validate(shipment)
            logger.info("Shipment serialized successfully")
        except Exception as e:
            logger.error(f"Failed to serialize shipment: {type(e).__name__}: {e}")
            raise

        # Serialize event
        event_data = None
        if latest_event:
            try:
                event_data = EventInfo.model_validate(latest_event)
                logger.info("Event serialized successfully")
            except Exception as e:
                logger.error(f"Failed to serialize event: {type(e).__name__}: {e}")
                raise

        # Serialize documents
        doc_data = []
        for i, doc in enumerate(documents):
            try:
                doc_data.append(DocumentInfo.model_validate(doc))
            except Exception as e:
                logger.error(f"Failed to serialize document {i}: {type(e).__name__}: {e}")
                logger.error(f"Document fields: id={doc.id}, type={doc.document_type}, status={doc.status}, name={doc.name}")
                raise
        logger.info(f"Documents serialized: {len(doc_data)}")

        return ShipmentDetailResponse(
            shipment=shipment_data,
            latest_event=event_data,
            documents=doc_data,
            document_summary=doc_completeness
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error in get_shipment: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


@router.get("/{shipment_id}/documents")
async def get_shipment_documents(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """List all documents for a shipment."""
    # Eagerly load products to ensure HS code lookup works for compliance
    # Filter by organization for multi-tenancy security
    shipment = (
        db.query(Shipment)
        .options(joinedload(Shipment.products))
        .filter(
            Shipment.id == shipment_id,
            Shipment.organization_id == current_user.organization_id
        )
        .first()
    )
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
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get container event history for a shipment."""
    # Filter by organization for multi-tenancy security
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    events = (
        db.query(ContainerEvent)
        .filter(ContainerEvent.shipment_id == shipment_id)
        .order_by(ContainerEvent.event_time.asc())
        .all()
    )

    return {"events": events}


@router.get("/{shipment_id}/audit-pack")
async def download_audit_pack(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Download audit pack ZIP for a shipment."""
    # Filter by organization for multi-tenancy security
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
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
