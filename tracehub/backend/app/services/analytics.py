"""Analytics service - provides metrics and statistics for the dashboard."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from ..models import (
    Shipment, ShipmentStatus,
    Document, DocumentType, DocumentStatus,
    ContainerEvent, EventType,
)
from ..models.audit_log import AuditLog
from .audit_log import AuditAction


class AnalyticsService:
    """Service for generating analytics and metrics."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    def get_shipment_stats(self) -> Dict[str, Any]:
        """
        Get shipment statistics.

        Returns:
            - total: Total number of shipments
            - by_status: Count of shipments by status
            - avg_transit_days: Average transit time in days
            - recent_shipments: Number created in last 30 days
            - in_transit_count: Number currently in transit
            - completed_this_month: Number delivered this month
        """
        # Total shipments
        total = self.db.query(Shipment).count()

        # Count by status
        status_counts = (
            self.db.query(
                Shipment.status,
                func.count(Shipment.id).label('count')
            )
            .group_by(Shipment.status)
            .all()
        )

        by_status = {status.value: count for status, count in status_counts}

        # Fill in zeros for missing statuses
        for status in ShipmentStatus:
            if status.value not in by_status:
                by_status[status.value] = 0

        # Average transit time (for delivered shipments with ATD and ATA)
        avg_transit_result = (
            self.db.query(
                func.avg(
                    func.extract('epoch', Shipment.ata) -
                    func.extract('epoch', Shipment.atd)
                ) / 86400  # Convert seconds to days
            )
            .filter(
                Shipment.atd.isnot(None),
                Shipment.ata.isnot(None),
                Shipment.status.in_([ShipmentStatus.DELIVERED, ShipmentStatus.CLOSED])
            )
            .scalar()
        )

        avg_transit_days = round(avg_transit_result, 1) if avg_transit_result else None

        # Recent shipments (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_count = (
            self.db.query(Shipment)
            .filter(Shipment.created_at >= thirty_days_ago)
            .count()
        )

        # Completed this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = (
            self.db.query(Shipment)
            .filter(
                Shipment.status.in_([ShipmentStatus.DELIVERED, ShipmentStatus.CLOSED]),
                Shipment.updated_at >= month_start
            )
            .count()
        )

        # Shipments with delays
        delayed_count = (
            self.db.query(Shipment)
            .join(ContainerEvent)
            .filter(ContainerEvent.delay_hours > 0)
            .distinct()
            .count()
        )

        return {
            "total": total,
            "by_status": by_status,
            "avg_transit_days": avg_transit_days,
            "recent_shipments": recent_count,
            "in_transit_count": by_status.get("in_transit", 0),
            "completed_this_month": completed_this_month,
            "delayed_count": delayed_count,
        }

    def get_document_stats(self) -> Dict[str, Any]:
        """
        Get document statistics.

        Returns:
            - total: Total number of documents
            - by_status: Count by document status
            - by_type: Count by document type
            - completion_rate: Percentage of shipments with complete docs
            - common_missing: Most commonly missing document types
            - pending_validation: Documents awaiting validation
        """
        # Total documents
        total = self.db.query(Document).count()

        # Count by status
        status_counts = (
            self.db.query(
                Document.status,
                func.count(Document.id).label('count')
            )
            .group_by(Document.status)
            .all()
        )

        by_status = {status.value: count for status, count in status_counts}

        # Fill in zeros for missing statuses
        for status in DocumentStatus:
            if status.value not in by_status:
                by_status[status.value] = 0

        # Count by type
        type_counts = (
            self.db.query(
                Document.document_type,
                func.count(Document.id).label('count')
            )
            .group_by(Document.document_type)
            .all()
        )

        by_type = {doc_type.value: count for doc_type, count in type_counts}

        # Pending validation count
        pending_validation = by_status.get("uploaded", 0)

        # Calculate completion rate
        # A shipment is "complete" if it has at least 5 validated/compliance_ok documents
        shipments_with_complete_docs = (
            self.db.query(Document.shipment_id)
            .filter(Document.status.in_([
                DocumentStatus.VALIDATED,
                DocumentStatus.COMPLIANCE_OK,
                DocumentStatus.LINKED
            ]))
            .group_by(Document.shipment_id)
            .having(func.count(Document.id) >= 5)
            .count()
        )

        total_shipments = self.db.query(Shipment).count()
        completion_rate = (
            round((shipments_with_complete_docs / total_shipments) * 100, 1)
            if total_shipments > 0 else 0
        )

        # Expiring soon (within 30 days)
        thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
        expiring_soon = (
            self.db.query(Document)
            .filter(
                Document.expiry_date.isnot(None),
                Document.expiry_date <= thirty_days_from_now.date(),
                Document.expiry_date >= datetime.utcnow().date()
            )
            .count()
        )

        # Recently uploaded (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recently_uploaded = (
            self.db.query(Document)
            .filter(Document.created_at >= seven_days_ago)
            .count()
        )

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "completion_rate": completion_rate,
            "pending_validation": pending_validation,
            "expiring_soon": expiring_soon,
            "recently_uploaded": recently_uploaded,
        }

    def get_compliance_metrics(self) -> Dict[str, Any]:
        """
        Get compliance-related metrics.

        Returns:
            - compliant_rate: Percentage of shipments meeting compliance
            - issues_by_type: Compliance issues grouped by type
            - eudr_coverage: Percentage with EUDR documentation
            - shipments_needing_attention: Shipments with compliance flags
        """
        total_shipments = self.db.query(Shipment).count()

        if total_shipments == 0:
            return {
                "compliant_rate": 0,
                "eudr_coverage": 0,
                "shipments_needing_attention": 0,
                "failed_documents": 0,
                "issues_summary": {},
            }

        # Shipments with all required docs validated
        # Using docs_complete status as proxy for compliance
        compliant_count = (
            self.db.query(Shipment)
            .filter(Shipment.status.in_([
                ShipmentStatus.DOCS_COMPLETE,
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.ARRIVED,
                ShipmentStatus.DELIVERED,
                ShipmentStatus.CLOSED,
            ]))
            .count()
        )

        compliant_rate = round((compliant_count / total_shipments) * 100, 1)

        # EUDR documentation coverage
        shipments_with_eudr = (
            self.db.query(Document.shipment_id)
            .filter(
                Document.document_type == DocumentType.EUDR_DUE_DILIGENCE,
                Document.status.in_([
                    DocumentStatus.VALIDATED,
                    DocumentStatus.COMPLIANCE_OK,
                    DocumentStatus.LINKED
                ])
            )
            .distinct()
            .count()
        )

        eudr_coverage = round((shipments_with_eudr / total_shipments) * 100, 1)

        # Shipments needing attention (docs_pending or failed docs)
        shipments_with_failed_docs = (
            self.db.query(Document.shipment_id)
            .filter(Document.status == DocumentStatus.COMPLIANCE_FAILED)
            .distinct()
            .subquery()
        )

        needing_attention = (
            self.db.query(Shipment)
            .filter(
                (Shipment.status == ShipmentStatus.DOCS_PENDING) |
                (Shipment.id.in_(shipments_with_failed_docs))
            )
            .count()
        )

        # Failed document count
        failed_documents = (
            self.db.query(Document)
            .filter(Document.status == DocumentStatus.COMPLIANCE_FAILED)
            .count()
        )

        # Issues summary
        issues_summary = {
            "missing_documents": (
                self.db.query(Shipment)
                .filter(Shipment.status == ShipmentStatus.DOCS_PENDING)
                .count()
            ),
            "failed_validation": failed_documents,
            "expiring_certificates": (
                self.db.query(Document)
                .filter(
                    Document.expiry_date.isnot(None),
                    Document.expiry_date <= (datetime.utcnow() + timedelta(days=30)).date()
                )
                .count()
            ),
        }

        return {
            "compliant_rate": compliant_rate,
            "eudr_coverage": eudr_coverage,
            "shipments_needing_attention": needing_attention,
            "failed_documents": failed_documents,
            "issues_summary": issues_summary,
        }

    def get_tracking_stats(self) -> Dict[str, Any]:
        """
        Get container tracking statistics.

        Returns:
            - total_events: Total tracking events recorded
            - events_by_type: Events grouped by type
            - delays_detected: Number of delay events
            - avg_delay_hours: Average delay duration
            - api_calls_today: Tracking API calls today (from audit log)
        """
        # Total events
        total_events = self.db.query(ContainerEvent).count()

        # Events by type
        type_counts = (
            self.db.query(
                ContainerEvent.event_type,
                func.count(ContainerEvent.id).label('count')
            )
            .group_by(ContainerEvent.event_type)
            .all()
        )

        events_by_type = {event_type.value: count for event_type, count in type_counts}

        # Delays detected
        delays_detected = (
            self.db.query(ContainerEvent)
            .filter(ContainerEvent.delay_hours > 0)
            .count()
        )

        # Average delay
        avg_delay = (
            self.db.query(func.avg(ContainerEvent.delay_hours))
            .filter(ContainerEvent.delay_hours > 0)
            .scalar()
        )

        avg_delay_hours = round(avg_delay, 1) if avg_delay else 0

        # Recent tracking activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_events = (
            self.db.query(ContainerEvent)
            .filter(ContainerEvent.created_at >= yesterday)
            .count()
        )

        # API calls today from audit log
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        api_calls_today = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.action.like("tracking.%"),
                AuditLog.timestamp >= today_start
            )
            .count()
        )

        # Containers being tracked (unique containers with events)
        containers_tracked = (
            self.db.query(Shipment.container_number)
            .join(ContainerEvent)
            .distinct()
            .count()
        )

        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "delays_detected": delays_detected,
            "avg_delay_hours": avg_delay_hours,
            "recent_events_24h": recent_events,
            "api_calls_today": api_calls_today,
            "containers_tracked": containers_tracked,
        }

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get combined statistics for the dashboard overview.

        Returns aggregated stats from all domains.
        """
        shipment_stats = self.get_shipment_stats()
        document_stats = self.get_document_stats()
        compliance_metrics = self.get_compliance_metrics()
        tracking_stats = self.get_tracking_stats()

        return {
            "shipments": {
                "total": shipment_stats["total"],
                "in_transit": shipment_stats["in_transit_count"],
                "delivered_this_month": shipment_stats["completed_this_month"],
                "with_delays": shipment_stats["delayed_count"],
            },
            "documents": {
                "total": document_stats["total"],
                "pending_validation": document_stats["pending_validation"],
                "completion_rate": document_stats["completion_rate"],
                "expiring_soon": document_stats["expiring_soon"],
            },
            "compliance": {
                "rate": compliance_metrics["compliant_rate"],
                "eudr_coverage": compliance_metrics["eudr_coverage"],
                "needing_attention": compliance_metrics["shipments_needing_attention"],
            },
            "tracking": {
                "events_today": tracking_stats["recent_events_24h"],
                "delays_detected": tracking_stats["delays_detected"],
                "containers_tracked": tracking_stats["containers_tracked"],
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_shipments_over_time(
        self,
        days: int = 30,
        group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get shipment creation trends over time.

        Args:
            days: Number of days to look back
            group_by: Grouping interval ("day", "week", "month")

        Returns:
            List of date/count pairs
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        if group_by == "day":
            date_trunc = func.date_trunc('day', Shipment.created_at)
        elif group_by == "week":
            date_trunc = func.date_trunc('week', Shipment.created_at)
        else:
            date_trunc = func.date_trunc('month', Shipment.created_at)

        results = (
            self.db.query(
                date_trunc.label('date'),
                func.count(Shipment.id).label('count')
            )
            .filter(Shipment.created_at >= start_date)
            .group_by(date_trunc)
            .order_by(date_trunc)
            .all()
        )

        return [
            {"date": date.isoformat() if date else None, "count": count}
            for date, count in results
        ]

    def get_document_status_distribution(self) -> List[Dict[str, Any]]:
        """Get document count by status for pie chart."""
        results = (
            self.db.query(
                Document.status,
                func.count(Document.id).label('count')
            )
            .group_by(Document.status)
            .all()
        )

        return [
            {"status": status.value, "count": count}
            for status, count in results
        ]


def get_analytics_service(db: Session) -> AnalyticsService:
    """Factory function to create analytics service."""
    return AnalyticsService(db)
