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
    ContainerEvent, EventType,
    User, UserRole
)
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


def seed_sample_data(db: Session):
    """Seed database with sample shipment data."""

    print("Seeding sample data...")

    # =========================================================================
    # PARTIES
    # =========================================================================

    # Supplier: TEMIRA INDUSTRIES
    supplier_temira = Party(
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
    db.add(supplier_temira)

    # Buyer: WITATRADE GMBH
    buyer_witatrade = Party(
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
    db.add(buyer_witatrade)

    db.flush()  # Get IDs

    # =========================================================================
    # SHIPMENT 1: VIBO-2026-001 (REF NO - 1416)
    # =========================================================================

    etd_1 = datetime(2025, 12, 13)
    eta_1 = datetime(2026, 1, 3)

    shipment_1 = Shipment(
        reference="VIBO-2026-001",
        container_number="MRSU3452572",
        bl_number="262495038",
        booking_reference="MAERSK-550N-001",
        vessel_name="RHINE MAERSK",
        voyage_number="550N",
        etd=etd_1,
        eta=eta_1,
        pol_code="NGAPP",
        pol_name="Apapa, Lagos",
        pod_code="DEHAM",
        pod_name="Hamburg",
        final_destination="Stelle, Germany",
        incoterms="FOB",
        status=ShipmentStatus.IN_TRANSIT,
        buyer_id=buyer_witatrade.id,
        supplier_id=supplier_temira.id
    )
    db.add(shipment_1)
    db.flush()

    # Product for Shipment 1
    product_1 = Product(
        shipment_id=shipment_1.id,
        hs_code="0506.90.00",
        description="Crushed Cow Hooves & Horns",
        quantity_net_kg=Decimal("25000"),
        quantity_gross_kg=Decimal("25200"),
        unit_of_measure="KG",
        packaging_type="1x40ft Container, 20 CBM",
        packaging_count=1,
        batch_lot_number="VIBO-2026-001-LOT1",
        quality_grade="Export Grade",
        moisture_percentage=Decimal("12.0"),
        production_date=date(2025, 11, 30)
    )
    db.add(product_1)
    db.flush()

    # Origin for Shipment 1
    origin_1 = Origin(
        product_id=product_1.id,
        farm_plot_identifier="NG-LA-TEMIRA-001",
        geolocation_lat=Decimal("6.4541"),
        geolocation_lng=Decimal("3.3947"),
        country="NG",
        region="Lagos State",
        district="Lagos Industrial",
        production_start_date=date(2025, 10, 1),
        production_end_date=date(2025, 11, 30),
        supplier_id=supplier_temira.id,
        deforestation_cutoff_compliant=True,
        deforestation_free_statement="Animal by-products sourced from established slaughterhouses. Not subject to EUDR deforestation provisions."
    )
    db.add(origin_1)

    # Documents for Shipment 1 - with actual files
    docs_shipment_1 = [
        {
            "document_type": DocumentType.BILL_OF_LADING,
            "name": "Bill of Lading - ONE (1)",
            "file_name": "BILL OF LADING - ONE (1).pdf",
            "file_path": "VIBO-2026-001/BILL OF LADING - ONE (1).pdf",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "262495038",
            "issue_date": date(2025, 12, 13),
            "issuing_authority": "Maersk Line"
        },
        {
            "document_type": DocumentType.COMMERCIAL_INVOICE,
            "name": "Commercial Invoice - REF NO 1416",
            "file_name": "REF NO - 1416.pdf",
            "file_path": "VIBO-2026-001/REF NO - 1416.pdf",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "1416",
            "issue_date": date(2025, 12, 10)
        },
        {
            "document_type": DocumentType.CERTIFICATE_OF_ORIGIN,
            "name": "Certificate of Origin - 0029532",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "0029532",
            "issue_date": date(2025, 12, 10),
            "issuing_authority": "Lagos Chamber of Commerce"
        },
        {
            "document_type": DocumentType.FUMIGATION_CERTIFICATE,
            "name": "Fumigation Certificate - 77091",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "77091",
            "issue_date": date(2025, 12, 5),
            "issuing_authority": "NAQS Nigeria"
        },
        {
            "document_type": DocumentType.PACKING_LIST,
            "name": "Packing List - VIBO-PL-2026-001",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "VIBO-PL-2026-001",
            "issue_date": date(2025, 12, 10)
        },
        {
            "document_type": DocumentType.PHYTOSANITARY_CERTIFICATE,
            "name": "Federal Produce Inspection Certificate",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "FPIS-2025-001",
            "issue_date": date(2025, 12, 8),
            "issuing_authority": "Federal Produce Inspection Service"
        },
        # Horn & Hoof specific documents (NO EUDR required)
        {
            "document_type": DocumentType.EU_TRACES_CERTIFICATE,
            "name": "EU TRACES Certificate - RC1479592",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "RC1479592",
            "issue_date": date(2025, 12, 9),
            "issuing_authority": "European Commission TRACES System"
        },
        {
            "document_type": DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            "name": "Veterinary Health Certificate - VHC-2025-0506",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "VHC-2025-0506",
            "issue_date": date(2025, 12, 7),
            "issuing_authority": "Nigerian Veterinary Research Institute (NVRI)"
        },
        {
            "document_type": DocumentType.EXPORT_DECLARATION,
            "name": "Export Declaration - NXP/2025/LA/001234",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "NXP/2025/LA/001234",
            "issue_date": date(2025, 12, 11),
            "issuing_authority": "Nigeria Customs Service"
        },
    ]

    for doc_data in docs_shipment_1:
        doc = Document(
            shipment_id=shipment_1.id,
            uploaded_by="temira_exports",
            uploaded_at=datetime(2025, 12, 10, 10, 0),
            **doc_data
        )
        if doc.status == DocumentStatus.VALIDATED:
            doc.validated_at = datetime(2025, 12, 12, 16, 0)
            doc.validated_by = "compliance_team"
        db.add(doc)

    # Container Events for Shipment 1
    events_shipment_1 = [
        {
            "event_type": EventType.GATE_IN,
            "event_timestamp": datetime(2025, 12, 11, 8, 30),
            "location_name": "Apapa Container Terminal",
            "location_code": "NGAPP",
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

    for event_data in events_shipment_1:
        event = ContainerEvent(
            shipment_id=shipment_1.id,
            source="seed_data",
            **event_data
        )
        db.add(event)

    # =========================================================================
    # SHIPMENT 2: VIBO-2026-002 (REF NO - 1417)
    # =========================================================================

    etd_2 = datetime(2025, 12, 20)
    eta_2 = datetime(2026, 1, 10)

    shipment_2 = Shipment(
        reference="VIBO-2026-002",
        container_number="TCNU7654321",
        bl_number="262495039",
        booking_reference="MAERSK-550N-002",
        vessel_name="RHINE MAERSK",
        voyage_number="551N",
        etd=etd_2,
        eta=eta_2,
        pol_code="NGAPP",
        pol_name="Apapa, Lagos",
        pod_code="DEHAM",
        pod_name="Hamburg",
        final_destination="Stelle, Germany",
        incoterms="FOB",
        status=ShipmentStatus.IN_TRANSIT,
        buyer_id=buyer_witatrade.id,
        supplier_id=supplier_temira.id
    )
    db.add(shipment_2)
    db.flush()

    # Product for Shipment 2
    product_2 = Product(
        shipment_id=shipment_2.id,
        hs_code="0506.90.00",
        description="Crushed Cow Hooves & Horns",
        quantity_net_kg=Decimal("22000"),
        quantity_gross_kg=Decimal("22200"),
        unit_of_measure="KG",
        packaging_type="1x40ft Container, 18 CBM",
        packaging_count=1,
        batch_lot_number="VIBO-2026-002-LOT1",
        quality_grade="Export Grade",
        moisture_percentage=Decimal("11.5"),
        production_date=date(2025, 12, 5)
    )
    db.add(product_2)
    db.flush()

    # Origin for Shipment 2
    origin_2 = Origin(
        product_id=product_2.id,
        farm_plot_identifier="NG-LA-TEMIRA-002",
        geolocation_lat=Decimal("6.4550"),
        geolocation_lng=Decimal("3.3950"),
        country="NG",
        region="Lagos State",
        district="Lagos Industrial",
        production_start_date=date(2025, 11, 1),
        production_end_date=date(2025, 12, 5),
        supplier_id=supplier_temira.id,
        deforestation_cutoff_compliant=True,
        deforestation_free_statement="Animal by-products sourced from established slaughterhouses. Not subject to EUDR deforestation provisions."
    )
    db.add(origin_2)

    # Documents for Shipment 2 - with actual files
    docs_shipment_2 = [
        {
            "document_type": DocumentType.BILL_OF_LADING,
            "name": "Bill of Lading - TWO (2)",
            "file_name": "BILL OF LADING - TWO (2).pdf",
            "file_path": "VIBO-2026-002/BILL OF LADING - TWO (2).pdf",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "262495039",
            "issue_date": date(2025, 12, 20),
            "issuing_authority": "Maersk Line"
        },
        {
            "document_type": DocumentType.COMMERCIAL_INVOICE,
            "name": "Commercial Invoice - REF NO 1417",
            "file_name": "REF NO - 1417.pdf",
            "file_path": "VIBO-2026-002/REF NO - 1417.pdf",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "1417",
            "issue_date": date(2025, 12, 18)
        },
        {
            "document_type": DocumentType.CERTIFICATE_OF_ORIGIN,
            "name": "Certificate of Origin - 0029533",
            "status": DocumentStatus.DRAFT,
            "reference_number": "0029533",
        },
        {
            "document_type": DocumentType.FUMIGATION_CERTIFICATE,
            "name": "Fumigation Certificate",
            "status": DocumentStatus.DRAFT,
        },
        {
            "document_type": DocumentType.PACKING_LIST,
            "name": "Packing List - VIBO-PL-2026-002",
            "status": DocumentStatus.DRAFT,
            "reference_number": "VIBO-PL-2026-002",
        },
        {
            "document_type": DocumentType.PHYTOSANITARY_CERTIFICATE,
            "name": "Phytosanitary Certificate",
            "status": DocumentStatus.DRAFT,
        },
        # Horn & Hoof specific documents (NO EUDR required) - pending for shipment 2
        {
            "document_type": DocumentType.EU_TRACES_CERTIFICATE,
            "name": "EU TRACES Certificate - Pending",
            "status": DocumentStatus.DRAFT,
        },
        {
            "document_type": DocumentType.VETERINARY_HEALTH_CERTIFICATE,
            "name": "Veterinary Health Certificate - Pending",
            "status": DocumentStatus.DRAFT,
        },
        {
            "document_type": DocumentType.EXPORT_DECLARATION,
            "name": "Export Declaration - Pending",
            "status": DocumentStatus.DRAFT,
        },
    ]

    for doc_data in docs_shipment_2:
        doc = Document(
            shipment_id=shipment_2.id,
            uploaded_by="temira_exports",
            uploaded_at=datetime(2025, 12, 18, 10, 0) if doc_data.get("file_path") else None,
            **doc_data
        )
        if doc.status == DocumentStatus.VALIDATED:
            doc.validated_at = datetime(2025, 12, 19, 16, 0)
            doc.validated_by = "compliance_team"
        db.add(doc)

    # Container Events for Shipment 2
    events_shipment_2 = [
        {
            "event_type": EventType.GATE_IN,
            "event_timestamp": datetime(2025, 12, 18, 9, 0),
            "location_name": "Apapa Container Terminal",
            "location_code": "NGAPP",
        },
        {
            "event_type": EventType.LOADED,
            "event_timestamp": datetime(2025, 12, 19, 15, 0),
            "location_name": "Apapa, Lagos",
            "location_code": "NGAPP",
            "vessel_name": "RHINE MAERSK",
            "voyage_number": "551N"
        },
        {
            "event_type": EventType.DEPARTED,
            "event_timestamp": datetime(2025, 12, 20, 16, 0),
            "location_name": "Apapa, Lagos",
            "location_code": "NGAPP",
            "vessel_name": "RHINE MAERSK",
            "voyage_number": "551N"
        },
    ]

    for event_data in events_shipment_2:
        event = ContainerEvent(
            shipment_id=shipment_2.id,
            source="seed_data",
            **event_data
        )
        db.add(event)

    db.commit()

    print(f"\n{'='*60}")
    print("Sample data seeded successfully!")
    print(f"{'='*60}\n")

    print(f"SHIPMENT 1: {shipment_1.reference}")
    print(f"  - Container: {shipment_1.container_number}")
    print(f"  - B/L Number: {shipment_1.bl_number}")
    print(f"  - Vessel: {shipment_1.vessel_name} / {shipment_1.voyage_number}")
    print(f"  - Route: {shipment_1.pol_name} -> {shipment_1.pod_name}")
    print(f"  - Documents: {len(docs_shipment_1)} (all validated)")
    print(f"  - Events: {len(events_shipment_1)} tracking events")

    print(f"\nSHIPMENT 2: {shipment_2.reference}")
    print(f"  - Container: {shipment_2.container_number}")
    print(f"  - B/L Number: {shipment_2.bl_number}")
    print(f"  - Vessel: {shipment_2.vessel_name} / {shipment_2.voyage_number}")
    print(f"  - Route: {shipment_2.pol_name} -> {shipment_2.pod_name}")
    print(f"  - Documents: {len(docs_shipment_2)} (2 uploaded, 4 pending)")
    print(f"  - Events: {len(events_shipment_2)} tracking events")


def seed_users(db: Session):
    """Seed database with test users."""
    print("\nSeeding test users...")

    # Check if users already exist
    existing_user = db.query(User).first()
    if existing_user:
        print("Users already exist. Skipping user seed.")
        return

    # Create test users for each role
    users = [
        {
            "email": "admin@tracehub.io",
            "full_name": "System Administrator",
            "password": "Admin123!",
            "role": UserRole.ADMIN,
        },
        {
            "email": "compliance@tracehub.io",
            "full_name": "Compliance Officer",
            "password": "Compliance123!",
            "role": UserRole.COMPLIANCE,
        },
        {
            "email": "buyer@witatrade.de",
            "full_name": "Hans Mueller",
            "password": "Buyer123!",
            "role": UserRole.BUYER,
        },
        {
            "email": "supplier@temira.ng",
            "full_name": "Chioma Nwosu",
            "password": "Supplier123!",
            "role": UserRole.SUPPLIER,
        },
        {
            "email": "viewer@tracehub.io",
            "full_name": "View Only User",
            "password": "Viewer123!",
            "role": UserRole.VIEWER,
        },
    ]

    for user_data in users:
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password=pwd_context.hash(user_data["password"]),
            role=user_data["role"],
            is_active=True
        )
        db.add(user)

    db.commit()

    print(f"\n{'='*60}")
    print("Test users created successfully!")
    print(f"{'='*60}")
    print("\nTest User Credentials:")
    print("-" * 40)
    for user_data in users:
        print(f"  {user_data['role'].value.upper()}:")
        print(f"    Email: {user_data['email']}")
        print(f"    Password: {user_data['password']}")
        print()


def main():
    """Main entry point."""
    create_tables()

    db = SessionLocal()
    try:
        # Seed users first
        seed_users(db)

        # Check if shipment data already exists
        existing = db.query(Shipment).first()
        if existing:
            print(f"\nShipment data already exists (shipment {existing.reference}). Skipping shipment seed.")
            print("To reseed, drop the database tables first.")
            return

        seed_sample_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
