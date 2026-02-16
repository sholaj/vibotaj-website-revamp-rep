"""Mock customs backend for development and testing (PRD-021).

Simulates NCS/SON responses with configurable behavior.
Same pattern as ConsoleBackend (email), MockLLMBackend (LLM).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .customs import (
    ClearanceStatus,
    DeclarationResult,
    DeclarationStatus,
    DutyCalculation,
    PreClearanceResult,
)

logger = logging.getLogger(__name__)

# HS codes that are restricted for export from Nigeria
RESTRICTED_HS_CODES = {"2709", "2710"}  # Crude oil, petroleum products

# Standard required documents per category
REQUIRED_DOCS = {
    "animal": [
        "EU TRACES Certificate",
        "Veterinary Health Certificate",
        "Certificate of Origin",
        "Bill of Lading",
        "Commercial Invoice",
        "Packing List",
    ],
    "eudr": [
        "EUDR Due Diligence Statement",
        "Geolocation Data",
        "Certificate of Origin",
        "Bill of Lading",
        "Commercial Invoice",
        "Packing List",
        "Phytosanitary Certificate",
    ],
    "general": [
        "Certificate of Origin",
        "Bill of Lading",
        "Commercial Invoice",
        "Packing List",
    ],
}

# Standard duty rates by HS chapter
DUTY_RATES: Dict[str, float] = {
    "05": 0.0,  # Animal products (horn/hoof) — zero duty
    "09": 0.0,  # Coffee, tea — zero duty (GSP)
    "15": 3.8,  # Fats and oils
    "18": 0.0,  # Cocoa — zero duty (GSP)
    "40": 0.0,  # Rubber — zero duty (GSP)
}

EU_VAT_RATE = 19.0  # Standard German VAT


class MockCustomsBackend:
    """Mock customs backend for dev/test.

    Simulates NCS responses with realistic data.
    Tracks calls for test assertions.
    """

    def __init__(self, available: bool = True) -> None:
        self._available = available
        self._declarations: Dict[str, DeclarationResult] = {}
        self._call_count = 0
        self._last_method: Optional[str] = None

    def check_pre_clearance(
        self, hs_code: str, origin_country: str, destination_country: str = "DE"
    ) -> PreClearanceResult:
        """Simulate pre-clearance check."""
        self._call_count += 1
        self._last_method = "check_pre_clearance"

        chapter = hs_code[:2] if len(hs_code) >= 2 else hs_code

        # Check restrictions
        if hs_code[:4] in RESTRICTED_HS_CODES:
            return PreClearanceResult(
                hs_code=hs_code,
                origin_country=origin_country,
                status=ClearanceStatus.RESTRICTED,
                restrictions=["Export license required for petroleum products"],
                provider=self.get_provider_name(),
            )

        # Determine required docs based on HS code
        if chapter == "05":
            docs = REQUIRED_DOCS["animal"]
        elif chapter in ("09", "18", "15", "12", "40"):
            docs = REQUIRED_DOCS["eudr"]
        else:
            docs = REQUIRED_DOCS["general"]

        logger.info(
            "[MockCustoms] Pre-clearance check: hs=%s origin=%s dest=%s → CLEARED",
            hs_code,
            origin_country,
            destination_country,
        )

        return PreClearanceResult(
            hs_code=hs_code,
            origin_country=origin_country,
            status=ClearanceStatus.CLEARED,
            required_documents=docs,
            provider=self.get_provider_name(),
        )

    def calculate_duty(
        self,
        hs_code: str,
        cif_value: float,
        currency: str = "EUR",
        quantity: float = 1.0,
    ) -> DutyCalculation:
        """Simulate duty calculation."""
        self._call_count += 1
        self._last_method = "calculate_duty"

        chapter = hs_code[:2] if len(hs_code) >= 2 else "00"
        duty_rate = DUTY_RATES.get(chapter, 5.0)  # Default 5% for unknown

        import_duty = cif_value * (duty_rate / 100)
        vat = (cif_value + import_duty) * (EU_VAT_RATE / 100)
        surcharges: List[Dict[str, object]] = []

        # Add customs processing fee
        processing_fee = max(cif_value * 0.005, 25.0)  # 0.5% min €25
        surcharges.append(
            {
                "name": "Customs Processing Fee",
                "rate": 0.5,
                "amount": round(processing_fee, 2),
            }
        )

        total = import_duty + vat + processing_fee

        logger.info(
            "[MockCustoms] Duty calc: hs=%s cif=%.2f → duty=%.2f vat=%.2f total=%.2f",
            hs_code,
            cif_value,
            import_duty,
            vat,
            total,
        )

        return DutyCalculation(
            hs_code=hs_code,
            cif_value=cif_value,
            currency=currency,
            import_duty_rate=duty_rate,
            import_duty_amount=round(import_duty, 2),
            vat_rate=EU_VAT_RATE,
            vat_amount=round(vat, 2),
            surcharges=surcharges,
            total_duty=round(total, 2),
            provider=self.get_provider_name(),
        )

    def submit_declaration(
        self,
        shipment_reference: str,
        hs_code: str,
        exporter_name: str,
        consignee_name: str,
        cif_value: float,
        currency: str = "EUR",
        extra_data: Optional[Dict[str, object]] = None,
    ) -> DeclarationResult:
        """Simulate export declaration submission."""
        self._call_count += 1
        self._last_method = "submit_declaration"

        ref = f"NCS-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        result = DeclarationResult(
            reference_number=ref,
            status=DeclarationStatus.SUBMITTED,
            submitted_at=now,
            provider=self.get_provider_name(),
        )

        self._declarations[ref] = result

        logger.info(
            "[MockCustoms] Declaration submitted: ref=%s shipment=%s hs=%s",
            ref,
            shipment_reference,
            hs_code,
        )

        return result

    def get_declaration_status(self, reference_number: str) -> DeclarationResult:
        """Simulate declaration status check."""
        self._call_count += 1
        self._last_method = "get_declaration_status"

        if reference_number in self._declarations:
            return self._declarations[reference_number]

        return DeclarationResult(
            reference_number=reference_number,
            status=DeclarationStatus.DRAFT,
            provider=self.get_provider_name(),
            error="Declaration not found",
        )

    def is_available(self) -> bool:
        """Check availability."""
        return self._available

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "mock"

    def get_status(self) -> Dict[str, object]:
        """Return status info."""
        return {
            "provider": "mock",
            "available": self._available,
            "call_count": self._call_count,
            "declarations_tracked": len(self._declarations),
        }

    # --- Test helpers ---

    def set_available(self, available: bool) -> None:
        """Set availability for testing."""
        self._available = available

    def reset(self) -> None:
        """Reset state for testing."""
        self._call_count = 0
        self._last_method = None
        self._declarations.clear()

    @property
    def call_count(self) -> int:
        """Number of API calls made."""
        return self._call_count

    @property
    def last_method(self) -> Optional[str]:
        """Last method called."""
        return self._last_method
