#!/usr/bin/env python3
"""Local test script for AI document processing.

Tests the document classification, OCR, and data extraction capabilities
on historic customer documents.

Usage:
    cd tracehub/backend
    python scripts/test_ai_document_processing.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check dependencies
print("=" * 60)
print("AI Document Processing - Local Test")
print("=" * 60)
print()

print("1. Checking Dependencies...")
print("-" * 40)

dependencies = {
    "pymupdf": {"installed": False, "version": None},
    "pytesseract": {"installed": False, "version": None},
    "pdf2image": {"installed": False, "version": None},
    "anthropic": {"installed": False, "version": None},
    "pillow": {"installed": False, "version": None},
}

try:
    import fitz
    dependencies["pymupdf"]["installed"] = True
    dependencies["pymupdf"]["version"] = fitz.version[0]
    print(f"  [OK] PyMuPDF: {fitz.version[0]}")
except ImportError:
    print("  [MISSING] PyMuPDF - PDF processing unavailable")

try:
    import pytesseract
    dependencies["pytesseract"]["installed"] = True
    try:
        ver = pytesseract.get_tesseract_version()
        dependencies["pytesseract"]["version"] = str(ver)
        print(f"  [OK] pytesseract + Tesseract: {ver}")
    except Exception:
        print("  [WARN] pytesseract installed but Tesseract not found in PATH")
except ImportError:
    print("  [MISSING] pytesseract - OCR unavailable")

try:
    import pdf2image
    dependencies["pdf2image"]["installed"] = True
    print(f"  [OK] pdf2image")
except ImportError:
    print("  [MISSING] pdf2image - PDF to image conversion unavailable")

try:
    import anthropic
    dependencies["anthropic"]["installed"] = True
    print(f"  [OK] anthropic")
except ImportError:
    print("  [MISSING] anthropic - AI classification unavailable")

try:
    from PIL import Image
    dependencies["pillow"]["installed"] = True
    print(f"  [OK] Pillow (PIL)")
except ImportError:
    print("  [MISSING] Pillow - Image processing unavailable")

# Check API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    print(f"  [OK] ANTHROPIC_API_KEY set ({api_key[:10]}...)")
else:
    print("  [WARN] ANTHROPIC_API_KEY not set - AI classification will use fallback")

print()

# Import app modules
print("2. Loading TraceHub Modules...")
print("-" * 40)

try:
    from app.services.pdf_processor import pdf_processor, PDF_PROCESSING_AVAILABLE, OCR_AVAILABLE
    print(f"  [OK] pdf_processor (PDF: {PDF_PROCESSING_AVAILABLE}, OCR: {OCR_AVAILABLE})")
except Exception as e:
    print(f"  [ERROR] pdf_processor: {e}")
    pdf_processor = None

try:
    from app.services.document_classifier import document_classifier
    print(f"  [OK] document_classifier (AI: {document_classifier.is_ai_available()})")
except Exception as e:
    print(f"  [ERROR] document_classifier: {e}")
    document_classifier = None

try:
    from app.models.document import DocumentType
    print(f"  [OK] DocumentType enum")
except Exception as e:
    print(f"  [ERROR] DocumentType: {e}")
    DocumentType = None

print()

# Define test directories
UPLOAD_BASE = Path(__file__).parent.parent / "uploads"
CUSTOMER_DIRS = {
    "felix": UPLOAD_BASE / "felix",
    "hages": UPLOAD_BASE / "hages",
    "witatrade": UPLOAD_BASE / "witatrade",
    "beckmann": UPLOAD_BASE / "beckmann",
}

# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".jpeg", ".jpg", ".png"}
SKIP_EXTENSIONS = {".mp4", ".docx", ".xlsx", ".xls", ".zip", ".mov"}


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    name: str
    extension: str
    size_kb: float
    customer: str


@dataclass
class ProcessingResult:
    """Result of processing a document."""
    file_info: FileInfo
    success: bool
    document_type: Optional[str] = None
    confidence: float = 0.0
    detection_method: str = ""
    reference_number: Optional[str] = None
    text_extracted: int = 0
    ocr_used: bool = False
    error: Optional[str] = None
    processing_time_ms: float = 0.0


@dataclass
class TestReport:
    """Complete test report."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_files: int = 0
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    by_customer: Dict[str, Dict] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)
    low_confidence: List[Dict] = field(default_factory=list)
    ocr_processed: int = 0
    results: List[ProcessingResult] = field(default_factory=list)


