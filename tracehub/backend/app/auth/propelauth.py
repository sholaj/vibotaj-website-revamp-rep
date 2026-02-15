"""PropelAuth SDK integration for FastAPI.

Provides:
  - init_propelauth() — one-time SDK initialization
  - get_current_user_v2() — FastAPI dependency that returns CurrentUser

The v1 JWT auth in routers/auth.py is not touched. Both auth paths coexist.
Which one is used depends on the deployment:
  - Hostinger (v1): routers/auth.py → get_current_active_user()
  - Railway (v2):   auth/propelauth.py → get_current_user_v2()
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from ..config import get_settings
from ..schemas.user import CurrentUser
from .role_adapter import adapt_propelauth_to_current_user

logger = logging.getLogger(__name__)

# Module-level auth instance (initialized once via init_propelauth)
_auth = None


def init_propelauth(auth_url: str, api_key: str):
    """Initialize the PropelAuth SDK. Call once at app startup.

    Args:
        auth_url: PropelAuth auth URL (e.g. https://auth.yourdomain.com)
        api_key: PropelAuth API key
    """
    global _auth
    if not auth_url or not api_key:
        logger.info("PropelAuth not configured (auth_url or api_key missing)")
        return

    try:
        from propelauth_fastapi import init_auth
        _auth = init_auth(auth_url=auth_url, api_key=api_key)
        logger.info(f"PropelAuth initialized (auth_url={auth_url})")
    except ImportError:
        logger.warning("propelauth-fastapi not installed — PropelAuth auth disabled")
    except Exception as e:
        logger.error(f"Failed to initialize PropelAuth: {e}")


def _get_auth():
    """Get the initialized PropelAuth auth instance."""
    if _auth is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured",
        )
    return _auth


async def get_current_user_v2(request: Request) -> CurrentUser:
    """FastAPI dependency: authenticate via PropelAuth and return CurrentUser.

    This is the v2 replacement for v1's get_current_active_user().
    It produces the exact same CurrentUser schema shape.

    Flow:
    1. Validate the PropelAuth access token from Authorization header
    2. Extract user metadata (system_role, full_name)
    3. Get the user's active org membership + org metadata
    4. Map everything to CurrentUser via role_adapter
    """
    auth = _get_auth()

    # 1. Validate token and get PropelAuth user
    try:
        from propelauth_fastapi import User as PropelAuthUser
        propel_user = auth.require_user(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PropelAuth token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Extract user metadata
    user_metadata = propel_user.metadata if hasattr(propel_user, "metadata") else {}
    if not isinstance(user_metadata, dict):
        user_metadata = {}

    # 3. Get active org membership
    # PropelAuth provides org_id_to_org_member_info on the user object
    org_id: Optional[str] = None
    org_role_str: Optional[str] = None
    org_metadata: Optional[dict] = None

    org_memberships = getattr(propel_user, "org_id_to_org_member_info", {}) or {}

    if org_memberships:
        # Use the active org from the request header, or fall back to first org
        active_org_id = request.headers.get("X-Organization-Id")

        if active_org_id and active_org_id in org_memberships:
            org_info = org_memberships[active_org_id]
        else:
            # Default to first org
            first_org_id = next(iter(org_memberships))
            org_info = org_memberships[first_org_id]
            active_org_id = first_org_id

        org_id = active_org_id
        org_role_str = getattr(org_info, "user_role", None)

        # Get org metadata via PropelAuth API
        try:
            org_data = auth.fetch_org(org_id)
            org_metadata = getattr(org_data, "metadata", {})
            if not isinstance(org_metadata, dict):
                org_metadata = {}
        except Exception as e:
            logger.warning(f"Could not fetch org metadata for {org_id}: {e}")
            org_metadata = {}

    # 4. Adapt to CurrentUser
    current_user = adapt_propelauth_to_current_user(
        user_id=propel_user.user_id,
        email=propel_user.email,
        user_metadata=user_metadata,
        org_id=org_id,
        org_role_str=org_role_str,
        org_metadata=org_metadata,
    )

    # Set RLS context on request state (used by RLSContextMiddleware)
    request.state.organization_id = current_user.organization_id
    request.state.is_system_admin = current_user.role.value == "admin"

    return current_user
