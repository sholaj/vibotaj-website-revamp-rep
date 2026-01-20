# TraceHub Compliance Engine Specification

> The authoritative reference for document compliance, validation, and EUDR requirements

**Version:** 2.0
**Created:** 2026-01-20
**Status:** Active

---

## Executive Summary

The Compliance Engine is TraceHub's core differentiator. It ensures that every shipment has the correct documents, validates their content, and provides audit-ready compliance proof. This specification defines:

1. **Compliance Matrix** — Required documents per product type
2. **Document Schemas** — Structured data extraction
3. **Bill of Lading Schema** — BoL parsing specification
4. **OCR Processing** — Text extraction pipeline
5. **Validation Rules** — Cross-document consistency checks
6. **EUDR Compliance** — Deforestation regulation handling

---

## 1. Compliance Matrix

### Product Types & HS Codes

| Product Type | HS Code | EUDR Status | Notes |
|--------------|---------|-------------|-------|
| **Horn & Hoof** | 0506, 0507 | ❌ NOT EUDR | Animal bones, horns, hooves |
| **Sweet Potato** | 0714 | ❌ NOT EUDR | Pellets for animal feed |
| **Hibiscus** | 0902 | ❌ NOT EUDR | Dried flowers |
| **Dried Ginger** | 0910 | ❌ NOT EUDR | Spices |
| **Cocoa Beans** | 1801 | ✅ EUDR | Future support |
| **Coffee** | 0901 | ✅ EUDR | Future support |
| **Palm Oil** | 1511 | ✅ EUDR | Future support |
| **Rubber** | 4001 | ✅ EUDR | Future support |
| **Soya** | 1201 | ✅ EUDR | Future support |

### ⚠️ CRITICAL: Horn & Hoof Rules

**Horn & Hoof products (HS 0506, 0507) are NOT subject to EUDR.**

NEVER add to Horn & Hoof shipments:
- ❌ Geolocation coordinates
- ❌ Deforestation statements
- ❌ EUDR risk scores
- ❌ Production plot identifiers

### Required Documents by Product Type

#### Horn & Hoof (HS 0506, 0507)

| Document | Code | Required | Notes |
|----------|------|----------|-------|
| Bill of Lading | `bill_of_lading` | ✅ | Source of truth for shipment |
| Commercial Invoice | `commercial_invoice` | ✅ | Must match BoL quantities |
| Packing List | `packing_list` | ✅ | Container-level breakdown |
| Certificate of Origin | `certificate_of_origin` | ✅ | Must state Nigeria |
| EU TRACES Certificate | `eu_traces` | ✅ | Must reference RC1479592 |
| Veterinary Health Certificate | `veterinary_health_certificate` | ✅ | Nigerian authority |
| Export Declaration | `export_declaration` | ✅ | Customs declaration |
| Fumigation Certificate | `fumigation_certificate` | ⚡ Conditional | If buyer requires |

#### Plant Products (HS 0714, 0902, 0910)

| Document | Code | Required | Notes |
|----------|------|----------|-------|
| Bill of Lading | `bill_of_lading` | ✅ | Source of truth |
| Commercial Invoice | `commercial_invoice` | ✅ | |
| Packing List | `packing_list` | ✅ | |
| Certificate of Origin | `certificate_of_origin` | ✅ | |
| Phytosanitary Certificate | `phytosanitary_certificate` | ✅ | Plant health cert |
| Export Declaration | `export_declaration` | ✅ | |
| Quality Certificate | `quality_certificate` | ⚡ Conditional | If buyer requires |

#### EUDR Products (HS 1801, 0901, 1511, 4001, 1201)

| Document | Code | Required | Notes |
|----------|------|----------|-------|
| All standard documents | — | ✅ | Same as plant products |
| EUDR Due Diligence Statement | `eudr_due_diligence` | ✅ | Auto-generated |
| Geolocation Data | `geolocation_data` | ✅ | Farm/plot coordinates |
| Deforestation Declaration | `deforestation_declaration` | ✅ | Post-2020 compliance |

### Document Requirement Lookup

```typescript
// TypeScript interface for document requirements
interface DocumentRequirement {
  document_type: DocumentType;
  required: boolean;
  conditional_on?: string;  // e.g., "buyer_requires_fumigation"
  validation_rules: string[];
}

interface ProductTypeRequirements {
  product_type: ProductType;
  hs_codes: string[];
  eudr_applicable: boolean;
  documents: DocumentRequirement[];
}

// Example: Horn & Hoof
const HORN_HOOF_REQUIREMENTS: ProductTypeRequirements = {
  product_type: "horn_hoof",
  hs_codes: ["0506", "0507"],
  eudr_applicable: false,
  documents: [
    { document_type: "bill_of_lading", required: true, validation_rules: ["BOL_*"] },
    { document_type: "commercial_invoice", required: true, validation_rules: ["INV_*"] },
    { document_type: "packing_list", required: true, validation_rules: ["PKL_*"] },
    { document_type: "certificate_of_origin", required: true, validation_rules: ["COO_*"] },
    { document_type: "eu_traces", required: true, validation_rules: ["TRACES_*"] },
    { document_type: "veterinary_health_certificate", required: true, validation_rules: ["VET_*"] },
    { document_type: "export_declaration", required: true, validation_rules: ["EXP_*"] },
    {
      document_type: "fumigation_certificate",
      required: false,
      conditional_on: "buyer_requires_fumigation",
      validation_rules: ["FUM_*"]
    },
  ]
};
```

---

## 2. Document Schemas

### Base Document Schema

```typescript
// All documents inherit from this base
interface BaseDocumentData {
  document_type: DocumentType;
  reference_number: string | null;
  issue_date: string | null;  // ISO 8601
  expiry_date: string | null;
  issuer: string | null;
  extraction_confidence: number;  // 0.0 - 1.0
  raw_text: string;
  extracted_at: string;  // ISO 8601 timestamp
}
```

### Bill of Lading Schema

