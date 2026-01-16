"""Shipment data extraction service.

Extracts shipment-relevant data from documents:
- Port codes (POL/POD) from Bill of Lading
- HS codes from Commercial Invoice/Packing List
- Container numbers
- Vessel names and voyage numbers

Uses keyword-based extraction (always available) with AI enhancement when available.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from ..models.document import DocumentType

logger = logging.getLogger(__name__)


# ISO 6346 container number pattern: 4 uppercase letters + 7 digits
ISO_6346_PATTERN = re.compile(r'^[A-Z]{4}[0-9]{7}$')

# Placeholder detection patterns
PLACEHOLDER_PATTERNS = [
    r'-CNT-',           # BECKMANN-CNT-001 pattern
    r'^TEST',           # Starts with TEST
    r'PLACEHOLDER',     # Contains PLACEHOLDER
    r'^XXXX',           # Placeholder prefix
]


def is_valid_iso6346_container(container: str) -> bool:
    """Validate container number against ISO 6346 format.

    Format: 4 uppercase letters + 7 digits (e.g., MRSU3452572)

    Args:
        container: Container number to validate

    Returns:
        True if valid ISO 6346 format, False otherwise
    """
    if not container:
        return False
    return bool(ISO_6346_PATTERN.match(container.upper().strip()))


def is_placeholder_container(container: str) -> bool:
    """Check if container number is a placeholder.

    Placeholder patterns include:
    - Contains '-CNT-' (e.g., BECKMANN-CNT-001)
    - Starts with 'TEST'
    - Contains 'PLACEHOLDER'

    Args:
        container: Container number to check

    Returns:
        True if placeholder, False if real container
    """
    if not container:
        return True

    container_upper = container.upper()

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, container_upper):
            return True

    return False


# Common port codes and names (focus on VIBOTAJ routes: Nigeria -> EU)
PORT_DATABASE = {
    # Nigerian Ports
    "NGAPP": "Apapa, Lagos",
    "NGTIN": "Tin Can Island, Lagos",
    "NGONN": "Onne, Port Harcourt",
    "NGCAL": "Calabar",
    "NGWAR": "Warri",
    "NGLAG": "Lagos",
    # German Ports
    "DEHAM": "Hamburg",
    "DEBRE": "Bremen",
    "DEBHV": "Bremerhaven",
    # Netherlands Ports
    "NLRTM": "Rotterdam",
    "NLAMS": "Amsterdam",
    # Belgian Ports
    "BEANR": "Antwerp",
    "BEZEE": "Zeebrugge",
    # French Ports
    "FRLEH": "Le Havre",
    "FRDKK": "Dunkirk",
    # Spanish Ports
    "ESVLC": "Valencia",
    "ESBCN": "Barcelona",
    "ESALG": "Algeciras",
    # Italian Ports
    "ITGOA": "Genoa",
    "ITGIT": "Gioia Tauro",
    # UK Ports
    "GBFXT": "Felixstowe",
    "GBSOU": "Southampton",
    "GBLGP": "London Gateway",
}

# Reverse lookup: name -> code
PORT_NAME_TO_CODE = {}
for code, name in PORT_DATABASE.items():
    PORT_NAME_TO_CODE[name.lower()] = code
    # Also add without country prefix
    city = name.split(",")[0].strip().lower()
    if city not in PORT_NAME_TO_CODE:
        PORT_NAME_TO_CODE[city] = code


@dataclass
class ExtractedShipmentData:
    """Data extracted from a document for shipment enrichment."""
    # Port information
    port_of_loading_code: Optional[str] = None
    port_of_loading_name: Optional[str] = None
    port_of_discharge_code: Optional[str] = None
    port_of_discharge_name: Optional[str] = None
    final_destination: Optional[str] = None

    # Container/transport info
    container_number: Optional[str] = None
    bl_number: Optional[str] = None
    vessel_name: Optional[str] = None
    voyage_number: Optional[str] = None

    # Product info
    hs_codes: List[str] = field(default_factory=list)
    product_descriptions: List[Dict[str, Any]] = field(default_factory=list)

    # Quantities
    total_net_weight_kg: Optional[float] = None
    total_gross_weight_kg: Optional[float] = None

    # Metadata
    extraction_method: str = "keyword"
    confidence: float = 0.0
    raw_fields: Dict[str, Any] = field(default_factory=dict)


# Extraction patterns
EXTRACTION_PATTERNS = {
    # Container number patterns (ISO 6346 format: 4 letters + 7 digits)
    "container_number": [
        r'\b([A-Z]{4}\s*\d{7})\b',
        r'\b([A-Z]{4}[-\s]?\d{6,7}[-\s]?\d?)\b',
        r'(?:Container|CNTR|CTR)[\s:]*#?\s*([A-Z]{4}\s*\d{7})',
    ],

    # Bill of Lading number patterns
    "bl_number": [
        # Maersk format: B/N. 262495038
        r'B/N\.?\s*(\d{9,})',
        # Standard formats
        r'(?:B/?L\s*(?:No\.?|Number)?|Bill\s+of\s+Lading\s*(?:No\.?)?)\s*[:.]?\s*(\d{6,})',
        r'(?:BL\s*No|B/L\s*No|BL\s*Number)[\s.:]*\s*(\d{6,})',
        r'(?:Master\s+)?B/?L[\s:]+(\d{6,})',
    ],

    # Vessel name patterns - improved for Maersk format
    "vessel_name": [
        # Maersk format: vessel name followed by voyage on same line
        # e.g., "RHINE MAERSK 550N" - capture vessel name before voyage number
        r'\n([A-Z][A-Z\s]+MAERSK)\s+\d+[A-Z]?\n',
        r'\n([A-Z][A-Z\s]+MSC)\s+\d+[A-Z]?\n',
        # Generic format: VESSEL NAME followed by voyage
        r'\n([A-Z]{2,}(?:\s+[A-Z]{2,}){0,3})\s+\d{2,}[A-Z]?\s*\n',
        # Labeled formats
        r'(?:Ocean\s+)?Vessel[\s:]+([A-Z][A-Za-z\s]{3,25}?)(?:\s+\d|\n|$)',
        r'(?:Carrier|Vessel\s+Name)[\s:]+([A-Z][A-Za-z\s]{3,25}?)(?:\s+\d|\n|$)',
    ],

    # Voyage number patterns - improved for Maersk format
    "voyage_number": [
        # Maersk format: voyage number after vessel name (e.g., "550N")
        r'(?:MAERSK|MSC)\s+(\d{2,}[A-Z]?)\s*\n',
        # Standard formats
        r'(?:Voyage|Voy)\s*(?:No\.?)?\s*[:.]?\s*(\d{2,}[A-Z]?)',
        r'\bVoyage\s+No[,.]?\s*\d?\s*[^\n]*\n[A-Z\s]+\s+(\d{2,}[A-Z]?)',
    ],

    # Port of Loading patterns - improved for Maersk format
    "port_of_loading": [
        # Maersk format: "Port of Loading Port of Discharge" header, then "Apapa Hamburg" on next line
        r'Port\s+of\s+Loading\s+Port\s+of\s+Discharge[^\n]*\n([A-Za-z]+)\s+[A-Za-z]+',
        # Standard labeled formats
        r'(?:Port\s+of\s+Loading|POL|Load(?:ing)?\s+Port)[\s:]+([A-Za-z,\s]+?)(?:\n|$|Port)',
        r'(?:From|Origin|Shipped\s+From)[\s:]+([A-Za-z,\s]+?)(?:\n|$|To)',
    ],

    # Port of Discharge patterns - improved for Maersk format
    "port_of_discharge": [
        # Maersk format: "Port of Loading Port of Discharge" header, then "Apapa Hamburg" on next line
        r'Port\s+of\s+Loading\s+Port\s+of\s+Discharge[^\n]*\n[A-Za-z]+\s+([A-Za-z]+)',
        # Standard labeled formats
        r'(?:Port\s+of\s+Discharge|POD|Discharge\s+Port)[\s:]+([A-Za-z]+)(?:\s|,|\n|$)',
        r'(?:Destination\s+Port)[\s:]+([A-Za-z]+)(?:\s|,|\n|$)',
    ],

    # Final destination patterns
    "final_destination": [
        r'(?:Final\s+Destination|Place\s+of\s+Delivery|Delivery\s+To)[\s:]+([A-Za-z,\s]+?)(?:\n|$)',
    ],

    # HS Code patterns (4-10 digit codes)
    "hs_code": [
        r'(?:HS\s*(?:Code)?|Tariff|HTS)[\s.:]*\s*(\d{4}(?:\.\d{2}(?:\.\d{2,4})?)?)',
        r'\b(\d{4}\.\d{2}(?:\.\d{2,4})?)\b',  # Standard HS format with dots
        r'\b(\d{8,10})\b',  # 8-10 digit codes (detailed HS)
    ],

    # Weight patterns
    "net_weight": [
        r'(?:Net\s+(?:Weight|Wt\.?)|N/?W)[\s:]*\s*([\d,]+(?:\.\d+)?)\s*(?:KG|KGS?|Kilos?)?',
        r'(?:Weight\s+Net)[\s:]*\s*([\d,]+(?:\.\d+)?)\s*(?:KG|KGS?)?',
    ],
    "gross_weight": [
        r'(?:Gross\s+(?:Weight|Wt\.?)|G/?W)[\s:]*\s*([\d,]+(?:\.\d+)?)\s*(?:KG|KGS?|Kilos?)?',
        r'(?:Weight\s+Gross|Total\s+Weight)[\s:]*\s*([\d,]+(?:\.\d+)?)\s*(?:KG|KGS?)?',
    ],
}

# Product-specific patterns for VIBOTAJ commodities
PRODUCT_PATTERNS = {
    # Horn & Hoof (HS 0506/0507)
    "hooves": [
        r'(?:hooves?|cow\s+hooves?|cattle\s+hooves?)',
        r'\b0506\b',
    ],
    "horns": [
        r'(?:horns?|cow\s+horns?|cattle\s+horns?|horn\s+(?:tips?|cores?))',
        r'\b0507\b',
    ],
    # Pellets (HS 2302)
    "pellets": [
        r'(?:pellets?|wheat\s+pellets?|feed\s+pellets?|bran\s+pellets?)',
        r'\b2302\b',
    ],
    # Sesame (HS 1207)
    "sesame": [
        r'(?:sesame|sesamum|til)',
        r'\b1207\b',
    ],
}


class ShipmentDataExtractor:
    """Service for extracting shipment-relevant data from document text."""

    # Invalid vessel name patterns (common false positives)
    INVALID_VESSEL_PATTERNS = [
        r'^per$', r'^the$', r'^and$', r'^for$', r'^via$', r'^see$',
        r'^clause', r'^shipped', r'^carrier', r'^vessel$',
    ]

    # Invalid port name patterns (legal text, not ports)
    INVALID_PORT_PATTERNS = [
        r'consignee', r'named', r'proof', r'identity', r'bearer',
        r'order', r'notify', r'delivery', r'clause', r'shipper',
    ]

    def __init__(self):
        self._ai_client = None

    def _is_valid_vessel_name(self, name: str) -> bool:
        """Validate that vessel name is not a false positive."""
        if not name or len(name) < 3:
            return False
        name_lower = name.lower().strip()
        for pattern in self.INVALID_VESSEL_PATTERNS:
            if re.match(pattern, name_lower):
                return False
        return True

    def _is_valid_port_name(self, name: str) -> bool:
        """Validate that port name is not legal text or false positive."""
        if not name or len(name) < 3:
            return False
        # Port names should be short (typically < 30 chars)
        if len(name) > 30:
            return False
        name_lower = name.lower()
        for pattern in self.INVALID_PORT_PATTERNS:
            if pattern in name_lower:
                return False
        return True

    def _is_valid_voyage(self, voyage: str) -> bool:
        """Validate voyage number format."""
        if not voyage or len(voyage) < 2:
            return False
        # Voyage should contain at least one digit
        if not any(c.isdigit() for c in voyage):
            return False
        # Filter common false positives
        voyage_upper = voyage.upper().strip()
        if voyage_upper in ['NO', 'NA', 'N/A', 'NIL', 'TBA', 'TBD']:
            return False
        return True

    def extract_from_text(
        self,
        text: str,
        document_type: Optional[DocumentType] = None
    ) -> ExtractedShipmentData:
        """Extract shipment data from document text.

        Args:
            text: The text content of the document
            document_type: Optional document type for context-aware extraction

        Returns:
            ExtractedShipmentData with all extracted fields
        """
        result = ExtractedShipmentData()

        # Normalize text for easier matching
        text_clean = text.replace('\r\n', '\n').replace('\r', '\n')

        # Extract container number
        container = self._extract_pattern(text_clean, "container_number")
        if container:
            result.container_number = self._normalize_container_number(container)
            result.raw_fields["container_number"] = container

        # Extract B/L number
        bl = self._extract_pattern(text_clean, "bl_number")
        if bl and bl.strip().isdigit():  # B/L should be numeric
            result.bl_number = bl.strip()
            result.raw_fields["bl_number"] = bl

        # Extract vessel and voyage
        vessel = self._extract_pattern(text_clean, "vessel_name")
        if vessel and self._is_valid_vessel_name(vessel):
            result.vessel_name = vessel.strip().title()
            result.raw_fields["vessel_name"] = vessel

        voyage = self._extract_pattern(text_clean, "voyage_number")
        if voyage and self._is_valid_voyage(voyage):
            result.voyage_number = voyage.strip().upper()
            result.raw_fields["voyage_number"] = voyage

        # Extract ports
        pol = self._extract_pattern(text_clean, "port_of_loading")
        if pol and self._is_valid_port_name(pol):
            result.port_of_loading_name = pol.strip().title()
            result.port_of_loading_code = self._resolve_port_code(pol)
            result.raw_fields["port_of_loading"] = pol

        pod = self._extract_pattern(text_clean, "port_of_discharge")
        if pod and self._is_valid_port_name(pod):
            result.port_of_discharge_name = pod.strip().title()
            result.port_of_discharge_code = self._resolve_port_code(pod)
            result.raw_fields["port_of_discharge"] = pod

        final_dest = self._extract_pattern(text_clean, "final_destination")
        if final_dest:
            result.final_destination = final_dest.strip().title()
            result.raw_fields["final_destination"] = final_dest

        # Extract HS codes
        hs_codes = self._extract_all_hs_codes(text_clean)
        if hs_codes:
            result.hs_codes = hs_codes
            result.raw_fields["hs_codes"] = hs_codes

        # Extract weights
        net_wt = self._extract_pattern(text_clean, "net_weight")
        if net_wt:
            try:
                result.total_net_weight_kg = float(net_wt.replace(",", ""))
                result.raw_fields["net_weight"] = net_wt
            except ValueError:
                pass

        gross_wt = self._extract_pattern(text_clean, "gross_weight")
        if gross_wt:
            try:
                result.total_gross_weight_kg = float(gross_wt.replace(",", ""))
                result.raw_fields["gross_weight"] = gross_wt
            except ValueError:
                pass

        # Detect products (VIBOTAJ specific)
        products = self._detect_products(text_clean, hs_codes)
        if products:
            result.product_descriptions = products
            result.raw_fields["products"] = products

        # Calculate confidence based on fields extracted
        result.confidence = self._calculate_confidence(result)
        result.extraction_method = "keyword"

        return result

    def _extract_pattern(self, text: str, field_name: str) -> Optional[str]:
        """Extract first match for a field pattern."""
        patterns = EXTRACTION_PATTERNS.get(field_name, [])

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)

        return None

    def _extract_all_hs_codes(self, text: str) -> List[str]:
        """Extract all unique HS codes from text."""
        hs_codes = set()

        for pattern in EXTRACTION_PATTERNS["hs_code"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Normalize: remove dots, then reformat
                normalized = self._normalize_hs_code(match)
                if normalized and self._is_valid_hs_code(normalized):
                    hs_codes.add(normalized)

        return sorted(list(hs_codes))

    def _normalize_hs_code(self, code: str) -> Optional[str]:
        """Normalize HS code to standard format."""
        # Remove dots and spaces
        clean = re.sub(r'[\s.]', '', code)

        # Must be 4-10 digits
        if not clean.isdigit():
            return None

        if len(clean) < 4 or len(clean) > 10:
            return None

        # Return first 4 digits as the chapter/heading
        return clean[:4]

    def _is_valid_hs_code(self, code: str) -> bool:
        """Check if HS code is valid (not a random number)."""
        if not code or len(code) < 4:
            return False

        # Skip common false positives (years, random numbers)
        first_two = int(code[:2])

        # Valid HS chapters are 01-99
        if first_two < 1 or first_two > 99:
            return False

        # Skip codes that look like years
        if 1900 <= int(code[:4]) <= 2100:
            return False

        return True

    def _normalize_container_number(self, container: str) -> str:
        """Normalize container number to standard format."""
        # Remove spaces and dashes
        clean = re.sub(r'[\s-]', '', container.upper())
        return clean

    def extract_container_with_confidence(self, text: str) -> Optional[Tuple[str, float]]:
        """Extract container number from text with confidence score.

        Args:
            text: Text to extract container from (e.g., BOL content)

        Returns:
            Tuple of (container_number, confidence) or None if not found
        """
        if not text:
            return None

        # Patterns with labels (high confidence)
        labeled_patterns = [
            (r'Container\s*No\.?\s*:?\s*([A-Z]{4}\s*\d{7})', 0.95),
            (r'Equipment\s*No\.?\s*:?\s*([A-Z]{4}\s*\d{7})', 0.92),
            (r'CNTR\s*#?\s*:?\s*([A-Z]{4}\s*\d{7})', 0.90),
            (r'Unit\s*No\.?\s*:?\s*([A-Z]{4}\s*\d{7})', 0.88),
            (r'Container\s*:?\s*([A-Z]{4}[-\s]?\d{3}[-\s]?\d{4})', 0.85),
        ]

        # Patterns without labels (medium confidence)
        unlabeled_patterns = [
            (r'\b([A-Z]{4}\s+\d{7})\b', 0.75),  # With space
            (r'\b([A-Z]{4}-\d{3}-\d{4})\b', 0.70),  # With dashes
            (r'\b([A-Z]{4}\d{7})\b', 0.65),  # Plain format
        ]

        text_upper = text.upper()

        # Try labeled patterns first (higher confidence)
        for pattern, confidence in labeled_patterns:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                container = self._normalize_container_number(match.group(1))
                if is_valid_iso6346_container(container) and not is_placeholder_container(container):
                    return (container, confidence)

        # Try unlabeled patterns
        for pattern, confidence in unlabeled_patterns:
            match = re.search(pattern, text_upper)
            if match:
                container = self._normalize_container_number(match.group(1))
                if is_valid_iso6346_container(container) and not is_placeholder_container(container):
                    return (container, confidence)

        return None

    def _resolve_port_code(self, port_text: str) -> Optional[str]:
        """Resolve port name to UN/LOCODE."""
        port_lower = port_text.lower().strip()

        # Direct lookup
        if port_lower in PORT_NAME_TO_CODE:
            return PORT_NAME_TO_CODE[port_lower]

        # Check if it's already a code
        port_upper = port_text.upper().strip()
        if port_upper in PORT_DATABASE:
            return port_upper

        # Partial match
        for name, code in PORT_NAME_TO_CODE.items():
            if name in port_lower or port_lower in name:
                return code

        return None

    def _detect_products(self, text: str, hs_codes: List[str]) -> List[Dict[str, Any]]:
        """Detect products mentioned in text."""
        products = []
        text_lower = text.lower()

        for product_name, patterns in PRODUCT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Determine HS code for this product
                    hs_code = None
                    if product_name == "hooves":
                        hs_code = "0506"
                    elif product_name == "horns":
                        hs_code = "0507"
                    elif product_name == "pellets":
                        hs_code = "2302"
                    elif product_name == "sesame":
                        hs_code = "1207"

                    products.append({
                        "name": product_name.title(),
                        "hs_code": hs_code,
                        "detected_by": "keyword"
                    })
                    break  # Don't duplicate same product

        # Also add products from HS codes
        for code in hs_codes:
            code_prefix = code[:4]
            existing_codes = [p.get("hs_code") for p in products]

            if code_prefix not in existing_codes:
                # Map common HS codes to descriptions
                descriptions = {
                    "0506": "Bones, horn-cores, hooves, etc.",
                    "0507": "Ivory, tortoise-shell, horns, etc.",
                    "2302": "Bran, sharps and other residues",
                    "1207": "Oil seeds (sesame)",
                }

                products.append({
                    "name": descriptions.get(code_prefix, f"Product (HS {code_prefix})"),
                    "hs_code": code_prefix,
                    "detected_by": "hs_code"
                })

        return products

    def _calculate_confidence(self, data: ExtractedShipmentData) -> float:
        """Calculate extraction confidence based on fields found."""
        # Weight different fields
        scores = []

        if data.container_number:
            scores.append(0.9)  # High confidence marker
        if data.bl_number:
            scores.append(0.85)
        if data.port_of_discharge_code:
            scores.append(0.9)  # Resolved to code = high confidence
        elif data.port_of_discharge_name:
            scores.append(0.7)  # Name only = medium confidence
        if data.port_of_loading_code:
            scores.append(0.9)
        elif data.port_of_loading_name:
            scores.append(0.7)
        if data.hs_codes:
            scores.append(0.85)
        if data.vessel_name:
            scores.append(0.7)
        if data.voyage_number:
            scores.append(0.7)
        if data.total_net_weight_kg or data.total_gross_weight_kg:
            scores.append(0.6)

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def extract_from_document(
        self,
        file_path: str,
        document_type: Optional[DocumentType] = None
    ) -> ExtractedShipmentData:
        """Extract shipment data from a PDF document file.

        Args:
            file_path: Path to the PDF file
            document_type: Optional document type for context

        Returns:
            ExtractedShipmentData with all extracted fields
        """
        from .pdf_processor import pdf_processor

        if not pdf_processor.is_available():
            logger.warning("PDF processing not available")
            return ExtractedShipmentData()

        # Extract text from PDF
        pages = pdf_processor.extract_text(file_path)
        if not pages:
            return ExtractedShipmentData()

        # Combine all page text
        full_text = "\n".join(page.text for page in pages)

        return self.extract_from_text(full_text, document_type)


# Global instance
shipment_data_extractor = ShipmentDataExtractor()
