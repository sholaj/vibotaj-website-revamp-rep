"""Documents router - document upload and management."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel
import os
import shutil

from ..database import get_db
from ..config import get_settings
from ..models import Document, DocumentType, DocumentStatus, Shipment
from ..routers.auth import get_current_user, get_current_active_user, User
from ..schemas.user import CurrentUser
from ..services.validation import (
    validate_document as run_validation,
    get_required_fields,
    check_expiring_documents,
    ValidationResult
)
from ..services.workflow import (
    get_allowed_transitions,
    transition_document,
    get_status_info,
    get_workflow_summary,
    TransitionResult
)
from ..services.notifications import (
    notify_document_uploaded,
    notify_document_validated,
    notify_document_rejected
)
from ..services.permissions import Permission, has_permission

router = APIRouter()
settings = get_settings()


def check_permission(user: CurrentUser, permission: Permission) -> None:
    """Check if user has the required permission, raise 403 if not."""
    if not has_permission(user.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: {permission.value}"
        )


# Request/Response models
class TransitionRequest(BaseModel):
    """Request to transition a document to a new state."""
    target_status: DocumentStatus
    notes: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request to approve or reject a document."""
    notes: Optional[str] = None


class DocumentMetadataUpdate(BaseModel):
    """Update document metadata fields."""
    reference_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    extra_data: Optional[dict] = None