```typescript
interface BillOfLadingData extends BaseDocumentData {
  document_type: "bill_of_lading";

  // Identification
  bol_number: string;
  booking_number: string | null;

  // Parties
  shipper: PartyInfo;
  consignee: PartyInfo;
  notify_party: PartyInfo | null;

  // Vessel & Voyage
  vessel_name: string | null;
  voyage_number: string | null;
  flag_state: string | null;

  // Ports
  port_of_loading: PortInfo;
  port_of_discharge: PortInfo;
  place_of_delivery: string | null;

  // Containers
  containers: ContainerInfo[];

  // Cargo
  cargo_description: string;
  hs_codes: string[];
  package_count: number | null;
  package_type: string | null;

  // Weights & Measures
  gross_weight_kg: number | null;
  net_weight_kg: number | null;
  volume_cbm: number | null;

  // Dates
  shipped_on_board_date: string | null;
  etd: string | null;  // Estimated Time of Departure
  eta: string | null;  // Estimated Time of Arrival

  // Metadata
  shipping_line: string | null;
  freight_terms: "PREPAID" | "COLLECT" | null;
  number_of_originals: number | null;
}

interface PartyInfo {
  name: string;
  address: string | null;
  country: string | null;
  country_code: string | null;  // ISO 3166-1 alpha-2
}

interface PortInfo {
  name: string;
  code: string | null;  // UN/LOCODE
  country: string | null;
  country_code: string | null;
}

interface ContainerInfo {
  number: string;  // ISO 6346 format: XXXX1234567
  seal_number: string | null;
  type: string | null;  // e.g., "40HC", "20GP"
  size_ft: number | null;  // 20 or 40
  tare_weight_kg: number | null;
  gross_weight_kg: number | null;
}
```

### Commercial Invoice Schema

```typescript
interface CommercialInvoiceData extends BaseDocumentData {
  document_type: "commercial_invoice";

  // Identification
  invoice_number: string;
  invoice_date: string;

  // Parties
  seller: PartyInfo & {
    tax_id: string | null;
    bank_details: BankDetails | null;
  };
  buyer: PartyInfo & {
    tax_id: string | null;
  };

  // References
  purchase_order_number: string | null;
  bol_reference: string | null;
  contract_number: string | null;

  // Line Items
  line_items: InvoiceLineItem[];

  // Totals
  subtotal: MoneyAmount;
  freight_charges: MoneyAmount | null;
  insurance_charges: MoneyAmount | null;
  other_charges: MoneyAmount | null;
  total_amount: MoneyAmount;

  // Terms
  payment_terms: string | null;
  incoterms: string | null;  // e.g., "FOB Lagos"
  country_of_origin: string | null;
}

interface InvoiceLineItem {
  description: string;
  hs_code: string | null;
  quantity: number;
  unit: string;  // e.g., "KG", "MT", "PCS"
  unit_price: MoneyAmount;
  total_price: MoneyAmount;
}

interface MoneyAmount {
  amount: number;
  currency: string;  // ISO 4217
}

interface BankDetails {
  bank_name: string;
  account_number: string | null;
  swift_code: string | null;
  iban: string | null;
}
```

### Packing List Schema

```typescript
interface PackingListData extends BaseDocumentData {
  document_type: "packing_list";

  // Identification
  packing_list_number: string | null;
  date: string;

  // References
  invoice_reference: string | null;
  bol_reference: string | null;

  // Parties
  shipper: PartyInfo;
  consignee: PartyInfo;

  // Containers
  containers: PackingContainer[];

  // Totals
  total_packages: number;
  total_gross_weight_kg: number;
  total_net_weight_kg: number | null;
  total_volume_cbm: number | null;
}

interface PackingContainer {
  container_number: string;
  seal_number: string | null;
  items: PackingItem[];
  gross_weight_kg: number;
  net_weight_kg: number | null;
  package_count: number;
}

interface PackingItem {
  description: string;
  hs_code: string | null;
  quantity: number;
  unit: string;
  gross_weight_kg: number;
  net_weight_kg: number | null;
  package_type: string | null;
  marks_and_numbers: string | null;
}
```

### Certificate of Origin Schema

```typescript
interface CertificateOfOriginData extends BaseDocumentData {
  document_type: "certificate_of_origin";

  // Identification
  certificate_number: string;
  issue_date: string;

  // Origin
  country_of_origin: string;
  country_of_origin_code: string;  // ISO 3166-1 alpha-2

  // Parties
  exporter: PartyInfo;
  importer: PartyInfo;

  // Goods
  goods_description: string;
  hs_codes: string[];
  quantity: number | null;
  unit: string | null;
  gross_weight_kg: number | null;

  // Certification
  certifying_authority: string;
  authorized_signatory: string | null;
  stamp_present: boolean;

  // References
  invoice_reference: string | null;
  transport_details: string | null;
}
```

### Veterinary Health Certificate Schema

```typescript
interface VeterinaryHealthCertificateData extends BaseDocumentData {
  document_type: "veterinary_health_certificate";

  // Identification
  certificate_number: string;
  issue_date: string;
  expiry_date: string | null;

  // EU TRACES Integration
  traces_reference: string | null;  // Must contain RC1479592 for VIBOTAJ
  intra_reference: string | null;

  // Authority
  issuing_authority: string;
  issuing_country: string;
  veterinary_officer: string | null;
  official_stamp_present: boolean;

  // Parties
  exporter: PartyInfo & {
    establishment_number: string | null;
  };
  consignee: PartyInfo;
  destination_country: string;

  // Animals/Products
  species: string;
  product_type: string;
  quantity: number;
  unit: string;

  // Health Attestations
  health_attestations: HealthAttestation[];
  treatment_details: string | null;

  // Transport
  means_of_transport: string | null;
  container_numbers: string[];
  seal_numbers: string[];
}

interface HealthAttestation {
  statement: string;
  attested: boolean;
}
```

### EU TRACES Certificate Schema

