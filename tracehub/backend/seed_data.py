"""Seed script to populate database with sample shipment data.

Run with: python -m seed_data
"""

import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import (
    Party, PartyType,
    Shipment, ShipmentStatus,
    Product,
    Origin,
    Document, DocumentType, DocumentStatus,
    ContainerEvent, EventType
)


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


def seed_sample_data(db: Session):
    """Seed database with sample shipment data."""

    print("Seeding sample data...")

    # Create Supplier (Real: TEMIRA INDUSTRIES)
    supplier = Party(
        type=PartyType.SUPPLIER,
        company_name="TEMIRA INDUSTRIES NIGERIA LTD",
        contact_name="Operations Manager",
        email="exports@temira.ng",
        phone="+234 XXX XXX XXXX",
        address="Lagos, Nigeria",
        city="Lagos",
        country="NG",
        registration_number="RC-TEMIRA",
        tax_id="NG-TAX-TEMIRA"
    )
    db.add(supplier)

    # Create Buyer (Real: WITATRADE GMBH)
    buyer = Party(
        type=PartyType.BUYER,
        company_name="WITATRADE GMBH",
        contact_name="Imports Manager",
        email="imports@witatrade.de",
        phone="+49 XXX XXX XXXX",
        address="98A Duvendahl, Stelle, 21435",
        city="Stelle",
        country="DE",
        registration_number="HRB-WITA",
        tax_id="DE-WITATRADE"
    )
    db.add(buyer)

    db.flush()  # Get IDs

    # Create Shipment (Real: from Bill of Lading 262495038)
    # Ship date: 2025-12-13, typical transit Lagos->Hamburg is ~18-21 days
    etd = datetime(2025, 12, 13)
    eta = datetime(2026, 1, 3)  # Estimated arrival

    shipment = Shipment(
        reference="TEMIRA-2025-001",
        container_number="MRSU3452572",  # Real container from B/L
        bl_number="262495038",  # Real Maersk B/L number
        booking_reference="MAERSK-550N",
        vessel_name="RHINE MAERSK",
        voyage_number="550N",
        etd=etd,
        eta=eta,
        pol_code="NGAPP",
        pol_name="Apapa, Lagos",
        pod_code="DEHAM",
        pod_name="Hamburg",
        final_destination="Stelle, Germany",
        incoterms="FOB",
        status=ShipmentStatus.IN_TRANSIT,
        buyer_id=buyer.id,
        supplier_id=supplier.id
    )
    db.add(shipment)
    db.flush()

    # Create Product (Real: Crushed Cow Hooves & Horns from B/L)
    product = Product(
        shipment_id=shipment.id,
        hs_code="0506.90.00",
        description="Crushed Cow Hooves & Horns",
        quantity_net_kg=Decimal("25000"),  # Real: 25,000 KGS from B/L
        quantity_gross_kg=Decimal("25200"),  # Including packaging
        unit_of_measure="KG",
        packaging_type="1x40ft Container, 20 CBM",
        packaging_count=1,
        batch_lot_number="TEMIRA-2025-001-LOT1",
        quality_grade="Export Grade",
        moisture_percentage=Decimal("12.0"),
        production_date=date(2025, 11, 30)
    )
    db.add(product)
    db.flush()

    # Create Origin (EUDR compliance data for TEMIRA sourcing)
    origin = Origin(
        product_id=product.id,
        farm_plot_identifier="NG-LA-TEMIRA-001",
        geolocation_lat=Decimal("6.4541"),  # Lagos area coordinates
        geolocation_lng=Decimal("3.3947"),
        country="NG",
        region="Lagos State",
        district="Lagos Industrial",
        production_start_date=date(2025, 10, 1),
        production_end_date=date(2025, 11, 30),
        supplier_id=supplier.id,
        deforestation_cutoff_compliant=True,
        deforestation_free_statement="Animal by-products sourced from established slaughterhouses and processing facilities. Not subject to EUDR deforestation provisions as non-forest commodities."
    )
    db.add(origin)

    # Create Documents (Real documents from TEMIRA shipment B/L package)
    documents_data = [
        {
            "document_type": DocumentType.BILL_OF_LADING,
            "name": "Bill of Lading - Maersk 262495038",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "262495038",
            "issue_date": date(2025, 12, 13),  # Ship date from B/L
            "issuing_authority": "Maersk Line"
        },
        {
            "document_type": DocumentType.CERTIFICATE_OF_ORIGIN,
            "name": "Certificate of Origin - 0029532",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "0029532",  # Real COO number from docs
            "issue_date": date(2025, 12, 10),
            "issuing_authority": "Lagos Chamber of Commerce"
        },
        {
            "document_type": DocumentType.FUMIGATION_CERTIFICATE,
            "name": "Fumigation Certificate - 77091",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "77091",  # Real fumigation cert from docs
            "issue_date": date(2025, 12, 5),  # 05/12/2025 from document
            "issuing_authority": "NAQS Nigeria"
        },
        {
            "document_type": DocumentType.COMMERCIAL_INVOICE,
            "name": "Commercial Invoice - TEMIRA-INV-2025-001",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "TEMIRA-INV-2025-001",
            "issue_date": date(2025, 12, 10)
        },
        {
            "document_type": DocumentType.PACKING_LIST,
            "name": "Packing List - TEMIRA-PL-2025-001",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "TEMIRA-PL-2025-001",
            "issue_date": date(2025, 12, 10)
        },
        {
            "document_type": DocumentType.PHYTOSANITARY_CERTIFICATE,
            "name": "Federal Produce Inspection Certificate",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "FPIS-2025-TEMIRA",
            "issue_date": date(2025, 12, 8),
            "issuing_authority": "Federal Produce Inspection Service"
        },
        # Missing documents for demo purposes - to show compliance gaps
        # SANITARY_CERTIFICATE - not yet uploaded
        # INSURANCE_CERTIFICATE - not yet uploaded
        # EUDR_DECLARATION - not yet uploaded
    ]

    for doc_data in documents_data:
        doc = Document(
            shipment_id=shipment.id,
            uploaded_by="temira_exports",
            uploaded_at=datetime(2025, 12, 10, 10, 0),  # Uploaded before shipping
            **doc_data
        )
        if doc.status == DocumentStatus.VALIDATED:
            doc.validated_at = datetime(2025, 12, 12, 16, 0)  # Validated before departure
            doc.validated_by = "compliance_team"
        db.add(doc)

    # Create Container Events (Real vessel: RHINE MAERSK 550N, departed 2025-12-13)
    events_data = [
        {
            "event_type": EventType.GATE_IN,
            "event_timestamp": datetime(2025, 12, 11, 8, 30),
            "location_name": "Apapa Container Terminal",
            "location_code": "NGAPP",
            "vessel_name": None,
        },
        {
            "event_type": EventType.LOADED,
            "event_timestamp": datetime(2025, 12, 12, 14, 0),
            "location_name": "Apapa, Lagos",
            "location_code": "NGAPP",
            "vessel_name": "RHINE MAERSK",
            "voyage_number": "550N"
        },
        {
            "event_type": EventType.DEPARTED,
            "event_timestamp": datetime(2025, 12, 13, 18, 0),
            "location_name": "Apapa, Lagos",
            "location_code": "NGAPP",
            "vessel_name": "RHINE MAERSK",
            "voyage_number": "550N"
        },
        {
            "event_type": EventType.TRANSSHIPMENT,
            "event_timestamp": datetime(2025, 12, 22, 6, 0),
            "location_name": "Tangier Med",
            "location_code": "MAPTM",
            "vessel_name": "RHINE MAERSK",
            "voyage_number": "550N"
        },
        {
            "event_type": EventType.DEPARTED,
            "event_timestamp": datetime(2025, 12, 23, 12, 0),
            "location_name": "Tangier Med",
            "location_code": "MAPTM",
            "vessel_name": "RHINE MAERSK",
            "voyage_number": "550N"
        },
    ]

    for event_data in events_data:
        event = ContainerEvent(
            shipment_id=shipment.id,
            source="seed_data",
            **event_data
        )
        db.add(event)

    db.commit()
    print(f"Real shipment data seeded successfully!")
    print(f"  - Shipment: {shipment.reference}")
    print(f"  - Container: {shipment.container_number} (Seal: ML-NG0091820)")
    print(f"  - B/L Number: {shipment.bl_number}")
    print(f"  - Vessel: {shipment.vessel_name} / Voyage {shipment.voyage_number}")
    print(f"  - Route: {shipment.pol_name} → {shipment.pod_name}")
    print(f"  - Cargo: 25,000 KGS Crushed Cow Hooves & Horns")
    print(f"  - Shipper: TEMIRA INDUSTRIES NIGERIA LTD")
    print(f"  - Consignee: WITATRADE GMBH")
    print(f"  - Documents: {len(documents_data)} uploaded (3 required docs missing for demo)")
    print(f"  - Events: {len(events_data)} tracking events")


def main():
    """Main entry point."""
    create_tables()

    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(Shipment).first()
        if existing:
            print(f"Data already exists (shipment {existing.reference}). Skipping seed.")
            return

        seed_sample_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