def scan_directory(base_path: Path, customer: str) -> List[FileInfo]:
    """Scan a directory recursively for files."""
    files = []

    if not base_path.exists():
        print(f"  [WARN] Directory not found: {base_path}")
        return files

    for item in base_path.rglob("*"):
        if item.is_file():
            ext = item.suffix.lower()
            files.append(FileInfo(
                path=item,
                name=item.name,
                extension=ext,
                size_kb=item.stat().st_size / 1024,
                customer=customer
            ))

    return files


def process_document(file_info: FileInfo) -> ProcessingResult:
    """Process a single document."""
    import time
    start = time.time()

    result = ProcessingResult(
        file_info=file_info,
        success=False
    )

    try:
        file_path = str(file_info.path)
        ext = file_info.extension.lower()

        # Handle PDFs
        if ext == ".pdf":
            if not pdf_processor or not pdf_processor.is_available():
                result.error = "PDF processor not available"
                return result

            # Extract text
            pages = pdf_processor.extract_text(file_path, use_ocr_fallback=True)

            if pages:
                full_text = "\n".join(p.text for p in pages)
                result.text_extracted = len(full_text)

                # Check if OCR was likely used (based on extraction method)
                # OCR is used when initial extraction yields < 100 chars
                initial_chars = sum(p.char_count for p in pages)
                if initial_chars < 100 and result.text_extracted > 100:
                    result.ocr_used = True

                # Classify document
                if document_classifier:
                    classification = document_classifier.classify(full_text, prefer_ai=True)
                    result.document_type = classification.document_type.value
                    result.confidence = classification.confidence
                    result.detection_method = classification.detected_fields.get("detection_method", "unknown")
                    result.reference_number = classification.reference_number

                result.success = True
            else:
                result.error = "No text extracted"

        # Handle images
        elif ext in {".jpeg", ".jpg", ".png"}:
            if not OCR_AVAILABLE:
                result.error = "OCR not available for image processing"
                return result

            # Use pytesseract directly on image
            try:
                from PIL import Image
                import pytesseract

                image = Image.open(file_path)
                text = pytesseract.image_to_string(image, lang="eng")
                result.text_extracted = len(text)
                result.ocr_used = True

                if text.strip() and document_classifier:
                    classification = document_classifier.classify(text, prefer_ai=True)
                    result.document_type = classification.document_type.value
                    result.confidence = classification.confidence
                    result.detection_method = classification.detected_fields.get("detection_method", "unknown")
                    result.reference_number = classification.reference_number
                    result.success = True
                elif not text.strip():
                    result.error = "No text extracted from image"
                else:
                    result.success = True
                    result.document_type = "unknown"

            except Exception as e:
                result.error = f"Image processing error: {e}"

        else:
            result.error = f"Unsupported file type: {ext}"

    except Exception as e:
        result.error = str(e)

    result.processing_time_ms = (time.time() - start) * 1000
    return result