```typescript
interface EuTracesCertificateData extends BaseDocumentData {
  document_type: "eu_traces";

  // Identification
  traces_reference: string;  // e.g., "INTRA.XX.2026.0001234"
  certificate_number: string;

  // VIBOTAJ Registration
  operator_reference: string;  // Must be RC1479592

  // Validity
  issue_date: string;
  validity_start: string;
  validity_end: string;

  // Parties
  consignor: PartyInfo & {
    traces_operator_id: string | null;
  };
  consignee: PartyInfo & {
    traces_operator_id: string | null;
  };

  // Commodities
  commodities: TracesCommodity[];

  // Transport
  means_of_transport: string;
  expected_arrival_date: string | null;
  border_crossing_point: string | null;

  // Status
  certificate_status: "DRAFT" | "VALIDATED" | "CANCELLED";
}

interface TracesCommodity {
  cn_code: string;  // Combined Nomenclature code
  description: string;
  quantity: number;
  unit: string;
  country_of_origin: string;
}
```

### Phytosanitary Certificate Schema

```typescript
interface PhytosanitaryCertificateData extends BaseDocumentData {
  document_type: "phytosanitary_certificate";

  // Identification
  certificate_number: string;
  issue_date: string;

  // Authority
  issuing_authority: string;  // e.g., "Nigeria Plant Quarantine Service"
  issuing_country: string;
  inspector_name: string | null;

  // Parties
  exporter: PartyInfo;
  consignee: PartyInfo;

  // Plants/Products
  botanical_name: string | null;
  common_name: string;
  plant_parts: string | null;  // e.g., "dried roots", "seeds"
  quantity: number;
  unit: string;

  // Origin & Destination
  place_of_origin: string;
  declared_point_of_entry: string | null;
  destination_country: string;

  // Treatment
  treatment_type: string | null;  // e.g., "Fumigation", "Heat treatment"
  treatment_chemical: string | null;
  treatment_date: string | null;
  treatment_duration: string | null;

  // Declarations
  additional_declarations: string[];
  phytosanitary_statement: string;
}
```

### Fumigation Certificate Schema

```typescript
interface FumigationCertificateData extends BaseDocumentData {
  document_type: "fumigation_certificate";

  // Identification
  certificate_number: string;
  issue_date: string;

  // Treatment Provider
  company_name: string;
  company_registration: string | null;
  license_number: string | null;

  // Treatment Details
  treatment_date: string;
  treatment_location: string;

  // Method
  fumigant_used: string;  // e.g., "Methyl Bromide", "Phosphine"
  dosage: string;  // e.g., "48g/m³"
  exposure_time: string;  // e.g., "24 hours"
  temperature: string | null;

  // Target
  containers: string[];
  commodity_treated: string;
  quantity_treated: number;
  unit: string;

  // Certification
  certified_by: string;
  certification_standard: string | null;  // e.g., "ISPM 15"
}
```

---

## 3. Bill of Lading Parsing Specification

### Parser Architecture

```
PDF Upload
    ↓
Text Extraction (PyMuPDF)
    ↓
[If < 100 chars] → OCR Fallback (Azure Form Recognizer)
    ↓
Shipping Line Detection
    ↓
Field Extraction (Regex Patterns)
    ↓
Confidence Scoring
    ↓
CanonicalBoL Object
    ↓
Validation Rules
```

### Supported Shipping Lines

| Shipping Line | SCAC Code | BoL Pattern |
|---------------|-----------|-------------|
| MSC | MSCU | `MSC[A-Z]{2}[0-9]{6,}` |
| Maersk | MAEU | `[0-9]{9}` |
| Hapag-Lloyd | HLCU | `HLXU[0-9]{8,}` |
| CMA CGM | CMDU | `[A-Z]{3}[0-9]{7,}` |
| Evergreen | EGLV | `EISU[0-9]{10}` |
| COSCO | COSU | `[0-9]{10}` |
| ONE | ONEY | `ONEY[0-9]{10}` |

### Container Number Validation

**ISO 6346 Format:** `XXXX1234567`
- First 3 characters: Owner code (letters)
- Fourth character: Equipment category (U, J, Z)
- Next 6 characters: Serial number (digits)
- Last character: Check digit (digit)

```typescript
function validateContainerNumber(container: string): boolean {
  const cleaned = container.replace(/[\s-]/g, '').toUpperCase();
  const pattern = /^[A-Z]{4}[0-9]{7}$/;

  if (!pattern.test(cleaned)) return false;

  // Calculate check digit
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let sum = 0;

  for (let i = 0; i < 10; i++) {
    const char = cleaned[i];
    let value: number;

    if (i < 4) {
      value = alphabet.indexOf(char) + 10;
    } else {
      value = parseInt(char);
    }

    sum += value * Math.pow(2, i);
  }

  const checkDigit = sum % 11 % 10;
  return checkDigit === parseInt(cleaned[10]);
}
```

### Field Extraction Patterns

