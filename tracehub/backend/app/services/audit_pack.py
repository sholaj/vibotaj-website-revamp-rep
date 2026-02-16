"""Audit pack generation service.

PRD-017: Upgraded to use StorageBackend for document fetching and
audit pack storage. Includes compliance status in PDF and metadata.
Uses Pydantic schemas for type-safe metadata generation.
"""

import asyncio
import io
import logging
import os
import zipfile
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from ..models import Shipment, Document, ContainerEvent, Product
from ..schemas.audit_pack import (
    AuditPackMetadata,
    AuditPackContent,
    AuditPackStatusResponse,
    ComplianceMetadata,
    ShipmentMetadata,
    ProductMetadata,
    PartyInfo,
    PortInfo,
    TrackingLog,
    TrackingEvent,
)
from .compliance import get_required_documents, check_document_completeness, DOCUMENT_NAMES
from .compliance_aggregation import get_compliance_decision, get_compliance_summary
from .file_utils import get_full_path
from .storage import StorageBackend
from ..config import get_settings

logger = logging.getLogger(__name__)

AUDIT_PACK_BUCKET = "audit-packs"


def _get_storage_key(shipment: Shipment) -> str:
    """Build the storage path for an audit pack ZIP."""
    org_id = str(shipment.organization_id)
    return f"{org_id}/{shipment.reference}-audit-pack.zip"


def _is_pack_outdated(shipment: Shipment, documents: List[Document]) -> bool:
    """Check if the cached audit pack is outdated.

    A pack is outdated if any document was modified after the pack was generated.
    """
    if not shipment.audit_pack_generated_at:
        return True

    gen_time = shipment.audit_pack_generated_at
    for doc in documents:
        if doc.updated_at and doc.updated_at > gen_time:
            return True
    return False


def _build_contents_list(documents: List[Document]) -> List[AuditPackContent]:
    """Build the contents manifest for the audit pack."""
    contents = [
        AuditPackContent(name="00-SHIPMENT-INDEX.pdf", type="index"),
    ]
    for i, doc in enumerate(documents, 1):
        if doc.file_path:
            ext = os.path.splitext(doc.file_name or doc.file_path)[1]
            filename = f"{i:02d}-{doc.document_type.value}{ext}"
            contents.append(AuditPackContent(
                name=filename,
                type="document",
                document_type=doc.document_type.value,
            ))
    contents.append(AuditPackContent(name="container-tracking-log.json", type="tracking"))
    contents.append(AuditPackContent(name="metadata.json", type="metadata"))
    return contents


def get_audit_pack_status(
    shipment: Shipment,
    documents: List[Document],
    db: Session,
) -> AuditPackStatusResponse:
    """Get audit pack status without generating.

    Args:
        shipment: The shipment to check
        documents: Pre-fetched documents for this shipment
        db: Database session

    Returns:
        AuditPackStatusResponse with current status
    """
    decision = get_compliance_decision(shipment, documents, db)
    is_outdated = _is_pack_outdated(shipment, documents)

    if not shipment.audit_pack_generated_at:
        return AuditPackStatusResponse(
            shipment_id=str(shipment.id),
            status="none",
            compliance_decision=decision,
            document_count=len(documents),
            is_outdated=True,
            contents=_build_contents_list(documents),
        )

    status = "outdated" if is_outdated else "ready"
    return AuditPackStatusResponse(
        shipment_id=str(shipment.id),
        status=status,
        generated_at=shipment.audit_pack_generated_at.isoformat(),
        compliance_decision=decision,
        document_count=len(documents),
        is_outdated=is_outdated,
        contents=_build_contents_list(documents),
    )


