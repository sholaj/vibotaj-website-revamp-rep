"""Analytics router - provides metrics and statistics endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..routers.auth import get_current_active_user
from ..schemas.user import CurrentUser
from ..services.analytics import get_analytics_service
from ..services.audit_log import get_audit_logger, AuditAction

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get overall dashboard statistics.

    Returns combined metrics across shipments, documents, compliance, and tracking.
    Suitable for populating dashboard overview cards.
    """
    analytics = get_analytics_service(db, current_user.organization_id)
    stats = analytics.get_dashboard_stats()

    # Log analytics view
    audit_logger = get_audit_logger()
    audit_logger.log(
        AuditAction.ANALYTICS_VIEW,
        username=current_user.username,
        resource_type="analytics",
        resource_id="dashboard",
        success=True,
        db=db
    )

    return stats


@router.get("/shipments")
async def get_shipment_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get detailed shipment statistics.

    Returns:
        - total: Total number of shipments
        - by_status: Breakdown by shipment status
        - avg_transit_days: Average transit time
        - recent_shipments: Count created in last 30 days
        - in_transit_count: Currently in transit
        - completed_this_month: Delivered this month
        - delayed_count: Shipments with delays
    """
    analytics = get_analytics_service(db, current_user.organization_id)
    return analytics.get_shipment_stats()


@router.get("/shipments/trends")
async def get_shipment_trends(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Grouping interval"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get shipment creation trends over time.

    Useful for line charts showing shipment volume over time.

    Args:
        days: Number of days to look back (7-365)
        group_by: How to group data points ("day", "week", "month")

    Returns:
        List of {date, count} objects
    """
    analytics = get_analytics_service(db, current_user.organization_id)
    return {
        "period_days": days,
        "group_by": group_by,
        "data": analytics.get_shipments_over_time(days=days, group_by=group_by)
    }


@router.get("/documents")
async def get_document_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get detailed document statistics.

    Returns:
        - total: Total document count
        - by_status: Breakdown by document status
        - by_type: Breakdown by document type
        - completion_rate: Percentage of shipments with complete docs
        - pending_validation: Documents awaiting validation
        - expiring_soon: Documents expiring in 30 days
        - recently_uploaded: Documents uploaded in last 7 days
    """
    analytics = get_analytics_service(db, current_user.organization_id)
    return analytics.get_document_stats()


@router.get("/documents/distribution")
async def get_document_distribution(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get document status distribution for charts.

    Returns list of {status, count} suitable for pie/bar charts.
    """
    analytics = get_analytics_service(db, current_user.organization_id)
    return {
        "data": analytics.get_document_status_distribution()
    }


@router.get("/compliance")
async def get_compliance_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get compliance-related metrics.

    Returns:
        - compliant_rate: Percentage meeting compliance requirements
        - eudr_coverage: Percentage with EUDR documentation
        - shipments_needing_attention: Count requiring action
        - failed_documents: Documents that failed validation
        - issues_summary: Breakdown of compliance issues
    """
    analytics = get_analytics_service(db, current_user.organization_id)
    return analytics.get_compliance_metrics()


@router.get("/tracking")
async def get_tracking_metrics(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get container tracking statistics.

    Returns:
        - total_events: Total tracking events
        - events_by_type: Breakdown by event type
        - delays_detected: Number of delays
        - avg_delay_hours: Average delay duration
        - recent_events_24h: Events in last 24 hours
        - api_calls_today: Tracking API calls today
        - containers_tracked: Unique containers being tracked
    """
    analytics = get_analytics_service(db, current_user.organization_id)
    return analytics.get_tracking_stats()
