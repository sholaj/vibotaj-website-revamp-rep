"""Request tracking middleware - adds request IDs and timing."""

import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Header names
REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_TIME_HEADER = "X-Request-Time"


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds request tracking capabilities.

    Features:
    - Generates unique request ID for each request
    - Measures request duration
    - Logs request/response details
    - Adds tracking headers to response
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))

        # Store request ID in state for access by other components
        request.state.request_id = request_id

        # Record start time
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": self._get_client_ip(request),
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Add tracking headers to response
            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[REQUEST_TIME_HEADER] = f"{duration_ms:.2f}ms"

            # Log completed request
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed with exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxy headers."""
        # Check X-Forwarded-For first (common with reverse proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in the list is the original client
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"
