"""Seed script to populate database with sample shipment data.

Run with: python -m seed_data
"""

import os
import sys
import uuid
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
    ContainerEvent, EventStatus,
    User, UserRole,
    Organization, OrganizationType, OrganizationStatus,
    OrganizationMembership, OrgRole
)
import bcrypt


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly (same as auth.py)."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


def seed_sample_data(db: Session, vibotaj_org_id: uuid.UUID, witatrade_org_id: uuid.UUID):
    """Seed database with sample shipment data."""

    print("Seeding sample data...")

    # Get admin and compliance users for document ownership
    admin_user = db.query(User).filter_by(email="admin@vibotaj.com").first()
    compliance_user = db.query(User).filter_by(email="compliance@vibotaj.com").first()

    # =========================================================================
    # SHIPMENT 1: VIBO-2026-001
    # =========================================================================

    etd_1 = datetime(2025, 12, 13)
    eta_1 = datetime(2026, 1, 3)

    shipment_1 = Shipment(
        reference="VIBO-2026-001",
        container_number="MRSU3452572",
        bl_number="262495038",
        booking_ref="MAERSK-550N-001",
        vessel_name="RHINE MAERSK",
        voyage_number="550N",
        etd=etd_1,
        eta=eta_1,
        pol_code="NGAPP",
        pol_name="Apapa, Lagos",
        pod_code="DEHAM",
        pod_name="Hamburg",
        incoterms="FOB",
        status=ShipmentStatus.IN_TRANSIT,
        organization_id=vibotaj_org_id,
        exporter_name="TEMIRA INDUSTRIES NIGERIA LTD",
        importer_name="WITATRADE GMBH"
    )
    db.add(shipment_1)
    db.flush()

    # Product for Shipment 1
    product_1 = Product(
        shipment_id=shipment_1.id,
        organization_id=vibotaj_org_id,
        name="Crushed Cow Hooves & Horns",
        description="Crushed Cow Hooves & Horns (HS 0506.90.00)",
        hs_code="0506.90.00",
        quantity_net_kg=25000.0,
        quantity_gross_kg=25200.0,
        packaging="1x40ft Container",
        batch_number="VIBO-2026-001",
        lot_number="LOT-1",
        quality_grade="Export Grade",
        moisture_content=12.0
    )
    db.add(product_1)
    db.flush()

    # Origin for Shipment 1
    origin_1 = Origin(
        shipment_id=shipment_1.id,
        organization_id=vibotaj_org_id,
        farm_name="TEMIRA Lagos Hub",
        plot_identifier="NG-LA-001",
        latitude=6.4541,
        longitude=3.3947,
        country="NG",
        region="Lagos",
        production_date=datetime(2025, 11, 30),
        deforestation_free=True,
        eudr_cutoff_compliant=True
    )
    db.add(origin_1)

    # Documents for Shipment 1
    docs_shipment_1 = [
        {
            "document_type": DocumentType.BILL_OF_LADING,
            "name": "Bill of Lading - ONE (1)",
            "file_name": "BILL OF LADING - ONE (1).pdf",
            "file_path": "VIBO-2026-001/BILL OF LADING - ONE (1).pdf",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "262495038",
            "document_date": datetime(2025, 12, 13),
            "issuer": "Maersk Line"
        },
        {
            "document_type": DocumentType.COMMERCIAL_INVOICE,
            "name": "Commercial Invoice - REF NO 1416",
            "file_name": "REF NO - 1416.pdf",
            "file_path": "VIBO-2026-001/REF NO - 1416.pdf",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "1416",
            "document_date": datetime(2025, 12, 10)
        }
    ]

    for doc_data in docs_shipment_1:
        doc = Document(
            shipment_id=shipment_1.id,
            organization_id=vibotaj_org_id,
            uploaded_by=admin_user.id,
            **doc_data
        )
        if doc.status == DocumentStatus.VALIDATED:
            doc.validated_at = datetime(2025, 12, 12, 16, 0)
            doc.validated_by = compliance_user.id
        db.add(doc)

    # Container Events for Shipment 1
    events_shipment_1 = [
        {
            "event_status": EventStatus.GATE_IN,
            "event_time": datetime(2025, 12, 11, 8, 30),
            "location_name": "Apapa Container Terminal",
            "location_code": "NGAPP",
        },
        {
            "event_status": EventStatus.LOADED,
            "event_time": datetime(2025, 12, 12, 14, 0),
            "location_name": "Apapa, Lagos",
            "location_code": "NGAPP",
            "vessel_name": "RHINE MAERSK",
            "voyage_number": "550N"
        }
    ]

    for event_data in events_shipment_1:
        event = ContainerEvent(
            shipment_id=shipment_1.id,
            organization_id=vibotaj_org_id,
            source="seed_data",
            **event_data
        )
        db.add(event)

    # =========================================================================
    # SHIPMENT 2: VIBO-2026-002
    # =========================================================================

    etd_2 = datetime(2025, 12, 20)
    eta_2 = datetime(2026, 1, 10)

    shipment_2 = Shipment(
        reference="VIBO-2026-002",
        container_number="TCNU7654321",
        bl_number="262495039",
        booking_ref="MAERSK-550N-002",
        vessel_name="RHINE MAERSK",
        voyage_number="551N",
        etd=etd_2,
        eta=eta_2,
        pol_code="NGAPP",
        pol_name="Apapa, Lagos",
        pod_code="DEHAM",
        pod_name="Hamburg",
        incoterms="FOB",
        status=ShipmentStatus.IN_TRANSIT,
        organization_id=vibotaj_org_id,
        exporter_name="TEMIRA INDUSTRIES NIGERIA LTD",
        importer_name="WITATRADE GMBH"
    )
    db.add(shipment_2)
    db.flush()

    # Product for Shipment 2
    product_2 = Product(
        shipment_id=shipment_2.id,
        organization_id=vibotaj_org_id,
        name="Crushed Cow Hooves & Horns",
        description="Crushed Cow Hooves & Horns (HS 0506.90.00)",
        hs_code="0506.90.00",
        quantity_net_kg=22000.0,
        quantity_gross_kg=22200.0,
        packaging="1x40ft Container",
        batch_number="VIBO-2026-002",
        lot_number="LOT-2",
        quality_grade="Export Grade",
        moisture_content=11.5
    )
    db.add(product_2)
    db.flush()

    # Origin for Shipment 2
    origin_2 = Origin(
        shipment_id=shipment_2.id,
        organization_id=vibotaj_org_id,
        farm_name="TEMIRA Lagos Hub",
        plot_identifier="NG-LA-002",
        latitude=6.4550,
        longitude=3.3950,
        country="NG",
        region="Lagos",
        production_date=datetime(2025, 12, 5),
        deforestation_free=True,
        eudr_cutoff_compliant=True
    )
    db.add(origin_2)

    # Documents for Shipment 2
    docs_shipment_2 = [
        {
            "document_type": DocumentType.BILL_OF_LADING,
            "name": "Bill of Lading - TWO (2)",
            "file_name": "BILL OF LADING - TWO (2).pdf",
            "file_path": "VIBO-2026-002/BILL OF LADING - TWO (2).pdf",
            "status": DocumentStatus.VALIDATED,
            "reference_number": "262495039",
            "document_date": datetime(2025, 12, 20),
            "issuer": "Maersk Line"
        },
        {
            "document_type": DocumentType.CERTIFICATE_OF_ORIGIN,
            "name": "Certificate of Origin - 0029533",
            "status": DocumentStatus.UPLOADED,
            "reference_number": "0029533",
        }
    ]

    for doc_data in docs_shipment_2:
        doc = Document(
            shipment_id=shipment_2.id,
            organization_id=vibotaj_org_id,
            uploaded_by=admin_user.id,
            **doc_data
        )
        if doc.status == DocumentStatus.VALIDATED:
            doc.validated_at = datetime(2025, 12, 19, 16, 0)
            doc.validated_by = compliance_user.id
        db.add(doc)

    db.commit()
    print("Sample data seeded successfully!")


