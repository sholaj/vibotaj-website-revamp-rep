"""Error handling middleware - structured error logging and responses."""

import logging
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware.

    Features:
    - Catches unhandled exceptions
    - Logs errors with full context
    - Returns consistent error responses
    - Prepares for external error tracking (Sentry)
    """

    def __init__(self, app, sentry_dsn: str = None):
        super().__init__(app)
        self.sentry_dsn = sentry_dsn
        self._sentry_initialized = False

        # Check if Sentry is already initialized (via sentry_setup.init_sentry)
        # or initialize here as a fallback
        if sentry_dsn:
            self._check_or_init_sentry(sentry_dsn)

    def _check_or_init_sentry(self, dsn: str):
        """Check if Sentry is initialized or initialize as fallback."""
        try:
            import sentry_sdk
            # If Sentry was already initialized by sentry_setup.init_sentry(),
            # just mark as ready — don't re-initialize
            client = sentry_sdk.get_client()
            if client and client.dsn:
                self._sentry_initialized = True
                logger.info("Sentry already initialized — error handler will report exceptions")
                return

            # Fallback: initialize here (e.g. if sentry_setup wasn't called)
            from sentry_sdk.integrations.starlette import StarletteIntegration
            from sentry_sdk.integrations.fastapi import FastApiIntegration

            sentry_sdk.init(
                dsn=dsn,
                integrations=[
                    StarletteIntegration(),
                    FastApiIntegration(),
                ],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment="production",
            )
            self._sentry_initialized = True
            logger.info("Sentry error tracking initialized (fallback)")
        except ImportError:
            logger.warning("Sentry SDK not installed. Error tracking disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response

        except HTTPException:
            # Let FastAPI handle HTTP exceptions normally
            raise

        except Exception as e:
            # Get request context
            request_id = getattr(request.state, "request_id", "unknown")
            client_ip = self._get_client_ip(request)

            # Log the error with full context
            error_context = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_ip,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }

            logger.error(
                f"Unhandled exception in request",
                extra=error_context,
                exc_info=True
            )

            # Report to Sentry if initialized
            if self._sentry_initialized:
                self._report_to_sentry(e, request, error_context)

            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred",
                    "request_id": request_id,
                    # Include error type in development
                    "error_type": type(e).__name__ if self._is_debug(request) else None,
                },
                headers={
                    "X-Request-ID": request_id,
                }
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_debug(self, request: Request) -> bool:
        """Check if we're in debug mode."""
        # Could check app settings or environment variable
        return False

    def _report_to_sentry(self, exception: Exception, request: Request, context: dict):
        """Report exception to Sentry with context."""
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                scope.set_tag("request_id", context.get("request_id"))
                sentry_sdk.capture_exception(exception)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to report to Sentry: {e}")


# Custom exception classes for better error handling

class TraceHubError(Exception):
    """Base exception for TraceHub application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: dict = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code or "TRACEHUB_ERROR"
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ValidationError(TraceHubError):
    """Raised when validation fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )


class ResourceNotFoundError(TraceHubError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=404
        )


class ExternalServiceError(TraceHubError):
    """Raised when an external service fails."""

    def __init__(self, service: str, message: str, details: dict = None):
        super().__init__(
            message=f"External service error ({service}): {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, **(details or {})},
            status_code=502
        )


class ComplianceError(TraceHubError):
    """Raised for compliance-related issues."""

    def __init__(self, message: str, issues: list = None):
        super().__init__(
            message=message,
            error_code="COMPLIANCE_ERROR",
            details={"issues": issues or []},
            status_code=400
        )
