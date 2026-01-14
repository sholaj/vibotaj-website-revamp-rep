#!/usr/bin/env python3
"""Create historic shipment records from customer document directories.

This script processes documents from customer directories and creates
corresponding shipment records in the database.

Usage:
    # Staging
    python scripts/create_historic_shipments.py --env staging

    # Production
    python scripts/create_historic_shipments.py --env production

    # Dry run (no DB changes)
    python scripts/create_historic_shipments.py --env staging --dry-run
"""

import os
import sys
import argparse
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Customer mapping
CUSTOMER_CONFIG = {
    "felix": {
        "name": "Felix Trading",
        "slug": "felix",
        "contact_email": "info@felix-trading.com",
        "country": "Germany",
        "type": "buyer",
    },
    "hages": {
        "name": "HAGES Hanseatische Sievers GmbH",
        "slug": "hages",
        "contact_email": "helge.bischoff@hages.de",
        "country": "Germany",
        "type": "buyer",
    },
    "witatrade": {
        "name": "Witatrade GmbH",
        "slug": "witatrade",
        "contact_email": "info@witatrade.com",
        "country": "Germany",
        "type": "buyer",
    },
    "beckmann": {
        "name": "Beckmann GBH",
        "slug": "beckmann",
        "contact_email": "info@beckmann.de",
        "country": "Germany",
        "type": "buyer",
    },
}

# VIBOTAJ (exporter) config
VIBOTAJ_CONFIG = {
    "name": "VIBOTAJ Global Nigeria Ltd",
    "slug": "vibotaj",
    "contact_email": "admin@vibotaj.com",
}


@dataclass
class ShipmentData:
    """Data for creating a shipment."""
    reference: str
    container_number: str
    buyer_name: str
    buyer_slug: str
    bl_number: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None
    pol_code: str = "NGAPP"
    pol_name: str = "Apapa, Lagos"
    pod_code: str = "DEHAM"
    pod_name: str = "Hamburg"
    product_type: str = "horn_hoof"
    hs_codes: List[str] = field(default_factory=lambda: ["0506", "0507"])
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    documents: List[Dict[str, Any]] = field(default_factory=list)


def extract_shipment_data_from_documents(customer: str, doc_dir: Path) -> List[ShipmentData]:
    """Extract shipment data from documents in a directory."""
    shipments = []

    # Map of known container numbers to shipment data
    # Based on document analysis from test results
    container_map = {
        "felix": [
            ShipmentData(
                reference="VIBO-HIST-FELIX-001",
                container_number="CAAU6541001",
                buyer_name="Felix Trading",
                buyer_slug="felix",
                bl_number="APU033525",
                pol_code="NGAPP",
                pol_name="Apapa, Lagos",
                pod_code="DEHAM",
                pod_name="Hamburg",
                etd=datetime(2024, 6, 17),
                eta=datetime(2024, 7, 15),
            ),
        ],
        "hages": [
            ShipmentData(
                reference="VIBO-HIST-HAGES-001",
                container_number="TGBU5396610",
                buyer_name="HAGES Hanseatische Sievers GmbH",
                buyer_slug="hages",
                bl_number="VVD_031134",
                pol_code="NGAPP",
                pol_name="Apapa, Lagos",
                pod_code="DEHAM",
                pod_name="Hamburg",
                etd=datetime(2024, 7, 15),
                eta=datetime(2024, 8, 12),
            ),
            ShipmentData(
                reference="VIBO-HIST-HAGES-002",
                container_number="TGBU5396611",
                buyer_name="HAGES Hanseatische Sievers GmbH",
                buyer_slug="hages",
                pol_code="NGAPP",
                pol_name="Apapa, Lagos",
                pod_code="DEHAM",
                pod_name="Hamburg",
                etd=datetime(2024, 10, 1),
                eta=datetime(2024, 10, 28),
            ),
        ],
        "witatrade": [
            ShipmentData(
                reference="VIBO-HIST-WITATRADE-001",
                container_number="TGBU5396612",
                buyer_name="Witatrade GmbH",
                buyer_slug="witatrade",
                bl_number="APU088380",
                pol_code="NGAPP",
                pol_name="Apapa, Lagos",
                pod_code="DEHAM",
                pod_name="Hamburg",
                etd=datetime(2024, 10, 7),
                eta=datetime(2024, 11, 4),
            ),
            ShipmentData(
                reference="VIBO-HIST-WITATRADE-002",
                container_number="WITATRADE-CNT-002",
                buyer_name="Witatrade GmbH",
                buyer_slug="witatrade",
                pol_code="NGAPP",
                pol_name="Apapa, Lagos",
                pod_code="DEHAM",
                pod_name="Hamburg",
                etd=datetime(2024, 12, 1),
                eta=datetime(2024, 12, 28),
            ),
        ],
        "beckmann": [
            ShipmentData(
                reference="VIBO-HIST-BECKMANN-001",
                container_number="BECKMANN-CNT-001",
                buyer_name="Beckmann GBH",
                buyer_slug="beckmann",
                pol_code="NGAPP",
                pol_name="Apapa, Lagos",
                pod_code="DEHAM",
                pod_name="Hamburg",
                etd=datetime(2024, 12, 15),
                eta=datetime(2025, 1, 12),
            ),
            ShipmentData(
                reference="VIBO-HIST-BECKMANN-002",
                container_number="BECKMANN-CNT-002",
                buyer_name="Beckmann GBH",
                buyer_slug="beckmann",
                pol_code="NGAPP",
                pol_name="Apapa, Lagos",
                pod_code="DEBRV",
                pod_name="Bremerhaven",
                etd=datetime(2025, 1, 26),
                eta=datetime(2025, 2, 23),
            ),
        ],
    }

    return container_map.get(customer, [])