def run_tests(limit_per_customer: int = 10) -> TestReport:
    """Run tests on customer documents."""
    report = TestReport()

    print("3. Scanning Customer Directories...")
    print("-" * 40)

    all_files: List[FileInfo] = []

    for customer, path in CUSTOMER_DIRS.items():
        files = scan_directory(path, customer)

        # Categorize files
        supported = [f for f in files if f.extension in SUPPORTED_EXTENSIONS]
        skipped = [f for f in files if f.extension in SKIP_EXTENSIONS]
        other = [f for f in files if f.extension not in SUPPORTED_EXTENSIONS and f.extension not in SKIP_EXTENSIONS]

        print(f"  {customer.upper()}: {len(files)} total files")
        print(f"    - Supported (PDF/images): {len(supported)}")
        print(f"    - Skipped (video/docs): {len(skipped)}")
        if other:
            print(f"    - Other: {len(other)} ({', '.join(set(f.extension for f in other))})")

        report.by_customer[customer] = {
            "total": len(files),
            "supported": len(supported),
            "skipped": len(skipped),
        }

        all_files.extend(supported)
        report.skipped += len(skipped)

    report.total_files = len(all_files) + report.skipped

    print()
    print(f"4. Processing Documents (limit: {limit_per_customer} per customer)...")
    print("-" * 40)

    # Process limited samples from each customer
    for customer in CUSTOMER_DIRS:
        customer_files = [f for f in all_files if f.customer == customer]

        # Prioritize PDFs
        pdfs = [f for f in customer_files if f.extension == ".pdf"]
        images = [f for f in customer_files if f.extension in {".jpeg", ".jpg", ".png"}]

        # Take mix of PDFs and images
        sample = pdfs[:limit_per_customer - 1] + images[:1] if images else pdfs[:limit_per_customer]
        sample = sample[:limit_per_customer]

        print(f"\n  {customer.upper()} ({len(sample)} samples):")

        for file_info in sample:
            result = process_document(file_info)
            report.results.append(result)

            if result.success:
                report.processed += 1

                # Track document types
                if result.document_type:
                    report.by_type[result.document_type] = report.by_type.get(result.document_type, 0) + 1

                # Track low confidence
                if result.confidence < 0.7:
                    report.low_confidence.append({
                        "file": file_info.name,
                        "customer": customer,
                        "type": result.document_type,
                        "confidence": result.confidence
                    })

                # Track OCR usage
                if result.ocr_used:
                    report.ocr_processed += 1

                status = f"OK ({result.document_type}, {result.confidence:.0%})"
                if result.ocr_used:
                    status += " [OCR]"
                print(f"    [OK] {file_info.name[:40]:<40} -> {result.document_type} ({result.confidence:.0%})")
            else:
                report.errors += 1
                print(f"    [ERR] {file_info.name[:40]:<40} -> {result.error}")

        # Update customer stats
        customer_results = [r for r in report.results if r.file_info.customer == customer]
        report.by_customer[customer]["processed"] = len([r for r in customer_results if r.success])
        report.by_customer[customer]["errors"] = len([r for r in customer_results if not r.success])

    return report


def print_report(report: TestReport):
    """Print test report summary."""
    print()
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print()

    print(f"Timestamp: {report.timestamp}")
    print()

    print("Overall Statistics:")
    print(f"  Total files found:    {report.total_files}")
    print(f"  Processed:            {report.processed}")
    print(f"  Skipped (video/docs): {report.skipped}")
    print(f"  Errors:               {report.errors}")
    print(f"  OCR processed:        {report.ocr_processed}")
    print()

    if report.processed > 0:
        accuracy = (report.processed - len(report.low_confidence)) / report.processed * 100
        print(f"  High-confidence rate: {accuracy:.1f}%")

    print()
    print("By Customer:")
    for customer, stats in report.by_customer.items():
        print(f"  {customer.upper()}:")
        print(f"    Total: {stats['total']}, Processed: {stats.get('processed', 0)}, Errors: {stats.get('errors', 0)}")

    print()
    print("Document Types Detected:")
    for doc_type, count in sorted(report.by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {doc_type}: {count}")

    if report.low_confidence:
        print()
        print("Low Confidence Classifications (<70%):")
        for item in report.low_confidence[:10]:
            print(f"  - {item['file']}: {item['type']} ({item['confidence']:.0%})")

    print()
    print("=" * 60)


def main():
    """Main entry point."""
    print()

    # Check if we can proceed
    if not pdf_processor or not pdf_processor.is_available():
        print("ERROR: PDF processing not available. Please install PyMuPDF:")
        print("  pip install pymupdf")
        return 1

    if not document_classifier:
        print("ERROR: Document classifier not available.")
        return 1

    # Run tests
    report = run_tests(limit_per_customer=5)

    # Print report
    print_report(report)

    # Save report to file
    report_path = Path(__file__).parent / "test_results.json"
    report_data = {
        "timestamp": report.timestamp,
        "total_files": report.total_files,
        "processed": report.processed,
        "skipped": report.skipped,
        "errors": report.errors,
        "ocr_processed": report.ocr_processed,
        "by_customer": report.by_customer,
        "by_type": report.by_type,
        "low_confidence": report.low_confidence,
        "results": [
            {
                "file": r.file_info.name,
                "customer": r.file_info.customer,
                "success": r.success,
                "document_type": r.document_type,
                "confidence": r.confidence,
                "detection_method": r.detection_method,
                "reference_number": r.reference_number,
                "text_extracted": r.text_extracted,
                "ocr_used": r.ocr_used,
                "error": r.error,
                "processing_time_ms": r.processing_time_ms
            }
            for r in report.results
        ]
    }

    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"Report saved to: {report_path}")
    print()

    return 0 if report.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
