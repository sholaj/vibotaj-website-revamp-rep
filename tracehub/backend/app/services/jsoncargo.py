"""JSONCargo API client for container tracking.

API Documentation: https://jsoncargo.com/documentation-api/
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Mapping of carrier names to JSONCargo shipping_line parameter
CARRIER_MAPPING = {
    "MAERSK": "maersk",
    "MSC": "msc",
    "HAPAG-LLOYD": "hapag-lloyd",
    "ONE": "one",
    "EVERGREEN": "evergreen",
    "CMA CGM": "cma-cgm",
    "COSCO": "cosco",
    "ZIM": "zim",
    "HMM": "hmm",
    "YANG MING": "yang-ming",
}

# Container prefix to carrier mapping (common prefixes)
PREFIX_TO_CARRIER = {
    "MRSU": "maersk",  # Maersk
    "MSKU": "maersk",
    "MAEU": "maersk",
    "MSCU": "msc",     # MSC
    "MEDU": "msc",
    "HLCU": "hapag-lloyd",  # Hapag-Lloyd
    "HLXU": "hapag-lloyd",
    "ONEY": "one",     # ONE
    "ONEU": "one",
    "CMAU": "cma-cgm", # CMA CGM
    "CGMU": "cma-cgm",
    "EGLV": "evergreen",  # Evergreen
    "EGHU": "evergreen",
    "COSU": "cosco",   # COSCO
    "CCLU": "cosco",
    "ZIMU": "zim",     # ZIM
    "HMMU": "hmm",     # HMM
    "YMLU": "yang-ming",  # Yang Ming
}


class JSONCargoClient:
    """Client for JSONCargo container tracking API."""

    def __init__(self):
        self.api_key = settings.jsoncargo_api_key
        self.base_url = "https://api.jsoncargo.com/api/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _detect_carrier(self, container_number: str) -> Optional[str]:
        """Detect carrier from container number prefix."""
        if len(container_number) >= 4:
            prefix = container_number[:4].upper()
            return PREFIX_TO_CARRIER.get(prefix)
        return None

    async def get_container_status(
        self,
        container_number: str,
        shipping_line: Optional[str] = None,
        bl_number: Optional[str] = None,
        vessel_name: Optional[str] = None,
        voyage_number: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get current tracking status for a container.

        Args:
            container_number: Container ID (e.g., MRSU3452572)
            shipping_line: Shipping line name (auto-detected if not provided)
            bl_number: Bill of Lading number for shipment context
            vessel_name: Vessel name for shipment context
            voyage_number: Voyage number for shipment context

        Returns:
            Container status and events, or None if not found

        Note:
            The bl_number, vessel_name, and voyage_number parameters help
            disambiguate tracking results when a container is reused across
            multiple shipments. See PRP: Container Tracking Enhancement.
        """
        if not self.api_key:
            logger.warning("JSONCargo API key not configured - using mock mode")
            return self._mock_container_status(container_number)

        # Auto-detect carrier if not provided
        if not shipping_line:
            shipping_line = self._detect_carrier(container_number)
            if not shipping_line:
                logger.error(f"Could not detect carrier for container {container_number}")
                return None

        # Build request params with shipment context
        params = {"shipping_line": shipping_line}
        if bl_number:
            params["bl_number"] = bl_number
        if vessel_name:
            params["vessel_name"] = vessel_name
        if voyage_number:
            params["voyage_number"] = voyage_number

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/containers/{container_number}",
                    params=params,
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._normalize_response(data, container_number)
                elif response.status_code == 404:
                    logger.warning(f"Container {container_number} not found")
                    return None
                else:
                    logger.error(f"JSONCargo API error: {response.status_code} - {response.text}")
                    response.raise_for_status()

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching container {container_number}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching container {container_number}: {e}")
            return None

    async def get_container_by_bol(
        self,
        bl_number: str,
        shipping_line: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get container tracking by Bill of Lading number.

        Args:
            bl_number: Bill of Lading number
            shipping_line: Shipping line name (required for B/L lookup)

        Returns:
            Container status and events, or None if not found
        """
        if not self.api_key:
            logger.warning("JSONCargo API key not configured - using mock mode")
            return self._mock_container_status(f"MOCK-{bl_number}")

        if not shipping_line:
            logger.error("Shipping line required for B/L lookup")
            return None

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/containers/bol/{bl_number}",
                    params={"shipping_line": shipping_line},
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._normalize_response(data, bl_number)
                elif response.status_code == 404:
                    logger.warning(f"B/L {bl_number} not found")
                    return None
                else:
                    logger.error(f"JSONCargo API error: {response.status_code}")
                    response.raise_for_status()

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching B/L {bl_number}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching B/L {bl_number}: {e}")
            return None

    async def get_api_usage(self) -> Optional[Dict[str, Any]]:
        """Get API usage statistics.

        Returns:
            Usage stats including requests used and remaining
        """
        if not self.api_key:
            return {"status": "mock", "message": "API key not configured"}

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/api_key/stats",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get API stats: {response.status_code}")
                    return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching API stats: {e}")
            return None

    def _normalize_response(self, data: Dict[str, Any], reference: str) -> Dict[str, Any]:
        """Normalize JSONCargo response to TraceHub format.

        Args:
            data: Raw JSONCargo API response
            reference: Container number or B/L for reference

        Returns:
            Normalized container status
        """
        # JSONCargo response structure: {"data": {...}}
        container_data = data.get("data", data)

        # Build events from available data points (JSONCargo doesn't return event list)
        events = []

        # Departure event
        if container_data.get("atd_origin"):
            events.append({
                "id": f"{reference}-departed-origin",
                "type": "VESSEL_DEPARTED",
                "timestamp": container_data.get("atd_origin"),
                "location": container_data.get("shipped_from", ""),
                "location_code": container_data.get("shipped_from", ""),
                "vessel": container_data.get("last_vessel_name"),
                "voyage": container_data.get("last_voyage_number"),
                "description": "Departed from origin port"
            })

        # Last location event
        if container_data.get("timestamp_of_last_location"):
            events.append({
                "id": f"{reference}-last-location",
                "type": "TRANSSHIPMENT" if container_data.get("last_location") != container_data.get("shipped_from") else "IN_TRANSIT",
                "timestamp": container_data.get("timestamp_of_last_location"),
                "location": container_data.get("last_location", ""),
                "location_code": container_data.get("last_location", ""),
                "vessel": container_data.get("current_vessel_name"),
                "voyage": container_data.get("current_voyage_number"),
                "description": f"At {container_data.get('last_location_terminal', '')}"
            })

        # Departure from last location
        if container_data.get("atd_last_location"):
            events.append({
                "id": f"{reference}-departed-last",
                "type": "VESSEL_DEPARTED",
                "timestamp": container_data.get("atd_last_location"),
                "location": container_data.get("last_location", ""),
                "location_code": container_data.get("last_location", ""),
                "vessel": container_data.get("current_vessel_name"),
                "voyage": container_data.get("current_voyage_number"),
                "description": "Departed for final destination"
            })

        return {
            "container_number": container_data.get("container_id", reference),
            "container_type": container_data.get("container_type", ""),
            "status": container_data.get("container_status", "UNKNOWN"),
            "carrier": container_data.get("shipping_line_name", ""),
            "carrier_id": container_data.get("shipping_line_id", ""),
            "eta": container_data.get("eta_final_destination"),
            "eta_next": container_data.get("eta_next_destination"),
            "atd_origin": container_data.get("atd_origin"),
            "origin": {
                "port": container_data.get("shipped_from", ""),
                "terminal": container_data.get("shipped_from_terminal", ""),
                "loading_port": container_data.get("loading_port", "")
            },
            "destination": {
                "port": container_data.get("shipped_to", ""),
                "terminal": container_data.get("shipped_to_terminal", ""),
                "discharging_port": container_data.get("discharging_port", "")
            },
            "current_location": {
                "port": container_data.get("last_location", ""),
                "terminal": container_data.get("last_location_terminal", ""),
                "timestamp": container_data.get("timestamp_of_last_location")
            },
            "next_location": {
                "port": container_data.get("next_location", ""),
                "terminal": container_data.get("next_location_terminal", ""),
                "eta": container_data.get("eta_next_destination")
            },
            "vessel": {
                "original_name": container_data.get("last_vessel_name", ""),
                "original_voyage": container_data.get("last_voyage_number", ""),
                "current_name": container_data.get("current_vessel_name", ""),
                "current_voyage": container_data.get("current_voyage_number", "")
            },
            "last_updated": container_data.get("last_updated"),
            "last_movement": container_data.get("last_movement_timestamp"),
            "events": events,
            "raw_data": data  # Include raw data for debugging
        }

    def _map_event_type(self, event_type: str) -> str:
        """Map JSONCargo event types to TraceHub event types."""
        event_mapping = {
            "GATE_IN": "GATE_IN",
            "GATE_OUT": "GATE_OUT",
            "LOADED": "CONTAINER_LOADED",
            "LOAD": "CONTAINER_LOADED",
            "DISCHARGED": "CONTAINER_DISCHARGED",
            "DISCHARGE": "CONTAINER_DISCHARGED",
            "DEPARTED": "VESSEL_DEPARTED",
            "DEPARTURE": "VESSEL_DEPARTED",
            "ARRIVED": "VESSEL_ARRIVED",
            "ARRIVAL": "VESSEL_ARRIVED",
            "TRANSSHIPMENT": "TRANSSHIPMENT",
            "DELIVERED": "DELIVERED",
            "EMPTY_RETURN": "EMPTY_RETURN",
        }
        return event_mapping.get(event_type.upper(), event_type.upper())

    def _mock_container_status(self, container_number: str) -> Dict[str, Any]:
        """Generate mock container status for development."""
        now = datetime.utcnow()

        return {
            "container_number": container_number,
            "status": "IN_TRANSIT",
            "carrier": "MAERSK",
            "eta": "2026-01-03T12:00:00Z",
            "origin": {
                "port": "Apapa, Lagos",
                "port_code": "NGAPP"
            },
            "destination": {
                "port": "Hamburg",
                "port_code": "DEHAM"
            },
            "vessel": {
                "name": "RHINE MAERSK",
                "voyage": "550N"
            },
            "events": [
                {
                    "id": f"{container_number}-gate-in",
                    "type": "GATE_IN",
                    "timestamp": "2025-12-11T08:30:00Z",
                    "location": "Apapa Container Terminal",
                    "location_code": "NGAPP",
                    "vessel": None,
                    "voyage": None,
                    "description": "Container received at terminal"
                },
                {
                    "id": f"{container_number}-loaded",
                    "type": "CONTAINER_LOADED",
                    "timestamp": "2025-12-12T14:00:00Z",
                    "location": "Apapa, Lagos",
                    "location_code": "NGAPP",
                    "vessel": "RHINE MAERSK",
                    "voyage": "550N",
                    "description": "Loaded on vessel"
                },
                {
                    "id": f"{container_number}-departed",
                    "type": "VESSEL_DEPARTED",
                    "timestamp": "2025-12-13T18:00:00Z",
                    "location": "Apapa, Lagos",
                    "location_code": "NGAPP",
                    "vessel": "RHINE MAERSK",
                    "voyage": "550N",
                    "description": "Vessel departed from port"
                }
            ],
            "raw_data": {"mock": True}
        }


# Singleton instance
_client: Optional[JSONCargoClient] = None


def get_jsoncargo_client() -> JSONCargoClient:
    """Get or create JSONCargo client singleton."""
    global _client
    if _client is None:
        _client = JSONCargoClient()
    return _client
