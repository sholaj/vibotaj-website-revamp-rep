"""User deletion service - handles soft and hard delete operations.

This service provides:
- Soft delete: Sets deleted_at timestamp, blocks auth, preserves record for audit
- Hard delete: Physically removes user record, anonymizes audit log references
- Restore: Restores soft-deleted users

All deletion operations:
- Require a reason for audit trail
- Check guards (cannot delete self, last admin, higher-role user)
- Create audit log entries
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.user import User, UserRole
from ..models.organization import OrganizationMembership, OrgRole
from ..models.audit_log import AuditLog
from ..services.audit_log import AuditLogger, AuditAction

logger = logging.getLogger(__name__)


class UserDeletionError(Exception):
    """Base exception for user deletion errors."""
    pass


class CannotDeleteSelfError(UserDeletionError):
    """Raised when a user tries to delete themselves."""
    pass


class CannotDeleteLastAdminError(UserDeletionError):
    """Raised when trying to delete the last admin of an organization."""
    pass


class CannotDeleteHigherRoleError(UserDeletionError):
    """Raised when trying to delete a user with a higher role."""
    pass


class UserNotFoundError(UserDeletionError):
    """Raised when the target user is not found."""
    pass


class UserAlreadyDeletedError(UserDeletionError):
    """Raised when trying to delete an already deleted user."""
    pass


class UserNotDeletedError(UserDeletionError):
    """Raised when trying to restore a user that is not deleted."""
    pass


class InvalidDeletionReasonError(UserDeletionError):
    """Raised when the deletion reason is invalid."""
    pass


# Add audit action constants for user deletion
class UserAuditAction:
    """Audit action types for user deletion."""
    USER_SOFT_DELETE = "user.delete.soft"
    USER_HARD_DELETE = "user.delete.hard"
    USER_RESTORE = "user.restore"
    USER_DELETE_ATTEMPT_BLOCKED = "user.delete.blocked"


# Role hierarchy for permission checks
ROLE_HIERARCHY = {
    UserRole.ADMIN: 5,
    UserRole.COMPLIANCE: 4,
    UserRole.LOGISTICS_AGENT: 3,
    UserRole.BUYER: 2,
    UserRole.SUPPLIER: 2,
    UserRole.VIEWER: 1,
}


class UserDeletionService:
    """Service for managing user deletion operations."""

    def __init__(self, db: Session, audit_logger: Optional[AuditLogger] = None):
        """Initialize the service with a database session."""
        self.db = db
        self.audit_logger = audit_logger or AuditLogger(db)

    def _validate_reason(self, reason: str) -> None:
        """Validate deletion reason meets requirements."""
        if not reason or len(reason.strip()) < 10:
            raise InvalidDeletionReasonError(
                "Deletion reason must be at least 10 characters long"
            )
        if len(reason) > 500:
            raise InvalidDeletionReasonError(
                "Deletion reason must not exceed 500 characters"
            )

    def _can_manage_role(self, manager_role: UserRole, target_role: UserRole) -> bool:
        """Check if a role can manage (delete) another role."""
        # Only admin can manage other admins
        if target_role == UserRole.ADMIN:
            return manager_role == UserRole.ADMIN

        # Must be strictly higher in hierarchy to manage
        return ROLE_HIERARCHY.get(manager_role, 0) > ROLE_HIERARCHY.get(target_role, 0)

    def count_active_admins(self, organization_id: UUID) -> int:
        """Count the number of active (non-deleted) admins in an organization."""
        return (
            self.db.query(User)
            .filter(
                User.organization_id == organization_id,
                User.role == UserRole.ADMIN,
                User.is_active == True,  # noqa: E712
                User.deleted_at.is_(None),
            )
            .count()
        )

    def soft_delete_user(
        self,
        user_id: UUID,
        deleted_by: UUID,
        reason: str,
        organization_id: UUID,
    ) -> User:
        """
        Soft delete a user by setting deleted_at timestamp.

        Args:
            user_id: UUID of the user to delete
            deleted_by: UUID of the admin performing the deletion
            reason: Required reason for deletion (10-500 chars)
            organization_id: UUID of the organization context

        Returns:
            The deleted User object

        Raises:
            CannotDeleteSelfError: If trying to delete yourself
            CannotDeleteLastAdminError: If trying to delete the last admin
            CannotDeleteHigherRoleError: If trying to delete a user with higher role
            UserNotFoundError: If the user is not found
            UserAlreadyDeletedError: If the user is already deleted
            InvalidDeletionReasonError: If the reason is invalid
        """
        self._validate_reason(reason)

        # Get the user to delete
        user = (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.organization_id == organization_id,
            )
            .first()
        )

        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        if user.is_deleted:
            raise UserAlreadyDeletedError(f"User {user.email} is already deleted")

        # Get the deleting user
        deleting_user = self.db.query(User).filter(User.id == deleted_by).first()
        if not deleting_user:
            raise UserNotFoundError(f"Deleting user with ID {deleted_by} not found")

        # Guard: Cannot delete self
        if user_id == deleted_by:
            self.audit_logger.log(
                UserAuditAction.USER_DELETE_ATTEMPT_BLOCKED,
                user_id=str(deleted_by),
                username=deleting_user.email,
                organization_id=str(organization_id),
                resource_type="user",
                resource_id=str(user_id),
                success=False,
                error_message="Cannot delete self",
                details={"target_user": user.email, "reason": reason},
                db=self.db,
            )
            raise CannotDeleteSelfError("You cannot delete your own account")

        # Guard: Cannot delete user with higher or equal role
        if not self._can_manage_role(deleting_user.role, user.role):
            self.audit_logger.log(
                UserAuditAction.USER_DELETE_ATTEMPT_BLOCKED,
                user_id=str(deleted_by),
                username=deleting_user.email,
                organization_id=str(organization_id),
                resource_type="user",
                resource_id=str(user_id),
                success=False,
                error_message="Cannot delete user with higher role",
                details={
                    "target_user": user.email,
                    "target_role": user.role.value,
                    "deleter_role": deleting_user.role.value,
                    "reason": reason,
                },
                db=self.db,
            )
            raise CannotDeleteHigherRoleError(
                f"You cannot delete a user with role '{user.role.value}'"
            )

        # Guard: Cannot delete last admin
        if user.role == UserRole.ADMIN:
            admin_count = self.count_active_admins(organization_id)
            if admin_count <= 1:
                self.audit_logger.log(
                    UserAuditAction.USER_DELETE_ATTEMPT_BLOCKED,
                    user_id=str(deleted_by),
                    username=deleting_user.email,
                    organization_id=str(organization_id),
                    resource_type="user",
                    resource_id=str(user_id),
                    success=False,
                    error_message="Cannot delete last admin",
                    details={"target_user": user.email, "reason": reason},
                    db=self.db,
                )
                raise CannotDeleteLastAdminError(
                    "Cannot delete the last admin of the organization"
                )

        # Perform soft delete
        user.deleted_at = datetime.utcnow()
        user.deleted_by = deleted_by
        user.deletion_reason = reason.strip()
        user.is_active = False  # Also deactivate
        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        # Log the deletion
        self.audit_logger.log(
            UserAuditAction.USER_SOFT_DELETE,
            user_id=str(deleted_by),
            username=deleting_user.email,
            organization_id=str(organization_id),
            resource_type="user",
            resource_id=str(user_id),
            success=True,
            details={
                "deleted_user_email": user.email,
                "deleted_user_role": user.role.value,
                "reason": reason,
            },
            db=self.db,
        )

        logger.info(f"User {user.email} soft deleted by {deleting_user.email}")
        return user

    def hard_delete_user(
        self,
        user_id: UUID,
        deleted_by: UUID,
        reason: str,
        organization_id: UUID,
    ) -> dict:
        """
        Hard delete a user by physically removing the record.

        Also anonymizes audit log references to the deleted user.

        Args:
            user_id: UUID of the user to delete
            deleted_by: UUID of the admin performing the deletion
            reason: Required reason for deletion (10-500 chars)
            organization_id: UUID of the organization context

        Returns:
            Dict with deletion details

        Raises:
            CannotDeleteSelfError: If trying to delete yourself
            CannotDeleteLastAdminError: If trying to delete the last admin
            CannotDeleteHigherRoleError: If trying to delete a user with higher role
            UserNotFoundError: If the user is not found
            InvalidDeletionReasonError: If the reason is invalid
        """
        self._validate_reason(reason)

        # Get the user to delete
        user = (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.organization_id == organization_id,
            )
            .first()
        )

        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Get the deleting user
        deleting_user = self.db.query(User).filter(User.id == deleted_by).first()
        if not deleting_user:
            raise UserNotFoundError(f"Deleting user with ID {deleted_by} not found")

        # Store user info before deletion for audit
        deleted_user_email = user.email
        deleted_user_role = user.role.value

        # Guard: Cannot delete self
        if user_id == deleted_by:
            raise CannotDeleteSelfError("You cannot delete your own account")

        # Guard: Cannot delete user with higher or equal role
        if not self._can_manage_role(deleting_user.role, user.role):
            raise CannotDeleteHigherRoleError(
                f"You cannot delete a user with role '{user.role.value}'"
            )

        # Guard: Cannot delete last admin
        if user.role == UserRole.ADMIN:
            admin_count = self.count_active_admins(organization_id)
            # If the user is not already soft-deleted, they count in the admin count
            if not user.is_deleted and admin_count <= 1:
                raise CannotDeleteLastAdminError(
                    "Cannot delete the last admin of the organization"
                )

        # Anonymize audit log references to this user
        anonymized_count = (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == str(user_id))
            .update({
                AuditLog.username: "[deleted]",
                AuditLog.user_id: None,
            })
        )

        # Delete organization memberships
        self.db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user_id
        ).delete()

        # Delete the user
        self.db.delete(user)
        self.db.commit()

        # Log the deletion (before commit to ensure it's recorded)
        self.audit_logger.log(
            UserAuditAction.USER_HARD_DELETE,
            user_id=str(deleted_by),
            username=deleting_user.email,
            organization_id=str(organization_id),
            resource_type="user",
            resource_id=str(user_id),
            success=True,
            details={
                "deleted_user_email": deleted_user_email,
                "deleted_user_role": deleted_user_role,
                "reason": reason,
                "anonymized_audit_logs": anonymized_count,
            },
            db=self.db,
        )

        logger.info(f"User {deleted_user_email} hard deleted by {deleting_user.email}")
        return {
            "user_id": str(user_id),
            "email": deleted_user_email,
            "role": deleted_user_role,
            "anonymized_audit_logs": anonymized_count,
        }

    def restore_user(
        self,
        user_id: UUID,
        restored_by: UUID,
        organization_id: UUID,
    ) -> User:
        """
        Restore a soft-deleted user.

        Args:
            user_id: UUID of the user to restore
            restored_by: UUID of the admin performing the restoration
            organization_id: UUID of the organization context

        Returns:
            The restored User object

        Raises:
            UserNotFoundError: If the user is not found
            UserNotDeletedError: If the user is not deleted
        """
        # Get the user to restore
        user = (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.organization_id == organization_id,
            )
            .first()
        )

        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        if not user.is_deleted:
            raise UserNotDeletedError(f"User {user.email} is not deleted")

        # Get the restoring user
        restoring_user = self.db.query(User).filter(User.id == restored_by).first()
        if not restoring_user:
            raise UserNotFoundError(f"Restoring user with ID {restored_by} not found")

        # Store deletion info for audit
        original_deletion_reason = user.deletion_reason
        original_deleted_at = user.deleted_at.isoformat() if user.deleted_at else None

        # Restore the user
        user.deleted_at = None
        user.deleted_by = None
        user.deletion_reason = None
        user.is_active = True
        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        # Log the restoration
        self.audit_logger.log(
            UserAuditAction.USER_RESTORE,
            user_id=str(restored_by),
            username=restoring_user.email,
            organization_id=str(organization_id),
            resource_type="user",
            resource_id=str(user_id),
            success=True,
            details={
                "restored_user_email": user.email,
                "restored_user_role": user.role.value,
                "original_deletion_reason": original_deletion_reason,
                "original_deleted_at": original_deleted_at,
            },
            db=self.db,
        )

        logger.info(f"User {user.email} restored by {restoring_user.email}")
        return user

    def get_deleted_users(
        self,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        """
        Get a list of soft-deleted users for an organization.

        Args:
            organization_id: UUID of the organization
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of deleted User objects
        """
        return (
            self.db.query(User)
            .filter(
                User.organization_id == organization_id,
                User.deleted_at.isnot(None),
            )
            .order_by(User.deleted_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
