"""Notification service for creating and managing user notifications."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.notification import Notification, NotificationType
from ..models.document import Document, DocumentType
from ..models.shipment import Shipment


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: str,  # UUID string - Sprint 11: changed from email to user UUID
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a new notification for a user.

        Args:
            user_id: User UUID as string (str(user.id))
            notification_type: Type of notification (from NotificationType enum)
            title: Short notification title
            message: Full notification message
            data: Optional additional data (shipment_id, document_id, etc.)

        Returns:
            Created Notification object
        """
        notification = Notification(
            user_id=UUID(user_id),  # Convert string to UUID
            type=notification_type,
            title=title,
            message=message,
            data=data or {},
            read=False,
            created_at=datetime.utcnow()
        )
        self.db.add(notification)
        self.db.flush()  # Get the ID without committing
        return notification

    def get_user_notifications(
        self,
        user_id: str,  # UUID string
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: User UUID as string (str(user.id))
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip

        Returns:
            List of Notification objects
        """
        query = self.db.query(Notification).filter(
            Notification.user_id == UUID(user_id)
        )

        if unread_only:
            query = query.filter(Notification.read == False)

        return query.order_by(
            Notification.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User UUID as string (str(user.id))

        Returns:
            Count of unread notifications
        """
        return self.db.query(Notification).filter(
            Notification.user_id == UUID(user_id),
            Notification.read == False
        ).count()

    def mark_as_read(self, notification_id: UUID, user_id: str) -> Optional[Notification]:
        """
        Mark a specific notification as read.

        Args:
            notification_id: UUID of the notification
            user_id: User UUID as string (str(user.id)) for authorization

        Returns:
            Updated Notification or None if not found
        """
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == UUID(user_id)
        ).first()

        if notification and not notification.read:
            notification.read = True
            notification.read_at = datetime.utcnow()
            self.db.flush()

        return notification

    def mark_all_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User UUID as string (str(user.id))

        Returns:
            Number of notifications marked as read
        """
        count = self.db.query(Notification).filter(
            Notification.user_id == UUID(user_id),
            Notification.read == False
        ).update({
            "read": True,
            "read_at": datetime.utcnow()
        })
        self.db.flush()
        return count

    def delete_notification(self, notification_id: UUID, user_id: str) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: UUID of the notification
            user_id: User UUID as string (str(user.id)) for authorization

        Returns:
            True if deleted, False if not found
        """
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == UUID(user_id)
        ).first()

        if notification:
            self.db.delete(notification)
            self.db.flush()
            return True
        return False


# ============================================
# Event-triggered notification creators
# ============================================

def notify_document_uploaded(
    db: Session,
    document: Document,
    uploader: str,
    notify_users: List[str]
) -> List[Notification]:
    """
    Create notifications when a document is uploaded.
    Typically notifies compliance team/admins.
    """
    service = NotificationService(db)
    notifications = []

    document_type_display = document.document_type.value.replace('_', ' ').title()

    for user_id in notify_users:
        if user_id != uploader:  # Don't notify the uploader
            notification = service.create_notification(
                user_id=user_id,
                notification_type=NotificationType.DOCUMENT_UPLOADED.value,
                title=f"New Document Uploaded",
                message=f"{document_type_display} has been uploaded for review. Uploaded by {uploader}.",
                data={
                    "document_id": str(document.id),
                    "document_type": document.document_type.value,
                    "document_name": document.name,
                    "shipment_id": str(document.shipment_id),
                    "uploaded_by": uploader
                }
            )
            notifications.append(notification)

    return notifications


def notify_document_validated(
    db: Session,
    document: Document,
    validator: str,
    uploader: str
) -> Optional[Notification]:
    """
    Create notification when a document is validated/approved.
    Notifies the original uploader.
    """
    if uploader == validator:
        return None

    service = NotificationService(db)
    document_type_display = document.document_type.value.replace('_', ' ').title()

    return service.create_notification(
        user_id=uploader,
        notification_type=NotificationType.DOCUMENT_VALIDATED.value,
        title=f"Document Approved",
        message=f"Your {document_type_display} has been validated and approved by {validator}.",
        data={
            "document_id": str(document.id),
            "document_type": document.document_type.value,
            "document_name": document.name,
            "shipment_id": str(document.shipment_id),
            "validated_by": validator
        }
    )


def notify_document_rejected(
    db: Session,
    document: Document,
    rejector: str,
    uploader: str,
    reason: str
) -> Optional[Notification]:
    """
    Create notification when a document is rejected.
    Notifies the original uploader with rejection reason.
    """
    if uploader == rejector:
        return None

    service = NotificationService(db)
    document_type_display = document.document_type.value.replace('_', ' ').title()

    return service.create_notification(
        user_id=uploader,
        notification_type=NotificationType.DOCUMENT_REJECTED.value,
        title=f"Document Rejected",
        message=f"Your {document_type_display} has been rejected. Reason: {reason}",
        data={
            "document_id": str(document.id),
            "document_type": document.document_type.value,
            "document_name": document.name,
            "shipment_id": str(document.shipment_id),
            "rejected_by": rejector,
            "rejection_reason": reason
        }
    )