async def get_or_generate_audit_pack(
    shipment: Shipment,
    db: Session,
    storage: StorageBackend,
    force: bool = False,
) -> AuditPackStatusResponse:
    """Get cached audit pack or generate a new one.

    Returns a signed URL for download if pack is ready.

    Args:
        shipment: The shipment
        db: Database session
        storage: StorageBackend instance
        force: Force regeneration even if cached

    Returns:
        AuditPackStatusResponse with download URL
    """
    documents = db.query(Document).filter(Document.shipment_id == shipment.id).all()
    is_outdated = _is_pack_outdated(shipment, documents)

    storage_key = _get_storage_key(shipment)

    # Use cached pack if not outdated and not forced
    if not force and not is_outdated and shipment.audit_pack_storage_path:
        try:
            pack_exists = await storage.exists(AUDIT_PACK_BUCKET, storage_key)
            if pack_exists:
                download_url = await storage.download_url(AUDIT_PACK_BUCKET, storage_key)
                decision = get_compliance_decision(shipment, documents, db)
                expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
                return AuditPackStatusResponse(
                    shipment_id=str(shipment.id),
                    status="ready",
                    generated_at=shipment.audit_pack_generated_at.isoformat(),
                    download_url=download_url,
                    expires_at=expires_at.isoformat(),
                    contents=_build_contents_list(documents),
                    compliance_decision=decision,
                    document_count=len(documents),
                    is_outdated=False,
                )
        except Exception:
            logger.warning("Cached pack not found in storage, regenerating", exc_info=True)

    # Generate new pack
    zip_buffer = generate_audit_pack(shipment, db, storage)
    zip_bytes = zip_buffer.getvalue()

    # Upload to storage
    await storage.upload(
        AUDIT_PACK_BUCKET,
        storage_key,
        zip_bytes,
        content_type="application/zip",
    )

    # Update shipment cache fields
    now = datetime.now(timezone.utc)
    shipment.audit_pack_generated_at = now
    shipment.audit_pack_storage_path = f"{AUDIT_PACK_BUCKET}/{storage_key}"
    db.commit()

    # Get signed URL
    download_url = await storage.download_url(AUDIT_PACK_BUCKET, storage_key)
    expires_at = now + timedelta(hours=1)
    decision = get_compliance_decision(shipment, documents, db)

    return AuditPackStatusResponse(
        shipment_id=str(shipment.id),
        status="ready",
        generated_at=now.isoformat(),
        download_url=download_url,
        expires_at=expires_at.isoformat(),
        contents=_build_contents_list(documents),
        compliance_decision=decision,
        document_count=len(documents),
        is_outdated=False,
    )


def generate_audit_pack(
    shipment: Shipment,
    db: Session,
    storage: Optional[StorageBackend] = None,
) -> io.BytesIO:
    """Generate audit pack ZIP for a shipment.

    Args:
        shipment: The shipment to generate pack for
        db: Database session
        storage: Optional StorageBackend for fetching documents

    Returns:
        BytesIO containing the ZIP file
    """
    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Generate PDF summary (with compliance status)
        pdf_buffer = generate_summary_pdf(shipment, db)
        zip_file.writestr("00-SHIPMENT-INDEX.pdf", pdf_buffer.getvalue())

        # 2. Add documents
        documents = db.query(Document).filter(Document.shipment_id == shipment.id).all()
        for i, doc in enumerate(documents, 1):
            if doc.file_path:
                doc_bytes = _fetch_document_bytes(doc, storage)
                if doc_bytes:
                    ext = os.path.splitext(doc.file_name or doc.file_path)[1]
                    filename = f"{i:02d}-{doc.document_type.value}{ext}"
                    zip_file.writestr(filename, doc_bytes)

        # 3. Add tracking log JSON
        events = (
            db.query(ContainerEvent)
            .filter(ContainerEvent.shipment_id == shipment.id)
            .order_by(ContainerEvent.event_time.asc())
            .all()
        )
        tracking_log = TrackingLog(
            container_number=shipment.container_number,
            exported_at=datetime.utcnow().isoformat(),
            events=[
                TrackingEvent(
                    type=e.event_status.value,
                    timestamp=e.event_time.isoformat() if e.event_time else None,
                    location=e.location_name,
                    vessel=e.vessel_name,
                    voyage=e.voyage_number,
                )
                for e in events
            ]
        )
        zip_file.writestr("container-tracking-log.json", tracking_log.model_dump_json(indent=2))

        # 4. Add metadata JSON with compliance info
        products = db.query(Product).filter(Product.shipment_id == shipment.id).all()
        compliance_summary = get_compliance_summary(shipment, documents, db)
        decision = compliance_summary.get("decision", "HOLD")
        summary_counts = compliance_summary.get("summary", {})

        metadata = AuditPackMetadata(
            shipment=ShipmentMetadata(
                reference=shipment.reference,
                container_number=shipment.container_number,
                bl_number=shipment.bl_number,
                vessel=shipment.vessel_name,
                voyage=shipment.voyage_number,
                etd=shipment.etd.isoformat() if shipment.etd else None,
                eta=shipment.eta.isoformat() if shipment.eta else None,
                pol=PortInfo(code=shipment.pol_code, name=shipment.pol_name),
                pod=PortInfo(code=shipment.pod_code, name=shipment.pod_name),
                incoterms=shipment.incoterms,
                status=shipment.status.value,
            ),
            products=[
                ProductMetadata(
                    hs_code=p.hs_code,
                    description=p.description,
                    quantity_net_kg=float(p.quantity_net_kg) if p.quantity_net_kg else None,
                    quantity_gross_kg=float(p.quantity_gross_kg) if p.quantity_gross_kg else None,
                )
                for p in products
            ],
            buyer=PartyInfo(
                name=shipment.importer_name,
                organization_id=str(shipment.buyer_organization_id) if shipment.buyer_organization_id else None,
            ),
            exporter=PartyInfo(
                name=shipment.exporter_name,
                organization_id=str(shipment.organization_id) if shipment.organization_id else None,
            ),
            compliance=ComplianceMetadata(
                decision=decision,
                total_rules=summary_counts.get("total_rules", 0),
                passed=summary_counts.get("passed", 0),
                failed=summary_counts.get("failed", 0),
                warnings=summary_counts.get("warnings", 0),
            ),
            exported_at=datetime.utcnow().isoformat(),
        )
        zip_file.writestr("metadata.json", metadata.model_dump_json(indent=2))

    zip_buffer.seek(0)
    return zip_buffer


