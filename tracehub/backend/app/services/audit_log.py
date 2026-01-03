"""Audit logging service - tracks user actions for compliance and debugging."""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.audit_log import AuditLog
from ..database import SessionLocal

logger = logging.getLogger(__name__)

# Action constants for consistent logging
class AuditAction:
    """Predefined audit action types."""
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"

    # Shipments
    SHIPMENT_LIST = "shipment.list"
    SHIPMENT_VIEW = "shipment.view"
    SHIPMENT_CREATE = "shipment.create"
    SHIPMENT_UPDATE = "shipment.update"
    SHIPMENT_DELETE = "shipment.delete"

    # Documents
    DOCUMENT_LIST = "document.list"
    DOCUMENT_VIEW = "document.view"
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_DOWNLOAD = "document.download"
    DOCUMENT_VALIDATE = "document.validate"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_TRANSITION = "document.transition"

    # Tracking
    TRACKING_STATUS = "tracking.status"
    TRACKING_REFRESH = "tracking.refresh"
    TRACKING_LIVE = "tracking.live"

    # Audit Pack
    AUDIT_PACK_DOWNLOAD = "auditpack.download"

    # Analytics
    ANALYTICS_VIEW = "analytics.view"

    # Admin
    AUDIT_LOG_VIEW = "admin.auditlog.view"


class AuditLogger:
    """Service for logging and querying audit events."""

    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self._db = db
        self._request_id: Optional[str] = None

    @property
    def db(self) -> Session:
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def set_request_id(self, request_id: str):
        """Set the current request ID for correlation."""
        self._request_id = request_id

    def log(
        self,
        action: str,
        *,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None,
        db: Optional[Session] = None,
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            action: The action being performed (use AuditAction constants)
            user_id: ID of the user performing the action
            username: Username of the user
            ip_address: Client IP address
            user_agent: Client user agent string
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            method: HTTP method
            path: Request path
            status_code: HTTP response status code
            success: Whether the action succeeded
            details: Additional action-specific details
            error_message: Error message if action failed
            duration_ms: Request duration in milliseconds
            db: Optional database session (uses instance session if not provided)

        Returns:
            The created AuditLog record
        """
        session = db or self.db

        audit_entry = AuditLog(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            request_id=self._request_id or str(uuid.uuid4()),
            method=method,
            path=path[:500] if path else None,
            status_code=str(status_code) if status_code else None,
            success="true" if success else "false",
            details=details or {},
            error_message=error_message,
            duration_ms=str(int(duration_ms)) if duration_ms else None,
            timestamp=datetime.utcnow(),
        )

        try:
            session.add(audit_entry)
            session.commit()
            logger.debug(f"Audit log created: {action} by {username}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create audit log: {e}")
            raise

        return audit_entry

    def query(
        self,
        *,
        db: Session,
        username: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.

        Args:
            db: Database session
            username: Filter by username
            action: Filter by action (supports prefix matching)
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            success_only: If True, only return successful actions
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of matching AuditLog records
        """
        query = db.query(AuditLog)

        filters = []

        if username:
            filters.append(AuditLog.username == username)

        if action:
            if action.endswith("*"):
                # Prefix matching
                filters.append(AuditLog.action.like(f"{action[:-1]}%"))
            else:
                filters.append(AuditLog.action == action)

        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)

        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)

        if start_date:
            filters.append(AuditLog.timestamp >= start_date)

        if end_date:
            filters.append(AuditLog.timestamp <= end_date)

        if success_only is not None:
            filters.append(AuditLog.success == ("true" if success_only else "false"))

        if filters:
            query = query.filter(and_(*filters))

        return (
            query
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count(
        self,
        *,
        db: Session,
        username: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count audit logs matching filters."""
        query = db.query(AuditLog)

        filters = []

        if username:
            filters.append(AuditLog.username == username)

        if action:
            if action.endswith("*"):
                filters.append(AuditLog.action.like(f"{action[:-1]}%"))
            else:
                filters.append(AuditLog.action == action)

        if start_date:
            filters.append(AuditLog.timestamp >= start_date)

        if end_date:
            filters.append(AuditLog.timestamp <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        return query.count()

    def get_recent_activity(
        self,
        db: Session,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity feed for dashboard.

        Returns simplified activity items suitable for display.
        """
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.success == "true")
            .filter(AuditLog.action.notin_([
                AuditAction.SHIPMENT_LIST,
                AuditAction.ANALYTICS_VIEW,
            ]))
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )

        activities = []
        for log in logs:
            activities.append({
                "id": str(log.id),
                "action": log.action,
                "username": log.username,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.timestamp.isoformat(),
                "details": log.details,
            })

        return activities

    def cleanup_old_logs(
        self,
        db: Session,
        retention_days: int = 90,
    ) -> int:
        """
        Delete audit logs older than retention period.

        Args:
            db: Database session
            retention_days: Number of days to retain logs

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        result = (
            db.query(AuditLog)
            .filter(AuditLog.timestamp < cutoff_date)
            .delete(synchronize_session=False)
        )

        db.commit()
        logger.info(f"Cleaned up {result} audit logs older than {retention_days} days")

        return result


# Global audit logger instance
audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    return audit_logger
