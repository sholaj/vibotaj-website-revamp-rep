"""Permission system for role-based access control.

This module defines permissions per role and provides decorators for route protection.
"""

from enum import Enum
from functools import wraps
from typing import List, Set, Callable, Optional
from fastapi import HTTPException, status, Depends

from ..models.user import UserRole


class Permission(str, Enum):
    """Available permissions in the system."""

    # User management
    USERS_CREATE = "users:create"
    USERS_READ = "users:read"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    USERS_LIST = "users:list"

    # Shipment permissions
    SHIPMENTS_CREATE = "shipments:create"
    SHIPMENTS_READ = "shipments:read"
    SHIPMENTS_UPDATE = "shipments:update"
    SHIPMENTS_DELETE = "shipments:delete"
    SHIPMENTS_LIST = "shipments:list"

    # Document permissions
    DOCUMENTS_CREATE = "documents:create"
    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_UPDATE = "documents:update"
    DOCUMENTS_DELETE = "documents:delete"
    DOCUMENTS_UPLOAD = "documents:upload"
    DOCUMENTS_VALIDATE = "documents:validate"
    DOCUMENTS_APPROVE = "documents:approve"
    DOCUMENTS_REJECT = "documents:reject"
    DOCUMENTS_TRANSITION = "documents:transition"

    # Tracking permissions
    TRACKING_READ = "tracking:read"
    TRACKING_REFRESH = "tracking:refresh"

    # Audit pack
    AUDIT_PACK_DOWNLOAD = "audit_pack:download"

    # Admin-only permissions
    SYSTEM_ADMIN = "system:admin"


# Define permissions for each role
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # Admin has all permissions
        Permission.USERS_CREATE,
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.USERS_LIST,
        Permission.SHIPMENTS_CREATE,
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_UPDATE,
        Permission.SHIPMENTS_DELETE,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_CREATE,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_UPDATE,
        Permission.DOCUMENTS_DELETE,
        Permission.DOCUMENTS_UPLOAD,
        Permission.DOCUMENTS_VALIDATE,
        Permission.DOCUMENTS_APPROVE,
        Permission.DOCUMENTS_REJECT,
        Permission.DOCUMENTS_TRANSITION,
        Permission.TRACKING_READ,
        Permission.TRACKING_REFRESH,
        Permission.AUDIT_PACK_DOWNLOAD,
        Permission.SYSTEM_ADMIN,
    },
    UserRole.COMPLIANCE: {
        # Compliance can validate/approve documents, view all shipments
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_VALIDATE,
        Permission.DOCUMENTS_APPROVE,
        Permission.DOCUMENTS_REJECT,
        Permission.DOCUMENTS_TRANSITION,
        Permission.TRACKING_READ,
        Permission.TRACKING_REFRESH,
        Permission.AUDIT_PACK_DOWNLOAD,
    },
    UserRole.LOGISTICS_AGENT: {
        # Logistics agent: schedule containers, upload ALL documents, manage shipments
        Permission.SHIPMENTS_CREATE,
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_UPDATE,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_CREATE,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_UPDATE,
        Permission.DOCUMENTS_UPLOAD,
        Permission.TRACKING_READ,
        Permission.TRACKING_REFRESH,
        Permission.AUDIT_PACK_DOWNLOAD,
    },
    UserRole.BUYER: {
        # Buyer has read-only access to their shipments and documents
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_READ,
        Permission.TRACKING_READ,
        Permission.AUDIT_PACK_DOWNLOAD,
    },
    UserRole.SUPPLIER: {
        # Supplier can upload documents, view assigned shipments
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_UPLOAD,
        Permission.DOCUMENTS_CREATE,
        Permission.TRACKING_READ,
    },
    UserRole.VIEWER: {
        # Viewer has read-only access to all data
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_READ,
        Permission.TRACKING_READ,
    },
}


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_role_permissions(role)


def has_any_permission(role: UserRole, permissions: List[Permission]) -> bool:
    """Check if a role has any of the specified permissions."""
    role_perms = get_role_permissions(role)
    return any(perm in role_perms for perm in permissions)


def has_all_permissions(role: UserRole, permissions: List[Permission]) -> bool:
    """Check if a role has all of the specified permissions."""
    role_perms = get_role_permissions(role)
    return all(perm in role_perms for perm in permissions)


class PermissionChecker:
    """Dependency class for checking permissions in route handlers."""

    def __init__(
        self,
        required_permissions: Optional[List[Permission]] = None,
        required_roles: Optional[List[UserRole]] = None,
        require_all: bool = True
    ):
        """
        Initialize permission checker.

        Args:
            required_permissions: List of permissions to check
            required_roles: List of allowed roles (alternative to permissions)
            require_all: If True, all permissions must be present; if False, any one is sufficient
        """
        self.required_permissions = required_permissions or []
        self.required_roles = required_roles or []
        self.require_all = require_all

    def check(self, user_role: UserRole) -> bool:
        """Check if the user's role satisfies the requirements."""
        # If specific roles are required, check those first
        if self.required_roles:
            if user_role in self.required_roles:
                return True
            # Admin always has access if role check is used
            if user_role == UserRole.ADMIN:
                return True
            return False

        # Check permissions
        if not self.required_permissions:
            return True

        if self.require_all:
            return has_all_permissions(user_role, self.required_permissions)
        else:
            return has_any_permission(user_role, self.required_permissions)


def require_permission(*permissions: Permission, require_all: bool = True):
    """
    Create a dependency that requires specific permissions.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_permission(Permission.SYSTEM_ADMIN))
        ):
            ...
    """
    checker = PermissionChecker(required_permissions=list(permissions), require_all=require_all)

    def dependency(current_user):
        from ..routers.auth import get_current_active_user  # Avoid circular import
        if not checker.check(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[p.value for p in permissions]}"
            )
        return None

    return dependency


def require_role(*roles: UserRole):
    """
    Create a dependency that requires specific roles.

    Usage:
        @router.post("/users")
        async def create_user(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_role(UserRole.ADMIN))
        ):
            ...
    """
    checker = PermissionChecker(required_roles=list(roles))

    def dependency(current_user):
        if not checker.check(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return None

    return dependency


def get_permission_matrix() -> dict:
    """Return the complete permission matrix for documentation/debugging."""
    matrix = {}
    for role in UserRole:
        perms = get_role_permissions(role)
        matrix[role.value] = [p.value for p in perms]
    return matrix


# Role hierarchy for comparison
ROLE_HIERARCHY = {
    UserRole.ADMIN: 5,
    UserRole.COMPLIANCE: 4,
    UserRole.LOGISTICS_AGENT: 3,
    UserRole.BUYER: 2,
    UserRole.SUPPLIER: 2,
    UserRole.VIEWER: 1,
}


def is_role_higher_or_equal(role: UserRole, compared_to: UserRole) -> bool:
    """Check if a role is higher or equal to another in the hierarchy."""
    return ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get(compared_to, 0)


def can_manage_role(manager_role: UserRole, target_role: UserRole) -> bool:
    """Check if a role can manage (create/update/delete) another role."""
    # Only admin can manage other admins
    if target_role == UserRole.ADMIN:
        return manager_role == UserRole.ADMIN

    # Must be strictly higher in hierarchy to manage
    return ROLE_HIERARCHY.get(manager_role, 0) > ROLE_HIERARCHY.get(target_role, 0)