def notify_document_expiring(
    db: Session,
    document: Document,
    days_until_expiry: int,
    notify_users: List[str]
) -> List[Notification]:
    """
    Create notifications for documents nearing expiry.
    Notifies admins and relevant parties.
    """
    service = NotificationService(db)
    notifications = []

    document_type_display = document.document_type.value.replace('_', ' ').title()
    urgency = "URGENT: " if days_until_expiry <= 7 else ""

    for user_id in notify_users:
        notification = service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.EXPIRY_WARNING.value,
            title=f"{urgency}Document Expiring Soon",
            message=f"{document_type_display} expires in {days_until_expiry} days. Please renew or replace.",
            data={
                "document_id": str(document.id),
                "document_type": document.document_type.value,
                "document_name": document.name,
                "shipment_id": str(document.shipment_id),
                "expiry_date": document.expiry_date.isoformat() if document.expiry_date else None,
                "days_until_expiry": days_until_expiry
            }
        )
        notifications.append(notification)

    return notifications


def notify_shipment_status_change(
    db: Session,
    shipment: Shipment,
    old_status: str,
    new_status: str,
    notify_users: List[str],
    event_details: Optional[Dict[str, Any]] = None
) -> List[Notification]:
    """
    Create notifications for shipment status changes.
    Notifies buyers and relevant parties.
    """
    service = NotificationService(db)
    notifications = []

    # Determine notification type and message based on new status
    status_messages = {
        "in_transit": {
            "type": NotificationType.SHIPMENT_DEPARTED.value,
            "title": "Shipment Departed",
            "message": f"Shipment {shipment.reference} has departed from origin."
        },
        "arrived": {
            "type": NotificationType.SHIPMENT_ARRIVED.value,
            "title": "Shipment Arrived",
            "message": f"Shipment {shipment.reference} has arrived at destination port."
        },
        "delivered": {
            "type": NotificationType.SHIPMENT_DELIVERED.value,
            "title": "Shipment Delivered",
            "message": f"Shipment {shipment.reference} has been delivered successfully."
        }
    }

    status_info = status_messages.get(new_status)
    if not status_info:
        return notifications

    for user_id in notify_users:
        data = {
            "shipment_id": str(shipment.id),
            "shipment_reference": shipment.reference,
            "container_number": shipment.container_number,
            "old_status": old_status,
            "new_status": new_status
        }
        if event_details:
            data.update(event_details)

        notification = service.create_notification(
            user_id=user_id,
            notification_type=status_info["type"],
            title=status_info["title"],
            message=status_info["message"],
            data=data
        )
        notifications.append(notification)

    return notifications


def notify_eta_changed(
    db: Session,
    shipment: Shipment,
    old_eta: Optional[datetime],
    new_eta: datetime,
    notify_users: List[str]
) -> List[Notification]:
    """
    Create notifications when ETA changes.
    Notifies buyers and relevant parties.
    """
    service = NotificationService(db)
    notifications = []

    old_eta_str = old_eta.strftime('%Y-%m-%d %H:%M') if old_eta else "Not set"
    new_eta_str = new_eta.strftime('%Y-%m-%d %H:%M')

    # Determine if it's a delay or improvement
    if old_eta and new_eta > old_eta:
        title = "ETA Delayed"
        message = f"Shipment {shipment.reference} ETA has been delayed. New ETA: {new_eta_str}"
    elif old_eta and new_eta < old_eta:
        title = "ETA Updated - Earlier Arrival"
        message = f"Shipment {shipment.reference} now expected earlier. New ETA: {new_eta_str}"
    else:
        title = "ETA Updated"
        message = f"Shipment {shipment.reference} ETA has been updated to {new_eta_str}"

    for user_id in notify_users:
        notification = service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.ETA_CHANGED.value,
            title=title,
            message=message,
            data={
                "shipment_id": str(shipment.id),
                "shipment_reference": shipment.reference,
                "container_number": shipment.container_number,
                "old_eta": old_eta_str,
                "new_eta": new_eta_str
            }
        )
        notifications.append(notification)

    return notifications


def notify_compliance_alert(
    db: Session,
    shipment: Shipment,
    alert_message: str,
    missing_documents: List[str],
    notify_users: List[str]
) -> List[Notification]:
    """
    Create notifications for compliance issues.
    Notifies compliance team and admins.
    """
    service = NotificationService(db)
    notifications = []

    for user_id in notify_users:
        notification = service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.COMPLIANCE_ALERT.value,
            title="Compliance Alert",
            message=f"Shipment {shipment.reference}: {alert_message}",
            data={
                "shipment_id": str(shipment.id),
                "shipment_reference": shipment.reference,
                "container_number": shipment.container_number,
                "missing_documents": missing_documents,
                "alert_message": alert_message
            }
        )
        notifications.append(notification)

    return notifications
