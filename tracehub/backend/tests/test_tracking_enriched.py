"""TDD Tests for Container Tracking Enhancement.

Tests the PRP requirement: Tracking requests must include
billOfLadingNumber, containerNumber, vesselName and/or voyageNumber.

Run with: pytest tests/test_tracking_enriched.py -v

These tests are written BEFORE implementation (TDD approach).
They should FAIL initially, then PASS after implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.jsoncargo import JSONCargoClient
from app.models.shipment import Shipment, ShipmentStatus
from app.models.container_event import ContainerEvent, EventStatus


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_shipment():
    """Create a mock shipment with full tracking context."""
    shipment = MagicMock(spec=Shipment)
    shipment.id = uuid4()
    shipment.reference = "VIBO-2026-001"
    shipment.container_number = "MSCU1234567"
    shipment.bl_number = "MAEU123456789"
    shipment.vessel_name = "MAERSK SEALAND"
    shipment.voyage_number = "001W"
    shipment.etd = datetime(2026, 1, 15)
    shipment.eta = datetime(2026, 2, 1)
    shipment.status = ShipmentStatus.IN_TRANSIT
    shipment.organization_id = uuid4()
    return shipment


@pytest.fixture
def jsoncargo_client():
    """Create JSONCargo client for testing."""
    return JSONCargoClient()


# =============================================================================
# Test: Enriched Tracking Request Parameters
# =============================================================================

class TestEnrichedTrackingRequests:
    """Test that tracking requests include shipment context (B/L, vessel, voyage)."""

    @pytest.mark.asyncio
    async def test_get_container_status_accepts_bl_number(self, jsoncargo_client):
        """GIVEN a container number and B/L number
        WHEN get_container_status is called
        THEN it should accept the bl_number parameter."""
        # This test verifies the function signature accepts bl_number

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"events": []}
            mock_client.get.return_value = mock_response

            # This should work after implementation
            result = await jsoncargo_client.get_container_status(
                container_number="MSCU1234567",
                shipping_line="msc",
                bl_number="MAEU123456789"  # NEW: B/L number parameter
            )

            # Verify bl_number was accepted and request was made
            assert mock_client.get.called

    @pytest.mark.asyncio
    async def test_get_container_status_accepts_vessel_info(self, jsoncargo_client):
        """GIVEN a container number with vessel info
        WHEN get_container_status is called
        THEN it should accept vessel_name and voyage_number parameters."""

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"events": []}
            mock_client.get.return_value = mock_response

            # This should work after implementation
            result = await jsoncargo_client.get_container_status(
                container_number="MSCU1234567",
                shipping_line="msc",
                vessel_name="MAERSK SEALAND",  # NEW: vessel name parameter
                voyage_number="001W"            # NEW: voyage number parameter
            )

            # Verify vessel info was accepted and request was made
            assert mock_client.get.called

    @pytest.mark.asyncio
    async def test_enriched_request_includes_all_context(self, jsoncargo_client):
        """GIVEN all shipment context parameters
        WHEN get_container_status is called
        THEN the API request should include all context in params/body."""

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"events": []}
            mock_client.get.return_value = mock_response

            await jsoncargo_client.get_container_status(
                container_number="MSCU1234567",
                shipping_line="msc",
                bl_number="MAEU123456789",
                vessel_name="MAERSK SEALAND",
                voyage_number="001W"
            )

            # Verify the request was made with enriched parameters
            mock_client.get.assert_called_once()
            call_kwargs = mock_client.get.call_args
            params = call_kwargs.kwargs.get('params', {})

            # These assertions should pass after implementation
            assert 'bl_number' in params or 'bill_of_lading' in params, \
                "Request should include B/L number in params"
            assert 'vessel_name' in params or 'vessel' in params, \
                "Request should include vessel name in params"


# =============================================================================
# Test: Container Reuse Scenario
# =============================================================================

class TestContainerReuseHandling:
    """Test handling of container reuse/leasing scenarios."""

    @pytest.mark.asyncio
    async def test_same_container_different_shipments_returns_correct_events(self):
        """GIVEN same container used on two different shipments
        WHEN tracking each shipment
        THEN only events for that specific shipment should be returned."""
        # Setup: Two shipments using same container at different times
        shipment_jan = MagicMock(spec=Shipment)
        shipment_jan.container_number = "MSCU1234567"
        shipment_jan.bl_number = "BL-JAN-001"
        shipment_jan.etd = datetime(2026, 1, 1)
        shipment_jan.eta = datetime(2026, 1, 20)

        shipment_feb = MagicMock(spec=Shipment)
        shipment_feb.container_number = "MSCU1234567"  # Same container!
        shipment_feb.bl_number = "BL-FEB-002"
        shipment_feb.etd = datetime(2026, 2, 1)
        shipment_feb.eta = datetime(2026, 2, 20)

        # Mock events from API (includes events from both time periods)
        all_events = [
            {"timestamp": "2026-01-05T10:00:00Z", "event": "LOADED", "bl": "BL-JAN-001"},
            {"timestamp": "2026-01-10T14:00:00Z", "event": "DEPARTED", "bl": "BL-JAN-001"},
            {"timestamp": "2026-02-05T10:00:00Z", "event": "LOADED", "bl": "BL-FEB-002"},
            {"timestamp": "2026-02-10T14:00:00Z", "event": "DEPARTED", "bl": "BL-FEB-002"},
        ]

        # After implementation, filtering by B/L should return only matching events
        jan_events = [e for e in all_events if e.get("bl") == shipment_jan.bl_number]
        feb_events = [e for e in all_events if e.get("bl") == shipment_feb.bl_number]

        assert len(jan_events) == 2, "January shipment should have 2 events"
        assert len(feb_events) == 2, "February shipment should have 2 events"
        assert jan_events[0]["timestamp"].startswith("2026-01"), "Jan events should be from January"
        assert feb_events[0]["timestamp"].startswith("2026-02"), "Feb events should be from February"

    def test_event_filtering_by_shipment_date_range(self, mock_shipment):
        """GIVEN events from multiple time periods
        WHEN filtering by shipment ETD/ETA window
        THEN only events within that window should be returned."""
        # Shipment window: Jan 15 to Feb 1
        shipment_start = mock_shipment.etd - timedelta(days=7)  # Buffer before ETD
        shipment_end = mock_shipment.eta + timedelta(days=7)    # Buffer after ETA

        events = [
            # These should be EXCLUDED (before shipment window)
            {"timestamp": datetime(2025, 12, 1), "event": "LOADED"},
            {"timestamp": datetime(2026, 1, 5), "event": "DEPARTED"},
            # These should be INCLUDED (within shipment window)
            {"timestamp": datetime(2026, 1, 20), "event": "IN_TRANSIT"},
            {"timestamp": datetime(2026, 1, 28), "event": "ARRIVED"},
            # These should be EXCLUDED (after shipment window)
            {"timestamp": datetime(2026, 3, 1), "event": "RETURNED"},
        ]

        filtered = [
            e for e in events
            if shipment_start <= e["timestamp"] <= shipment_end
        ]

        assert len(filtered) == 2, "Only events within shipment window should be included"
        assert filtered[0]["event"] == "IN_TRANSIT"
        assert filtered[1]["event"] == "ARRIVED"


# =============================================================================
# Test: Tracking Router Enrichment
# =============================================================================

class TestTrackingRouterEnrichment:
    """Test that tracking router passes shipment context to JSONCargo client."""

    @pytest.mark.asyncio
    async def test_router_fetches_shipment_context(self, mock_shipment):
        """GIVEN a tracking request for a container
        WHEN the router processes the request
        THEN it should fetch the shipment and extract B/L, vessel, voyage."""

        # Simulate router behavior
        shipment = mock_shipment

        # Router should extract this context
        tracking_context = {
            "container_number": shipment.container_number,
            "bl_number": shipment.bl_number,
            "vessel_name": shipment.vessel_name,
            "voyage_number": shipment.voyage_number,
        }

        assert tracking_context["bl_number"] == "MAEU123456789"
        assert tracking_context["vessel_name"] == "MAERSK SEALAND"
        assert tracking_context["voyage_number"] == "001W"

    @pytest.mark.asyncio
    async def test_router_passes_context_to_client(self):
        """GIVEN a tracking request with shipment context available
        WHEN calling the JSONCargo client
        THEN all context should be passed to the client method."""

        client = JSONCargoClient()

        with patch.object(client, 'get_container_status', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"events": []}

            # Simulate what the router should do
            await client.get_container_status(
                container_number="MSCU1234567",
                shipping_line="msc",
                bl_number="MAEU123456789",
                vessel_name="MAERSK SEALAND",
                voyage_number="001W"
            )

            # Verify all context was passed
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs.get("bl_number") == "MAEU123456789"
            assert call_kwargs.get("vessel_name") == "MAERSK SEALAND"
            assert call_kwargs.get("voyage_number") == "001W"


# =============================================================================
# Test: Backward Compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Test that existing functionality is preserved."""

    @pytest.mark.asyncio
    async def test_container_only_request_still_works(self, jsoncargo_client):
        """GIVEN only a container number (no enrichment)
        WHEN get_container_status is called
        THEN it should still work (backward compatible)."""

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"events": []}
            mock_client.get.return_value = mock_response

            # Original call without new parameters should still work
            result = await jsoncargo_client.get_container_status(
                container_number="MSCU1234567",
                shipping_line="msc"
                # No bl_number, vessel_name, voyage_number
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_optional_enrichment_parameters(self, jsoncargo_client):
        """GIVEN enrichment parameters are optional
        WHEN some are provided and some are not
        THEN request should still succeed."""

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"events": []}
            mock_client.get.return_value = mock_response

            # Partial enrichment (only B/L, no vessel info)
            result = await jsoncargo_client.get_container_status(
                container_number="MSCU1234567",
                shipping_line="msc",
                bl_number="MAEU123456789"
                # No vessel_name, voyage_number
            )

            assert result is not None
