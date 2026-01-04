#!/usr/bin/env python3
"""Simple standalone test for keyword-based document classification."""

import re
from typing import List, Tuple, Optional

# Document type keywords (copied from pdf_processor.py)
DOCUMENT_KEYWORDS = {
    "bill_of_lading": [
        'bill of lading', 'b/l', 'shipper', 'consignee', 'notify party',
        'port of loading', 'port of discharge', 'ocean bill', 'carrier'
    ],
    "certificate_of_origin": [
        'certificate of origin', 'country of origin', 'naccima',
        'chamber of commerce', 'preferential origin', 'form a'
    ],
    "phytosanitary_certificate": [
        'phytosanitary', 'plant health', 'plant protection',
        'plant quarantine', 'fao', 'ippc'
    ],
    "fumigation_certificate": [
        'fumigation', 'fumigated', 'methyl bromide', 'pest control',
        'treatment certificate'
    ],
    "sanitary_certificate": [
        'veterinary', 'health certificate', 'sanitary', 'animal health',
        'official veterinarian', 'chapter 18', 'eu health'
    ],
    "commercial_invoice": [
        'commercial invoice', 'invoice', 'pro forma', 'sold to',
        'bill to', 'unit price', 'total amount'
    ],
    "packing_list": [
        'packing list', 'packing specification', 'net weight',
        'gross weight', 'package', 'cartons', 'pallets'
    ],
    "quality_certificate": [
        'quality certificate', 'inspection certificate', 'grade',
        'moisture content', 'specification', 'test report'
    ],
    "insurance_certificate": [
        'insurance', 'insured', 'coverage', 'marine insurance',
        'cargo insurance', 'policy'
    ],
    "customs_declaration": [
        'customs', 'export declaration', 'import declaration',
        'customs declaration', 'hs code', 'tariff'
    ],
    "contract": [
        'contract', 'agreement', 'terms and conditions', 'buyer',
        'seller', 'purchase order'
    ],
    "eudr_due_diligence": [
        'eudr', 'due diligence', 'deforestation', 'geolocation',
        'traceability', 'deforestation-free'
    ],
    # Horn & Hoof specific documents (HS 0506/0507)
    "eu_traces_certificate": [
        'traces', 'ched', 'common health entry document', 'eu traces',
        'animal products', 'third country', 'import permit', 'rc1479592'
    ],
    "veterinary_health_certificate": [
        'veterinary health', 'animal health certificate', 'veterinary certificate',
        'nvri', 'nigerian veterinary', 'federal department of veterinary',
        'official veterinarian', 'hooves', 'horns', 'animal by-products'
    ],
    "export_declaration": [
        'export declaration', 'nxp', 'customs export', 'single administrative document',
        'sad', 'export permit', 'export license', 'nigeria customs'
    ],
}


def detect_document_type(text: str) -> List[Tuple[str, float]]:
    """Detect document type based on keyword matching."""
    text_lower = text.lower()
    scores = {}

    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            confidence = min(matches / len(keywords), 1.0)
            if matches >= 3:
                confidence = min(confidence + 0.2, 1.0)
            scores[doc_type] = confidence

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# Test documents
TEST_DOCUMENTS = [
    ("Bill of Lading", """BILL OF LADING
B/L No: MAEU262495038
Shipper: VIBOTAJ GLOBAL VENTURES
Consignee: GERMAN IMPORTS GMBH
Port of Loading: Lagos, Nigeria
Port of Discharge: Hamburg, Germany""", "bill_of_lading"),

    ("EU TRACES Certificate", """EU TRACES CERTIFICATE
COMMON HEALTH ENTRY DOCUMENT (CHED)
Certificate Number: RC1479592
Product: Animal By-Products - Hooves and Horns
Origin: Third Country - Nigeria""", "eu_traces_certificate"),

    ("Veterinary Health Certificate", """VETERINARY HEALTH CERTIFICATE
Nigerian Veterinary Research Institute (NVRI)
Animal By-Products: Hooves and Horns
Animal Health Certificate
Official Veterinarian: Dr. A. Ibrahim""", "veterinary_health_certificate"),

    ("Certificate of Origin", """CERTIFICATE OF ORIGIN
NACCIMA No: COO/LAG/2026/5678
Country of Origin: Nigeria
Chamber of Commerce: Lagos Chamber""", "certificate_of_origin"),

    ("Commercial Invoice", """COMMERCIAL INVOICE
Invoice No: VBT-INV-2026-0042
Sold To: German Imports GmbH
Unit Price: $850/MT
Total Amount: $17,000.00 USD""", "commercial_invoice"),

    ("Export Declaration", """EXPORT DECLARATION
NXP Form No: NXP/2026/LAG/12345
Nigeria Customs Service
Export Permit: Valid
SAD Reference: 2026/EXP/54321""", "export_declaration"),
]


def main():
    print("=" * 60)
    print("KEYWORD-BASED DOCUMENT CLASSIFICATION TEST")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for name, text, expected in TEST_DOCUMENTS:
        print(f"Testing: {name}")
        print("-" * 40)

        results = detect_document_type(text)

        if results:
            detected, confidence = results[0]
            print(f"  Detected: {detected}")
            print(f"  Confidence: {confidence:.2f}")

            if detected == expected:
                print(f"  Result: PASS")
                passed += 1
            else:
                print(f"  Result: FAIL (expected {expected})")
                failed += 1
        else:
            print(f"  Detected: None")
            print(f"  Result: FAIL (expected {expected})")
            failed += 1

        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED!")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
