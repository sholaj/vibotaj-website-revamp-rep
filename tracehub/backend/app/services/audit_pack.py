"""Audit pack generation service."""

import io
import os
import json
import zipfile
from datetime import datetime
from typing import BinaryIO

from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from ..models import Shipment, Document, ContainerEvent, Product
from .compliance import get_required_documents, check_document_completeness, DOCUMENT_NAMES
from ..config import get_settings

# Base directory for uploads (tracehub/ - parent of backend/)
UPLOAD_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def generate_audit_pack(shipment: Shipment, db: Session) -> io.BytesIO:
    """Generate audit pack ZIP for a shipment.

    Args:
        shipment: The shipment to generate pack for
        db: Database session

    Returns:
        BytesIO containing the ZIP file
    """
    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Generate PDF summary
        pdf_buffer = generate_summary_pdf(shipment, db)
        zip_file.writestr("00-SHIPMENT-INDEX.pdf", pdf_buffer.getvalue())

        # 2. Add documents
        documents = db.query(Document).filter(Document.shipment_id == shipment.id).all()
        for i, doc in enumerate(documents, 1):
            if doc.file_path:
                # Resolve full path from relative path
                full_path = os.path.join(UPLOAD_BASE_DIR, doc.file_path)
                if os.path.exists(full_path):
                    # Get file extension
                    ext = os.path.splitext(doc.file_name or doc.file_path)[1]
                    filename = f"{i:02d}-{doc.document_type.value}{ext}"
                    zip_file.write(full_path, filename)

        # 3. Add tracking log JSON
        events = (
            db.query(ContainerEvent)
            .filter(ContainerEvent.shipment_id == shipment.id)
            .order_by(ContainerEvent.event_timestamp.asc())
            .all()
        )
        tracking_log = {
            "container_number": shipment.container_number,
            "exported_at": datetime.utcnow().isoformat(),
            "events": [
                {
                    "type": e.event_type.value,
                    "timestamp": e.event_timestamp.isoformat() if e.event_timestamp else None,
                    "location": e.location_name,
                    "vessel": e.vessel_name,
                    "voyage": e.voyage_number,
                }
                for e in events
            ]
        }
        zip_file.writestr("container-tracking-log.json", json.dumps(tracking_log, indent=2))

        # 4. Add metadata JSON
        products = db.query(Product).filter(Product.shipment_id == shipment.id).all()
        metadata = {
            "shipment": {
                "reference": shipment.reference,
                "container_number": shipment.container_number,
                "bl_number": shipment.bl_number,
                "vessel": shipment.vessel_name,
                "voyage": shipment.voyage_number,
                "etd": shipment.etd.isoformat() if shipment.etd else None,
                "eta": shipment.eta.isoformat() if shipment.eta else None,
                "pol": {"code": shipment.pol_code, "name": shipment.pol_name},
                "pod": {"code": shipment.pod_code, "name": shipment.pod_name},
                "incoterms": shipment.incoterms,
                "status": shipment.status.value,
            },
            "products": [
                {
                    "hs_code": p.hs_code,
                    "description": p.description,
                    "quantity_net_kg": float(p.quantity_net_kg) if p.quantity_net_kg else None,
                    "quantity_gross_kg": float(p.quantity_gross_kg) if p.quantity_gross_kg else None,
                }
                for p in products
            ],
            "buyer": {
                "name": shipment.buyer.company_name if shipment.buyer else None,
                "country": shipment.buyer.country if shipment.buyer else None,
            },
            "supplier": {
                "name": shipment.supplier.company_name if shipment.supplier else None,
                "country": shipment.supplier.country if shipment.supplier else None,
            },
            "exported_at": datetime.utcnow().isoformat(),
        }
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)
    return zip_buffer


def generate_summary_pdf(shipment: Shipment, db: Session) -> io.BytesIO:
    """Generate PDF summary document for shipment.

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
    story.append(Paragraph(f"SHIPMENT AUDIT PACK", title_style))
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
    documents = db.query(Document).filter(Document.shipment_id == shipment.id).all()
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
        .order_by(ContainerEvent.event_timestamp.asc())
        .all()
    )
    if events:
        story.append(Paragraph("CONTAINER TRACKING HISTORY", heading_style))
        event_data = [["Date", "Event", "Location", "Vessel"]]
        for e in events:
            event_data.append([
                e.event_timestamp.strftime("%Y-%m-%d %H:%M") if e.event_timestamp else "-",
                e.event_type.value.replace("_", " ").title(),
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
