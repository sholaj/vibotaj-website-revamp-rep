"""Satellite deforestation detection service.

Sprint 14: AI-powered deforestation detection using satellite data.

Supported providers:
- Global Forest Watch (GFW) API - Free tier available
- Country-level fallback when API unavailable

Configuration:
    Set GFW_API_KEY in environment to enable satellite detection.
    Without API key, falls back to country-level risk assessment.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal
import httpx
from functools import lru_cache

from ..config import get_settings
from ..models.origin import RiskLevel

logger = logging.getLogger(__name__)
settings = get_settings()

# Cache TTL for satellite results (24 hours)
CACHE_TTL_HOURS = 24

# Global Forest Watch API configuration
GFW_API_BASE = "https://data-api.globalforestwatch.org"
GFW_TREE_COVER_LOSS_ENDPOINT = "/dataset/gfw_tree_cover_loss/latest/query"

# Country risk levels (fallback when API unavailable)
COUNTRY_RISK_LEVELS = {
    # Low risk countries (Europe)
    "DE": RiskLevel.LOW, "FR": RiskLevel.LOW, "NL": RiskLevel.LOW,
    "BE": RiskLevel.LOW, "IT": RiskLevel.LOW, "ES": RiskLevel.LOW,
    "PT": RiskLevel.LOW, "PL": RiskLevel.LOW, "CZ": RiskLevel.LOW,
    "AT": RiskLevel.LOW, "CH": RiskLevel.LOW, "DK": RiskLevel.LOW,
    "SE": RiskLevel.LOW, "NO": RiskLevel.LOW, "FI": RiskLevel.LOW,
    "UK": RiskLevel.LOW, "IE": RiskLevel.LOW,

    # Medium risk (some deforestation concerns)
    "NG": RiskLevel.MEDIUM,  # Nigeria - our main origin
    "GH": RiskLevel.MEDIUM,  # Ghana
    "CM": RiskLevel.MEDIUM,  # Cameroon
    "CI": RiskLevel.MEDIUM,  # Ivory Coast
    "KE": RiskLevel.MEDIUM,  # Kenya
    "TZ": RiskLevel.MEDIUM,  # Tanzania
    "UG": RiskLevel.MEDIUM,  # Uganda
    "ET": RiskLevel.MEDIUM,  # Ethiopia
    "IN": RiskLevel.MEDIUM,  # India
    "VN": RiskLevel.MEDIUM,  # Vietnam
    "ID": RiskLevel.MEDIUM,  # Indonesia (some regions)
    "MY": RiskLevel.MEDIUM,  # Malaysia (some regions)

    # High risk (significant deforestation)
    "BR": RiskLevel.HIGH,   # Brazil (Amazon)
    "CO": RiskLevel.HIGH,   # Colombia
    "PE": RiskLevel.HIGH,   # Peru
    "BO": RiskLevel.HIGH,   # Bolivia
    "PY": RiskLevel.HIGH,   # Paraguay
    "EC": RiskLevel.HIGH,   # Ecuador
    "CG": RiskLevel.HIGH,   # Congo
    "CD": RiskLevel.HIGH,   # DRC
}


class SatelliteService:
    """Service for satellite-based deforestation detection."""

    def __init__(self):
        self.api_key = os.getenv("GFW_API_KEY")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

    @property
    def is_available(self) -> bool:
        """Check if satellite API is configured."""
        return bool(self.api_key)

    def _get_cache_key(self, lat: float, lng: float) -> str:
        """Generate cache key for coordinates (rounded to 3 decimal places)."""
        return f"{round(lat, 3)}:{round(lng, 3)}"

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached result is still valid."""
        if key not in self._cache_timestamps:
            return False
        expires_at = self._cache_timestamps[key] + timedelta(hours=CACHE_TTL_HOURS)
        return datetime.utcnow() < expires_at

    async def check_deforestation(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        country: str,
        radius_km: float = 5.0
    ) -> Dict[str, Any]:
        """Check for deforestation at given coordinates.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            country: ISO 2-letter country code
            radius_km: Search radius in kilometers

        Returns:
            Dictionary with deforestation assessment:
            {
                "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
                "source": "satellite|country_baseline",
                "forest_loss_detected": bool,
                "forest_loss_hectares": float,
                "analysis_period": "YYYY-YYYY",
                "confidence": float (0-1),
                "provider": "Global Forest Watch"|null,
                "checked_at": "ISO timestamp",
                "recommendations": [...],
                "raw_data": {...}  # Original API response
            }
        """
        # Validate coordinates
        if latitude is None or longitude is None:
            return self._country_fallback(country, "No coordinates provided")

        lat = float(latitude)
        lng = float(longitude)

        # Check cache first
        cache_key = self._get_cache_key(lat, lng)
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached satellite result for {cache_key}")
            return self._cache[cache_key]

        # If API is not configured, use country fallback
        if not self.is_available:
            return self._country_fallback(country, "Satellite API not configured")

        # Call Global Forest Watch API
        try:
            result = await self._query_gfw(lat, lng, radius_km, country)

            # Cache result
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.utcnow()

            return result

        except Exception as e:
            logger.error(f"Satellite API error: {e}")
            return self._country_fallback(country, f"API error: {str(e)}")

    async def _query_gfw(
        self,
        lat: float,
        lng: float,
        radius_km: float,
        country: str
    ) -> Dict[str, Any]:
        """Query Global Forest Watch API for tree cover loss."""

        # Build query for point with buffer
        # GFW uses SQL-like queries
        query = {
            "sql": f"""
                SELECT SUM(area__ha) as total_loss_ha,
                       COUNT(*) as loss_events,
                       MAX(gfw_tree_cover_loss__year) as latest_year
                FROM data
                WHERE ST_DWithin(
                    ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography,
                    geometry::geography,
                    {radius_km * 1000}
                )
                AND gfw_tree_cover_loss__year >= 2020
            """
        }

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GFW_API_BASE}{GFW_TREE_COVER_LOSS_ENDPOINT}",
                json=query,
                headers=headers,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return self._process_gfw_response(data, lat, lng, country)
            elif response.status_code == 401:
                logger.error("GFW API authentication failed - check API key")
                return self._country_fallback(country, "API authentication failed")
            elif response.status_code == 429:
                logger.warning("GFW API rate limit reached")
                return self._country_fallback(country, "API rate limit reached")
            else:
                logger.error(f"GFW API error: {response.status_code}")
                return self._country_fallback(country, f"API returned {response.status_code}")

    def _process_gfw_response(
        self,
        data: Dict,
        lat: float,
        lng: float,
        country: str
    ) -> Dict[str, Any]:
        """Process Global Forest Watch API response."""

        # Extract results
        results = data.get("data", [{}])
        if not results:
            results = [{}]

        result = results[0]
        total_loss_ha = result.get("total_loss_ha", 0) or 0
        loss_events = result.get("loss_events", 0) or 0
        latest_year = result.get("latest_year")

        # Determine risk level based on forest loss
        forest_loss_detected = total_loss_ha > 0

        if total_loss_ha > 100:
            risk_level = RiskLevel.CRITICAL
        elif total_loss_ha > 50:
            risk_level = RiskLevel.HIGH
        elif total_loss_ha > 10:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Calculate confidence (higher with more recent data)
        confidence = 0.9 if latest_year and latest_year >= 2023 else 0.7

        return {
            "risk_level": risk_level.value,
            "source": "satellite",
            "forest_loss_detected": forest_loss_detected,
            "forest_loss_hectares": round(total_loss_ha, 2),
            "loss_events_count": loss_events,
            "analysis_period": "2020-present",
            "confidence": confidence,
            "provider": "Global Forest Watch",
            "coordinates": {"lat": lat, "lng": lng},
            "country": country,
            "checked_at": datetime.utcnow().isoformat(),
            "recommendations": self._get_recommendations(risk_level, forest_loss_detected),
            "eudr_article": "Article 9 - Risk Assessment",
            "raw_data": data
        }

    def _country_fallback(self, country: str, reason: str) -> Dict[str, Any]:
        """Return country-level risk when satellite data unavailable."""

        country_upper = country.upper() if country else "UNKNOWN"
        risk_level = COUNTRY_RISK_LEVELS.get(country_upper, RiskLevel.MEDIUM)

        return {
            "risk_level": risk_level.value,
            "source": "country_baseline",
            "forest_loss_detected": None,
            "forest_loss_hectares": None,
            "analysis_period": None,
            "confidence": 0.5,  # Lower confidence for country-level
            "provider": None,
            "coordinates": None,
            "country": country_upper,
            "checked_at": datetime.utcnow().isoformat(),
            "fallback_reason": reason,
            "recommendations": self._get_recommendations(risk_level, None),
            "eudr_article": "Article 9 - Risk Assessment",
            "satellite_check": {
                "available": False,
                "message": reason
            }
        }

    def _get_recommendations(
        self,
        risk_level: RiskLevel,
        forest_loss_detected: Optional[bool]
    ) -> list:
        """Generate recommendations based on risk assessment."""

        base_recommendations = {
            RiskLevel.LOW: [
                "Standard due diligence procedures apply",
                "Maintain documentation for 5 years",
            ],
            RiskLevel.MEDIUM: [
                "Enhanced due diligence recommended",
                "Request supplier deforestation-free declaration",
                "Consider on-site verification visit",
                "Maintain documentation for 5 years",
            ],
            RiskLevel.HIGH: [
                "Full due diligence required before import",
                "On-site verification strongly recommended",
                "Independent third-party audit advised",
                "Request recent satellite imagery (within 3 months)",
                "Maintain documentation for 5 years",
            ],
            RiskLevel.CRITICAL: [
                "DO NOT PROCEED - High deforestation risk detected",
                "Immediate supplier audit required",
                "Consider alternative sourcing locations",
                "Contact compliance team before any action",
                "This origin may not meet EUDR requirements",
            ],
        }

        recommendations = base_recommendations.get(
            risk_level,
            base_recommendations[RiskLevel.MEDIUM]
        )

        # Add specific recommendations if forest loss detected
        if forest_loss_detected:
            recommendations.insert(0, "ALERT: Forest loss detected in this area since 2020")
            recommendations.append("Verify production date is before deforestation event")

        return recommendations

    def clear_cache(self):
        """Clear the satellite results cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Satellite cache cleared")


# Global service instance
satellite_service = SatelliteService()


# Synchronous wrapper for compatibility with existing code
def check_deforestation_sync(
    latitude: Optional[float],
    longitude: Optional[float],
    country: str
) -> Dict[str, Any]:
    """Synchronous wrapper for deforestation check.

    For use in non-async contexts. Uses country-level fallback
    since async HTTP calls require async context.
    """
    if not satellite_service.is_available:
        return satellite_service._country_fallback(country, "Sync mode - using country baseline")

    # In sync context, use country fallback (async HTTP not available)
    return satellite_service._country_fallback(
        country,
        "Sync context - satellite API requires async. Use check_deforestation() in async context."
    )
