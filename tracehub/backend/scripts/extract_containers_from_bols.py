#!/usr/bin/env python3
"""Extract container numbers from Bill of Lading documents for existing shipments.

Finds shipments with placeholder container numbers and extracts real container
numbers from their associated BOL documents.

Usage:
    # Dry run - preview changes
    python scripts/extract_containers_from_bols.py --dry-run

    # Apply changes
    python scripts/extract_containers_from_bols.py

    # Target specific environment
    python scripts/extract_containers_from_bols.py --env staging
    python scripts/extract_containers_from_bols.py --env production

    # Process specific shipment
    python scripts/extract_containers_from_bols.py --shipment-id <uuid>
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass, field, asdict
from uuid import UUID

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ShipmentRow(NamedTuple):
    """Row data from shipments table."""
    id: UUID
    reference: str
    container_number: str


class DocumentRow(NamedTuple):
    """Row data from documents table."""
    id: UUID
    name: str
    file_path: Optional[str]
    extracted_container_number: Optional[str]
    extraction_confidence: Optional[float]


@dataclass
class ExtractionResult:
    """Result of container extraction for a shipment."""
    shipment_id: str
    shipment_reference: str
    old_container: str
    new_container: Optional[str]
    confidence: float
    document_name: Optional[str]
    status: str  # 'extracted', 'no_bol', 'no_text', 'not_found', 'error'
    error_message: Optional[str] = None


@dataclass
class BatchReport:
    """Report for batch extraction run."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    dry_run: bool = True
    total_shipments_checked: int = 0
    placeholder_shipments: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    results: List[ExtractionResult] = field(default_factory=list)


def is_placeholder_container(container: str) -> bool:
    """Check if container number is a placeholder."""
    if not container:
        return True
    patterns = ['-CNT-', 'PLACEHOLDER', 'TEST', 'XXXX']
    upper = container.upper()
    return any(p in upper for p in patterns)


