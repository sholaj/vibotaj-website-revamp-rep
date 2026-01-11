"""Organization-scoped permission system for multi-tenancy.

Sprint 8: Multi-Tenancy Feature
Sprint 13.4: Role-Based Organization Permissions

This module extends the existing permission system to support:
- Organization-scoped permissions
- Cross-organization access for VIBOTAJ users
- Role-based access within organizations
- Organization admin member management
"""

from enum import Enum
from typing import List, Set, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.organization import (
    OrganizationType,
    OrgRole,
    OrganizationMembership,
    MembershipStatus,
    ORG_ROLE_HIERARCHY,
    can_manage_org_role
)

if TYPE_CHECKING:
    from ..schemas.user import CurrentUser


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


# Permissions granted by each organization role
ORG_ROLE_PERMISSIONS: Dict[OrgRole, Set[OrgPermission]] = {
    OrgRole.ADMIN: {
        # Full access to all organization resources
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
        # Can manage most resources but not organization settings
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
        # Standard access - can view and contribute
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
        # Read-only access
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


# Additional permissions based on organization type
ORG_TYPE_PERMISSIONS: Dict[OrganizationType, Set[OrgPermission]] = {
    OrganizationType.VIBOTAJ: {
        # VIBOTAJ can approve/validate documents for any org they have access to
        OrgPermission.DOCUMENTS_APPROVE,
        OrgPermission.DOCUMENTS_VALIDATE,
        OrgPermission.COMPLIANCE_MANAGE,
    },
    OrganizationType.BUYER: {
        # Buyers can approve/validate documents
        OrgPermission.DOCUMENTS_APPROVE,
        OrgPermission.DOCUMENTS_VALIDATE,
    },
    OrganizationType.SUPPLIER: {
        # Suppliers have upload-focused permissions (already in base role)
    },
    OrganizationType.LOGISTICS_AGENT: {
        # Logistics agents can refresh tracking
        OrgPermission.TRACKING_REFRESH,
    },
}


def get_org_role_permissions(role: OrgRole) -> Set[OrgPermission]:
    """Get all permissions for an organization role."""
    return ORG_ROLE_PERMISSIONS.get(role, set())


def get_org_type_bonus_permissions(org_type: OrganizationType) -> Set[OrgPermission]:
    """Get additional permissions granted by organization type."""
    return ORG_TYPE_PERMISSIONS.get(org_type, set())


def compute_effective_permissions(
    org_role: OrgRole,
    org_type: OrganizationType,
    is_system_admin: bool = False
) -> Set[OrgPermission]:
    """Compute effective permissions based on role, org type, and system role.

    Args:
        org_role: User's role within the organization
        org_type: Type of the organization
        is_system_admin: Whether the user is a VIBOTAJ system admin

    Returns:
        Set of effective permissions
    """
    # Start with role-based permissions
    permissions = get_org_role_permissions(org_role).copy()

    # Add organization type bonus permissions (intersection with role permissions)
    type_bonus = get_org_type_bonus_permissions(org_type)
    # Only add bonus permissions that make sense for the role
    if org_role in [OrgRole.ADMIN, OrgRole.MANAGER]:
        permissions.update(type_bonus)

    # System admins get full access
    if is_system_admin:
        permissions = set(OrgPermission)

    return permissions


def has_org_permission(
    permissions: Set[OrgPermission],
    required: OrgPermission
) -> bool:
    """Check if a permission set includes the required permission."""
    return required in permissions


def has_any_org_permission(
    permissions: Set[OrgPermission],
    required: List[OrgPermission]
) -> bool:
    """Check if a permission set includes any of the required permissions."""
    return any(perm in permissions for perm in required)


def has_all_org_permissions(
    permissions: Set[OrgPermission],
    required: List[OrgPermission]
) -> bool:
    """Check if a permission set includes all required permissions."""
    return all(perm in permissions for perm in required)


class OrgContext:
    """Organization context for a user session.

    This class encapsulates the organization context from a JWT token
    and provides permission checking methods.
    """

    def __init__(
        self,
        user_id: UUID,
        org_id: UUID,
        org_type: OrganizationType,
        org_role: OrgRole,
        system_role: str = "user"
    ):
        self.user_id = user_id
        self.org_id = org_id
        self.org_type = org_type
        self.org_role = org_role
        self.system_role = system_role
        self._permissions: Optional[Set[OrgPermission]] = None

    @property
    def is_system_admin(self) -> bool:
        """Check if user is a system admin."""
        return self.system_role == "system_admin"

    @property
    def is_vibotaj_org(self) -> bool:
        """Check if current organization is VIBOTAJ."""
        return self.org_type == OrganizationType.VIBOTAJ

    @property
    def permissions(self) -> Set[OrgPermission]:
        """Get computed permissions (cached)."""
        if self._permissions is None:
            self._permissions = compute_effective_permissions(
                self.org_role,
                self.org_type,
                self.is_system_admin
            )
        return self._permissions

    @property
    def permission_list(self) -> List[str]:
        """Get permissions as a list of strings."""
        return [p.value for p in self.permissions]

    def has_permission(self, permission: OrgPermission) -> bool:
        """Check if user has a specific permission."""
        return has_org_permission(self.permissions, permission)

    def has_any_permission(self, permissions: List[OrgPermission]) -> bool:
        """Check if user has any of the specified permissions."""
        return has_any_org_permission(self.permissions, permissions)

    def has_all_permissions(self, permissions: List[OrgPermission]) -> bool:
        """Check if user has all specified permissions."""
        return has_all_org_permissions(self.permissions, permissions)

    def can_manage_role(self, target_role: OrgRole) -> bool:
        """Check if user can manage (invite/promote/demote) a target role."""
        if self.is_system_admin:
            return True
        return can_manage_org_role(self.org_role, target_role)

    def can_access_organization(self, target_org_id: UUID) -> bool:
        """Check if user can access a specific organization.

        System admins can access any organization.
        Regular users can only access their current organization.
        """
        if self.is_system_admin:
            return True
        return self.org_id == target_org_id

    def can_access_shipment(
        self,
        shipment_org_id: UUID,
        shipment_buyer_id: Optional[UUID] = None,
        shipment_supplier_id: Optional[UUID] = None
    ) -> bool:
        """Check if user can access a specific shipment.

        Access is granted if:
        - User is a system admin
        - Shipment belongs to user's organization
        - User's organization is the buyer
        - User's organization is the supplier
        """
        if self.is_system_admin:
            return True
        if shipment_org_id == self.org_id:
            return True
        if shipment_buyer_id and shipment_buyer_id == self.org_id:
            return True
        if shipment_supplier_id and shipment_supplier_id == self.org_id:
            return True
        return False


def get_org_permission_matrix() -> Dict[str, Any]:
    """Get the complete organization permission matrix for documentation."""
    matrix = {
        "roles": {},
        "org_types": {},
        "all_permissions": [p.value for p in OrgPermission]
    }

    for role in OrgRole:
        matrix["roles"][role.value] = {
            "permissions": [p.value for p in get_org_role_permissions(role)],
            "hierarchy_level": ORG_ROLE_HIERARCHY.get(role, 0)
        }

    for org_type in OrganizationType:
        matrix["org_types"][org_type.value] = {
            "bonus_permissions": [p.value for p in get_org_type_bonus_permissions(org_type)]
        }

    return matrix


# ============ Data Access Scoping ============

def build_org_filter(context: OrgContext) -> Optional[Dict[str, Any]]:
    """Build a data access filter based on organization context.

    Returns None for system admins (no filter needed).
    Returns organization_id filter for regular users.
    """
    if context.is_system_admin:
        return None
    return {"organization_id": context.org_id}


def build_shipment_filter(context: OrgContext) -> Optional[Dict[str, Any]]:
    """Build a shipment access filter based on organization context.

    Shipments can be accessed by:
    - The owning organization
    - The buyer organization
    - The supplier organization
    """
    if context.is_system_admin:
        return None

    # This returns a filter that should be applied as an OR condition:
    # (organization_id = org_id) OR (buyer_org_id = org_id) OR (supplier_org_id = org_id)
    return {
        "or_conditions": [
            {"organization_id": context.org_id},
            {"buyer_org_id": context.org_id},
            {"supplier_org_id": context.org_id},
        ]
    }


# ============ Organization Member Management Permissions (Sprint 13.4) ============


def get_user_org_membership(
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> Optional[OrganizationMembership]:
    """Get user's membership in a specific organization.

    Args:
        db: Database session
        user_id: The user's UUID
        org_id: The organization's UUID

    Returns:
        OrganizationMembership if found, None otherwise
    """
    return db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.status == MembershipStatus.ACTIVE
    ).first()


def is_system_admin(user: "CurrentUser") -> bool:
    """Check if user is a system admin.

    Args:
        user: The current user from authentication

    Returns:
        True if user has system admin role
    """
    from ..models.user import UserRole
    return user.role == UserRole.ADMIN


def can_manage_org_members(
    db: Session,
    user: "CurrentUser",
    org_id: UUID
) -> bool:
    """Check if user can manage members of an organization.

    Returns True if:
    - User is system admin OR
    - User is org admin of the specified organization

    Args:
        db: Database session
        user: The current authenticated user
        org_id: The organization ID to check

    Returns:
        True if user can manage members, False otherwise
    """
    # System admins can manage any organization's members
    if is_system_admin(user):
        return True

    # Check if user is an org admin of this organization
    membership = get_user_org_membership(db, user.id, org_id)
    if membership is None:
        return False

    return membership.org_role == OrgRole.ADMIN


def can_view_org_members(
    db: Session,
    user: "CurrentUser",
    org_id: UUID
) -> bool:
    """Check if user can view members of an organization.

    Returns True if:
    - User is system admin OR
    - User is a member of the organization (any role)

    Args:
        db: Database session
        user: The current authenticated user
        org_id: The organization ID to check

    Returns:
        True if user can view members, False otherwise
    """
    # System admins can view any organization's members
    if is_system_admin(user):
        return True

    # Check if user is a member of this organization (any role)
    membership = get_user_org_membership(db, user.id, org_id)
    return membership is not None


def can_modify_member(
    db: Session,
    user: "CurrentUser",
    org_id: UUID,
    target_membership: OrganizationMembership
) -> tuple[bool, str]:
    """Check if user can modify a specific member.

    Rules:
    - System admins can modify anyone
    - Org admins cannot modify other admins
    - Nobody can modify themselves

    Args:
        db: Database session
        user: The current authenticated user
        org_id: The organization ID
        target_membership: The membership being modified

    Returns:
        Tuple of (can_modify: bool, reason: str)
        reason is empty string if can_modify is True
    """
    # Nobody can modify themselves
    if target_membership.user_id == user.id:
        return False, "You cannot modify your own membership"

    # System admins can modify anyone else
    if is_system_admin(user):
        return True, ""

    # Check if user is an org admin
    user_membership = get_user_org_membership(db, user.id, org_id)
    if user_membership is None or user_membership.org_role != OrgRole.ADMIN:
        return False, "Only organization admins can modify members"

    # Org admins cannot modify other admins
    if target_membership.org_role == OrgRole.ADMIN:
        return False, "Organization admins cannot modify other admins. Contact a system administrator."

    return True, ""


def check_org_admin_permission(
    db: Session,
    user: "CurrentUser",
    org_id: UUID
) -> None:
    """Raise HTTPException 403 if user cannot manage org members.

    Args:
        db: Database session
        user: The current authenticated user
        org_id: The organization ID to check

    Raises:
        HTTPException: 403 Forbidden if user cannot manage members
    """
    if not can_manage_org_members(db, user, org_id):
        # Provide more specific error message
        if is_system_admin(user):
            detail = "Access denied"
        else:
            membership = get_user_org_membership(db, user.id, org_id)
            if membership is None:
                detail = "You are not a member of this organization"
            else:
                detail = "Only organization admins can manage members"

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def check_org_view_permission(
    db: Session,
    user: "CurrentUser",
    org_id: UUID
) -> None:
    """Raise HTTPException 403 if user cannot view org members.

    Args:
        db: Database session
        user: The current authenticated user
        org_id: The organization ID to check

    Raises:
        HTTPException: 403 Forbidden if user cannot view members
    """
    if not can_view_org_members(db, user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this organization to view its members"
        )


def check_member_modification_permission(
    db: Session,
    user: "CurrentUser",
    org_id: UUID,
    target_membership: OrganizationMembership
) -> None:
    """Raise HTTPException 403 if user cannot modify the target member.

    Args:
        db: Database session
        user: The current authenticated user
        org_id: The organization ID
        target_membership: The membership being modified

    Raises:
        HTTPException: 403 Forbidden if user cannot modify the member
    """
    can_modify, reason = can_modify_member(db, user, org_id, target_membership)
    if not can_modify:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason
        )
