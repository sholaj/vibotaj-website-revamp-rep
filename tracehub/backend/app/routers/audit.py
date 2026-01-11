"""Audit log router - provides access to audit trail (admin only)."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from ..database import get_db
from ..routers.auth import get_current_active_user
from ..schemas.user import CurrentUser
from ..services.audit_log import get_audit_logger, AuditAction

router = APIRouter()


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: str
    user_id: Optional[str]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    method: Optional[str]
    path: Optional[str]
    status_code: Optional[str]
    success: str
    details: dict
    error_message: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated audit log response."""
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    username: Optional[str] = Query(None, description="Filter by username"),
    action: Optional[str] = Query(None, description="Filter by action (use * suffix for prefix match)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    days: int = Query(7, ge=1, le=90, description="Look back period in days"),
    success_only: Optional[bool] = Query(None, description="Filter by success status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Query audit logs with filtering.

    Admin-only endpoint for reviewing system activity.
    Supports filtering by user, action type, resource, and time period.

    Note: Actions can be filtered with prefix matching using '*' suffix.
    For example: action="document.*" matches all document actions.
    """
    audit_logger = get_audit_logger()

    start_date = datetime.utcnow() - timedelta(days=days)

    # Multi-tenancy: filter by current user's organization
    org_id = str(current_user.organization_id) if current_user.organization_id else None

    logs = audit_logger.query(
        db=db,
        organization_id=org_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        success_only=success_only,
        limit=limit,
        offset=offset,
    )

    total = audit_logger.count(
        db=db,
        organization_id=org_id,
        username=username,
        action=action,
        start_date=start_date,
    )

    # Log this access
    audit_logger.log(
        AuditAction.AUDIT_LOG_VIEW,
        username=current_user.username,
        resource_type="audit_log",
        details={"filters": {
            "username": username,
            "action": action,
            "days": days,
        }},
        success=True,
        db=db,
    )

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                user_id=log.user_id,
                username=log.username,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                method=log.method,
                path=log.path,
                status_code=log.status_code,
                success=log.success,
                details=log.details or {},
                error_message=log.error_message,
                timestamp=log.timestamp,
            )
            for log in logs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/recent")
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100, description="Number of activities"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get recent activity feed for dashboard.

    Returns a simplified list of recent actions suitable for display
    in an activity feed widget.
    """
    audit_logger = get_audit_logger()

    # Multi-tenancy: filter by current user's organization
    org_id = str(current_user.organization_id) if current_user.organization_id else None

    activities = audit_logger.get_recent_activity(db, organization_id=org_id, limit=limit)

    return {"activities": activities}


@router.get("/summary")
async def get_audit_summary(
    days: int = Query(7, ge=1, le=30, description="Look back period"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get summary statistics from audit logs.

    Provides counts by action type for the specified period.
    """
    audit_logger = get_audit_logger()
    start_date = datetime.utcnow() - timedelta(days=days)

    # Multi-tenancy: filter by current user's organization
    org_id = str(current_user.organization_id) if current_user.organization_id else None

    # Get counts for key action categories
    summary = {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "counts": {
            "logins": audit_logger.count(db=db, organization_id=org_id, action=AuditAction.LOGIN_SUCCESS, start_date=start_date),
            "failed_logins": audit_logger.count(db=db, organization_id=org_id, action=AuditAction.LOGIN_FAILURE, start_date=start_date),
            "shipment_views": audit_logger.count(db=db, organization_id=org_id, action="shipment.*", start_date=start_date),
            "document_uploads": audit_logger.count(db=db, organization_id=org_id, action=AuditAction.DOCUMENT_UPLOAD, start_date=start_date),
            "document_downloads": audit_logger.count(db=db, organization_id=org_id, action=AuditAction.DOCUMENT_DOWNLOAD, start_date=start_date),
            "tracking_refreshes": audit_logger.count(db=db, organization_id=org_id, action=AuditAction.TRACKING_REFRESH, start_date=start_date),
            "audit_pack_downloads": audit_logger.count(db=db, organization_id=org_id, action=AuditAction.AUDIT_PACK_DOWNLOAD, start_date=start_date),
        }
    }

    return summary