def run_extraction(env: str, dry_run: bool = True, shipment_id: Optional[str] = None):
    """Run the container extraction process.

    Uses raw SQL queries to avoid enum mismatch issues between database
    and Python models (e.g., product_type case differences).
    """
    print(f"\n{'=' * 60}")
    print(f"Container Extraction from BOL Documents - {env.upper()}")
    print(f"{'=' * 60}")
    print(f"Dry Run: {dry_run}")
    print()

    # Import database modules
    try:
        from app.database import engine
        from app.services.shipment_data_extractor import ShipmentDataExtractor
        from app.services.pdf_processor import pdf_processor
        from sqlalchemy import text
        print("[OK] Database modules loaded")
    except Exception as e:
        print(f"[ERROR] Failed to load modules: {e}")
        import traceback
        traceback.print_exc()
        return None

    report = BatchReport(dry_run=dry_run)
    extractor = ShipmentDataExtractor()

    try:
        with engine.connect() as conn:
            # Get total shipment count
            total_result = conn.execute(text("SELECT COUNT(*) FROM shipments"))
            report.total_shipments_checked = total_result.scalar()

            # Query shipments with placeholder containers (or specific shipment)
            if shipment_id:
                query = text("""
                    SELECT id, reference, container_number
                    FROM shipments
                    WHERE id = :sid
                """)
                result = conn.execute(query, {"sid": shipment_id})
                print(f"[INFO] Processing specific shipment: {shipment_id}")
            else:
                query = text("""
                    SELECT id, reference, container_number
                    FROM shipments
                    WHERE container_number LIKE '%-CNT-%'
                       OR container_number LIKE '%PLACEHOLDER%'
                       OR container_number LIKE 'TEST%'
                       OR container_number LIKE 'XXXX%'
                """)
                result = conn.execute(query)

            shipments = [ShipmentRow(r.id, r.reference, r.container_number) for r in result]
            report.placeholder_shipments = len(shipments)

            print(f"\n[INFO] Found {len(shipments)} shipments with placeholder containers")
            print()

            for shipment in shipments:
                print(f"--- {shipment.reference} ---")
                print(f"  Current container: {shipment.container_number}")

                extraction_result = ExtractionResult(
                    shipment_id=str(shipment.id),
                    shipment_reference=shipment.reference,
                    old_container=shipment.container_number,
                    new_container=None,
                    confidence=0.0,
                    document_name=None,
                    status='checking'
                )

                # Find BOL documents for this shipment (use uppercase enum value)
                bol_query = text("""
                    SELECT id, name, file_path, extracted_container_number, extraction_confidence
                    FROM documents
                    WHERE shipment_id = :sid AND document_type = 'BILL_OF_LADING'
                """)
                bol_result = conn.execute(bol_query, {"sid": shipment.id})
                bols = [DocumentRow(r.id, r.name, r.file_path,
                                   r.extracted_container_number, r.extraction_confidence)
                       for r in bol_result]

                if not bols:
                    print(f"  [SKIP] No BOL documents found")
                    extraction_result.status = 'no_bol'
                    report.results.append(extraction_result)
                    report.failed_extractions += 1
                    continue

                print(f"  Found {len(bols)} BOL document(s)")

                # Try to extract from each BOL
                extracted = False
                for bol in bols:
                    # Check if already extracted
                    if bol.extracted_container_number:
                        print(f"  [CACHED] Already extracted: {bol.extracted_container_number}")
                        extraction_result.new_container = bol.extracted_container_number
                        extraction_result.confidence = bol.extraction_confidence or 0.0
                        extraction_result.document_name = bol.name
                        extraction_result.status = 'extracted'
                        extracted = True
                        break

                    # Try to extract from file
                    file_path = None
                    if bol.file_path:
                        # file_path may be relative or absolute
                        if bol.file_path.startswith('/'):
                            file_path = Path(bol.file_path)
                        else:
                            # Check uploads directory
                            file_path = Path(__file__).parent.parent / "uploads" / bol.file_path
                            if not file_path.exists():
                                # Try without uploads prefix
                                file_path = Path(__file__).parent.parent / bol.file_path

                    if file_path and file_path.exists() and pdf_processor.is_available():
                        try:
                            pages = pdf_processor.extract_text(str(file_path))
                            if pages:
                                full_text = "\n".join(p.text for p in pages)
                                extraction = extractor.extract_container_with_confidence(full_text)

                                if extraction:
                                    container, confidence = extraction
                                    print(f"  [EXTRACTED] {container} (confidence: {confidence:.0%})")
                                    extraction_result.new_container = container
                                    extraction_result.confidence = confidence
                                    extraction_result.document_name = bol.name
                                    extraction_result.status = 'extracted'
                                    extracted = True

                                    # Update BOL document with extraction
                                    if not dry_run:
                                        update_doc = text("""
                                            UPDATE documents
                                            SET extracted_container_number = :container,
                                                extraction_confidence = :confidence,
                                                updated_at = NOW()
                                            WHERE id = :doc_id
                                        """)
                                        conn.execute(update_doc, {
                                            "container": container,
                                            "confidence": confidence,
                                            "doc_id": bol.id
                                        })
                                    break
                                else:
                                    print(f"  [NOT FOUND] No container number in {bol.name}")
                            else:
                                print(f"  [NO TEXT] Could not extract text from {bol.name}")
                                extraction_result.status = 'no_text'
                        except Exception as e:
                            print(f"  [ERROR] Failed to process {bol.name}: {e}")
                            extraction_result.error_message = str(e)
                            extraction_result.status = 'error'
                    elif file_path:
                        print(f"  [SKIP] File not found: {file_path}")
                    else:
                        print(f"  [SKIP] No file path for document: {bol.name}")

                if not extracted:
                    if extraction_result.status == 'checking':
                        extraction_result.status = 'not_found'
                    print(f"  [RESULT] Could not extract container from BOL")
                    report.failed_extractions += 1
                elif extraction_result.new_container:
                    report.successful_extractions += 1

                    # Update shipment if not dry run and confidence is high enough
                    if not dry_run and extraction_result.confidence >= 0.8:
                        print(f"  [UPDATE] Setting container to {extraction_result.new_container}")
                        update_shipment = text("""
                            UPDATE shipments
                            SET container_number = :container,
                                updated_at = NOW()
                            WHERE id = :sid
                        """)
                        conn.execute(update_shipment, {
                            "container": extraction_result.new_container,
                            "sid": shipment.id
                        })
                    elif not dry_run and extraction_result.confidence < 0.8:
                        print(f"  [SKIP UPDATE] Confidence {extraction_result.confidence:.0%} below 80% threshold")
                    else:
                        print(f"  [DRY-RUN] Would update container to {extraction_result.new_container}")

                report.results.append(extraction_result)
                print()

            # Commit changes if not dry run
            if not dry_run:
                conn.commit()
                print("\n[OK] Changes committed to database")
            else:
                conn.rollback()
                print("\n[DRY-RUN] No changes made to database")

        # Print summary
        print(f"\n{'=' * 60}")
        print("EXTRACTION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Environment: {env}")
        print(f"Dry Run: {dry_run}")
        print(f"Total shipments in database: {report.total_shipments_checked}")
        print(f"Shipments with placeholders: {report.placeholder_shipments}")
        print(f"Successful extractions: {report.successful_extractions}")
        print(f"Failed extractions: {report.failed_extractions}")

        if report.successful_extractions > 0:
            print("\nSuccessful Extractions:")
            for r in report.results:
                if r.status == 'extracted' and r.new_container:
                    print(f"  {r.shipment_reference}: {r.old_container} -> {r.new_container} ({r.confidence:.0%})")

        if report.failed_extractions > 0:
            print("\nFailed Extractions:")
            for r in report.results:
                if r.status != 'extracted':
                    reason = r.status
                    if r.error_message:
                        reason = f"{r.status}: {r.error_message}"
                    print(f"  {r.shipment_reference}: {reason}")

        return report

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract container numbers from BOL documents"
    )
    parser.add_argument(
        "--env",
        choices=["local", "staging", "production"],
        default="local",
        help="Target environment"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--shipment-id",
        type=str,
        help="Process specific shipment by ID"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save report to JSON file"
    )

    args = parser.parse_args()

    # Set database URL based on environment
    if args.env == "local":
        os.environ.setdefault(
            "DATABASE_URL",
            "postgresql://tracehub:tracehub@localhost:5432/tracehub"
        )
    elif args.env in ["staging", "production"]:
        print(f"Note: For {args.env}, run this script inside the Docker container:")
        print(f"  docker exec tracehub-backend{'_staging' if args.env == 'staging' else ''} python scripts/extract_containers_from_bols.py --env {args.env}")
        if "DATABASE_URL" not in os.environ:
            print("Or set DATABASE_URL environment variable")

    report = run_extraction(
        env=args.env,
        dry_run=args.dry_run,
        shipment_id=args.shipment_id
    )

    # Save report if requested
    if report and args.output:
        report_dict = {
            "timestamp": report.timestamp,
            "dry_run": report.dry_run,
            "total_shipments_checked": report.total_shipments_checked,
            "placeholder_shipments": report.placeholder_shipments,
            "successful_extractions": report.successful_extractions,
            "failed_extractions": report.failed_extractions,
            "results": [asdict(r) for r in report.results]
        }
        with open(args.output, "w") as f:
            json.dump(report_dict, f, indent=2)
        print(f"\nReport saved to: {args.output}")

    return 0 if report else 1


if __name__ == "__main__":
    sys.exit(main())
