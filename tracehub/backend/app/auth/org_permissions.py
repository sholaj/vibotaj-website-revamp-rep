"""Organization-scoped permission definitions for TraceHub.

Extracted from v1 services/org_permissions.py. This is the single source of
truth for org-level role permissions and org-type bonus permissions.

4 org roles × 23 org permissions. Org-type bonuses for VIBOTAJ (3),
BUYER (2), LOGISTICS_AGENT (1).
"""

from enum import Enum
from typing import Set

from ..models.organization import OrgRole, OrganizationType


class OrgPermission(str, Enum):
    """Permissions within an organization context."""

    # Member management
    MEMBERS_VIEW = "members:view"
    MEMBERS_INVITE = "members:invite"
    MEMBERS_MANAGE = "members:manage"
    MEMBERS_REMOVE = "members:remove"

    # Organization settings
    SETTINGS_VIEW = "settings:view"
    SETTINGS_MANAGE = "settings:manage"

    # Shipment permissions (org-scoped)
    SHIPMENTS_VIEW = "shipments:view"
    SHIPMENTS_CREATE = "shipments:create"
    SHIPMENTS_UPDATE = "shipments:update"
    SHIPMENTS_DELETE = "shipments:delete"

    # Document permissions (org-scoped)
    DOCUMENTS_VIEW = "documents:view"
    DOCUMENTS_UPLOAD = "documents:upload"
    DOCUMENTS_VALIDATE = "documents:validate"
    DOCUMENTS_APPROVE = "documents:approve"
    DOCUMENTS_DELETE = "documents:delete"

    # Tracking permissions
    TRACKING_VIEW = "tracking:view"
    TRACKING_REFRESH = "tracking:refresh"

    # Invitation permissions
    INVITATIONS_VIEW = "invitations:view"
    INVITATIONS_CREATE = "invitations:create"
    INVITATIONS_REVOKE = "invitations:revoke"

    # Audit and compliance
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_MANAGE = "compliance:manage"


# Exact replica of v1 ORG_ROLE_PERMISSIONS
ORG_ROLE_PERMISSIONS: dict[OrgRole, set[OrgPermission]] = {
    OrgRole.ADMIN: {
        OrgPermission.MEMBERS_VIEW,
        OrgPermission.MEMBERS_INVITE,
        OrgPermission.MEMBERS_MANAGE,
        OrgPermission.MEMBERS_REMOVE,
        OrgPermission.SETTINGS_VIEW,
        OrgPermission.SETTINGS_MANAGE,
        OrgPermission.SHIPMENTS_VIEW,
        OrgPermission.SHIPMENTS_CREATE,
        OrgPermission.SHIPMENTS_UPDATE,
        OrgPermission.SHIPMENTS_DELETE,
        OrgPermission.DOCUMENTS_VIEW,
        OrgPermission.DOCUMENTS_UPLOAD,
        OrgPermission.DOCUMENTS_VALIDATE,
        OrgPermission.DOCUMENTS_APPROVE,
        OrgPermission.DOCUMENTS_DELETE,
        OrgPermission.TRACKING_VIEW,
        OrgPermission.TRACKING_REFRESH,
        OrgPermission.INVITATIONS_VIEW,
        OrgPermission.INVITATIONS_CREATE,
        OrgPermission.INVITATIONS_REVOKE,
        OrgPermission.AUDIT_VIEW,
        OrgPermission.AUDIT_EXPORT,
        OrgPermission.COMPLIANCE_VIEW,
        OrgPermission.COMPLIANCE_MANAGE,
    },
    OrgRole.MANAGER: {
        OrgPermission.MEMBERS_VIEW,
        OrgPermission.MEMBERS_INVITE,
        OrgPermission.SETTINGS_VIEW,
        OrgPermission.SHIPMENTS_VIEW,
        OrgPermission.SHIPMENTS_CREATE,
        OrgPermission.SHIPMENTS_UPDATE,
        OrgPermission.DOCUMENTS_VIEW,
        OrgPermission.DOCUMENTS_UPLOAD,
        OrgPermission.DOCUMENTS_VALIDATE,
        OrgPermission.DOCUMENTS_APPROVE,
        OrgPermission.TRACKING_VIEW,
        OrgPermission.TRACKING_REFRESH,
        OrgPermission.INVITATIONS_VIEW,
        OrgPermission.INVITATIONS_CREATE,
        OrgPermission.AUDIT_VIEW,
        OrgPermission.AUDIT_EXPORT,
        OrgPermission.COMPLIANCE_VIEW,
    },
    OrgRole.MEMBER: {
        OrgPermission.MEMBERS_VIEW,
        OrgPermission.SETTINGS_VIEW,
        OrgPermission.SHIPMENTS_VIEW,
        OrgPermission.SHIPMENTS_CREATE,
        OrgPermission.DOCUMENTS_VIEW,
        OrgPermission.DOCUMENTS_UPLOAD,
        OrgPermission.TRACKING_VIEW,
        OrgPermission.TRACKING_REFRESH,
        OrgPermission.INVITATIONS_VIEW,
        OrgPermission.AUDIT_VIEW,
        OrgPermission.COMPLIANCE_VIEW,
    },
    OrgRole.VIEWER: {
        OrgPermission.MEMBERS_VIEW,
        OrgPermission.SETTINGS_VIEW,
        OrgPermission.SHIPMENTS_VIEW,
        OrgPermission.DOCUMENTS_VIEW,
        OrgPermission.TRACKING_VIEW,
        OrgPermission.INVITATIONS_VIEW,
        OrgPermission.AUDIT_VIEW,
        OrgPermission.COMPLIANCE_VIEW,
    },
}


