"""Notifications router - user notification management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from ..database import get_db
from ..models.notification import Notification, NotificationType
from ..routers.auth import get_current_active_user
from ..schemas.user import CurrentUser
from ..services.notifications import NotificationService

router = APIRouter()


# ============================================
# Response Models
# ============================================

class NotificationResponse(BaseModel):
    """Notification response model."""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    data: dict
    read: bool
    read_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response for notification list."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Response for unread count."""
    unread_count: int


class MarkReadResponse(BaseModel):
    """Response for mark as read operations."""
    message: str
    notification_id: Optional[str] = None
    marked_count: Optional[int] = None


# ============================================
# Endpoints
# ============================================

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = Query(default=False, description="Only return unread notifications"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum notifications to return"),
    offset: int = Query(default=0, ge=0, description="Number of notifications to skip"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get current user's notifications.

    Returns a list of notifications, most recent first.
    Optionally filter to only unread notifications.
    """
    service = NotificationService(db)

    notifications = service.get_user_notifications(
        user_id=str(current_user.id),
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    # Get total count for pagination
    total_query = db.query(Notification).filter(
        Notification.user_id == current_user.id  # Compare UUID directly
    )
    if unread_only:
        total_query = total_query.filter(Notification.read == False)
    total = total_query.count()

    # Get unread count
    unread_count = service.get_unread_count(str(current_user.id))

    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=str(n.id),
                user_id=str(n.user_id),  # Convert UUID to string
                type=n.type,
                title=n.title,
                message=n.message,
                data=n.data or {},
                read=n.read,
                read_at=n.read_at.isoformat() if n.read_at else None,
                created_at=n.created_at.isoformat() if n.created_at else ""
            )
            for n in notifications
        ],
        total=total,
        unread_count=unread_count
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get count of unread notifications for current user.

    Lightweight endpoint for updating notification badges.
    """
    service = NotificationService(db)
    count = service.get_unread_count(str(current_user.id))

    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Mark a specific notification as read.
    """
    service = NotificationService(db)

    notification = service.mark_as_read(
        notification_id=notification_id,
        user_id=str(current_user.id)
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    db.commit()

    return MarkReadResponse(
        message="Notification marked as read",
        notification_id=str(notification_id)
    )


@router.post("/read-all", response_model=MarkReadResponse)
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Mark all notifications as read for current user.
    """
    service = NotificationService(db)
    count = service.mark_all_read(user_id=str(current_user.id))
    db.commit()

    return MarkReadResponse(
        message=f"Marked {count} notifications as read",
        marked_count=count
    )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Delete a notification.
    """
    service = NotificationService(db)

    deleted = service.delete_notification(
        notification_id=notification_id,
        user_id=str(current_user.id)
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    db.commit()

    return {"message": "Notification deleted", "notification_id": str(notification_id)}


@router.get("/types")
async def get_notification_types(
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get available notification types with descriptions.
    """
    type_descriptions = {
        NotificationType.DOCUMENT_UPLOADED.value: {
            "name": "Document Uploaded",
            "description": "A new document has been uploaded and needs review",
            "icon": "file-plus",
            "color": "blue"
        },
        NotificationType.DOCUMENT_VALIDATED.value: {
            "name": "Document Validated",
            "description": "A document has been approved",
            "icon": "check-circle",
            "color": "green"
        },
        NotificationType.DOCUMENT_REJECTED.value: {
            "name": "Document Rejected",
            "description": "A document has been rejected and needs attention",
            "icon": "x-circle",
            "color": "red"
        },
        NotificationType.ETA_CHANGED.value: {
            "name": "ETA Changed",
            "description": "Shipment arrival time has been updated",
            "icon": "clock",
            "color": "yellow"
        },
        NotificationType.SHIPMENT_ARRIVED.value: {
            "name": "Shipment Arrived",
            "description": "Container has arrived at destination port",
            "icon": "anchor",
            "color": "green"
        },
        NotificationType.SHIPMENT_DEPARTED.value: {
            "name": "Shipment Departed",
            "description": "Container has departed from origin",
            "icon": "ship",
            "color": "blue"
        },
        NotificationType.SHIPMENT_DELIVERED.value: {
            "name": "Shipment Delivered",
            "description": "Shipment has been delivered to final destination",
            "icon": "package-check",
            "color": "green"
        },
        NotificationType.COMPLIANCE_ALERT.value: {
            "name": "Compliance Alert",
            "description": "Compliance issue requires attention",
            "icon": "alert-triangle",
            "color": "orange"
        },
        NotificationType.EXPIRY_WARNING.value: {
            "name": "Expiry Warning",
            "description": "A document is approaching its expiry date",
            "icon": "calendar-alert",
            "color": "yellow"
        },
        NotificationType.SYSTEM_ALERT.value: {
            "name": "System Alert",
            "description": "System notification",
            "icon": "info",
            "color": "gray"
        }
    }

    return {
        "types": type_descriptions
    }
