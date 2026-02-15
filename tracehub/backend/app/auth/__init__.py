"""PropelAuth integration for TraceHub v2.

This module provides the v2 authentication layer using PropelAuth,
while preserving the v1 CurrentUser contract for backward compatibility.

The v1 JWT auth in routers/auth.py is untouched — both coexist.
On Railway (v2), endpoints use PropelAuth.
On Hostinger (v1), endpoints continue to use JWT.
"""

from .propelauth import get_current_user_v2, init_propelauth
from .role_adapter import adapt_propelauth_to_current_user

__all__ = [
    "get_current_user_v2",
    "init_propelauth",
    "adapt_propelauth_to_current_user",
]