```typescript
const BOL_PATTERNS = {
  bol_number: [
    /B\/L\s*(?:No\.?|Number|#)?\s*[:.]?\s*([A-Z0-9-]{6,})/i,
    /Bill\s+of\s+Lading\s*(?:No\.?|#)?\s*[:.]?\s*([A-Z0-9-]{6,})/i,
    /BILL\s+NUMBER\s*[:.]?\s*([A-Z0-9-]{6,})/i,
    /BL\s*[:.]?\s*([A-Z0-9-]{6,})/i,
  ],

  shipper: [
    /Shipper[:\s]*\n?([\s\S]*?)(?=Consignee|Notify|$)/i,
    /Exporter[:\s]*\n?([\s\S]*?)(?=Consignee|Importer|$)/i,
  ],

  consignee: [
    /Consignee[:\s]*\n?([\s\S]*?)(?=Notify|Port|$)/i,
    /Importer[:\s]*\n?([\s\S]*?)(?=Notify|Port|$)/i,
  ],

  vessel: [
    /(?:M\/V|MV|Vessel)\s*[:.]?\s*([A-Z][A-Z\s]+)/i,
    /(?:Ocean\s+Vessel|Carrier)\s*[:.]?\s*([A-Z][A-Z\s]+)/i,
  ],

  voyage: [
    /(?:Voyage|Voy)\s*(?:No\.?)?\s*[:.]?\s*([A-Z0-9-]+)/i,
  ],

  port_of_loading: [
    /(?:Port\s+of\s+Loading|POL|Load\s+Port)\s*[:.]?\s*([A-Z\s,]+)/i,
    /(?:From|Origin)\s*[:.]?\s*([A-Z]+(?:\s+[A-Z]+)*)/i,
  ],

  port_of_discharge: [
    /(?:Port\s+of\s+Discharge|POD|Discharge\s+Port)\s*[:.]?\s*([A-Z\s,]+)/i,
    /(?:To|Destination)\s*[:.]?\s*([A-Z]+(?:\s+[A-Z]+)*)/i,
  ],

  container: [
    /([A-Z]{4}\s*[0-9]{7})/g,  // ISO 6346 format
  ],

  gross_weight: [
    /(?:Gross\s+Weight|GW)\s*[:.]?\s*([\d,]+\.?\d*)\s*(?:KG|KGS|MT)/i,
  ],

  net_weight: [
    /(?:Net\s+Weight|NW)\s*[:.]?\s*([\d,]+\.?\d*)\s*(?:KG|KGS|MT)/i,
  ],
};
```

### Confidence Scoring

```typescript
interface ConfidenceWeights {
  bol_number: 0.15;
  shipper: 0.15;
  consignee: 0.15;
  container: 0.15;
  vessel: 0.10;
  port_of_loading: 0.10;
  port_of_discharge: 0.10;
  cargo_description: 0.10;
}

function calculateConfidence(extracted: Partial<BillOfLadingData>): number {
  let score = 0;

  if (extracted.bol_number && extracted.bol_number !== "UNKNOWN") score += 0.15;
  if (extracted.shipper?.name && extracted.shipper.name !== "Unknown Shipper") score += 0.15;
  if (extracted.consignee?.name && extracted.consignee.name !== "Unknown Consignee") score += 0.15;
  if (extracted.containers?.length > 0) score += 0.15;
  if (extracted.vessel_name) score += 0.10;
  if (extracted.port_of_loading?.code) score += 0.10;
  if (extracted.port_of_discharge?.code) score += 0.10;
  if (extracted.cargo_description) score += 0.10;

  return Math.round(score * 100) / 100;
}
```

---

## 4. OCR Processing Pipeline

### Architecture (Azure-Native)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Upload                               │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Azure Blob Storage                               │
│                 (documents container)                            │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Azure Functions                                  │
│                 (Blob Trigger)                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Text Extraction (PyMuPDF)                                   │
│     ↓                                                            │
│  2. If < 100 chars → Azure Form Recognizer (OCR)                │
│     ↓                                                            │
│  3. Document Type Detection                                      │
│     ↓                                                            │
│  4. Field Extraction                                             │
│     ↓                                                            │
│  5. Schema Validation                                            │
│     ↓                                                            │
│  6. Store in Database + Update Document Record                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Azure Form Recognizer Integration

```python
# backend/app/services/ocr_processor.py
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

class AzureOCRProcessor:
    """
    Azure Form Recognizer-based OCR processor.
    Replaces Tesseract with enterprise-grade OCR.
    """

    def __init__(self):
        self.client = DocumentAnalysisClient(
            endpoint=settings.FORM_RECOGNIZER_ENDPOINT,
            credential=AzureKeyCredential(settings.FORM_RECOGNIZER_KEY)
        )

    async def extract_text(self, file_content: bytes) -> OCRResult:
        """Extract text from PDF using Form Recognizer."""

        # Use prebuilt-read model for general text extraction
        poller = await self.client.begin_analyze_document(
            "prebuilt-read",
            file_content
        )
        result = await poller.result()

        pages = []
        for page in result.pages:
            lines = [line.content for line in page.lines]
            pages.append(PageContent(
                page_number=page.page_number,
                text="\n".join(lines),
                confidence=self._calculate_page_confidence(page)
            ))

        return OCRResult(
            pages=pages,
            full_text="\n\n".join(p.text for p in pages),
            confidence=sum(p.confidence for p in pages) / len(pages)
        )

    async def extract_invoice(self, file_content: bytes) -> dict:
        """Use prebuilt invoice model for commercial invoices."""

        poller = await self.client.begin_analyze_document(
            "prebuilt-invoice",
            file_content
        )
        result = await poller.result()

        if result.documents:
            doc = result.documents[0]
            return {
                "invoice_number": self._get_field(doc, "InvoiceId"),
                "invoice_date": self._get_field(doc, "InvoiceDate"),
                "vendor_name": self._get_field(doc, "VendorName"),
                "vendor_address": self._get_field(doc, "VendorAddress"),
                "customer_name": self._get_field(doc, "CustomerName"),
                "customer_address": self._get_field(doc, "CustomerAddress"),
                "subtotal": self._get_field(doc, "SubTotal"),
                "total": self._get_field(doc, "InvoiceTotal"),
                "items": self._extract_items(doc),
                "confidence": doc.confidence
            }

        return None

    def _get_field(self, doc, field_name: str):
        field = doc.fields.get(field_name)
        return field.value if field else None

    def _extract_items(self, doc) -> list:
        items_field = doc.fields.get("Items")
        if not items_field:
            return []

        return [
            {
                "description": self._get_field(item, "Description"),
                "quantity": self._get_field(item, "Quantity"),
                "unit_price": self._get_field(item, "UnitPrice"),
                "amount": self._get_field(item, "Amount")
            }
            for item in items_field.value
        ]
```

### Document Type Detection