# Exact replica of v1 ORG_TYPE_PERMISSIONS
ORG_TYPE_PERMISSIONS: dict[OrganizationType, set[OrgPermission]] = {
    OrganizationType.VIBOTAJ: {
        OrgPermission.DOCUMENTS_APPROVE,
        OrgPermission.DOCUMENTS_VALIDATE,
        OrgPermission.COMPLIANCE_MANAGE,
    },
    OrganizationType.BUYER: {
        OrgPermission.DOCUMENTS_APPROVE,
        OrgPermission.DOCUMENTS_VALIDATE,
    },
    OrganizationType.SUPPLIER: set(),
    OrganizationType.LOGISTICS_AGENT: {
        OrgPermission.TRACKING_REFRESH,
    },
}


# Org role hierarchy (higher number = more authority)
ORG_ROLE_HIERARCHY: dict[OrgRole, int] = {
    OrgRole.ADMIN: 4,
    OrgRole.MANAGER: 3,
    OrgRole.MEMBER: 2,
    OrgRole.VIEWER: 1,
}


def get_org_role_permissions(role: OrgRole) -> set[OrgPermission]:
    """Get all permissions for an organization role."""
    return ORG_ROLE_PERMISSIONS.get(role, set())


def get_org_type_bonus_permissions(org_type: OrganizationType) -> set[OrgPermission]:
    """Get additional permissions granted by organization type."""
    return ORG_TYPE_PERMISSIONS.get(org_type, set())


def compute_effective_org_permissions(
    org_role: OrgRole,
    org_type: OrganizationType,
    is_system_admin: bool = False,
) -> set[OrgPermission]:
    """Compute effective org permissions from role + org type + system admin.

    Mirrors v1 compute_effective_permissions() from services/org_permissions.py.
    Bonus permissions only apply to admin and manager roles.
    System admins get all permissions.
    """
    if is_system_admin:
        return set(OrgPermission)

    permissions = get_org_role_permissions(org_role).copy()

    # Org-type bonuses only apply to admin/manager
    if org_role in {OrgRole.ADMIN, OrgRole.MANAGER}:
        permissions.update(get_org_type_bonus_permissions(org_type))

    return permissions
