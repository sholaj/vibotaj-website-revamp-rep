"""Analytics schemas for API responses."""

from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime


class ShipmentStatsResponse(BaseModel):
    """Shipment statistics response."""
    total: int
    by_status: Dict[str, int]
    avg_transit_days: Optional[float]
    recent_shipments: int
    in_transit_count: int
    completed_this_month: int
    delayed_count: int


class DocumentStatsResponse(BaseModel):
    """Document statistics response."""
    total: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    completion_rate: float
    pending_validation: int
    expiring_soon: int
    recently_uploaded: int


class ComplianceMetricsResponse(BaseModel):
    """Compliance metrics response."""
    compliant_rate: float
    eudr_coverage: float
    shipments_needing_attention: int
    failed_documents: int
    issues_summary: Dict[str, int]


class TrackingStatsResponse(BaseModel):
    """Tracking statistics response."""
    total_events: int
    events_by_type: Dict[str, int]
    delays_detected: int
    avg_delay_hours: float
    recent_events_24h: int
    api_calls_today: int
    containers_tracked: int


class DashboardShipmentStats(BaseModel):
    """Shipment stats for dashboard."""
    total: int
    in_transit: int
    delivered_this_month: int
    with_delays: int


class DashboardDocumentStats(BaseModel):
    """Document stats for dashboard."""
    total: int
    pending_validation: int
    completion_rate: float
    expiring_soon: int


class DashboardComplianceStats(BaseModel):
    """Compliance stats for dashboard."""
    rate: float
    eudr_coverage: float
    needing_attention: int


class DashboardTrackingStats(BaseModel):
    """Tracking stats for dashboard."""
    events_today: int
    delays_detected: int
    containers_tracked: int


class DashboardStatsResponse(BaseModel):
    """Combined dashboard statistics response."""
    shipments: DashboardShipmentStats
    documents: DashboardDocumentStats
    compliance: DashboardComplianceStats
    tracking: DashboardTrackingStats
    generated_at: datetime


class ShipmentTrendDataPoint(BaseModel):
    """Single data point in shipment trend."""
    date: Optional[str]
    count: int


class ShipmentTrendsResponse(BaseModel):
    """Shipment trends over time response."""
    period_days: int
    group_by: str
    data: List[ShipmentTrendDataPoint]


class DocumentDistributionItem(BaseModel):
    """Single item in document distribution."""
    status: str
    count: int


class DocumentDistributionResponse(BaseModel):
    """Document distribution by status."""
    data: List[DocumentDistributionItem]