```python
# backend/app/services/document_classifier.py

DOCUMENT_KEYWORDS = {
    "bill_of_lading": {
        "keywords": [
            "bill of lading", "b/l", "shipped on board",
            "ocean bill", "sea waybill", "booking number"
        ],
        "negative": ["airway bill", "air waybill"],
        "weight": 1.0
    },
    "commercial_invoice": {
        "keywords": [
            "commercial invoice", "invoice", "proforma",
            "sold to", "bill to", "total amount"
        ],
        "negative": ["packing list"],
        "weight": 0.9
    },
    "packing_list": {
        "keywords": [
            "packing list", "packing slip", "package list",
            "marks and numbers", "gross weight", "net weight"
        ],
        "negative": ["commercial invoice"],
        "weight": 0.9
    },
    "certificate_of_origin": {
        "keywords": [
            "certificate of origin", "origin certificate",
            "country of origin", "form a", "eur.1"
        ],
        "negative": [],
        "weight": 0.9
    },
    "veterinary_health_certificate": {
        "keywords": [
            "veterinary health", "health certificate", "animal health",
            "sanitary certificate", "veterinary certificate"
        ],
        "negative": ["phytosanitary"],
        "weight": 1.0  # High weight - specific document
    },
    "eu_traces": {
        "keywords": [
            "traces", "intra", "health certificate",
            "official veterinarian", "rc1479592"
        ],
        "negative": [],
        "weight": 1.0
    },
    "phytosanitary_certificate": {
        "keywords": [
            "phytosanitary", "plant health", "plant quarantine",
            "plant protection", "pest free"
        ],
        "negative": ["veterinary"],
        "weight": 1.0
    },
    "fumigation_certificate": {
        "keywords": [
            "fumigation", "methyl bromide", "phosphine",
            "pest control", "treatment certificate"
        ],
        "negative": [],
        "weight": 0.9
    },
    "export_declaration": {
        "keywords": [
            "export declaration", "customs declaration",
            "single administrative document", "sad"
        ],
        "negative": [],
        "weight": 0.9
    }
}

def detect_document_type(text: str) -> list[tuple[str, float]]:
    """
    Detect document type from text content.
    Returns list of (document_type, confidence) sorted by confidence.
    """
    text_lower = text.lower()
    results = []

    for doc_type, config in DOCUMENT_KEYWORDS.items():
        score = 0.0
        matched = 0

        # Check positive keywords
        for keyword in config["keywords"]:
            if keyword in text_lower:
                matched += 1
                score += config["weight"]

        # Check negative keywords (reduce score)
        for negative in config.get("negative", []):
            if negative in text_lower:
                score *= 0.5

        if matched > 0:
            # Normalize by number of keywords
            confidence = min(score / len(config["keywords"]), 1.0)
            results.append((doc_type, confidence))

    return sorted(results, key=lambda x: x[1], reverse=True)
```

---

## 5. Validation Rules Engine

### Rule Categories

| Category | Code Prefix | Description |
|----------|-------------|-------------|
| Presence | `PRES_` | Required documents are present |
| Content | `CONT_` | Document content is valid |
| Cross-Document | `XDOC_` | Fields match across documents |
| Date | `DATE_` | Dates are valid and in sequence |
| Compliance | `COMP_` | Regulatory requirements met |

### Rule Severity Levels

| Level | Code | Impact | Action |
|-------|------|--------|--------|
| CRITICAL | `C` | Blocks shipment | Must fix before export |
| ERROR | `E` | Compliance failure | Requires correction |
| WARNING | `W` | Potential issue | Review recommended |
| INFO | `I` | Advisory | No action required |

### Presence Rules

```typescript
// PRES_001: All required documents present
interface PresenceRule {
  rule_id: "PRES_001";
  name: "Required Documents Present";
  severity: "CRITICAL";

  check(shipment: Shipment, documents: Document[]): RuleResult {
    const required = getRequiredDocuments(shipment.product_type);
    const uploaded = new Set(documents.map(d => d.document_type));

    const missing = required.filter(r => !uploaded.has(r));

    return {
      passed: missing.length === 0,
      severity: missing.length > 0 ? "CRITICAL" : "INFO",
      message: missing.length > 0
        ? `Missing documents: ${missing.join(", ")}`
        : "All required documents present",
      details: { required, uploaded: [...uploaded], missing }
    };
  }
}
```

### Content Validation Rules

```typescript
// CONT_001: BoL has valid shipper
interface BolShipperRule {
  rule_id: "CONT_001";
  name: "BoL Shipper Valid";
  severity: "ERROR";
  applies_to: "bill_of_lading";

  check(document: BillOfLadingData): RuleResult {
    const shipper = document.shipper?.name;

    if (!shipper || shipper === "Unknown Shipper") {
      return {
        passed: false,
        severity: "ERROR",
        message: "Bill of Lading missing valid shipper name",
        field: "shipper.name"
      };
    }

    return { passed: true };
  }
}

// CONT_002: BoL has valid consignee
// CONT_003: BoL has valid container number(s)
// CONT_004: BoL has valid port codes
// CONT_005: Invoice has valid amounts
// CONT_006: EU TRACES references RC1479592
```

### Cross-Document Validation Rules

