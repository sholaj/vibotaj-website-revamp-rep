"""Canonical permission definitions for TraceHub.

Extracted from v1 services/permissions.py. This is the single source of truth
for system-level role permissions in the v2 auth layer.

6 system roles × 22 permissions. Role hierarchy: admin(5) > compliance(4) >
logistics_agent(3) > buyer(2) = supplier(2) > viewer(1).
"""

from enum import Enum
from typing import Set

from ..models.user import UserRole


class Permission(str, Enum):
    """System-level permissions."""

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

    # Admin-only
    SYSTEM_ADMIN = "system:admin"


# Exact replica of v1 ROLE_PERMISSIONS from services/permissions.py
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: {
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
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_READ,
        Permission.TRACKING_READ,
        Permission.AUDIT_PACK_DOWNLOAD,
    },
    UserRole.SUPPLIER: {
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_UPLOAD,
        Permission.DOCUMENTS_CREATE,
        Permission.TRACKING_READ,
    },
    UserRole.VIEWER: {
        Permission.SHIPMENTS_READ,
        Permission.SHIPMENTS_LIST,
        Permission.DOCUMENTS_READ,
        Permission.TRACKING_READ,
    },
}


# Role hierarchy for comparison (higher number = more authority)
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.ADMIN: 5,
    UserRole.COMPLIANCE: 4,
    UserRole.LOGISTICS_AGENT: 3,
    UserRole.BUYER: 2,
    UserRole.SUPPLIER: 2,
    UserRole.VIEWER: 1,
}


def get_role_permissions(role: UserRole) -> set[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def is_role_higher_or_equal(role: UserRole, compared_to: UserRole) -> bool:
    """Check if a role is higher or equal to another in the hierarchy."""
    return ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get(compared_to, 0)


def can_manage_role(manager_role: UserRole, target_role: UserRole) -> bool:
    """Check if a role can manage (create/update/delete) another role."""
    if target_role == UserRole.ADMIN:
        return manager_role == UserRole.ADMIN
    return ROLE_HIERARCHY.get(manager_role, 0) > ROLE_HIERARCHY.get(target_role, 0)
