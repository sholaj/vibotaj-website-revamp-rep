"""Bill of Lading Shipment Sync Service.

This service synchronizes shipment details from parsed Bill of Lading data.
When a BoL is uploaded and parsed, it becomes the SOURCE OF TRUTH for
shipment details.

Key Features:
- Detects and replaces placeholder container numbers
- Updates vessel, voyage, and port information
- Tracks all changes for audit logging
- Works with all product types

Placeholder Detection:
- BUYER-CNT-XXX patterns (e.g., HAGES-CNT-001, BECKMANN-CNT-002)
- TBD, TBC, PENDING values
- Empty or null values
"""

import re
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..schemas.bol import CanonicalBoL

logger = logging.getLogger(__name__)


# Patterns that indicate a placeholder container number
PLACEHOLDER_PATTERNS = [
    r".*-CNT-\d+$",  # BUYER-CNT-001, HAGES-CNT-002, etc.
    r"^TBD$",
    r"^TBC$",
    r"^PENDING$",
    r"^PLACEHOLDER$",
    r"^TO\s*BE\s*CONFIRMED$",
    r"^N/?A$",
]


def is_placeholder_container(container: Optional[str]) -> bool:
    """Check if a container number is a placeholder.

    Args:
        container: Container number to check

    Returns:
        True if the container is a placeholder or empty
    """
    if not container:
        return True

    container_upper = container.strip().upper()
    if not container_upper:
        return True

    for pattern in PLACEHOLDER_PATTERNS:
        if re.match(pattern, container_upper, re.IGNORECASE):
            return True

    return False


class BolShipmentSync:
    """Synchronize shipment data from parsed Bill of Lading.

    This service determines what fields need to be updated in a shipment
    based on the parsed BoL data. It follows these rules:

    - B/L number: Always updated from BoL (authoritative source)
    - Container: Only updated if current value is a placeholder
    - Vessel/Voyage: Always updated from BoL if present
    - Ports: Always updated from BoL if present
    - Shipped date: Updates actual departure (ATD) if present

    Usage:
        sync = BolShipmentSync()
        changes = sync.get_sync_changes(shipment, parsed_bol)
        if changes:
            sync.apply_sync_changes(shipment, parsed_bol)
    """

    def __init__(self):
        """Initialize the sync service."""
        pass

    def get_sync_changes(
        self,
        shipment: Any,
        bol: CanonicalBoL
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate what changes would be made to the shipment.

        This method does NOT modify the shipment - it only calculates
        what would change. Use apply_sync_changes() to actually apply.

        Args:
            shipment: The shipment object (SQLAlchemy model or mock)
            bol: Parsed BoL data

        Returns:
            Dict of field names to {old: value, new: value} pairs
        """
        changes = {}

        # B/L number - always update if BoL has a valid number
        if bol.bol_number and bol.bol_number != "UNKNOWN":
            if shipment.bl_number != bol.bol_number:
                changes["bl_number"] = {
                    "old": shipment.bl_number,
                    "new": bol.bol_number,
                }

        # Container number - only update if current is placeholder
        if bol.containers and len(bol.containers) > 0:
            new_container = bol.containers[0].number
            if new_container and is_placeholder_container(shipment.container_number):
                changes["container_number"] = {
                    "old": shipment.container_number,
                    "new": new_container,
                }

        # Vessel name - update if BoL has it
        if bol.vessel_name:
            if shipment.vessel_name != bol.vessel_name:
                changes["vessel_name"] = {
                    "old": shipment.vessel_name,
                    "new": bol.vessel_name,
                }

        # Voyage number - update if BoL has it
        if bol.voyage_number:
            if shipment.voyage_number != bol.voyage_number:
                changes["voyage_number"] = {
                    "old": shipment.voyage_number,
                    "new": bol.voyage_number,
                }

        # Port of Loading - extract code and update
        if bol.port_of_loading:
            pol_code = self._extract_port_code(bol.port_of_loading)
            if pol_code and shipment.pol_code != pol_code:
                changes["pol_code"] = {
                    "old": shipment.pol_code,
                    "new": pol_code,
                }

        # Port of Discharge - extract code and update
        if bol.port_of_discharge:
            pod_code = self._extract_port_code(bol.port_of_discharge)
            if pod_code and shipment.pod_code != pod_code:
                changes["pod_code"] = {
                    "old": shipment.pod_code,
                    "new": pod_code,
                }

        # Shipped on board date -> ATD (actual time of departure)
        if bol.shipped_on_board_date:
            # Convert date to datetime if needed for comparison
            current_atd = shipment.atd
            if isinstance(current_atd, datetime):
                current_atd = current_atd.date()

            if current_atd != bol.shipped_on_board_date:
                changes["atd"] = {
                    "old": shipment.atd,
                    "new": bol.shipped_on_board_date,
                }

        return changes

    def apply_sync_changes(
        self,
        shipment: Any,
        bol: CanonicalBoL
    ) -> Dict[str, Dict[str, Any]]:
        """Apply sync changes to the shipment.

        This method modifies the shipment object in place.

        Args:
            shipment: The shipment object to update
            bol: Parsed BoL data

        Returns:
            Dict of changes that were applied (same format as get_sync_changes)
        """
        changes = self.get_sync_changes(shipment, bol)

        for field, change_data in changes.items():
            new_value = change_data["new"]

            # Handle date to datetime conversion for atd
            if field == "atd" and isinstance(new_value, date):
                new_value = datetime.combine(new_value, datetime.min.time())

            setattr(shipment, field, new_value)

        return changes

    def _extract_port_code(self, port_string: str) -> Optional[str]:
        """Extract UN/LOCODE from port string.

        Handles various formats:
        - "HAMBURG, GERMANY (DEHAM)" -> "DEHAM"
        - "NGAPP APAPA" -> "NGAPP"
        - "DEHAM" -> "DEHAM"
        - "APAPA, NIGERIA" -> None (no code found)

        Args:
            port_string: Port description string

        Returns:
            UN/LOCODE if found, None otherwise
        """
        if not port_string:
            return None

        port_string = port_string.strip().upper()

        # Try to extract from parentheses first: "HAMBURG (DEHAM)"
        match = re.search(r"\(([A-Z]{5})\)", port_string)
        if match:
            return match.group(1)

        # Try to find a 5-character UN/LOCODE at the start
        match = re.match(r"^([A-Z]{5})(?:\s|$)", port_string)
        if match:
            return match.group(1)

        # Check if the entire string is a valid UN/LOCODE
        if re.match(r"^[A-Z]{5}$", port_string):
            return port_string

        # No code found
        return None

    def format_changes_for_audit(
        self,
        changes: Dict[str, Dict[str, Any]],
        shipment_reference: str
    ) -> str:
        """Format changes for audit log entry.

        Args:
            changes: Dict of field changes from get_sync_changes
            shipment_reference: Shipment reference number

        Returns:
            Formatted string for audit logging
        """
        if not changes:
            return f"No changes applied to shipment {shipment_reference}"

        lines = [f"BoL sync for shipment {shipment_reference}:"]
        for field, data in changes.items():
            old_val = data["old"] if data["old"] is not None else "None"
            new_val = data["new"] if data["new"] is not None else "None"
            lines.append(f"  {field}: '{old_val}' -> '{new_val}'")

        return "\n".join(lines)


# Singleton instance
bol_shipment_sync = BolShipmentSync()