```typescript
// XDOC_001: Container numbers match across documents
interface ContainerConsistencyRule {
  rule_id: "XDOC_001";
  name: "Container Number Consistency";
  severity: "ERROR";
  documents: ["bill_of_lading", "packing_list", "fumigation_certificate"];

  check(documents: Map<string, BaseDocumentData>): RuleResult {
    const bol = documents.get("bill_of_lading") as BillOfLadingData;
    const packing = documents.get("packing_list") as PackingListData;
    const fumigation = documents.get("fumigation_certificate") as FumigationCertificateData;

    const bolContainers = new Set(bol?.containers?.map(c => c.number) || []);
    const packingContainers = new Set(packing?.containers?.map(c => c.container_number) || []);
    const fumContainers = new Set(fumigation?.containers || []);

    // All containers in BoL must appear in other documents
    const mismatches: string[] = [];

    for (const container of bolContainers) {
      if (packing && !packingContainers.has(container)) {
        mismatches.push(`${container} missing from packing list`);
      }
      if (fumigation && !fumContainers.has(container)) {
        mismatches.push(`${container} missing from fumigation certificate`);
      }
    }

    return {
      passed: mismatches.length === 0,
      severity: mismatches.length > 0 ? "ERROR" : "INFO",
      message: mismatches.length > 0
        ? `Container mismatches: ${mismatches.join("; ")}`
        : "Container numbers consistent across documents",
      details: {
        bol: [...bolContainers],
        packing: [...packingContainers],
        fumigation: [...fumContainers],
        mismatches
      }
    };
  }
}

// XDOC_002: Weights within 5% tolerance
interface WeightConsistencyRule {
  rule_id: "XDOC_002";
  name: "Weight Consistency";
  severity: "WARNING";
  tolerance: 0.05;  // 5%

  check(documents: Map<string, BaseDocumentData>): RuleResult {
    const bol = documents.get("bill_of_lading") as BillOfLadingData;
    const packing = documents.get("packing_list") as PackingListData;
    const invoice = documents.get("commercial_invoice") as CommercialInvoiceData;

    const weights = {
      bol: bol?.gross_weight_kg,
      packing: packing?.total_gross_weight_kg,
      invoice: this.extractInvoiceWeight(invoice)
    };

    const validWeights = Object.entries(weights)
      .filter(([_, v]) => v != null) as [string, number][];

    if (validWeights.length < 2) {
      return { passed: true, message: "Insufficient weight data to compare" };
    }

    const [first, ...rest] = validWeights;
    const issues: string[] = [];

    for (const [source, weight] of rest) {
      const diff = Math.abs(weight - first[1]) / first[1];
      if (diff > this.tolerance) {
        issues.push(
          `${source} (${weight}kg) differs from ${first[0]} (${first[1]}kg) by ${(diff * 100).toFixed(1)}%`
        );
      }
    }

    return {
      passed: issues.length === 0,
      severity: issues.length > 0 ? "WARNING" : "INFO",
      message: issues.length > 0
        ? `Weight discrepancies: ${issues.join("; ")}`
        : "Weights consistent within tolerance",
      details: { weights, tolerance: `${this.tolerance * 100}%` }
    };
  }
}

// XDOC_003: HS codes consistent
// XDOC_004: Parties match (shipper/consignee)
// XDOC_005: Port codes match
```

### Date Validation Rules

```typescript
// DATE_001: Vet certificate issued before vessel ETD
interface VetCertDateRule {
  rule_id: "DATE_001";
  name: "Vet Certificate Date Valid";
  severity: "ERROR";
  applies_to: "veterinary_health_certificate";

  check(vetCert: VeterinaryHealthCertificateData, shipment: Shipment): RuleResult {
    const certDate = new Date(vetCert.issue_date);
    const etd = shipment.etd ? new Date(shipment.etd) : null;

    if (!etd) {
      return { passed: true, message: "No ETD to validate against" };
    }

    if (certDate > etd) {
      return {
        passed: false,
        severity: "ERROR",
        message: `Vet certificate issued ${certDate.toISOString()} after vessel ETD ${etd.toISOString()}`,
        field: "issue_date"
      };
    }

    // Check cert is not too old (typically valid 10 days)
    const daysBefore = (etd.getTime() - certDate.getTime()) / (1000 * 60 * 60 * 24);
    if (daysBefore > 10) {
      return {
        passed: false,
        severity: "WARNING",
        message: `Vet certificate issued ${daysBefore.toFixed(0)} days before ETD (max 10 days)`,
        field: "issue_date"
      };
    }

    return { passed: true };
  }
}

// DATE_002: Documents not expired
// DATE_003: Invoice date reasonable
// DATE_004: ETD before ETA
```

### Horn & Hoof Specific Rules

```typescript
// HORN_001: EU TRACES references VIBOTAJ registration
interface TracesReferenceRule {
  rule_id: "HORN_001";
  name: "EU TRACES VIBOTAJ Reference";
  severity: "CRITICAL";
  vibotaj_registration: "RC1479592";

  check(traces: EuTracesCertificateData): RuleResult {
    const hasReference =
      traces.operator_reference?.includes(this.vibotaj_registration) ||
      traces.traces_reference?.includes(this.vibotaj_registration) ||
      traces.raw_text?.includes(this.vibotaj_registration);

    return {
      passed: hasReference,
      severity: hasReference ? "INFO" : "CRITICAL",
      message: hasReference
        ? `VIBOTAJ registration ${this.vibotaj_registration} found`
        : `EU TRACES must reference VIBOTAJ registration ${this.vibotaj_registration}`,
      field: "operator_reference"
    };
  }
}

// HORN_002: Vet cert from Nigerian authority
interface NigerianAuthorityRule {
  rule_id: "HORN_002";
  name: "Nigerian Veterinary Authority";
  severity: "ERROR";
  authorities: ["NVRI", "Nigeria", "Nigerian", "Federal Ministry"];

  check(vetCert: VeterinaryHealthCertificateData): RuleResult {
    const authority = vetCert.issuing_authority?.toLowerCase() || "";
    const hasValidAuthority = this.authorities.some(
      a => authority.includes(a.toLowerCase())
    );

    return {
      passed: hasValidAuthority,
      severity: hasValidAuthority ? "INFO" : "ERROR",
      message: hasValidAuthority
        ? `Valid Nigerian authority: ${vetCert.issuing_authority}`
        : `Vet certificate must be issued by Nigerian authority`,
      field: "issuing_authority"
    };
  }
}

// HORN_003: No EUDR fields present
interface NoEudrFieldsRule {
  rule_id: "HORN_003";
  name: "No EUDR Fields for Horn & Hoof";
  severity: "ERROR";

  check(shipment: Shipment, origins: Origin[]): RuleResult {
    if (!isHornHoof(shipment.product_type)) {
      return { passed: true, message: "Not applicable - not Horn & Hoof" };
    }

    const eudrFields = origins.filter(o =>
      o.coordinates || o.geolocation_polygon || o.deforestation_statement
    );

    if (eudrFields.length > 0) {
      return {
        passed: false,
        severity: "ERROR",
        message: "Horn & Hoof shipments must NOT have EUDR fields (geolocation, deforestation statements)",
        details: { invalidOrigins: eudrFields.map(o => o.id) }
      };
    }

    return { passed: true, message: "No EUDR fields present (correct for Horn & Hoof)" };
  }
}
```

