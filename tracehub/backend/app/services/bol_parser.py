"""Bill of Lading Parser Service.

Parses Bill of Lading documents into the canonical BoL schema.
When a BoL is present, it is the SOURCE OF TRUTH for shipment details.

Supports multiple shipping line formats:
- MSC (Mediterranean Shipping Company)
- Hapag-Lloyd
- Maersk
- CMA CGM
- Evergreen
- Generic formats

Works with ALL product types:
- Horn & Hoof (HS 0506/0507)
- Agricultural products
- General cargo
"""

import re
from datetime import date, datetime
from typing import List, Optional, Tuple, Dict, Any
import logging

from ..schemas.bol import (
    CanonicalBoL,
    BolParty,
    BolContainer,
    BolCargo
)

logger = logging.getLogger(__name__)


class BolParser:
    """Parse Bill of Lading documents into canonical format.

    This parser uses regex patterns to extract structured data from
    BoL text. It supports multiple shipping line formats and calculates
    a confidence score based on how many fields were successfully extracted.
    """

    # Regex patterns for B/L number extraction
    # Note: Use \s*:\s* instead of [:\s]+ to avoid matching newlines
    BOL_NUMBER_PATTERNS = [
        # Pattern for "B/L No.:" and "B/L Number:" (MSC format)
        r'B/L\s*(?:No\.?|Number)?\s*:\s*([A-Z0-9-]+)',
        # Pattern for "Bill of Lading Number:" (Hapag-Lloyd format)
        r'Bill\s+of\s+Lading\s+Number\s*:\s*([A-Z0-9-]+)',
        # Pattern for "BL NUMBER:" (Witatrade format)
        r'BL\s+NUMBER\s*:\s*([A-Z0-9-]+)',
        # Pattern for "BL NO.:" or "BL:"
        r'BL\s*(?:NO\.?)?\s*:\s*([A-Z0-9-]+)',
    ]

    # Container number patterns (ISO 6346: 4 letters + 7 digits)
    CONTAINER_PATTERNS = [
        r'Container\s*(?:No\.?|Number)?[:\s]+([A-Z]{4}\s*\d{7})',
        r'Equipment\s*(?:No\.?)?[:\s]+([A-Z]{4}\s*\d{7})',
        r'CONTAINER/SEAL[:\s]+([A-Z]{4}\s*\d{7})',
        r'([A-Z]{4}\s*\d{7})\s*/\s*(?:SEAL|SL)',
        r'(?:^|\s)([A-Z]{4}\d{7})(?:\s|$)',  # Standalone container number
    ]

    # Seal number patterns
    SEAL_PATTERNS = [
        r'Seal\s*(?:No\.?)?[:\s]+([A-Z0-9-]+)',
        r'SEAL[:\s]+([A-Z0-9-]+)',
        r'/\s*SEAL[:\s-]*([A-Z0-9-]+)',
        r'SL[:\s]?([A-Z0-9]+)',
    ]

    # Container type patterns
    CONTAINER_TYPE_PATTERNS = [
        r"(?:40'?\s*(?:HIGH\s*CUBE|HC)|40HC)",
        r"(?:20'?\s*(?:GP|GENERAL\s*PURPOSE)|20GP)",
        r"(?:40'?\s*(?:GP|GENERAL\s*PURPOSE)|40GP)",
        r'Type[:\s]+(\d{2}[A-Z]{2})',
        r'Equipment[:\s]+(\d{2}[A-Z]{2})',
    ]

    # Vessel patterns
    VESSEL_PATTERNS = [
        r'Vessel\s*(?:Name)?[:\s]+([A-Z][A-Za-z\s]+?)(?:\n|VOY|VOYAGE|$)',
        r'OCEAN\s+VESSEL[:\s]+([A-Z][A-Za-z\s]+?)(?:\n|VOY|$)',
        r'Vessel/Voyage[:\s]+([A-Z][A-Za-z\s]+?)\s*/\s*\d',
        r'M/V\s+([A-Z][A-Za-z\s]+)',
        r'(?:V\.|VESSEL)[:\s]+([A-Z][A-Za-z\s]+)',
    ]

    # Voyage patterns
    VOYAGE_PATTERNS = [
        r'Voyage\s*(?:No\.?)?[:\s]+([A-Z0-9-]+)',
        r'VOY(?:AGE)?\s*(?:NO\.?)?[:\s]+([A-Z0-9-]+)',
        r'Vessel/Voyage[:\s]+[^/]+/\s*([A-Z0-9-]+)',
    ]

    # Port of Loading patterns
    POL_PATTERNS = [
        r'Port\s+of\s+Loading[:\s]+([A-Za-z,\s]+(?:\([A-Z]+\))?)',
        r'POL[:\s]+([A-Z]+\s*[A-Za-z,\s]*)',
        r'Place\s+of\s+Receipt[:\s]+([A-Za-z,\s]+)',
        r'NGAPP|APAPA',  # Nigerian port codes
    ]

    # Port of Discharge patterns
    POD_PATTERNS = [
        r'Port\s+of\s+Discharge[:\s]+([A-Za-z,\s]+(?:\([A-Z]+\))?)',
        r'POD[:\s]+([A-Z]+\s*[A-Za-z,\s]*)',
        r'DEHAM|HAMBURG|DEBRV|BREMERHAVEN',  # German port codes
    ]

    # Shipper patterns
    SHIPPER_PATTERNS = [
        r'(?:SHIPPER|EXPORTER)[:\s]*\n+([A-Z][A-Za-z\s]+(?:LTD|LIMITED|CO|COMPANY|NIG|NIGERIA)?)',
        r'Shipper[:\s]*\n+([A-Z][A-Za-z\s]+)',
        r'SHIPPER[:\s]+([A-Z][A-Za-z\s]+)',
    ]

    # Consignee patterns
    CONSIGNEE_PATTERNS = [
        r'CONSIGNEE[:\s]*(?:\(TO ORDER\))?[:\s]*\n+([A-Z][A-Za-z\s]+(?:GMBH|GBH|LTD|LIMITED)?)',
        r'Consignee[:\s]*\n+([A-Z][A-Za-z\s]+)',
        r'CONSIGNEE[:\s]+([A-Z][A-Za-z\s]+)',
    ]

    # Notify party patterns
    NOTIFY_PATTERNS = [
        r'NOTIFY\s*(?:PARTY)?[:\s]*\n+([A-Z][A-Za-z\s]+)',
        r'Notify[:\s]*([A-Z][A-Za-z\s]+)',
    ]

    # Cargo description patterns
    CARGO_PATTERNS = [
        r'(?:DESCRIPTION\s+OF\s+GOODS|CARGO\s+DESCRIPTION|Commodity)[:\s]*\n+([A-Z][A-Za-z\s]+)',
        r'(?:GOODS|Goods)[:\s]+([A-Z][A-Za-z\s]+)',
    ]

    # HS Code patterns
    HS_CODE_PATTERNS = [
        r'HS\s*(?:CODE)?[:\s]+(\d{4,6})',
        r'Harmonized\s*(?:System)?\s*Code[:\s]+(\d{4,6})',
        r'TARIFF[:\s]+(\d{4,6})',
    ]

    # Weight patterns
    WEIGHT_PATTERNS = [
        r'GROSS\s*(?:WEIGHT)?[:\s]+([0-9,]+)\s*(?:KG|KGS)',
        r'Gross\s*Weight[:\s]+([0-9,.]+)\s*(?:KG|KGS)?',
        r'([0-9,]+)\s*KGS?\s*(?:GROSS)',
    ]

    NET_WEIGHT_PATTERNS = [
        r'NET\s*(?:WEIGHT)?[:\s]+([0-9,]+)\s*(?:KG|KGS)',
        r'Net\s*Weight[:\s]+([0-9,.]+)\s*(?:KG|KGS)?',
    ]

    # Date patterns
    DATE_PATTERNS = [
        r'(?:SHIPPED\s+ON\s+BOARD|ON\s+BOARD\s+DATE)[:\s]+(\d{1,2}[-/\s]?[A-Z]{3}[-/\s]?\d{4})',
        r'Date\s+of\s+Issue[:\s]+(\d{1,2}[-/\s]?[A-Z]{3}[-/\s]?\d{4})',
        r'(\d{4}[-/]\d{2}[-/]\d{2})',  # ISO format
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
    ]

    # Freight terms patterns
    FREIGHT_PATTERNS = [
        r'FREIGHT[:\s]+(PREPAID|COLLECT)',
        r'(PREPAID|COLLECT)\s*FREIGHT',
        r'TERMS[:\s]+(CFR|CIF|FOB|PREPAID|COLLECT)',
    ]

    def __init__(self):
        """Initialize the parser."""
        self.field_weights = {
            'bol_number': 0.15,
            'shipper': 0.15,
            'consignee': 0.15,
            'container': 0.15,
            'vessel': 0.10,
            'port_of_loading': 0.10,
            'port_of_discharge': 0.10,
            'cargo': 0.10,
        }

    def parse(self, text: str) -> CanonicalBoL:
        """Parse BoL text into canonical schema.

        Args:
            text: Raw text extracted from BoL document

        Returns:
            CanonicalBoL instance with extracted data
        """
        if not text or not text.strip():
            return CanonicalBoL(
                bol_number="UNKNOWN",
                shipper=BolParty(name="Unknown Shipper"),
                consignee=BolParty(name="Unknown Consignee"),
                containers=[],
                cargo=[],
                confidence_score=0.0,
                raw_text=text
            )

        # Normalize text
        text = self._normalize_text(text)

        # Extract all fields
        bol_number = self._extract_bol_number(text)
        shipper = self._extract_shipper(text)
        consignee = self._extract_consignee(text)
        notify_party = self._extract_notify_party(text)
        containers = self._extract_containers(text)
        cargo = self._extract_cargo(text)
        vessel_name = self._extract_vessel(text)
        voyage_number = self._extract_voyage(text)
        port_of_loading = self._extract_port_of_loading(text)
        port_of_discharge = self._extract_port_of_discharge(text)
        shipped_date = self._extract_shipped_date(text)
        issue_date = self._extract_issue_date(text)
        freight_terms = self._extract_freight_terms(text)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            bol_number=bol_number,
            shipper=shipper,
            consignee=consignee,
            containers=containers,
            vessel_name=vessel_name,
            port_of_loading=port_of_loading,
            port_of_discharge=port_of_discharge,
            cargo=cargo
        )

        return CanonicalBoL(
            bol_number=bol_number or "UNKNOWN",
            shipper=shipper or BolParty(name="Unknown Shipper"),
            consignee=consignee or BolParty(name="Unknown Consignee"),
            notify_party=notify_party,
            containers=containers,
            cargo=cargo,
            vessel_name=vessel_name,
            voyage_number=voyage_number,
            port_of_loading=port_of_loading,
            port_of_discharge=port_of_discharge,
            shipped_on_board_date=shipped_date,
            date_of_issue=issue_date,
            freight_terms=freight_terms,
            confidence_score=confidence,
            raw_text=text
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for parsing."""
        # Convert to uppercase for consistent matching
        # But preserve original for raw_text
        return text.strip()

    def _extract_field(self, text: str, patterns: List[str], flags: int = re.IGNORECASE | re.MULTILINE) -> Optional[str]:
        """Try multiple patterns to extract a field."""
        for pattern in patterns:
            match = re.search(pattern, text, flags)
            if match:
                return match.group(1).strip() if match.lastindex else match.group(0).strip()
        return None

    def _extract_bol_number(self, text: str) -> Optional[str]:
        """Extract B/L number."""
        return self._extract_field(text, self.BOL_NUMBER_PATTERNS)

    def _extract_shipper(self, text: str) -> Optional[BolParty]:
        """Extract shipper information."""
        name = self._extract_field(text, self.SHIPPER_PATTERNS)
        if not name:
            return None

        # Clean up the name
        name = self._clean_party_name(name)

        # Try to extract country
        country = None
        if "NIGERIA" in text.upper():
            country = "Nigeria"
        elif "LAGOS" in text.upper():
            country = "Nigeria"

        return BolParty(name=name, country=country)

    def _extract_consignee(self, text: str) -> Optional[BolParty]:
        """Extract consignee information."""
        name = self._extract_field(text, self.CONSIGNEE_PATTERNS)
        if not name:
            return None

        name = self._clean_party_name(name)

        # Try to extract country
        country = None
        if "GERMANY" in text.upper():
            country = "Germany"
        elif "HAMBURG" in text.upper() or "BERLIN" in text.upper() or "BREMEN" in text.upper():
            country = "Germany"

        return BolParty(name=name, country=country)

    def _extract_notify_party(self, text: str) -> Optional[BolParty]:
        """Extract notify party information."""
        # Check for "SAME AS CONSIGNEE"
        if re.search(r'NOTIFY.*SAME\s+AS\s+CONSIGNEE', text, re.IGNORECASE):
            consignee = self._extract_consignee(text)
            return consignee

        name = self._extract_field(text, self.NOTIFY_PATTERNS)
        if not name:
            return None

        name = self._clean_party_name(name)
        return BolParty(name=name)

    def _clean_party_name(self, name: str) -> str:
        """Clean up extracted party name."""
        # Remove extra whitespace
        name = ' '.join(name.split())
        # Remove trailing punctuation
        name = name.rstrip(':,.')
        # Limit length
        if len(name) > 100:
            name = name[:100]
        return name

    def _extract_containers(self, text: str) -> List[BolContainer]:
        """Extract container information."""
        containers = []

        # Find container numbers
        for pattern in self.CONTAINER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                container_num = match.upper().replace(' ', '').replace('-', '')
                # Validate ISO 6346 format
                if re.match(r'^[A-Z]{4}\d{7}$', container_num):
                    # Avoid duplicates
                    if not any(c.number == container_num for c in containers):
                        containers.append(BolContainer(number=container_num))

        # Try to extract seal and type for first container
        if containers:
            seal = self._extract_field(text, self.SEAL_PATTERNS)
            if seal:
                containers[0].seal_number = seal

            container_type = self._extract_container_type(text)
            if container_type:
                containers[0].type = container_type

        return containers

    def _extract_container_type(self, text: str) -> Optional[str]:
        """Extract container type (20GP, 40HC, etc.)."""
        for pattern in self.CONTAINER_TYPE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1) if match.lastindex else match.group(0)
                # Normalize
                result = result.upper().replace(' ', '').replace("'", '')
                if 'HIGH' in result or 'HC' in result:
                    return '40HC'
                elif '40' in result:
                    return '40GP'
                elif '20' in result:
                    return '20GP'
                return result
        return None

    def _extract_vessel(self, text: str) -> Optional[str]:
        """Extract vessel name."""
        vessel = self._extract_field(text, self.VESSEL_PATTERNS)
        if vessel:
            # Clean up
            vessel = vessel.strip().rstrip('/')
            vessel = ' '.join(vessel.split())
            return vessel
        return None

    def _extract_voyage(self, text: str) -> Optional[str]:
        """Extract voyage number."""
        return self._extract_field(text, self.VOYAGE_PATTERNS)

    def _extract_port_of_loading(self, text: str) -> Optional[str]:
        """Extract port of loading."""
        pol = self._extract_field(text, self.POL_PATTERNS)
        if pol:
            return pol.strip()

        # Check for known port codes
        if re.search(r'NGAPP|APAPA', text, re.IGNORECASE):
            return "APAPA, NIGERIA (NGAPP)"
        return None

    def _extract_port_of_discharge(self, text: str) -> Optional[str]:
        """Extract port of discharge."""
        pod = self._extract_field(text, self.POD_PATTERNS)
        if pod:
            return pod.strip()

        # Check for known port codes
        if re.search(r'DEHAM|HAMBURG', text, re.IGNORECASE):
            return "HAMBURG, GERMANY (DEHAM)"
        elif re.search(r'DEBRV|BREMERHAVEN', text, re.IGNORECASE):
            return "BREMERHAVEN, GERMANY (DEBRV)"
        return None

    def _extract_cargo(self, text: str) -> List[BolCargo]:
        """Extract cargo information."""
        cargo_list = []

        # Extract description
        description = self._extract_field(text, self.CARGO_PATTERNS)
        if not description:
            # Try to find common cargo terms
            cargo_terms = ['HOOVES', 'HORNS', 'CATTLE', 'ANIMAL', 'BY-PRODUCTS']
            for term in cargo_terms:
                if term in text.upper():
                    description = f"ANIMAL BY-PRODUCTS ({term})"
                    break

        if not description:
            return cargo_list

        # Extract HS code
        hs_code = self._extract_field(text, self.HS_CODE_PATTERNS)

        # Extract weights
        gross_weight = self._extract_weight(text, self.WEIGHT_PATTERNS)
        net_weight = self._extract_weight(text, self.NET_WEIGHT_PATTERNS)

        cargo_list.append(BolCargo(
            description=description,
            hs_code=hs_code,
            gross_weight_kg=gross_weight,
            net_weight_kg=net_weight
        ))

        return cargo_list

    def _extract_weight(self, text: str, patterns: List[str]) -> Optional[float]:
        """Extract weight value from text."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                weight_str = match.group(1).replace(',', '').replace(' ', '')
                try:
                    return float(weight_str)
                except ValueError:
                    continue
        return None

    def _extract_shipped_date(self, text: str) -> Optional[date]:
        """Extract shipped on board date."""
        # Look for specific shipped date patterns
        patterns = [
            r'SHIPPED\s+ON\s+BOARD[:\s]+(\d{1,2}[-/\s]?[A-Z]{3}[-/\s]?\d{4})',
            r'ON\s+BOARD\s+DATE[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})',
            r'ON\s+BOARD\s+DATE[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ]
        return self._extract_date(text, patterns)

    def _extract_issue_date(self, text: str) -> Optional[date]:
        """Extract date of issue."""
        patterns = [
            r'Date\s+of\s+Issue[:\s]+(\d{1,2}[-/]?[A-Z]{3}[-/]?\d{4})',
            r'ISSUED[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})',
        ]
        return self._extract_date(text, patterns)

    def _extract_date(self, text: str, patterns: List[str]) -> Optional[date]:
        """Extract date from text using patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed = self._parse_date_string(date_str)
                if parsed:
                    return parsed
        return None

    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Parse various date formats."""
        formats = [
            '%d %b %Y',      # 12 JAN 2026
            '%d-%b-%Y',      # 12-JAN-2026
            '%d/%b/%Y',      # 12/JAN/2026
            '%Y-%m-%d',      # 2026-01-12
            '%d-%m-%Y',      # 12-01-2026
            '%d/%m/%Y',      # 12/01/2026
            '%d%b%Y',        # 12JAN2026
            '%Y/%m/%d',      # 2026/01/12
        ]

        # Clean up date string
        date_str = date_str.strip().upper()

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def _extract_freight_terms(self, text: str) -> Optional[str]:
        """Extract freight terms."""
        return self._extract_field(text, self.FREIGHT_PATTERNS)

    def _calculate_confidence(
        self,
        bol_number: Optional[str],
        shipper: Optional[BolParty],
        consignee: Optional[BolParty],
        containers: List[BolContainer],
        vessel_name: Optional[str],
        port_of_loading: Optional[str],
        port_of_discharge: Optional[str],
        cargo: List[BolCargo]
    ) -> float:
        """Calculate confidence score based on extracted fields."""
        score = 0.0

        if bol_number and bol_number != "UNKNOWN":
            score += self.field_weights['bol_number']

        if shipper and shipper.name and shipper.name != "Unknown Shipper":
            score += self.field_weights['shipper']

        if consignee and consignee.name and consignee.name != "Unknown Consignee":
            score += self.field_weights['consignee']

        if containers:
            score += self.field_weights['container']

        if vessel_name:
            score += self.field_weights['vessel']

        if port_of_loading:
            score += self.field_weights['port_of_loading']

        if port_of_discharge:
            score += self.field_weights['port_of_discharge']

        if cargo:
            score += self.field_weights['cargo']

        return round(score, 2)


# Singleton instance
bol_parser = BolParser()