def seed_users(db: Session):
    """Seed database with test users and organizations."""
    print("\nSeeding organizations and test users...")

    # Check if organizations already exist
    existing_org = db.query(Organization).first()
    if not existing_org:
        # Create VIBOTAJ Organization
        vibotaj_org = Organization(
            name="VIBOTAJ Global Nigeria Ltd",
            slug="vibotaj",
            type=OrganizationType.VIBOTAJ,
            status=OrganizationStatus.ACTIVE,
            contact_email="admin@vibotaj.com",
            contact_phone="+234 123 456 7890",
            address={"city": "Lagos", "country": "Nigeria"},
            tax_id="RC123456",
            registration_number="RC123456"
        )
        db.add(vibotaj_org)

        # Create WITATRADE Organization
        witatrade_org = Organization(
            name="WITATRADE GMBH",
            slug="witatrade",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="imports@witatrade.de",
            contact_phone="+49 40 123456",
            address={"city": "Hamburg", "country": "Germany"},
            tax_id="DE123456789",
            registration_number="HRB123456"
        )
        db.add(witatrade_org)

        # Create HAGES Organization (Pilot Customer)
        hages_org = Organization(
            name="HAGES GmbH",
            slug="hages",
            type=OrganizationType.BUYER,
            status=OrganizationStatus.ACTIVE,
            contact_email="info@hages.de",
            contact_phone="+49 4501 123456",
            address={"city": "Bad Schwartau", "country": "Germany"},
            tax_id="DE987654321",
            registration_number="HRB987654"
        )
        db.add(hages_org)
        db.flush()
    else:
        vibotaj_org = db.query(Organization).filter_by(slug="vibotaj").first()
        witatrade_org = db.query(Organization).filter_by(slug="witatrade").first()
        hages_org = db.query(Organization).filter_by(slug="hages").first()

        # Create HAGES if it doesn't exist
        if not hages_org:
            hages_org = Organization(
                name="HAGES GmbH",
                slug="hages",
                type=OrganizationType.BUYER,
                status=OrganizationStatus.ACTIVE,
                contact_email="info@hages.de",
                contact_phone="+49 4501 123456",
                address={"city": "Bad Schwartau", "country": "Germany"},
                tax_id="DE987654321",
                registration_number="HRB987654"
            )
            db.add(hages_org)
            db.flush()

    # Check if users already exist
    existing_user = db.query(User).first()
    force_reseed = os.environ.get("FORCE_RESEED", "").lower() in ("true", "1", "yes")
    if existing_user and not force_reseed:
        print("Users already exist. Skipping user seed. Set FORCE_RESEED=true to override.")
        return vibotaj_org.id, witatrade_org.id if witatrade_org else None
    elif existing_user and force_reseed:
        print("FORCE_RESEED enabled - clearing existing users and memberships...")
        db.query(OrganizationMembership).delete()
        db.query(User).delete()
        db.commit()
        print("Existing users cleared.")

    # Create test users
    users_data = [
        # VIBOTAJ users
        {
            "email": "admin@vibotaj.com",
            "full_name": "System Administrator",
            "password": "tracehub2026",
            "role": UserRole.ADMIN,
            "org": vibotaj_org,
            "org_role": OrgRole.ADMIN
        },
        {
            "email": "compliance@vibotaj.com",
            "full_name": "Compliance Officer",
            "password": "tracehub2026",
            "role": UserRole.COMPLIANCE,
            "org": vibotaj_org,
            "org_role": OrgRole.MANAGER
        },
        {
            "email": "logistic@vibotaj.com",
            "full_name": "Logistics Manager",
            "password": "tracehub2026",
            "role": UserRole.LOGISTICS_AGENT,
            "org": vibotaj_org,
            "org_role": OrgRole.MEMBER
        },
        {
            "email": "supplier@vibotaj.com",
            "full_name": "Origin Supplier",
            "password": "tracehub2026",
            "role": UserRole.SUPPLIER,
            "org": vibotaj_org,
            "org_role": OrgRole.MEMBER
        },
        {
            "email": "viewer@vibotaj.com",
            "full_name": "Audit Viewer",
            "password": "tracehub2026",
            "role": UserRole.VIEWER,
            "org": vibotaj_org,
            "org_role": OrgRole.MEMBER
        },
        # WITATRADE users
        {
            "email": "buyer@witatrade.de",
            "full_name": "Hans Mueller",
            "password": "tracehub2026",
            "role": UserRole.BUYER,
            "org": witatrade_org,
            "org_role": OrgRole.ADMIN
        },
        # HAGES users (Pilot Customer)
        {
            "email": "helge.bischoff@hages.de",
            "full_name": "Helge Bischoff",
            "password": "Hages2026Helge!",
            "role": UserRole.BUYER,
            "org": hages_org,
            "org_role": OrgRole.ADMIN  # Organization owner
        },
        {
            "email": "mats.jarsetz@hages.de",
            "full_name": "Mats Morten Jarsetz",
            "password": "Hages2026Mats!",
            "role": UserRole.BUYER,
            "org": hages_org,
            "org_role": OrgRole.ADMIN
        },
        {
            "email": "eike.pannen@hages.de",
            "full_name": "Eike Pannen",
            "password": "Hages2026Eike!",
            "role": UserRole.BUYER,
            "org": hages_org,
            "org_role": OrgRole.ADMIN
        },
    ]

    for ud in users_data:
        password_hash = get_password_hash(ud["password"])
        print(f"Creating user {ud['email']} with hash prefix: {password_hash[:20]}...")
        user = User(
            email=ud["email"],
            full_name=ud["full_name"],
            hashed_password=password_hash,
            role=ud["role"],
            organization_id=ud["org"].id,
            is_active=True
        )
        db.add(user)
        db.flush()

        # Add membership
        membership = OrganizationMembership(
            user_id=user.id,
            organization_id=ud["org"].id,
            org_role=ud["org_role"],
            status="active"
        )
        db.add(membership)

    db.commit()
    print("Test users and organizations created.")

    # Verify users were created
    user_count = db.query(User).count()
    print(f"Verified: {user_count} users in database after seeding.")
    return vibotaj_org.id, witatrade_org.id


def main():
    """Main entry point."""
    create_tables()

    # Use separate session for users to ensure they're committed independently
    db_users = SessionLocal()
    try:
        # Seed users first and get organization IDs
        vibotaj_id, witatrade_id = seed_users(db_users)
    finally:
        db_users.close()

    # Use separate session for sample data - if this fails, users are still committed
    db_sample = SessionLocal()
    try:
        # Check if shipment data already exists
        existing = db_sample.query(Shipment).first()
        if existing:
            print(f"\nShipment data already exists (shipment {existing.reference}). Skipping shipment seed.")
            return

        seed_sample_data(db_sample, vibotaj_id, witatrade_id)
    except Exception as e:
        print(f"\nWarning: Sample data seeding failed (schema might differ): {e}")
        print("User seeding completed successfully - login should work.")
    finally:
        db_sample.close()

if __name__ == "__main__":
    main()
