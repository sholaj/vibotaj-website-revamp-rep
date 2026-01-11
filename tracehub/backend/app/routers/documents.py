"""Documents router - document upload and management."""

import logging
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
from ..models import Document, DocumentType, DocumentStatus, DocumentContent, ReferenceRegistry, Shipment
from ..routers.auth import get_current_active_user
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
from ..services.pdf_processor import pdf_processor
from ..services.document_classifier import document_classifier
from ..services.shipment_enrichment import shipment_enrichment_service

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


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


class DetectedContent(BaseModel):
    """A detected document within a combined PDF."""
    document_type: str
    page_start: int
    page_end: int
    reference_number: Optional[str]
    confidence: float
    detection_method: str


class DetectionResult(BaseModel):
    """Result of auto-detection for a PDF."""
    is_combined: bool
    page_count: int
    detected_contents: List[DetectedContent]
    duplicates: List[dict]


class ConfirmDetectionRequest(BaseModel):
    """Request to confirm or correct auto-detected document types."""
    contents: List[dict]  # List of {document_type, page_start, page_end, reference_number}


@router.post("/upload")
async def upload_document(
    shipment_id: UUID = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    reference_number: Optional[str] = Form(None),
    auto_detect: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Upload a document for a shipment.

    Requires: documents:upload permission (admin, compliance, supplier roles)

    If auto_detect=true or the PDF has >3 pages, the system will analyze
    the PDF to detect multiple document types within it.
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

    # Check page count for PDFs
    page_count = 1
    is_pdf = file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf")
    if is_pdf and pdf_processor.is_available():
        page_count = pdf_processor.get_page_count(file_path)

    # Auto-detect if requested or PDF has multiple pages
    should_auto_detect = auto_detect or (is_pdf and page_count > 3)
    detected_contents = []
    duplicates_found = []

    if should_auto_detect and is_pdf and pdf_processor.is_available():
        # Analyze PDF for multiple document types
        sections = document_classifier.analyze_pdf(file_path, use_ai=True)

        for section in sections:
            detected_contents.append({
                "document_type": section.document_type.value if section.document_type else "other",
                "page_start": section.page_start,
                "page_end": section.page_end,
                "reference_number": section.reference_number,
                "confidence": section.confidence,
                "detection_method": section.detection_method,
                "detected_fields": section.detected_fields
            })

            # Check for duplicates
            if section.reference_number and section.document_type:
                existing = db.query(ReferenceRegistry).filter(
                    ReferenceRegistry.shipment_id == shipment_id,
                    ReferenceRegistry.reference_number == section.reference_number,
                    ReferenceRegistry.document_type == section.document_type
                ).first()

                if existing:
                    duplicates_found.append({
                        "reference_number": section.reference_number,
                        "document_type": section.document_type.value,
                        "existing_document_id": str(existing.document_id),
                        "first_seen_at": existing.first_seen_at.isoformat() if existing.first_seen_at else None
                    })

    # Determine if this is a combined document
    is_combined = len(detected_contents) > 1

    # If user selected "other" and AI detected a specific type with high confidence, use the AI result
    final_document_type = document_type
    if document_type == DocumentType.OTHER and detected_contents:
        # Find the highest confidence detection that's not "other"
        best_detection = None
        for dc in detected_contents:
            if dc["document_type"] != "other" and dc["confidence"] >= 0.7:
                if best_detection is None or dc["confidence"] > best_detection["confidence"]:
                    best_detection = dc

        if best_detection:
            try:
                final_document_type = DocumentType(best_detection["document_type"])
                logger.info(f"AI auto-classified document as {final_document_type.value} (confidence: {best_detection['confidence']:.2f})")
            except ValueError:
                pass  # Keep user's selection if AI type is invalid

    # Create document record
    document = Document(
        shipment_id=shipment_id,
        document_type=final_document_type,
        document_types=[dc["document_type"] for dc in detected_contents] if detected_contents else [final_document_type.value],
        name=file.filename,
        file_path=file_path,
        file_name=file.filename,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        status=DocumentStatus.UPLOADED,
        reference_number=reference_number,
        uploaded_by=current_user.email,
        uploaded_at=datetime.utcnow(),
        is_combined=is_combined,
        content_count=len(detected_contents) if detected_contents else 1,
        page_count=page_count
    )

    db.add(document)
    db.flush()  # Get document.id

    # Create DocumentContent records for detected sections
    if detected_contents:
        for dc in detected_contents:
            doc_type_enum = DocumentType(dc["document_type"]) if dc["document_type"] != "other" else DocumentType.OTHER
            content = DocumentContent(
                document_id=document.id,
                document_type=doc_type_enum,
                status=DocumentStatus.UPLOADED,
                page_start=dc["page_start"],
                page_end=dc["page_end"],
                reference_number=dc.get("reference_number"),
                confidence_score=dc["confidence"],
                detection_method=dc["detection_method"],
                detected_fields=dc.get("detected_fields", {})
            )
            db.add(content)
            db.flush()

            # Register reference numbers for duplicate detection (if not a duplicate)
            if dc.get("reference_number") and not any(
                d["reference_number"] == dc["reference_number"] for d in duplicates_found
            ):
                registry = ReferenceRegistry(
                    shipment_id=shipment_id,
                    reference_number=dc["reference_number"],
                    document_type=doc_type_enum,
                    document_content_id=content.id,
                    document_id=document.id,
                    first_seen_at=datetime.utcnow()
                )
                db.add(registry)

    # Notify compliance team/admins about new document
    notify_document_uploaded(
        db=db,
        document=document,
        uploader=current_user.email,
        notify_users=[settings.demo_username]
    )

    # Auto-enrich shipment with extracted data from document
    enrichment_result = None
    if is_pdf and pdf_processor.is_available():
        try:
            enrichment_result = shipment_enrichment_service.enrich_from_document(
                shipment=shipment,
                document=document,
                db=db,
                auto_create_products=True,
                overwrite_existing=False  # Don't overwrite existing data
            )
        except Exception as e:
            # Log but don't fail the upload
            import logging
            logging.getLogger(__name__).warning(f"Enrichment failed: {e}")

    db.commit()
    db.refresh(document)

    response = {
        "id": document.id,
        "name": document.name,
        "type": document.document_type,
        "status": document.status,
        "message": "Document uploaded successfully",
        "page_count": page_count,
        "is_combined": is_combined,
        "content_count": document.content_count
    }

    # Include detection results if auto-detect was used
    if should_auto_detect and detected_contents:
        response["detection"] = {
            "detected_contents": detected_contents,
            "duplicates_found": duplicates_found,
            "ai_available": document_classifier.is_ai_available(),
            "ai_reclassified": final_document_type != document_type,
            "original_type": document_type.value if final_document_type != document_type else None,
            "detected_type": final_document_type.value if final_document_type != document_type else None
        }

    # Include enrichment results if extraction was performed
    if enrichment_result:
        response["enrichment"] = {
            "success": enrichment_result.success,
            "updates_applied": enrichment_result.updates_applied,
            "products_created": enrichment_result.products_created,
            "warnings": enrichment_result.warnings,
            "extracted_data": enrichment_result.extracted_data
        }

    return response


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get document metadata."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Download document file."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file if exists
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted"}


@router.delete("/shipment/{shipment_id}/all")
async def delete_all_shipment_documents(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Delete all documents for a shipment.

    Requires: documents:delete permission (admin role)
    """
    check_permission(current_user, Permission.DOCUMENTS_DELETE)

    # Get all documents for this shipment
    documents = db.query(Document).filter(Document.shipment_id == shipment_id).all()

    if not documents:
        return {"message": "No documents found for this shipment", "deleted_count": 0}

    deleted_count = 0
    for document in documents:
        # Delete file if exists
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception as e:
                logger.warning(f"Failed to delete file {document.file_path}: {e}")

        db.delete(document)
        deleted_count += 1

    db.commit()
    logger.info(f"Deleted {deleted_count} documents for shipment {shipment_id}")

    return {"message": f"Deleted {deleted_count} documents", "deleted_count": deleted_count}


# ============ Validation & Workflow Endpoints ============

@router.get("/{document_id}/validation")
async def get_document_validation(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get validation status and required fields for a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Update document metadata fields."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
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
    current_user: CurrentUser = Depends(get_current_active_user)
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
    current_user: CurrentUser = Depends(get_current_active_user)
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
    current_user: CurrentUser = Depends(get_current_active_user)
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


# ============ Document Content Endpoints (Multi-Document PDFs) ============

@router.get("/{document_id}/contents")
async def get_document_contents(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get all document contents (detected document types) within a PDF.

    For combined PDFs, returns each detected document type with its
    page range, validation status, and reference number.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    contents = db.query(DocumentContent).filter(
        DocumentContent.document_id == document_id
    ).order_by(DocumentContent.page_start).all()

    return {
        "document_id": str(document_id),
        "file_name": document.file_name,
        "is_combined": document.is_combined,
        "page_count": document.page_count,
        "content_count": len(contents),
        "contents": [
            {
                "id": str(c.id),
                "document_type": c.document_type.value,
                "status": c.status.value,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "reference_number": c.reference_number,
                "confidence": c.confidence_score,
                "detection_method": c.detection_method,
                "validated_at": c.validated_at.isoformat() if c.validated_at else None,
                "validated_by": c.validated_by,
                "validation_notes": c.validation_notes,
                "detected_fields": c.detected_fields
            }
            for c in contents
        ]
    }


@router.post("/{document_id}/contents/{content_id}/validate")
async def validate_document_content(
    document_id: UUID,
    content_id: UUID,
    notes: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Validate a specific document content within a combined PDF.

    Requires: documents:validate permission (admin, compliance roles)
    """
    check_permission(current_user, Permission.DOCUMENTS_VALIDATE)

    content = db.query(DocumentContent).filter(
        DocumentContent.id == content_id,
        DocumentContent.document_id == document_id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="Document content not found")

    content.status = DocumentStatus.VALIDATED
    content.validated_at = datetime.utcnow()
    content.validated_by = current_user.email
    if notes:
        content.validation_notes = notes

    # Check if all contents are validated
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    all_contents = db.query(DocumentContent).filter(
        DocumentContent.document_id == document_id
    ).all()

    all_validated = all(c.status == DocumentStatus.VALIDATED for c in all_contents)
    if all_validated and document:
        document.status = DocumentStatus.VALIDATED
        document.validated_at = datetime.utcnow()
        document.validated_by = current_user.email

    db.commit()
    db.refresh(content)

    return {
        "message": f"Content validated: {content.document_type.value}",
        "content_id": str(content.id),
        "status": content.status.value,
        "all_contents_validated": all_validated
    }


@router.post("/{document_id}/contents/{content_id}/reject")
async def reject_document_content(
    document_id: UUID,
    content_id: UUID,
    request: ApprovalRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Reject a specific document content within a combined PDF.

    Requires: documents:reject permission (admin, compliance roles)
    """
    check_permission(current_user, Permission.DOCUMENTS_REJECT)

    if not request.notes:
        raise HTTPException(status_code=400, detail="Rejection notes are required")

    content = db.query(DocumentContent).filter(
        DocumentContent.id == content_id,
        DocumentContent.document_id == document_id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="Document content not found")

    content.status = DocumentStatus.COMPLIANCE_FAILED
    content.validation_notes = request.notes

    # If any content is rejected, the whole document is compliance_failed
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if document:
        document.status = DocumentStatus.COMPLIANCE_FAILED
        document.validation_notes = f"Content rejected: {content.document_type.value} - {request.notes}"

    db.commit()
    db.refresh(content)

    return {
        "message": f"Content rejected: {content.document_type.value}",
        "content_id": str(content.id),
        "status": content.status.value
    }


@router.post("/{document_id}/confirm-detection")
async def confirm_detection(
    document_id: UUID,
    request: ConfirmDetectionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Confirm or correct auto-detected document types.

    Allows users to correct misdetections before validation.
    """
    check_permission(current_user, Permission.DOCUMENTS_UPLOAD)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete existing contents
    db.query(DocumentContent).filter(DocumentContent.document_id == document_id).delete()

    # Create new contents based on user confirmation
    new_types = []
    for content_data in request.contents:
        doc_type = DocumentType(content_data["document_type"])
        content = DocumentContent(
            document_id=document_id,
            document_type=doc_type,
            status=DocumentStatus.UPLOADED,
            page_start=content_data["page_start"],
            page_end=content_data["page_end"],
            reference_number=content_data.get("reference_number"),
            confidence_score=1.0,  # User-confirmed = 100% confidence
            detection_method="manual"
        )
        db.add(content)
        new_types.append(doc_type.value)

    # Update document
    document.document_types = new_types
    document.is_combined = len(new_types) > 1
    document.content_count = len(new_types)

    db.commit()

    return {
        "message": "Detection confirmed",
        "document_id": str(document_id),
        "content_count": len(new_types),
        "document_types": new_types
    }


@router.get("/{document_id}/analyze")
async def analyze_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Re-analyze a document to detect document types.

    Useful for documents uploaded without auto-detection.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")

    is_pdf = document.mime_type == "application/pdf" or document.file_name.lower().endswith(".pdf")
    if not is_pdf:
        return {
            "message": "Only PDF documents can be analyzed",
            "document_id": str(document_id),
            "is_pdf": False
        }

    if not pdf_processor.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF processing is not available. Install PyMuPDF."
        )

    # Analyze the PDF
    sections = document_classifier.analyze_pdf(document.file_path, use_ai=True)

    return {
        "document_id": str(document_id),
        "file_name": document.file_name,
        "page_count": pdf_processor.get_page_count(document.file_path),
        "detected_sections": [
            {
                "document_type": s.document_type.value if s.document_type else "other",
                "page_start": s.page_start,
                "page_end": s.page_end,
                "reference_number": s.reference_number,
                "confidence": s.confidence,
                "detection_method": s.detection_method,
                "detected_fields": s.detected_fields
            }
            for s in sections
        ],
        "ai_available": document_classifier.is_ai_available()
    }


# ============ Duplicate Detection Endpoints ============

@router.get("/shipments/{shipment_id}/duplicates")
async def get_shipment_duplicates(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get all potential duplicate documents in a shipment.

    Returns reference numbers that appear in multiple documents.
    """
    # Multi-tenancy: verify shipment belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get all reference registries for this shipment
    registries = db.query(ReferenceRegistry).filter(
        ReferenceRegistry.shipment_id == shipment_id
    ).all()

    # Group by reference number
    ref_counts = {}
    for reg in registries:
        key = (reg.reference_number, reg.document_type.value)
        if key not in ref_counts:
            ref_counts[key] = []
        ref_counts[key].append({
            "document_id": str(reg.document_id),
            "content_id": str(reg.document_content_id) if reg.document_content_id else None,
            "first_seen_at": reg.first_seen_at.isoformat() if reg.first_seen_at else None
        })

    # Find duplicates (more than one occurrence)
    duplicates = [
        {
            "reference_number": key[0],
            "document_type": key[1],
            "occurrences": entries
        }
        for key, entries in ref_counts.items()
        if len(entries) > 1
    ]

    return {
        "shipment_id": str(shipment_id),
        "total_references": len(registries),
        "duplicate_count": len(duplicates),
        "duplicates": duplicates
    }


@router.get("/check-duplicate")
async def check_duplicate_reference(
    shipment_id: UUID = Query(..., description="Shipment ID"),
    reference_number: str = Query(..., description="Reference number to check"),
    document_type: DocumentType = Query(..., description="Document type"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Check if a reference number already exists for a shipment."""
    # Multi-tenancy: verify shipment belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    existing = db.query(ReferenceRegistry).filter(
        ReferenceRegistry.shipment_id == shipment_id,
        ReferenceRegistry.reference_number == reference_number,
        ReferenceRegistry.document_type == document_type
    ).first()

    if existing:
        return {
            "is_duplicate": True,
            "reference_number": reference_number,
            "document_type": document_type.value,
            "existing_document_id": str(existing.document_id),
            "first_seen_at": existing.first_seen_at.isoformat() if existing.first_seen_at else None
        }

    return {
        "is_duplicate": False,
        "reference_number": reference_number,
        "document_type": document_type.value
    }


# ============ AI Status Endpoint ============

@router.get("/ai/status")
async def get_ai_status(
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get AI document classification availability status.

    Returns detailed information about AI availability:
    - Whether AI classification is active
    - Fallback status (keyword-based classification always available)
    - Error messages if AI is unavailable
    """
    status = document_classifier.get_ai_status()

    return {
        "ai_classification": {
            "available": status["available"],
            "status": status["status"],
            "error": status["last_error"]
        },
        "fallback_classification": {
            "available": True,
            "type": "keyword",
            "active": status["fallback_active"],
            "description": "Keyword-based document detection is always available"
        },
        "pdf_processing": {
            "available": pdf_processor.is_available(),
            "library": "PyMuPDF"
        },
        "message": (
            "AI classification is active" if status["available"]
            else f"Using keyword-based fallback: {status['last_error'] or 'AI unavailable'}"
        )
    }


@router.post("/ai/test")
async def test_ai_classification(
    text: str = Body(..., embed=True, description="Sample text to classify"),
    prefer_ai: bool = Body(True, embed=True, description="Try AI first (if available)"),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Test document classification with sample text.

    Useful for verifying AI/keyword classification is working correctly.
    """
    result = document_classifier.classify(text, prefer_ai=prefer_ai)

    return {
        "classification": {
            "document_type": result.document_type.value,
            "confidence": result.confidence,
            "reference_number": result.reference_number,
            "reasoning": result.reasoning
        },
        "detection_method": result.detected_fields.get("detection_method", "unknown"),
        "ai_status": document_classifier.get_ai_status(),
        "detected_fields": result.detected_fields
    }


# ============ Document Intelligence / Extraction Endpoints ============

@router.post("/{document_id}/extract")
async def extract_shipment_data(
    document_id: UUID,
    auto_create_products: bool = Query(True, description="Auto-create products from HS codes"),
    overwrite_existing: bool = Query(False, description="Overwrite existing shipment data"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Extract shipment data from a document and update the shipment.

    This endpoint extracts data like:
    - Port of discharge (destination) from Bill of Lading
    - HS codes and product info from Commercial Invoice
    - Container numbers, vessel names, etc.

    The extracted data is used to:
    - Update shipment fields (ports, vessel, B/L number)
    - Auto-create product records from HS codes

    Requires: documents:upload permission
    """
    check_permission(current_user, Permission.DOCUMENTS_UPLOAD)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")

    shipment = db.query(Shipment).filter(Shipment.id == document.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    if not pdf_processor.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF processing is not available. Install PyMuPDF."
        )

    # Run extraction and enrichment
    result = shipment_enrichment_service.enrich_from_document(
        shipment=shipment,
        document=document,
        db=db,
        auto_create_products=auto_create_products,
        overwrite_existing=overwrite_existing
    )

    if result.updates_applied or result.products_created:
        db.commit()
        db.refresh(shipment)

    return {
        "document_id": str(document_id),
        "shipment_id": str(shipment.id),
        "shipment_reference": shipment.reference,
        "extraction_result": result.to_dict(),
        "updated_shipment": {
            "pod_code": shipment.pod_code,
            "pod_name": shipment.pod_name,
            "pol_code": shipment.pol_code,
            "pol_name": shipment.pol_name,
            "vessel_name": shipment.vessel_name,
            "voyage_number": shipment.voyage_number,
            "bl_number": shipment.bl_number,
            "product_count": len(shipment.products)
        }
    }


@router.get("/{document_id}/preview-extraction")
async def preview_extraction(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Preview what data would be extracted from a document.

    This endpoint shows what data can be extracted without actually
    updating the shipment. Useful for reviewing before applying changes.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")

    if not pdf_processor.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF processing is not available. Install PyMuPDF."
        )

    # Import extractor
    from ..services.shipment_data_extractor import shipment_data_extractor

    # Extract data without applying
    extracted = shipment_data_extractor.extract_from_document(
        document.file_path,
        document.document_type
    )

    # Get current shipment data for comparison
    shipment = db.query(Shipment).filter(Shipment.id == document.shipment_id).first()

    return {
        "document_id": str(document_id),
        "document_type": document.document_type.value,
        "extraction_confidence": extracted.confidence,
        "extraction_method": extracted.extraction_method,
        "extracted_data": {
            "port_of_loading": {
                "code": extracted.port_of_loading_code,
                "name": extracted.port_of_loading_name
            },
            "port_of_discharge": {
                "code": extracted.port_of_discharge_code,
                "name": extracted.port_of_discharge_name
            },
            "final_destination": extracted.final_destination,
            "container_number": extracted.container_number,
            "bl_number": extracted.bl_number,
            "vessel_name": extracted.vessel_name,
            "voyage_number": extracted.voyage_number,
            "hs_codes": extracted.hs_codes,
            "products": extracted.product_descriptions,
            "net_weight_kg": extracted.total_net_weight_kg,
            "gross_weight_kg": extracted.total_gross_weight_kg
        },
        "current_shipment": {
            "pod_code": shipment.pod_code if shipment else None,
            "pod_name": shipment.pod_name if shipment else None,
            "pol_code": shipment.pol_code if shipment else None,
            "pol_name": shipment.pol_name if shipment else None,
            "vessel_name": shipment.vessel_name if shipment else None,
            "voyage_number": shipment.voyage_number if shipment else None,
            "bl_number": shipment.bl_number if shipment else None,
            "product_count": len(shipment.products) if shipment else 0,
            "existing_hs_codes": [p.hs_code for p in shipment.products] if shipment else []
        },
        "raw_fields": extracted.raw_fields
    }