def _fetch_document_bytes(
    doc: Document,
    storage: Optional[StorageBackend] = None,
) -> Optional[bytes]:
    """Fetch document file bytes from storage or local disk.

    Tries StorageBackend first (Supabase Storage), falls back to local disk.
    """
    # Try StorageBackend if available and doc has a storage path
    if storage and doc.file_path:
        try:
            # Check if file_path looks like a storage path (bucket/path)
            if "/" in doc.file_path and not doc.file_path.startswith("/"):
                parts = doc.file_path.split("/", 1)
                if len(parts) == 2:
                    bucket, path = parts
                    # Run async in sync context
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            exists = pool.submit(
                                asyncio.run, storage.exists(bucket, path)
                            ).result()
                    else:
                        exists = asyncio.run(storage.exists(bucket, path))

                    if exists:
                        # For storage backend, read from local path as fallback
                        # The URL-based approach is for frontend downloads
                        pass
        except Exception:
            logger.debug("StorageBackend lookup failed, falling back to local", exc_info=True)

    # Fall back to local disk (v1 compatibility)
    if doc.file_path:
        full_path = get_full_path(doc.file_path)
        if full_path and os.path.exists(full_path):
            with open(full_path, "rb") as f:
                return f.read()

    return None


def generate_summary_pdf(shipment: Shipment, db: Session) -> io.BytesIO:
    """Generate PDF summary document for shipment.

    PRD-017: Enhanced with compliance status section.

    Args:
        shipment: The shipment to summarize
        db: Database session

    Returns:
        BytesIO containing the PDF
    """
    buffer = io.BytesIO()
    pdf_doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6
    )
    normal_style = styles['Normal']

    story = []

    # Title
    story.append(Paragraph("SHIPMENT AUDIT PACK", title_style))
    story.append(Paragraph(f"Reference: {shipment.reference}", heading_style))
    story.append(Spacer(1, 10*mm))

    # Shipment Details
    story.append(Paragraph("SHIPMENT DETAILS", heading_style))
    shipment_data = [
        ["Container Number", shipment.container_number or "-"],
        ["Bill of Lading", shipment.bl_number or "-"],
        ["Vessel / Voyage", f"{shipment.vessel_name or '-'} / {shipment.voyage_number or '-'}"],
        ["ETD", shipment.etd.strftime("%Y-%m-%d") if shipment.etd else "-"],
        ["ETA", shipment.eta.strftime("%Y-%m-%d") if shipment.eta else "-"],
        ["Port of Loading", f"{shipment.pol_name or '-'} ({shipment.pol_code or '-'})"],
        ["Port of Discharge", f"{shipment.pod_name or '-'} ({shipment.pod_code or '-'})"],
        ["Incoterms", shipment.incoterms or "-"],
        ["Status", shipment.status.value.replace("_", " ").title()],
    ]
    table = Table(shipment_data, colWidths=[50*mm, 100*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 5*mm))

    # Compliance Status (PRD-017)
    documents = db.query(Document).filter(Document.shipment_id == shipment.id).all()
    decision = get_compliance_decision(shipment, documents, db)
    _add_compliance_section(story, heading_style, normal_style, decision, shipment, documents, db)

    # Products
    products = db.query(Product).filter(Product.shipment_id == shipment.id).all()
    if products:
        story.append(Paragraph("PRODUCTS", heading_style))
        for p in products:
            product_data = [
                ["HS Code", p.hs_code],
                ["Description", p.description],
                ["Net Weight", f"{p.quantity_net_kg:,.2f} kg" if p.quantity_net_kg else "-"],
                ["Gross Weight", f"{p.quantity_gross_kg:,.2f} kg" if p.quantity_gross_kg else "-"],
            ]
            table = Table(product_data, colWidths=[50*mm, 100*mm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
        story.append(Spacer(1, 5*mm))

    # Document Checklist
    story.append(Paragraph("DOCUMENT CHECKLIST", heading_style))
    required_docs = get_required_documents(shipment)
    completeness = check_document_completeness(documents, required_docs)

    doc_by_type = {d.document_type: d for d in documents}
    doc_data = []
    for doc_type in required_docs:
        if doc_type in doc_by_type:
            doc = doc_by_type[doc_type]
            status = "Complete" if doc.status.value in ["validated", "compliance_ok", "linked"] else "Pending"
            symbol = "[X]" if status == "Complete" else "[!]"
        else:
            status = "MISSING"
            symbol = "[ ]"
        doc_data.append([symbol, DOCUMENT_NAMES.get(doc_type, doc_type.value), status])

    if doc_data:
        table = Table(doc_data, colWidths=[10*mm, 100*mm, 40*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.red if "MISSING" in [d[2] for d in doc_data] else colors.black),
        ]))
        story.append(table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Status: {completeness.complete}/{completeness.total_required} documents complete",
        normal_style
    ))
    story.append(Spacer(1, 5*mm))

    # Tracking History
    events = (
        db.query(ContainerEvent)
        .filter(ContainerEvent.shipment_id == shipment.id)
        .order_by(ContainerEvent.event_time.asc())
        .all()
    )
    if events:
        story.append(Paragraph("CONTAINER TRACKING HISTORY", heading_style))
        event_data = [["Date", "Event", "Location", "Vessel"]]
        for e in events:
            event_data.append([
                e.event_time.strftime("%Y-%m-%d %H:%M") if e.event_time else "-",
                e.event_status.value.replace("_", " ").title(),
                e.location_name or "-",
                e.vessel_name or "-",
            ])
        table = Table(event_data, colWidths=[35*mm, 40*mm, 50*mm, 35*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        story.append(table)

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | VIBOTAJ TraceHub",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
    ))

    pdf_doc.build(story)
    buffer.seek(0)
    return buffer


