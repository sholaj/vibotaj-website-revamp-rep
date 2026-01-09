"""Rate limiting middleware - prevents abuse.

Skips rate limiting automatically when running in CI or testing environments
to avoid interfering with automated test suites.
"""

import time
import logging
import os
from typing import Dict, Tuple
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.

    Features:
    - Per-IP rate limiting
    - Configurable limits per time window
    - Different limits for different endpoint patterns
    - Returns proper 429 responses with Retry-After header

    Note: For production with multiple workers, use Redis-based rate limiting.
    """

    def __init__(
        self,
        app,
        # Default: 100 requests per minute
        default_limit: int = 100,
        default_window: int = 60,
        # Endpoint-specific limits (path prefix -> (limit, window))
        endpoint_limits: Dict[str, Tuple[int, int]] = None,
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.endpoint_limits = endpoint_limits or {
            "/api/auth/login": (10, 60),  # 10 login attempts per minute
            "/api/tracking/": (50, 60),  # 50 tracking requests per minute
            "/api/documents/upload": (20, 60),  # 20 uploads per minute
        }

        # In-memory storage: {ip: {window_key: count}}
        self._requests: Dict[str, Dict[str, int]] = defaultdict(dict)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Clean up every 5 minutes

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for certain paths
        if self._should_skip(request):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Get applicable limit
        limit, window = self._get_limit_for_path(path)

        # Check rate limit
        if not self._is_allowed(client_ip, path, limit, window):
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "path": path,
                    "limit": limit,
                    "window": window,
                }
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": window,
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + window),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining(client_ip, path, limit, window)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time()) + window - (int(time.time()) % window)
        )

        # Periodic cleanup
        self._maybe_cleanup()

        return response

    def _should_skip(self, request: Request) -> bool:
        """Skip rate limiting for certain paths."""
        # Skip in CI/testing environments or when explicitly disabled
        if (
            os.getenv("TESTING", "").lower() == "true"
            or os.getenv("CI", "").lower() == "true"
            or os.getenv("RATE_LIMIT_DISABLED", "").lower() == "true"
        ):
            return True

        skip_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        return any(request.url.path.startswith(p) for p in skip_paths)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def _get_limit_for_path(self, path: str) -> Tuple[int, int]:
        """Get rate limit for a given path."""
        for prefix, (limit, window) in self.endpoint_limits.items():
            if path.startswith(prefix):
                return limit, window
        return self.default_limit, self.default_window

    def _get_window_key(self, window: int) -> str:
        """Get the current time window key."""
        return str(int(time.time()) // window)

    def _is_allowed(self, client_ip: str, path: str, limit: int, window: int) -> bool:
        """Check if request is allowed under rate limit."""
        window_key = self._get_window_key(window)
        key = f"{path}:{window_key}"

        current_count = self._requests[client_ip].get(key, 0)

        if current_count >= limit:
            return False

        # Increment counter
        self._requests[client_ip][key] = current_count + 1
        return True

    def _get_remaining(self, client_ip: str, path: str, limit: int, window: int) -> int:
        """Get remaining requests in current window."""
        window_key = self._get_window_key(window)
        key = f"{path}:{window_key}"
        current_count = self._requests[client_ip].get(key, 0)
        return limit - current_count

    def _maybe_cleanup(self):
        """Periodically clean up old entries."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        self._last_cleanup = now

        # Remove old window entries
        current_time = int(now)
        max_window = max(w for _, w in self.endpoint_limits.values()) if self.endpoint_limits else self.default_window

        for ip in list(self._requests.keys()):
            for key in list(self._requests[ip].keys()):
                # Extract window start time from key
                try:
                    _, window_start = key.rsplit(":", 1)
                    window_start_time = int(window_start) * max_window
                    # Remove if older than 2 * max_window
                    if current_time - window_start_time > 2 * max_window:
                        del self._requests[ip][key]
                except (ValueError, KeyError):
                    pass

            # Remove IP entry if empty
            if not self._requests[ip]:
                del self._requests[ip]

        logger.debug(f"Rate limit cleanup: {len(self._requests)} IPs tracked")