---

## 6. EUDR Compliance

### EUDR Applicability

```typescript
const EUDR_HS_CODES = new Set([
  "1801",  // Cocoa beans
  "0901",  // Coffee
  "1511",  // Palm oil
  "4001",  // Natural rubber
  "1201",  // Soya beans
  "4403",  // Wood
  "4407",  // Sawn wood
]);

function isEudrApplicable(hsCode: string): boolean {
  // Check first 4 digits
  const prefix = hsCode.substring(0, 4);
  return EUDR_HS_CODES.has(prefix);
}
```

### EUDR Data Requirements

```typescript
interface EudrOriginData {
  // Identification
  plot_identifier: string;
  farm_name: string | null;

  // Geolocation (REQUIRED)
  coordinates: {
    latitude: number;   // -90 to 90
    longitude: number;  // -180 to 180
  } | null;
  geolocation_polygon: GeoJSONPolygon | null;  // For plots > 4 hectares

  // Location
  country_code: string;  // ISO 3166-1 alpha-2
  region: string | null;

  // Production
  production_date: string;  // Must be after 2020-12-31
  harvest_date: string | null;

  // Supplier
  supplier_id: string;
  supplier_name: string;

  // Compliance
  deforestation_free_statement: boolean;
  due_diligence_date: string;
}

interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: number[][][];  // [[[lng, lat], [lng, lat], ...]]
}
```

### EUDR Cutoff Date

```typescript
const EUDR_CUTOFF_DATE = new Date("2020-12-31");

function validateProductionDate(date: string): { valid: boolean; message: string } {
  const productionDate = new Date(date);

  if (productionDate <= EUDR_CUTOFF_DATE) {
    return {
      valid: false,
      message: `Production date ${date} is on or before EUDR cutoff (${EUDR_CUTOFF_DATE.toISOString().split('T')[0]})`
    };
  }

  return { valid: true, message: "Production date is after EUDR cutoff" };
}
```

### Country Risk Classification

```typescript
type RiskLevel = "LOW" | "STANDARD" | "HIGH";

const COUNTRY_RISK: Record<string, RiskLevel> = {
  // High risk (significant deforestation)
  "BR": "HIGH",  // Brazil
  "ID": "HIGH",  // Indonesia
  "MY": "HIGH",  // Malaysia
  "CO": "HIGH",  // Colombia

  // Standard risk (moderate deforestation)
  "NG": "STANDARD",  // Nigeria
  "GH": "STANDARD",  // Ghana
  "CI": "STANDARD",  // Côte d'Ivoire
  "CM": "STANDARD",  // Cameroon

  // Low risk (minimal deforestation)
  "DE": "LOW",   // Germany
  "NL": "LOW",   // Netherlands
  "BE": "LOW",   // Belgium
  "FR": "LOW",   // France
};

function getCountryRisk(countryCode: string): RiskLevel {
  return COUNTRY_RISK[countryCode] || "STANDARD";
}
```

### Due Diligence Statement Generator

```typescript
interface DueDiligenceStatement {
  statement_id: string;
  generated_at: string;
  shipment_reference: string;

  // Declaration
  declaration: string;

  // Summary
  total_origins: number;
  risk_assessment: {
    low_risk_count: number;
    standard_risk_count: number;
    high_risk_count: number;
    overall_risk: RiskLevel;
  };

  // Origins
  origins: EudrOriginData[];

  // Compliance
  all_production_dates_valid: boolean;
  all_geolocations_valid: boolean;
  deforestation_free: boolean;

  // Certification
  certified_by: string;
  certification_date: string;
}

function generateDueDiligenceStatement(
  shipment: Shipment,
  origins: EudrOriginData[]
): DueDiligenceStatement {
  const riskCounts = origins.reduce(
    (acc, o) => {
      const risk = getCountryRisk(o.country_code);
      acc[`${risk.toLowerCase()}_risk_count`]++;
      return acc;
    },
    { low_risk_count: 0, standard_risk_count: 0, high_risk_count: 0 }
  );

  const overallRisk = riskCounts.high_risk_count > 0 ? "HIGH"
    : riskCounts.standard_risk_count > 0 ? "STANDARD"
    : "LOW";

  return {
    statement_id: generateUUID(),
    generated_at: new Date().toISOString(),
    shipment_reference: shipment.reference,

    declaration: `
      This Due Diligence Statement certifies that the products in shipment
      ${shipment.reference} have been assessed for compliance with EU
      Regulation 2023/1115 (EUDR). Based on our analysis of ${origins.length}
      production origins, we confirm that:

      1. All products were produced after the EUDR cutoff date (31 December 2020)
      2. Geolocation data has been collected and verified for all origins
      3. No evidence of deforestation has been found at the production sites
      4. The overall risk level for this shipment is: ${overallRisk}
    `.trim(),

    total_origins: origins.length,
    risk_assessment: { ...riskCounts, overall_risk: overallRisk },
    origins,

    all_production_dates_valid: origins.every(
      o => validateProductionDate(o.production_date).valid
    ),
    all_geolocations_valid: origins.every(
      o => o.coordinates != null || o.geolocation_polygon != null
    ),
    deforestation_free: origins.every(o => o.deforestation_free_statement),

    certified_by: "TraceHub Compliance Engine",
    certification_date: new Date().toISOString()
  };
}
```

