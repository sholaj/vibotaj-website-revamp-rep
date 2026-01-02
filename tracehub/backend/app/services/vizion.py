"""Vizion API client for container tracking."""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config import get_settings

settings = get_settings()


class VizionClient:
    """Client for Vizion container tracking API."""

    def __init__(self):
        self.api_key = settings.vizion_api_key
        self.base_url = settings.vizion_api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def subscribe_container(
        self,
        container_number: str,
        bl_number: Optional[str] = None,
        carrier_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Subscribe a container for tracking updates.

        Args:
            container_number: Container ID (e.g., MSCU1234567)
            bl_number: Bill of Lading number (optional, helps with carrier detection)
            carrier_code: Carrier SCAC code (optional if auto-detect is used)

        Returns:
            Subscription confirmation from Vizion
        """
        if not self.api_key:
            # Return mock response for development
            return {
                "status": "mock",
                "message": "Vizion API key not configured - using mock mode",
                "container_number": container_number
            }

        payload = {
            "container_id": container_number,
        }

        if bl_number:
            payload["bill_of_lading"] = bl_number

        if carrier_code:
            payload["carrier_code"] = carrier_code

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/containers",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code == 201:
                return response.json()
            elif response.status_code == 409:
                # Already subscribed
                return {"status": "already_subscribed", "container_number": container_number}
            else:
                response.raise_for_status()

    async def get_container_status(self, container_number: str) -> Optional[Dict[str, Any]]:
        """Get current tracking status for a container.

        Args:
            container_number: Container ID

        Returns:
            Container status and events, or None if not found
        """
        if not self.api_key:
            # Return mock data for development
            return self._mock_container_status(container_number)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/containers/{container_number}",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()

    def _mock_container_status(self, container_number: str) -> Dict[str, Any]:
        """Generate mock container status for development."""
        now = datetime.utcnow()

        return {
            "container_number": container_number,
            "status": "IN_TRANSIT",
            "carrier": "MSC",
            "eta": (now.replace(day=now.day + 10)).isoformat() + "Z",
            "current_location": {
                "name": "Mediterranean Sea",
                "coordinates": {"lat": 35.5, "lng": 18.5}
            },
            "events": [
                {
                    "id": f"{container_number}-loaded",
                    "type": "CONTAINER_LOADED",
                    "timestamp": (now.replace(day=now.day - 5)).isoformat() + "Z",
                    "location": "Lagos, Nigeria",
                    "location_code": "NGAPP",
                    "vessel": "MSC OSCAR",
                    "voyage": "2601E"
                },
                {
                    "id": f"{container_number}-departed",
                    "type": "VESSEL_DEPARTED",
                    "timestamp": (now.replace(day=now.day - 4)).isoformat() + "Z",
                    "location": "Lagos, Nigeria",
                    "location_code": "NGAPP",
                    "vessel": "MSC OSCAR",
                    "voyage": "2601E"
                }
            ]
        }
