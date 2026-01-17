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
from ..services.compliance import validate_document_content as validate_compliance
from ..services.shipment_data_extractor import ShipmentDataExtractor
from ..services.bol_parser import bol_parser
from ..services.bol_rules import (
    RulesEngine,
    STANDARD_BOL_RULES,
    get_compliance_decision,
)
from ..services.bol_shipment_sync import bol_shipment_sync
from ..services.entity_factory import create_document
from ..models import ComplianceResult

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
    document_date: Optional[date] = None  # TICKET-002: Renamed from issue_date
    expiry_date: Optional[date] = None
    issuer: Optional[str] = None  # TICKET-002: Renamed from issuing_authority
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

    # Verify shipment exists and belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
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
        # Wrap in try-except to prevent auto-detect failures from breaking upload
        try:
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
        except Exception as e:
            # Log but don't fail upload if auto-detect fails
            logger.warning(f"Auto-detection failed for {file.filename}: {e}")
            # Reset detected contents to empty - upload will proceed without auto-detect results
            detected_contents = []
            duplicates_found = []

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

    # Create document record using factory (ensures organization_id is always set)
    document = create_document(
        shipment=shipment,
        document_type=final_document_type,
        name=file.filename,
        file_path=file_path,
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        status=DocumentStatus.UPLOADED,
        reference_number=reference_number,
        uploaded_by=current_user.id
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
                # Check if reference already exists (to avoid IntegrityError on commit)
                existing_registry = db.query(ReferenceRegistry).filter(
                    ReferenceRegistry.shipment_id == shipment_id,
                    ReferenceRegistry.reference_number == dc["reference_number"],
                    ReferenceRegistry.document_type == doc_type_enum
                ).first()

                if not existing_registry:
                    registry = ReferenceRegistry(
                        shipment_id=shipment_id,
                        reference_number=dc["reference_number"],
                        document_type=doc_type_enum,
                        document_content_id=content.id,
                        document_id=document.id,
                        first_seen_at=datetime.utcnow()
                    )
                    db.add(registry)
                else:
                    logger.info(
                        f"Reference {dc['reference_number']} already registered for shipment "
                        f"{shipment_id}, document type {doc_type_enum.value} - skipping duplicate registry"
                    )

    # Notify compliance team/admins about new document
    # Note: notify_users expects user UUIDs, not emails
    try:
        # Get admins in the organization to notify
        from ..models import User, UserRole
        admins = db.query(User).filter(
            User.organization_id == current_user.organization_id,
            User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]),
            User.is_active == True,
            User.id != current_user.id  # Don't notify uploader
        ).all()
        admin_ids = [str(admin.id) for admin in admins]

        if admin_ids:
            notify_document_uploaded(
                db=db,
                document=document,
                uploader=current_user.email,
                notify_users=admin_ids
            )
    except Exception as e:
        # Don't fail upload if notification fails
        logger.warning(f"Failed to send document upload notification: {e}")

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

    # Extract container number from Bill of Lading documents
    # Store on document for later suggestion to user
    extracted_container = None
    if final_document_type == DocumentType.BILL_OF_LADING and is_pdf and pdf_processor.is_available():
        try:
            extractor = ShipmentDataExtractor()
            # Extract text from the PDF
            pages = pdf_processor.extract_text(file_path)
            if pages:
                full_text = "\n".join(page.text for page in pages)
                result = extractor.extract_container_with_confidence(full_text)
                if result:
                    container_number, confidence = result
                    extracted_container = {
                        "container_number": container_number,
                        "confidence": confidence
                    }
                    # Store extraction metadata in document extra_data for later use
                    document.extra_data = document.extra_data or {}
                    document.extra_data["extracted_container"] = {
                        "container_number": container_number,
                        "confidence": confidence,
                        "extraction_method": "keyword"
                    }
                    logger.info(
                        f"Extracted container {container_number} from BOL "
                        f"(confidence: {confidence:.2f}) for shipment {shipment.reference}"
                    )
        except Exception as e:
            # Log but don't fail the upload
            logger.warning(f"Container extraction failed: {e}")

    db.commit()
    db.refresh(document)

    # Calculate content_count from detected_contents
    content_count = len(detected_contents) if detected_contents else 1

    response = {
        "id": str(document.id),
        "name": document.name,
        "type": document.document_type.value,
        "status": document.status.value,
        "message": "Document uploaded successfully",
        "page_count": page_count,
        "is_combined": is_combined,
        "content_count": content_count
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

    # Include extracted container from BOL (for suggesting container update)
    if extracted_container:
        response["extracted_container"] = extracted_container

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

    Sprint 14: Now includes compliance validation for Horn & Hoof documents.
    - EU TRACES must reference RC1479592
    - Veterinary Health Certificate must be from Nigerian authority
    - Certificate of Origin must specify Nigeria

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

    # Get shipment for compliance context
    shipment = db.query(Shipment).filter(
        Shipment.id == document.shipment_id
    ).first() if document.shipment_id else None

    # Sprint 14: Run compliance validation
    compliance_result = validate_compliance(document, shipment)

    # If validation fails (errors), reject the validation
    if not compliance_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Document validation failed - compliance errors",
                "errors": compliance_result.errors,
                "warnings": compliance_result.warnings
            }
        )

    document.status = DocumentStatus.VALIDATED
    document.validated_at = datetime.utcnow()
    document.validated_by = current_user.id
    if notes:
        document.validation_notes = notes

    db.commit()
    db.refresh(document)

    # Include warnings in response even if validation passed
    response = {
        "message": "Document validated",
        "status": document.status.value if hasattr(document.status, 'value') else str(document.status)
    }
    if compliance_result.warnings:
        response["compliance_warnings"] = compliance_result.warnings

    return response


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
        user_id=current_user.id,
        user_email=current_user.email,
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
        user_id=current_user.id,
        user_email=current_user.email,
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
        user_id=current_user.id,
        user_email=current_user.email,
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
    if update.document_date is not None:
        document.document_date = update.document_date
    if update.expiry_date is not None:
        document.expiry_date = update.expiry_date
    if update.issuer is not None:
        document.issuer = update.issuer
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
    query = db.query(Document).filter(
        Document.expiry_date.isnot(None),
        Document.organization_id == current_user.organization_id
    )

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
    # Verify shipment exists and belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
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
    content.validated_by = current_user.id
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
        document.validated_by = current_user.id

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

    # Verify shipment belongs to user's organization (defense in depth)
    shipment = db.query(Shipment).filter(
        Shipment.id == document.shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
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

    # Get current shipment data for comparison (verify org ownership)
    shipment = db.query(Shipment).filter(
        Shipment.id == document.shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()

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


# ============ Bill of Lading Compliance Endpoints ============

class BolComplianceResponse(BaseModel):
    """Response for BoL compliance check."""
    document_id: str
    compliance_status: str  # APPROVE, HOLD, REJECT
    parsed_bol: Optional[dict] = None
    results: List[dict]
    summary: dict


@router.post("/{document_id}/bol/parse")
async def parse_bol_document(
    document_id: UUID,
    auto_sync_shipment: bool = Query(False, description="Auto-sync shipment data from parsed BoL"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Parse a Bill of Lading document and extract structured data.

    This endpoint extracts data from a BoL PDF and stores the parsed
    data in the document record. The BoL becomes the SOURCE OF TRUTH
    for shipment details.

    Args:
        document_id: Document UUID
        auto_sync_shipment: If True, automatically update shipment with BoL data

    Returns:
        Parsed BoL data with confidence score
    """
    check_permission(current_user, Permission.DOCUMENTS_UPLOAD)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify it's a Bill of Lading
    if document.document_type != DocumentType.BILL_OF_LADING:
        raise HTTPException(
            status_code=400,
            detail=f"Document is not a Bill of Lading (type: {document.document_type.value})"
        )

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")

    if not pdf_processor.is_available():
        raise HTTPException(
            status_code=503,
            detail="PDF processing is not available. Install PyMuPDF."
        )

    # Extract text from PDF
    pages = pdf_processor.extract_text(document.file_path)
    if not pages:
        # Check OCR status to provide better error message
        ocr_status = pdf_processor.get_ocr_status()
        if ocr_status.get("available"):
            detail = "Could not extract text from PDF even with OCR. The PDF may be corrupted or in an unsupported format."
        else:
            detail = (
                "Could not extract text from PDF. The document appears to be scanned/image-based. "
                "OCR is not available on this server. Please upload a text-based PDF or contact support."
            )
        raise HTTPException(status_code=400, detail=detail)

    # Check if we got meaningful text
    total_chars = sum(len(page.text) for page in pages)
    if total_chars < 50:
        ocr_status = pdf_processor.get_ocr_status()
        if not ocr_status.get("available"):
            raise HTTPException(
                status_code=400,
                detail=f"PDF has minimal extractable text ({total_chars} chars). The document may be scanned. OCR is not available."
            )

    full_text = "\n".join(page.text for page in pages)

    # Parse the BoL
    parsed_bol = bol_parser.parse(full_text)

    # Store parsed data in document
    document.bol_parsed_data = parsed_bol.model_dump(mode="json")
    document.updated_at = datetime.utcnow()

    # Update document metadata fields from parsed BoL for validation
    if parsed_bol.bol_number and parsed_bol.bol_number != "UNKNOWN":
        document.reference_number = parsed_bol.bol_number
    if parsed_bol.date_of_issue:
        document.issue_date = parsed_bol.date_of_issue
    # Use vessel name as shipping line/carrier (common on Maersk BOLs)
    if parsed_bol.vessel_name:
        document.issuing_authority = parsed_bol.vessel_name
    elif parsed_bol.shipper and parsed_bol.shipper.name:
        # Fallback to shipper name if no vessel
        document.issuing_authority = parsed_bol.shipper.name

    logger.info(
        f"BoL parsed - updating document fields: "
        f"reference_number={document.reference_number}, "
        f"issue_date={document.issue_date}, "
        f"issuing_authority={document.issuing_authority}"
    )

    # Auto-sync shipment data if requested
    sync_changes = None
    if auto_sync_shipment:
        shipment = db.query(Shipment).filter(
            Shipment.id == document.shipment_id,
            Shipment.organization_id == current_user.organization_id
        ).first()
        if shipment:
            sync_changes = bol_shipment_sync.apply_sync_changes(shipment, parsed_bol)
            logger.info(f"BoL sync applied to shipment {shipment.reference}: {sync_changes}")

    db.commit()
    db.refresh(document)

    response = {
        "document_id": str(document_id),
        "parsed_bol": parsed_bol.model_dump(mode="json"),
        "confidence_score": parsed_bol.confidence_score,
        "is_complete": parsed_bol.is_complete(),
        "message": "Bill of Lading parsed successfully"
    }

    if sync_changes:
        response["shipment_sync"] = {
            "applied": True,
            "changes": sync_changes
        }

    return response


@router.post("/{document_id}/bol/check-compliance")
async def check_bol_compliance(
    document_id: UUID,
    store_results: bool = Query(True, description="Store results in database"),
    auto_sync_shipment: bool = Query(False, description="Auto-sync shipment data from parsed BoL"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Run compliance checks on a Bill of Lading document.

    This endpoint:
    1. Parses the BoL document (if not already parsed)
    2. Runs all compliance rules against the parsed data
    3. Returns compliance decision (APPROVE, HOLD, REJECT)
    4. Optionally stores results in database

    Compliance Decisions:
    - APPROVE: All rules passed (or only INFO failures)
    - HOLD: WARNING severity failures (requires manual review)
    - REJECT: ERROR severity failures (critical issues)

    Args:
        document_id: Document UUID
        store_results: If True, store compliance results in database
        auto_sync_shipment: If True, automatically update shipment with BoL data
    """
    check_permission(current_user, Permission.DOCUMENTS_VALIDATE)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.document_type != DocumentType.BILL_OF_LADING:
        raise HTTPException(
            status_code=400,
            detail=f"Document is not a Bill of Lading (type: {document.document_type.value})"
        )

    # Get or parse BoL data
    parsed_data = document.bol_parsed_data
    if not parsed_data:
        # Parse the document first
        if not document.file_path or not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Document file not found")

        if not pdf_processor.is_available():
            raise HTTPException(
                status_code=503,
                detail="PDF processing is not available. Install PyMuPDF."
            )

        pages = pdf_processor.extract_text(document.file_path)
        if not pages:
            # Check OCR status to provide better error message
            ocr_status = pdf_processor.get_ocr_status()
            if ocr_status.get("available"):
                detail = "Could not extract text from PDF even with OCR. The PDF may be corrupted or in an unsupported format."
            else:
                detail = (
                    "Could not extract text from PDF. The document appears to be scanned/image-based. "
                    "OCR is not available on this server. Please upload a text-based PDF or contact support."
                )
            raise HTTPException(status_code=400, detail=detail)

        # Check if we got meaningful text
        total_chars = sum(len(page.text) for page in pages)
        if total_chars < 50:
            ocr_status = pdf_processor.get_ocr_status()
            if not ocr_status.get("available"):
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF has minimal extractable text ({total_chars} chars). The document may be scanned. OCR is not available."
                )

        full_text = "\n".join(page.text for page in pages)
        parsed_bol = bol_parser.parse(full_text)
        document.bol_parsed_data = parsed_bol.model_dump(mode="json")
        parsed_data = document.bol_parsed_data
    else:
        # Reconstruct BoL from stored data
        from ..schemas.bol import CanonicalBoL
        parsed_bol = CanonicalBoL.model_validate(parsed_data)

    # Run compliance rules
    engine = RulesEngine(STANDARD_BOL_RULES)
    results = engine.evaluate(parsed_bol)
    compliance_decision = get_compliance_decision(results)

    # Update document compliance status
    document.compliance_status = compliance_decision
    document.compliance_checked_at = datetime.utcnow()

    # Synchronize workflow status with compliance result
    # This ensures document.status reflects the compliance outcome
    if compliance_decision == "APPROVE":
        document.status = DocumentStatus.COMPLIANCE_OK
    elif compliance_decision == "REJECT":
        document.status = DocumentStatus.COMPLIANCE_FAILED
    # Note: HOLD keeps current status - document can still be processed

    # Store individual rule results if requested
    if store_results:
        # Clear existing results for this document
        db.query(ComplianceResult).filter(
            ComplianceResult.document_id == document_id
        ).delete()

        # Store new results
        for result in results:
            compliance_result = ComplianceResult(
                document_id=document_id,
                organization_id=current_user.organization_id,
                rule_id=result.rule_id,
                rule_name=result.rule_name,
                passed=result.passed,
                message=result.message,
                severity=result.severity,
                checked_at=datetime.utcnow()
            )
            db.add(compliance_result)

    # Auto-sync shipment data if requested and compliance passed
    sync_changes = None
    if auto_sync_shipment and compliance_decision != "REJECT":
        shipment = db.query(Shipment).filter(
            Shipment.id == document.shipment_id,
            Shipment.organization_id == current_user.organization_id
        ).first()
        if shipment:
            sync_changes = bol_shipment_sync.apply_sync_changes(shipment, parsed_bol)
            logger.info(f"BoL sync applied to shipment {shipment.reference}: {sync_changes}")

    db.commit()
    db.refresh(document)

    # Build response
    error_count = sum(1 for r in results if not r.passed and r.severity == "ERROR")
    warning_count = sum(1 for r in results if not r.passed and r.severity == "WARNING")
    info_count = sum(1 for r in results if not r.passed and r.severity == "INFO")
    passed_count = sum(1 for r in results if r.passed)

    response = {
        "document_id": str(document_id),
        "compliance_status": compliance_decision,
        "checked_at": document.compliance_checked_at.isoformat(),
        "results": [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "passed": r.passed,
                "message": r.message,
                "severity": r.severity
            }
            for r in results
        ],
        "summary": {
            "total_rules": len(results),
            "passed": passed_count,
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count
        },
        "parsed_bol": {
            "bol_number": parsed_bol.bol_number,
            "shipper": parsed_bol.shipper.name if parsed_bol.shipper else None,
            "consignee": parsed_bol.consignee.name if parsed_bol.consignee else None,
            "container_count": len(parsed_bol.containers),
            "confidence_score": parsed_bol.confidence_score
        }
    }

    if sync_changes:
        response["shipment_sync"] = {
            "applied": True,
            "changes": sync_changes
        }

    return response


@router.get("/{document_id}/bol/compliance-results")
async def get_bol_compliance_results(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get stored compliance results for a Bill of Lading document.

    Returns the most recent compliance check results stored in the database.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.document_type != DocumentType.BILL_OF_LADING:
        raise HTTPException(
            status_code=400,
            detail=f"Document is not a Bill of Lading (type: {document.document_type.value})"
        )

    # Get stored compliance results
    results = db.query(ComplianceResult).filter(
        ComplianceResult.document_id == document_id,
        ComplianceResult.organization_id == current_user.organization_id
    ).order_by(ComplianceResult.checked_at.desc()).all()

    if not results:
        return {
            "document_id": str(document_id),
            "compliance_status": document.compliance_status,
            "checked_at": document.compliance_checked_at.isoformat() if document.compliance_checked_at else None,
            "results": [],
            "message": "No compliance results found. Run /bol/check-compliance first."
        }

    # Calculate summary
    error_count = sum(1 for r in results if not r.passed and r.severity == "ERROR")
    warning_count = sum(1 for r in results if not r.passed and r.severity == "WARNING")
    info_count = sum(1 for r in results if not r.passed and r.severity == "INFO")
    passed_count = sum(1 for r in results if r.passed)

    return {
        "document_id": str(document_id),
        "compliance_status": document.compliance_status,
        "checked_at": document.compliance_checked_at.isoformat() if document.compliance_checked_at else None,
        "results": [
            {
                "id": str(r.id),
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "passed": r.passed,
                "message": r.message,
                "severity": r.severity,
                "checked_at": r.checked_at.isoformat() if r.checked_at else None
            }
            for r in results
        ],
        "summary": {
            "total_rules": len(results),
            "passed": passed_count,
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count
        },
        "parsed_bol": document.bol_parsed_data
    }


@router.get("/{document_id}/bol/sync-preview")
async def preview_bol_sync(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Preview what changes would be made to the shipment from BoL data.

    This endpoint shows what fields would be updated if the BoL data
    is synced to the shipment, without actually making the changes.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.document_type != DocumentType.BILL_OF_LADING:
        raise HTTPException(
            status_code=400,
            detail=f"Document is not a Bill of Lading (type: {document.document_type.value})"
        )

    if not document.bol_parsed_data:
        raise HTTPException(
            status_code=400,
            detail="BoL not parsed yet. Call /bol/parse first."
        )

    # Verify shipment belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.id == document.shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Reconstruct BoL from stored data
    from ..schemas.bol import CanonicalBoL
    parsed_bol = CanonicalBoL.model_validate(document.bol_parsed_data)

    # Get preview of changes (without applying)
    changes = bol_shipment_sync.get_sync_changes(shipment, parsed_bol)

    return {
        "document_id": str(document_id),
        "shipment_id": str(shipment.id),
        "shipment_reference": shipment.reference,
        "changes_to_apply": changes,
        "change_count": len(changes),
        "current_values": {
            "bl_number": shipment.bl_number,
            "container_number": shipment.container_number,
            "vessel_name": shipment.vessel_name,
            "voyage_number": shipment.voyage_number,
            "pol_code": shipment.pol_code,
            "pod_code": shipment.pod_code,
            "atd": shipment.atd.isoformat() if shipment.atd else None
        },
        "bol_values": {
            "bol_number": parsed_bol.bol_number,
            "container_number": parsed_bol.get_primary_container(),
            "vessel_name": parsed_bol.vessel_name,
            "voyage_number": parsed_bol.voyage_number,
            "port_of_loading": parsed_bol.port_of_loading,
            "port_of_discharge": parsed_bol.port_of_discharge,
            "shipped_on_board_date": parsed_bol.shipped_on_board_date.isoformat() if parsed_bol.shipped_on_board_date else None
        }
    }


@router.post("/{document_id}/bol/sync")
async def sync_bol_to_shipment(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Sync BoL data to the shipment.

    This endpoint applies the parsed BoL data to update the shipment record.
    Use /bol/sync-preview first to see what changes will be made.

    Requires: documents:upload permission
    """
    check_permission(current_user, Permission.DOCUMENTS_UPLOAD)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.document_type != DocumentType.BILL_OF_LADING:
        raise HTTPException(
            status_code=400,
            detail=f"Document is not a Bill of Lading (type: {document.document_type.value})"
        )

    if not document.bol_parsed_data:
        raise HTTPException(
            status_code=400,
            detail="BoL not parsed yet. Call /bol/parse first."
        )

    # Verify shipment belongs to user's organization
    shipment = db.query(Shipment).filter(
        Shipment.id == document.shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Reconstruct BoL from stored data
    from ..schemas.bol import CanonicalBoL
    parsed_bol = CanonicalBoL.model_validate(document.bol_parsed_data)

    # Apply changes
    changes = bol_shipment_sync.apply_sync_changes(shipment, parsed_bol)

    if changes:
        db.commit()
        db.refresh(shipment)
        logger.info(f"BoL sync applied to shipment {shipment.reference}: {changes}")

    return {
        "document_id": str(document_id),
        "shipment_id": str(shipment.id),
        "shipment_reference": shipment.reference,
        "sync_applied": bool(changes),
        "changes": changes,
        "updated_shipment": {
            "bl_number": shipment.bl_number,
            "container_number": shipment.container_number,
            "vessel_name": shipment.vessel_name,
            "voyage_number": shipment.voyage_number,
            "pol_code": shipment.pol_code,
            "pod_code": shipment.pod_code,
            "atd": shipment.atd.isoformat() if shipment.atd else None
        }
    }
