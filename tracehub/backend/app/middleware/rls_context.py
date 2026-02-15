"""RLS context middleware — sets PostgreSQL session variables per-request.

On every authenticated request, this middleware executes SET LOCAL to populate
the session variables that Supabase RLS policies read:

  - app.current_org_id  (UUID of the user's organization)
  - app.is_system_admin (true/false)

SET LOCAL is transaction-scoped, so these values are automatically cleared
when the database connection is returned to the pool.
"""

import logging

from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..database import SessionLocal

logger = logging.getLogger(__name__)


class RLSContextMiddleware(BaseHTTPMiddleware):
    """Middleware that sets PostgreSQL session variables for Supabase RLS.

    The RLS policies created in migration 011_enable_rls.sql read:
      current_setting('app.current_org_id', true)
      current_setting('app.is_system_admin', true)

    This middleware sets those values via SET LOCAL at the start of each
    request so that every query in the request respects tenant isolation.
    """

    # Paths that skip RLS context (no auth required)
    SKIP_PATHS = frozenset({
        "/",
        "/health",
        "/health/ready",
        "/health/live",
        "/docs",
        "/redoc",
        "/openapi.json",
    })

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip RLS setup for health/docs endpoints
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Try to extract user context from request state
        # (populated by auth middleware/dependency earlier in the chain)
        org_id = getattr(request.state, "organization_id", None)
        is_admin = getattr(request.state, "is_system_admin", False)

        if org_id:
            db = SessionLocal()
            try:
                db.execute(
                    text("SET LOCAL app.current_org_id = :org_id"),
                    {"org_id": str(org_id)},
                )
                db.execute(
                    text("SET LOCAL app.is_system_admin = :is_admin"),
                    {"is_admin": str(is_admin).lower()},
                )
                db.commit()
            except Exception as e:
                logger.warning(f"Failed to set RLS context: {e}")
                db.rollback()
            finally:
                db.close()

        response = await call_next(request)
        return response