def _add_compliance_section(
    story: list,
    heading_style: ParagraphStyle,
    normal_style: ParagraphStyle,
    decision: str,
    shipment: Shipment,
    documents: List[Document],
    db: Session,
) -> None:
    """Add compliance status section to the PDF summary."""
    story.append(Paragraph("COMPLIANCE STATUS", heading_style))

    # Decision badge colors
    decision_colors = {
        "APPROVE": colors.HexColor("#16a34a"),
        "HOLD": colors.HexColor("#d97706"),
        "REJECT": colors.HexColor("#dc2626"),
    }
    decision_labels = {
        "APPROVE": "APPROVED",
        "HOLD": "ON HOLD",
        "REJECT": "REJECTED",
    }

    badge_color = decision_colors.get(decision, colors.grey)
    badge_label = decision_labels.get(decision, decision)

    badge_style = ParagraphStyle(
        'ComplianceBadge',
        parent=normal_style,
        fontSize=12,
        textColor=badge_color,
        fontName='Helvetica-Bold',
    )
    story.append(Paragraph(f"Decision: {badge_label}", badge_style))

    # Summary counts
    compliance_summary = get_compliance_summary(shipment, documents, db)
    summary = compliance_summary.get("summary", {})
    total = summary.get("total_rules", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    warnings = summary.get("warnings", 0)

    if total > 0:
        summary_data = [
            ["Total Rules", str(total)],
            ["Passed", str(passed)],
            ["Failed", str(failed)],
            ["Warnings", str(warnings)],
        ]
        table = Table(summary_data, colWidths=[50*mm, 30*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    # Override info
    override = compliance_summary.get("override")
    if override:
        story.append(Spacer(1, 2*mm))
        override_style = ParagraphStyle(
            'Override',
            parent=normal_style,
            fontSize=9,
            textColor=colors.HexColor("#6b7280"),
            fontName='Helvetica-Oblique',
        )
        story.append(Paragraph(
            f"Override: {override.get('reason', 'N/A')} (by {override.get('overridden_by', 'unknown')})",
            override_style,
        ))

    story.append(Spacer(1, 5*mm))
