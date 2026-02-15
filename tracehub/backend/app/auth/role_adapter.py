"""Role adapter — bridges PropelAuth primitives to v1 CurrentUser contract.

PropelAuth provides:
  - user.user_id, user.email
  - user.metadata (contains system_role, full_name)
  - org membership with org_role
  - org metadata (contains org_type)

This adapter maps those into the exact CurrentUser schema shape that all
existing endpoints depend on (see schemas/user.py:CurrentUser).
"""

from uuid import UUID

from ..models.user import UserRole
from ..models.organization import OrgRole, OrganizationType
from ..schemas.user import CurrentUser
from .permissions import ROLE_PERMISSIONS, Permission
from .org_permissions import compute_effective_org_permissions


def _parse_user_role(role_str: str | None) -> UserRole:
    """Parse a system role string to UserRole enum, defaulting to VIEWER."""
    if not role_str:
        return UserRole.VIEWER
    try:
        return UserRole(role_str.lower())
    except ValueError:
        return UserRole.VIEWER


def _parse_org_role(role_str: str | None) -> OrgRole | None:
    """Parse an org role string to OrgRole enum."""
    if not role_str:
        return None
    try:
        return OrgRole(role_str.lower())
    except ValueError:
        return None


def _parse_org_type(type_str: str | None) -> OrganizationType | None:
    """Parse an org type string to OrganizationType enum."""
    if not type_str:
        return None
    try:
        return OrganizationType(type_str.lower())
    except ValueError:
        return None


def adapt_propelauth_to_current_user(
    user_id: str,
    email: str,
    user_metadata: dict,
    org_id: str | None = None,
    org_role_str: str | None = None,
    org_metadata: dict | None = None,
) -> CurrentUser:
    """Map PropelAuth user + org data to v1 CurrentUser schema.

    Args:
        user_id: PropelAuth user UUID string.
        email: User email.
        user_metadata: PropelAuth user metadata dict. Expected keys:
            - system_role: str (admin, compliance, logistics_agent, buyer, supplier, viewer)
            - full_name: str
        org_id: PropelAuth organization UUID string (primary org).
        org_role_str: PropelAuth org role string (admin, manager, member, viewer).
        org_metadata: PropelAuth org metadata dict. Expected keys:
            - org_type: str (vibotaj, buyer, supplier, logistics_agent)

    Returns:
        CurrentUser with all fields populated, matching the v1 contract.
    """
    # Parse system role
    system_role = _parse_user_role(user_metadata.get("system_role"))
    full_name = user_metadata.get("full_name", email.split("@")[0])
    is_system_admin = system_role == UserRole.ADMIN

    # System-level permissions
    system_permissions = [p.value for p in ROLE_PERMISSIONS.get(system_role, set())]

    # Parse org context
    org_role = _parse_org_role(org_role_str)
    org_type = _parse_org_type((org_metadata or {}).get("org_type"))

    # Org-level permissions
    org_permissions: list[str] = []
    if org_role and org_type:
        computed = compute_effective_org_permissions(
            org_role, org_type, is_system_admin=is_system_admin
        )
        org_permissions = [p.value for p in computed]

    # Default org_id to a sentinel if not provided (shouldn't happen in practice)
    resolved_org_id = UUID(org_id) if org_id else UUID("00000000-0000-0000-0000-000000000000")

    return CurrentUser(
        id=UUID(user_id),
        email=email,
        full_name=full_name,
        role=system_role,
        is_active=True,  # PropelAuth handles deactivation; if we get here, user is active
        organization_id=resolved_org_id,
        permissions=system_permissions,
        org_role=org_role,
        org_type=org_type,
        org_permissions=org_permissions,
    )