---

## 7. Validation Decision Logic

### Decision Matrix

```typescript
type ValidationDecision = "APPROVE" | "HOLD" | "REJECT";

interface ValidationSummary {
  decision: ValidationDecision;
  critical_errors: number;
  errors: number;
  warnings: number;
  info: number;
  rules_passed: number;
  rules_failed: number;
  blocking_issues: RuleResult[];
  non_blocking_issues: RuleResult[];
}

function calculateDecision(results: RuleResult[]): ValidationSummary {
  const summary = {
    decision: "APPROVE" as ValidationDecision,
    critical_errors: 0,
    errors: 0,
    warnings: 0,
    info: 0,
    rules_passed: 0,
    rules_failed: 0,
    blocking_issues: [] as RuleResult[],
    non_blocking_issues: [] as RuleResult[]
  };

  for (const result of results) {
    if (result.passed) {
      summary.rules_passed++;
      continue;
    }

    summary.rules_failed++;

    switch (result.severity) {
      case "CRITICAL":
        summary.critical_errors++;
        summary.blocking_issues.push(result);
        break;
      case "ERROR":
        summary.errors++;
        summary.blocking_issues.push(result);
        break;
      case "WARNING":
        summary.warnings++;
        summary.non_blocking_issues.push(result);
        break;
      case "INFO":
        summary.info++;
        summary.non_blocking_issues.push(result);
        break;
    }
  }

  // Decision logic
  if (summary.critical_errors > 0 || summary.errors > 0) {
    summary.decision = "REJECT";
  } else if (summary.warnings > 0) {
    summary.decision = "HOLD";
  } else {
    summary.decision = "APPROVE";
  }

  return summary;
}
```

### Validation Workflow

```
Document Upload
    ↓
┌─────────────────────────┐
│ Individual Document     │
│ Validation              │
│ - Content rules         │
│ - Field extraction      │
│ - Schema validation     │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ Cross-Document          │
│ Validation              │
│ - Container consistency │
│ - Weight consistency    │
│ - Party consistency     │
│ - Date sequence         │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ Compliance Rules        │
│                         │
│ Horn & Hoof:            │
│ - TRACES reference      │
│ - Nigerian authority    │
│ - No EUDR fields        │
│                         │
│ EUDR Products:          │
│ - Origin data complete  │
│ - Geolocation valid     │
│ - Production date valid │
│ - Risk assessment       │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ Decision                │
│                         │
│ APPROVE - All passed    │
│ HOLD - Warnings only    │
│ REJECT - Errors found   │
└─────────────────────────┘
```

---

## 8. API Endpoints

### Validation Endpoints

```typescript
// POST /api/shipments/{id}/validate
// Trigger full validation for a shipment
interface ValidateShipmentRequest {
  include_eudr?: boolean;  // Default based on product type
  force_revalidate?: boolean;  // Re-run even if already validated
}

interface ValidateShipmentResponse {
  shipment_id: string;
  validation_summary: ValidationSummary;
  document_results: Record<string, DocumentValidationResult>;
  cross_document_results: RuleResult[];
  compliance_results: RuleResult[];
  eudr_results?: EudrValidationResult;
}

// POST /api/documents/{id}/validate
// Validate a single document
interface ValidateDocumentResponse {
  document_id: string;
  document_type: string;
  extraction_confidence: number;
  extracted_data: BaseDocumentData;
  validation_results: RuleResult[];
  overall_status: "VALID" | "INVALID" | "NEEDS_REVIEW";
}

// GET /api/shipments/{id}/compliance-status
// Get current compliance status
interface ComplianceStatusResponse {
  shipment_id: string;
  product_type: string;
  eudr_applicable: boolean;

  documents: {
    required: string[];
    uploaded: string[];
    validated: string[];
    missing: string[];
  };

  validation: {
    last_validated: string | null;
    decision: ValidationDecision;
    blocking_issues_count: number;
    warnings_count: number;
  };

  progress: {
    documents_complete: number;  // 0-100
    validation_complete: number;  // 0-100
    overall: number;  // 0-100
  };
}
```

---

## 9. Future Enhancements

### AI/LLM Integration

1. **Intelligent Document Classification**
   - Use Claude/GPT for semantic document understanding
   - Handle non-standard document formats
   - Extract data from handwritten documents

2. **Anomaly Detection**
   - Learn patterns from historical shipments
   - Flag unusual values (weights, quantities, dates)
   - Detect potential fraud indicators

3. **Auto-Correction Suggestions**
   - Suggest fixes for validation errors
   - Auto-fill missing fields from other documents
   - Cross-reference with historical data

### Rule Configuration

1. **Admin UI for Rules**
   - Enable/disable rules per organization
   - Adjust severity levels
   - Add custom validation rules

2. **Rule Versioning**
   - Track rule changes over time
   - Audit trail for compliance

### Enhanced OCR

1. **Template Learning**
   - Learn document layouts from examples
   - Improve extraction accuracy over time

2. **Multi-Language Support**
   - Handle documents in various languages
   - Translate extracted data

---

## 10. Testing Requirements

### Unit Tests

- [ ] Test each validation rule in isolation
- [ ] Test BoL parsing with various formats
- [ ] Test container number validation
- [ ] Test date validation edge cases
- [ ] Test EUDR applicability logic

### Integration Tests

- [ ] Test full validation workflow
- [ ] Test cross-document validation
- [ ] Test OCR pipeline with sample PDFs
- [ ] Test decision logic with various scenarios

### Compliance Tests

- [ ] Horn & Hoof: Verify no EUDR fields allowed
- [ ] Horn & Hoof: Verify TRACES reference required
- [ ] EUDR: Verify geolocation required
- [ ] EUDR: Verify production date validation

---

*This specification is the authoritative reference for TraceHub's compliance engine. Update as requirements evolve.*

*Document maintained by TraceHub Engineering Team*
