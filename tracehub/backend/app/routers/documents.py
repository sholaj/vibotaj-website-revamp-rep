"""Documents router - document upload and management."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime
import os
import shutil

from ..database import get_db
from ..config import get_settings
from ..models import Document, DocumentType, DocumentStatus, Shipment
from ..routers.auth import get_current_user, User

router = APIRouter()
settings = get_settings()


@router.post("/upload")
async def upload_document(
    shipment_id: UUID = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    reference_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document for a shipment."""
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
        uploaded_by=current_user.username,
        uploaded_at=datetime.utcnow()
    )

    db.add(document)
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
    current_user: User = Depends(get_current_user)
):
    """Mark document as validated."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = DocumentStatus.VALIDATED
    document.validated_at = datetime.utcnow()
    document.validated_by = current_user.username
    if notes:
        document.validation_notes = notes

    db.commit()
    db.refresh(document)

    return {"message": "Document validated", "status": document.status}


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file if exists
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted"}