@router.post("/upload")
async def upload_document(
    shipment_id: UUID = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    reference_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Upload a document for a shipment.

    Requires: documents:upload permission (admin, compliance, supplier roles)
    """
    # Check permission
    check_permission(current_user, Permission.DOCUMENTS_UPLOAD)

    # Verify shipment exists
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Create upload directory if needed
    upload_dir = os.path.join(settings.upload_dir, str(shipment_id))
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document record
    document = Document(
        shipment_id=shipment_id,
        document_type=document_type,
        name=file.filename,
        file_path=file_path,
        file_name=file.filename,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        status=DocumentStatus.UPLOADED,
        reference_number=reference_number,
        uploaded_by=current_user.email,
        uploaded_at=datetime.utcnow()
    )

    db.add(document)

    # Notify compliance team/admins about new document
    # For POC, notify the demo user (typically an admin would review uploads)
    notify_document_uploaded(
        db=db,
        document=document,
        uploader=current_user.email,
        notify_users=[settings.demo_username]  # In production: query admin users
    )

    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "name": document.name,
        "type": document.document_type,
        "status": document.status,
        "message": "Document uploaded successfully"
    }


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document metadata."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download document file."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")

    return FileResponse(
        document.file_path,
        filename=document.file_name,
        media_type=document.mime_type
    )


@router.patch("/{document_id}/validate")
async def validate_document(
    document_id: UUID,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Mark document as validated.

    Requires: documents:validate permission (admin, compliance roles)
    """
    # Check permission
    check_permission(current_user, Permission.DOCUMENTS_VALIDATE)

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = DocumentStatus.VALIDATED
    document.validated_at = datetime.utcnow()
    document.validated_by = current_user.email
    if notes:
        document.validation_notes = notes

    db.commit()
    db.refresh(document)

    return {"message": "Document validated", "status": document.status}


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Delete a document.

    Requires: documents:delete permission (admin role)
    """
    # Check permission
    check_permission(current_user, Permission.DOCUMENTS_DELETE)

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file if exists
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted"}


# ============ Validation & Workflow Endpoints ============

@router.get("/{document_id}/validation")
async def get_document_validation(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get validation status and required fields for a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Run validation
    result = run_validation(document)

    # Get required fields for this document type
    required_fields = get_required_fields(document.document_type)

    return {
        "document_id": str(document.id),
        "document_type": document.document_type.value,
        "current_status": document.status.value,
        "validation": result.to_dict(),
        "required_fields": required_fields,
        "status_info": get_status_info(document.status)
    }


@router.get("/{document_id}/transitions")
async def get_document_transitions(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get allowed state transitions for a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Use actual user role for transition permissions
    user_role = current_user.role.value
    allowed = get_allowed_transitions(document.status, user_role)

    return {
        "document_id": str(document.id),
        "current_status": document.status.value,
        "current_status_info": get_status_info(document.status),
        "allowed_transitions": [
            {
                "status": status.value,
                "info": get_status_info(status)
            }
            for status in allowed
        ]
    }


@router.post("/{document_id}/transition")
async def transition_document_status(
    document_id: UUID,
    request: TransitionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Transition a document to a new workflow state.

    Requires: documents:transition permission (admin, compliance roles)
    """
    # Check permission
    check_permission(current_user, Permission.DOCUMENTS_TRANSITION)

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Use actual user role for transition permissions
    user_role = current_user.role.value

    result = transition_document(
        document=document,
        target_status=request.target_status,
        user=current_user.email,
        user_role=user_role,
        notes=request.notes
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.to_dict()
        )

    # Persist the changes
    db.commit()
    db.refresh(document)

    return {
        "message": f"Document transitioned to {request.target_status.value}",
        "result": result.to_dict()
    }


@router.post("/{document_id}/approve")
async def approve_document(
    document_id: UUID,
    request: ApprovalRequest = Body(default=ApprovalRequest()),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Approve a document (shortcut to transition to COMPLIANCE_OK).

    Requires: documents:approve permission (admin, compliance roles)
    """
    # Check permission
    check_permission(current_user, Permission.DOCUMENTS_APPROVE)

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Determine target status based on current status
    if document.status == DocumentStatus.UPLOADED:
        target_status = DocumentStatus.VALIDATED
    elif document.status == DocumentStatus.VALIDATED:
        target_status = DocumentStatus.COMPLIANCE_OK
    elif document.status == DocumentStatus.COMPLIANCE_OK:
        target_status = DocumentStatus.LINKED
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve document in {document.status.value} status"
        )

    result = transition_document(
        document=document,
        target_status=target_status,
        user=current_user.email,
        user_role=current_user.role.value,
        notes=request.notes
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.to_dict())

    # Notify the uploader that their document was approved
    if document.uploaded_by:
        notify_document_validated(
            db=db,
            document=document,
            validator=current_user.email,
            uploader=document.uploaded_by
        )

    db.commit()
    db.refresh(document)

    return {
        "message": f"Document approved - now {target_status.value}",
        "result": result.to_dict()
    }


@router.post("/{document_id}/reject")
async def reject_document(
    document_id: UUID,
    request: ApprovalRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Reject a document with notes explaining the rejection.

    Requires: documents:reject permission (admin, compliance roles)
    """
    # Check permission
    check_permission(current_user, Permission.DOCUMENTS_REJECT)

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not request.notes:
        raise HTTPException(
            status_code=400,
            detail="Rejection notes are required"
        )

    # Determine target status based on current status
    if document.status == DocumentStatus.UPLOADED:
        target_status = DocumentStatus.DRAFT
    elif document.status == DocumentStatus.VALIDATED:
        target_status = DocumentStatus.COMPLIANCE_FAILED
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject document in {document.status.value} status"
        )

    result = transition_document(
        document=document,
        target_status=target_status,
        user=current_user.email,
        user_role=current_user.role.value,
        notes=request.notes
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.to_dict())

    # Notify the uploader that their document was rejected
    if document.uploaded_by:
        notify_document_rejected(
            db=db,
            document=document,
            rejector=current_user.email,
            uploader=document.uploaded_by,
            reason=request.notes or "No reason provided"
        )

    db.commit()
    db.refresh(document)

    return {
        "message": f"Document rejected - now {target_status.value}",
        "result": result.to_dict()
    }


@router.patch("/{document_id}/metadata")
async def update_document_metadata(
    document_id: UUID,
    update: DocumentMetadataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update document metadata fields."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update provided fields
    if update.reference_number is not None:
        document.reference_number = update.reference_number
    if update.issue_date is not None:
        document.issue_date = update.issue_date
    if update.expiry_date is not None:
        document.expiry_date = update.expiry_date
    if update.issuing_authority is not None:
        document.issuing_authority = update.issuing_authority
    if update.extra_data is not None:
        # Merge with existing extra_data
        existing = document.extra_data or {}
        existing.update(update.extra_data)
        document.extra_data = existing

    document.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(document)

    return {
        "message": "Document metadata updated",
        "document_id": str(document.id),
        "updated_fields": update.dict(exclude_none=True)
    }


@router.get("/expiring")
async def get_expiring_documents(
    days: int = Query(default=30, ge=1, le=365, description="Days to look ahead"),
    shipment_id: Optional[UUID] = Query(default=None, description="Filter by shipment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents expiring within the specified timeframe."""
    query = db.query(Document).filter(Document.expiry_date.isnot(None))

    if shipment_id:
        query = query.filter(Document.shipment_id == shipment_id)

    documents = query.all()
    expiring = check_expiring_documents(documents, days_ahead=days)

    return {
        "days_ahead": days,
        "total_expiring": len(expiring),
        "documents": expiring
    }


@router.get("/types/{document_type}/requirements")
async def get_document_type_requirements(
    document_type: DocumentType,
    current_user: User = Depends(get_current_user)
):
    """Get validation requirements for a document type."""
    required_fields = get_required_fields(document_type)

    return {
        "document_type": document_type.value,
        "required_fields": required_fields
    }


@router.get("/workflow/summary")
async def get_shipment_workflow_summary(
    shipment_id: UUID = Query(..., description="Shipment ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow summary for all documents in a shipment."""
    # Verify shipment exists
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    documents = db.query(Document).filter(Document.shipment_id == shipment_id).all()
    summary = get_workflow_summary(documents)

    # Add expiring documents check
    expiring = check_expiring_documents(documents, days_ahead=30)

    return {
        "shipment_id": str(shipment_id),
        "workflow_summary": summary,
        "expiring_soon": len(expiring),
        "expiring_documents": expiring[:5]  # Top 5 most urgent
    }