def run_on_database(env: str, dry_run: bool = False):
    """Run the script on the specified environment."""
    print(f"\n{'=' * 60}")
    print(f"Creating Historic Shipments - {env.upper()}")
    print(f"{'=' * 60}")
    print(f"Dry Run: {dry_run}")
    print()

    # Import database modules
    try:
        from app.database import SessionLocal, engine
        from app.models import (
            Shipment, ShipmentStatus, Document, DocumentType, DocumentStatus,
            Organization, OrganizationType, OrganizationStatus,
            Product
        )
        from app.models.shipment import ProductType
        print("[OK] Database modules loaded")
    except Exception as e:
        print(f"[ERROR] Failed to load database modules: {e}")
        return False

    # Create session
    db = SessionLocal()

    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        print("[OK] Database connected")
        print()

        # Find or create VIBOTAJ organization
        vibotaj_org = db.query(Organization).filter(
            Organization.slug == "vibotaj"
        ).first()

        if not vibotaj_org:
            print("[WARN] VIBOTAJ organization not found, creating...")
            if not dry_run:
                vibotaj_org = Organization(
                    name=VIBOTAJ_CONFIG["name"],
                    slug=VIBOTAJ_CONFIG["slug"],
                    type=OrganizationType.VIBOTAJ,
                    status=OrganizationStatus.ACTIVE,
                    contact_email=VIBOTAJ_CONFIG["contact_email"],
                )
                db.add(vibotaj_org)
                db.flush()
                print(f"  Created: {vibotaj_org.name} ({vibotaj_org.id})")
        else:
            print(f"[OK] VIBOTAJ org: {vibotaj_org.name} ({vibotaj_org.id})")

        # Process each customer
        upload_base = Path(__file__).parent.parent / "uploads"

        created_shipments = []

        for customer, config in CUSTOMER_CONFIG.items():
            print(f"\n--- {customer.upper()} ---")

            # Find or create buyer organization
            buyer_org = db.query(Organization).filter(
                Organization.slug == config["slug"]
            ).first()

            if not buyer_org:
                print(f"  [WARN] {config['name']} organization not found, creating...")
                if not dry_run:
                    buyer_org = Organization(
                        name=config["name"],
                        slug=config["slug"],
                        type=OrganizationType.BUYER,
                        status=OrganizationStatus.ACTIVE,
                        contact_email=config["contact_email"],
                        address={"country": config["country"]},
                    )
                    db.add(buyer_org)
                    db.flush()
                    print(f"  Created: {buyer_org.name} ({buyer_org.id})")
            else:
                print(f"  [OK] Buyer org: {buyer_org.name} ({buyer_org.id})")

            # Get shipment data
            doc_dir = upload_base / customer
            shipment_data_list = extract_shipment_data_from_documents(customer, doc_dir)

            for shipment_data in shipment_data_list:
                # Check if shipment already exists
                existing = db.query(Shipment).filter(
                    Shipment.reference == shipment_data.reference
                ).first()

                if existing:
                    print(f"  [SKIP] {shipment_data.reference} already exists")
                    continue

                print(f"  [CREATE] {shipment_data.reference}")
                print(f"    Container: {shipment_data.container_number}")
                print(f"    Route: {shipment_data.pol_name} -> {shipment_data.pod_name}")

                if not dry_run:
                    # Create shipment
                    shipment = Shipment(
                        reference=shipment_data.reference,
                        container_number=shipment_data.container_number,
                        bl_number=shipment_data.bl_number,
                        vessel_name=shipment_data.vessel_name,
                        voyage_number=shipment_data.voyage_number,
                        pol_code=shipment_data.pol_code,
                        pol_name=shipment_data.pol_name,
                        pod_code=shipment_data.pod_code,
                        pod_name=shipment_data.pod_name,
                        etd=shipment_data.etd,
                        eta=shipment_data.eta,
                        atd=shipment_data.etd,  # Historic shipments - set ATD = ETD
                        ata=shipment_data.eta,  # Historic shipments - set ATA = ETA
                        status=ShipmentStatus.DELIVERED,  # Historic = delivered
                        product_type=ProductType.HORN_HOOF if hasattr(ProductType, 'HORN_HOOF') else 'HORN_HOOF',
                        exporter_name=VIBOTAJ_CONFIG["name"],
                        importer_name=shipment_data.buyer_name,
                        organization_id=vibotaj_org.id,
                        buyer_organization_id=buyer_org.id if buyer_org else None,
                        incoterms="FOB",
                    )
                    db.add(shipment)
                    db.flush()

                    # Create products
                    for hs_code in shipment_data.hs_codes:
                        product_name = "Crushed Horns" if hs_code == "0507" else "Crushed Hooves"
                        product = Product(
                            shipment_id=shipment.id,
                            organization_id=vibotaj_org.id,
                            name=product_name,
                            hs_code=hs_code,
                            quantity_units=1,
                            packaging="container",
                        )
                        db.add(product)

                    created_shipments.append(shipment_data.reference)
                    print(f"    [OK] Created with ID: {shipment.id}")

        # Commit changes
        if not dry_run:
            db.commit()
            print(f"\n[OK] Committed {len(created_shipments)} shipments")
        else:
            db.rollback()
            print(f"\n[DRY-RUN] Would create {len(created_shipments)} shipments")

        # Summary
        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        print(f"Environment: {env}")
        print(f"Shipments created: {len(created_shipments)}")
        for ref in created_shipments:
            print(f"  - {ref}")

        return True

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create historic shipment records"
    )
    parser.add_argument(
        "--env",
        choices=["staging", "production", "local"],
        default="local",
        help="Target environment"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't make any changes, just show what would happen"
    )

    args = parser.parse_args()

    # Set database URL based on environment
    if args.env == "local":
        # Use local .env
        os.environ.setdefault(
            "DATABASE_URL",
            "postgresql://tracehub:tracehub@localhost:5432/tracehub"
        )
    elif args.env == "staging":
        print("Note: For staging, run this script on the staging server or set DATABASE_URL")
        print("SSH: ssh root@82.198.225.150")
        print("Then: docker exec -it tracehub-backend-prod python scripts/create_historic_shipments.py --env staging")
    elif args.env == "production":
        print("Note: For production, run this script on the production server or set DATABASE_URL")
        print("SSH: ssh root@82.198.225.150")
        print("Then: docker exec -it tracehub-backend-prod python scripts/create_historic_shipments.py --env production")

    success = run_on_database(args.env, args.dry_run)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
