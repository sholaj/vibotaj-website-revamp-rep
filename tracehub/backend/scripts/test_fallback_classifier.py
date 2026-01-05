#!/usr/bin/env python3
"""Test document classification with keyword fallback."""

import sys
import os

# Add the app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.document_classifier import document_classifier
from app.services.pdf_processor import pdf_processor

# Test documents
TEST_DOCUMENTS = [
    {
        "name": "Bill of Lading",
        "text": """BILL OF LADING
B/L No: MAEU262495038
Shipper: VIBOTAJ GLOBAL VENTURES
Consignee: GERMAN IMPORTS GMBH
Container No: MAEU1234567
Port of Loading: Lagos, Nigeria
Port of Discharge: Hamburg, Germany
Description: Animal Hooves and Horns (HS Code 0506)
Notify Party: XYZ Logistics GmbH
Vessel: MSC EMMA
"""
    },
    {
        "name": "EU TRACES Certificate",
        "text": """EU TRACES CERTIFICATE
COMMON HEALTH ENTRY DOCUMENT (CHED)
Certificate Number: RC1479592
Product: Animal By-Products - Hooves and Horns
Origin: Third Country - Nigeria
Destination: Germany (EU)
Consignment Reference: VBT-2026-001
Animal Health Status: Approved
Import Permit: Valid
"""
    },
    {
        "name": "Veterinary Health Certificate",
        "text": """VETERINARY HEALTH CERTIFICATE
Certificate No: VHC/NIG/2026/0042
Federal Department of Veterinary Services
Nigerian Veterinary Research Institute (NVRI)
Animal By-Products: Hooves and Horns
Species: Bovine
Treatment: Heat-treated
Official Veterinarian: Dr. A. Ibrahim
Date of Inspection: 2026-01-02
"""
    },
    {
        "name": "Certificate of Origin",
        "text": """CERTIFICATE OF ORIGIN
NACCIMA No: COO/LAG/2026/5678
Exporter: VIBOTAJ GLOBAL VENTURES
Country of Origin: Nigeria
Description of Goods: Animal Hooves and Horns
HS Code: 0506.90.00
Chamber of Commerce: Lagos Chamber
Form A Certificate
"""
    },
    {
        "name": "Commercial Invoice",
        "text": """COMMERCIAL INVOICE
Invoice No: VBT-INV-2026-0042
Date: 2026-01-02
Sold To: German Imports GmbH
Bill To: Same as above
Description: Animal Hooves (HS 0506)
Quantity: 20 MT
Unit Price: $850/MT
Total Amount: $17,000.00 USD
Payment Terms: L/C at sight
"""
    },
    {
        "name": "Export Declaration",
        "text": """EXPORT DECLARATION
NXP Form No: NXP/2026/LAG/12345
Nigeria Customs Service
Exporter: VIBOTAJ GLOBAL VENTURES
Export Permit: Valid
HS Code: 0506.90.00
FOB Value: $17,000.00
Country of Destination: Germany
SAD Reference: 2026/EXP/54321
"""
    },
]


def test_keyword_classification():
    """Test keyword-based classification."""
    print("=" * 60)
    print("TESTING KEYWORD-BASED DOCUMENT CLASSIFICATION")
    print("=" * 60)
    print()

    # Get AI status
    status = document_classifier.get_ai_status()
    print(f"AI Available: {status['available']}")
    print(f"AI Status: {status['status']}")
    if status['last_error']:
        print(f"AI Error: {status['last_error']}")
    print(f"Fallback Active: {status['fallback_active']}")
    print()

    all_passed = True
    for doc in TEST_DOCUMENTS:
        print(f"Testing: {doc['name']}")
        print("-" * 40)

        # Test with keyword-only classification
        result = document_classifier.classify(doc['text'], prefer_ai=False)

        print(f"  Detected Type: {result.document_type.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reference: {result.reference_number or 'None'}")
        print(f"  Method: {result.detected_fields.get('detection_method', 'unknown')}")
        print(f"  Reasoning: {result.reasoning[:50]}...")

        # Check if we got a reasonable match
        expected_keywords = {
            "Bill of Lading": "bill_of_lading",
            "EU TRACES Certificate": "eu_traces_certificate",
            "Veterinary Health Certificate": "veterinary_health_certificate",
            "Certificate of Origin": "certificate_of_origin",
            "Commercial Invoice": "commercial_invoice",
            "Export Declaration": "export_declaration",
        }

        expected = expected_keywords.get(doc['name'])
        if expected and result.document_type.value == expected:
            print(f"  Result: PASS")
        else:
            print(f"  Result: FAIL (expected {expected})")
            all_passed = False

        print()

    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED - Check results above")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = test_keyword_classification()
    sys.exit(0 if success else 1)
