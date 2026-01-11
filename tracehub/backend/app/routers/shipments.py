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
from ..models.organization import OrganizationType
from ..schemas.shipment import ShipmentResponse, ShipmentDetailResponse, ShipmentListResponse, ShipmentCreate, ShipmentUpdate
from ..schemas.user import CurrentUser
from ..routers.auth import get_current_active_user
from ..services.compliance import get_required_documents, check_document_completeness
from ..services.audit_pack import generate_audit_pack
from ..services.permissions import Permission, has_permission
from ..services.access_control import get_accessible_shipments_filter, get_accessible_shipment, user_is_shipment_owner

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

    # Use current user's organization (auto-inject for multi-tenancy security)
    organization_id = current_user.organization_id
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User's organization not found"
        )

    # Validate buyer_organization_id if provided
    if shipment_data.buyer_organization_id:
        buyer_org = db.query(Organization).filter(
            Organization.id == shipment_data.buyer_organization_id
        ).first()

        if not buyer_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Buyer organization not found"
            )

        if buyer_org.type != OrganizationType.BUYER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization must be of type BUYER, got {buyer_org.type.value}"
            )

    # Create the shipment (updated for Sprint 8 schema)
    shipment = Shipment(
        reference=shipment_data.reference,
        container_number=shipment_data.container_number,
        product_type=shipment_data.product_type,  # Required - determines document requirements
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
        organization_id=organization_id,  # Auto-injected from current user
        buyer_organization_id=shipment_data.buyer_organization_id,  # Optional buyer org
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

    Sprint 11: Buyers can also see shipments assigned to them via buyer_organization_id.
    """
    # Filter by organization for multi-tenancy (owner OR buyer)
    query = db.query(Shipment).filter(
        get_accessible_shipments_filter(current_user)
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


@router.get("/{shipment_id}/debug")
async def get_shipment_debug(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Debug endpoint to identify serialization issues.

    Sprint 11: Buyers can also access shipments assigned to them.
    """
    # Use access control for owner OR buyer access
    shipment = (
        db.query(Shipment)
        .options(joinedload(Shipment.products))
        .filter(
            Shipment.id == shipment_id,
            get_accessible_shipments_filter(current_user)
        )
        .first()
    )
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Return raw data as dict
    return {
        "shipment_id": str(shipment.id),
        "reference": shipment.reference,
        "status": shipment.status.value if hasattr(shipment.status, 'value') else str(shipment.status),
        "product_count": len(shipment.products),
        "products": [
            {"id": str(p.id), "hs_code": p.hs_code}
            for p in shipment.products
        ]
    }


@router.get("/{shipment_id}", response_model=ShipmentDetailResponse)
async def get_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get shipment details with documents and tracking status.

    Sprint 11: Buyers can also access shipments assigned to them via buyer_organization_id.
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    try:
        # Eagerly load products to ensure HS code lookup works for compliance
        # Filter by organization for multi-tenancy security (owner OR buyer)
        shipment = (
            db.query(Shipment)
            .options(joinedload(Shipment.products))
            .filter(
                Shipment.id == shipment_id,
                get_accessible_shipments_filter(current_user)
            )
            .first()
        )
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")

        logger.info(f"Fetched shipment {shipment_id}, status: {shipment.status}")

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
        logger.info(f"Found {len(documents)} documents")

        required_docs = get_required_documents(shipment)
        logger.info(f"Required docs: {required_docs}")

        doc_completeness = check_document_completeness(documents, required_docs)
        logger.info(f"Doc completeness: {doc_completeness}")

        # Explicitly serialize to avoid Pydantic nested conversion issues
        from ..schemas.shipment import ShipmentResponse, EventInfo, DocumentInfo

        # Build response dict manually to debug
        shipment_dict = {
            "id": shipment.id,
            "reference": shipment.reference,
            "container_number": shipment.container_number,
            "bl_number": shipment.bl_number,
            "booking_ref": shipment.booking_ref,
            "vessel_name": shipment.vessel_name,
            "voyage_number": shipment.voyage_number,
            "carrier_code": shipment.carrier_code,
            "carrier_name": shipment.carrier_name,
            "etd": shipment.etd,
            "eta": shipment.eta,
            "atd": shipment.atd,
            "ata": shipment.ata,
            "pol_code": shipment.pol_code,
            "pol_name": shipment.pol_name,
            "pod_code": shipment.pod_code,
            "pod_name": shipment.pod_name,
            "incoterms": shipment.incoterms,
            "status": shipment.status.value if hasattr(shipment.status, 'value') else shipment.status,
            "exporter_name": shipment.exporter_name,
            "importer_name": shipment.importer_name,
            "eudr_compliant": shipment.eudr_compliant,
            "eudr_statement_id": shipment.eudr_statement_id,
            "organization_id": shipment.organization_id,
            "buyer_organization_id": shipment.buyer_organization_id,
            "created_at": shipment.created_at,
            "updated_at": shipment.updated_at,
            "products": [
                {
                    "id": p.id,
                    "hs_code": p.hs_code,
                    "description": p.description,
                    "quantity_net_kg": p.quantity_net_kg,
                    "quantity_gross_kg": p.quantity_gross_kg,
                    "packaging_type": getattr(p, 'packaging_type', None) or getattr(p, 'packaging', None),
                }
                for p in shipment.products
            ]
        }
        logger.info(f"Built shipment_dict with {len(shipment_dict.get('products', []))} products")
        shipment_data = ShipmentResponse(**shipment_dict)

        # Serialize event
        event_data = None
        if latest_event:
            event_dict = {
                "id": latest_event.id,
                "event_status": latest_event.event_status.value if hasattr(latest_event.event_status, 'value') else str(latest_event.event_status),
                "event_time": latest_event.event_time,
                "location_code": latest_event.location_code,
                "location_name": latest_event.location_name,
                "vessel_name": latest_event.vessel_name,
                "voyage_number": latest_event.voyage_number,
            }
            event_data = EventInfo(**event_dict)

        # Serialize documents
        doc_data = []
        for doc in documents:
            doc_dict = {
                "id": doc.id,
                "document_type": doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
                "name": doc.name,
                "status": doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
                "reference_number": doc.reference_number,
                "issue_date": getattr(doc, 'issue_date', None) or getattr(doc, 'document_date', None),
                "file_path": doc.file_path,
            }
            doc_data.append(DocumentInfo(**doc_dict))

        logger.info(f"Returning response with {len(doc_data)} documents")
        return ShipmentDetailResponse(
            shipment=shipment_data,
            latest_event=event_data,
            documents=doc_data,
            document_summary=doc_completeness
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error in get_shipment for {shipment_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: UUID,
    shipment_data: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Update a shipment.

    Requires: shipments:update permission (admin, logistics_agent roles)
    Sprint 11: Only shipment OWNERS can update (not buyers).
    """
    check_permission(current_user, Permission.SHIPMENTS_UPDATE)

    # Find shipment - first check if user can access it at all
    shipment = get_accessible_shipment(db, shipment_id, current_user)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Only owners can update, not buyers
    if not user_is_shipment_owner(shipment, current_user):
        raise HTTPException(
            status_code=403,
            detail="Only shipment owners can update shipments. Buyers have read-only access."
        )

    # Update only provided fields
    update_data = shipment_data.model_dump(exclude_unset=True)

    # Check for duplicate reference if reference is being changed
    if "reference" in update_data and update_data["reference"] != shipment.reference:
        existing = db.query(Shipment).filter(
            Shipment.reference == update_data["reference"],
            Shipment.id != shipment_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A shipment with reference '{update_data['reference']}' already exists"
            )

    for field, value in update_data.items():
        setattr(shipment, field, value)

    shipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(shipment)

    return shipment


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Delete a shipment.

    Requires: shipments:delete permission (admin role only)
    Sprint 11: Only shipment OWNERS can delete (not buyers).
    Also deletes associated documents, products, and events.
    """
    check_permission(current_user, Permission.SHIPMENTS_DELETE)

    # Find shipment - first check if user can access it at all
    shipment = get_accessible_shipment(db, shipment_id, current_user)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Only owners can delete, not buyers
    if not user_is_shipment_owner(shipment, current_user):
        raise HTTPException(
            status_code=403,
            detail="Only shipment owners can delete shipments. Buyers have read-only access."
        )

    # Delete associated records (cascade should handle this, but being explicit)
    db.query(Document).filter(Document.shipment_id == shipment_id).delete()
    db.query(ContainerEvent).filter(ContainerEvent.shipment_id == shipment_id).delete()
    db.query(Product).filter(Product.shipment_id == shipment_id).delete()

    # Delete the shipment
    db.delete(shipment)
    db.commit()

    return None


@router.get("/{shipment_id}/documents")
async def get_shipment_documents(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """List all documents for a shipment.

    Sprint 11: Buyers can also access documents for shipments assigned to them.
    """
    # Eagerly load products to ensure HS code lookup works for compliance
    # Filter by organization for multi-tenancy security (owner OR buyer)
    shipment = (
        db.query(Shipment)
        .options(joinedload(Shipment.products))
        .filter(
            Shipment.id == shipment_id,
            get_accessible_shipments_filter(current_user)
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
    """Get container event history for a shipment.

    Sprint 11: Buyers can also access events for shipments assigned to them.
    """
    # Filter by organization for multi-tenancy security (owner OR buyer)
    shipment = get_accessible_shipment(db, shipment_id, current_user)
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
    """Download audit pack ZIP for a shipment.

    Sprint 11: Buyers can also download audit packs for shipments assigned to them.
    """
    # Filter by organization for multi-tenancy security (owner OR buyer)
    shipment = get_accessible_shipment(db, shipment_id, current_user)
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
