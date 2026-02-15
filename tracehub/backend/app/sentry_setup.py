"""Sentry initialization and configuration for TraceHub backend.

Provides centralized Sentry setup with:
- Environment-aware sample rates (100% dev, 10% prod)
- PII scrubbing via before_send hook
- FastAPI, SQLAlchemy, and logging integrations
"""

import logging
import os

logger = logging.getLogger(__name__)


def init_sentry(dsn: str, environment: str = "development") -> bool:
    """Initialize Sentry error tracking and performance monitoring.

    Args:
        dsn: Sentry DSN string. If empty, Sentry is not initialized.
        environment: One of 'development', 'staging', 'production'.

    Returns:
        True if Sentry was initialized, False otherwise.
    """
    if not dsn:
        logger.info("Sentry DSN not configured — error tracking disabled")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Use git SHA as release if available
        release = os.environ.get("RAILWAY_GIT_COMMIT_SHA", None)

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.WARNING,
                    event_level=logging.ERROR,
                ),
            ],
            traces_sample_rate=1.0 if environment == "development" else 0.1,
            profiles_sample_rate=0.1 if environment == "production" else 0.0,
            send_default_pii=False,
            before_send=scrub_sensitive_data,
        )
        logger.info(f"Sentry initialized (environment={environment})")
        return True

    except ImportError:
        logger.warning("sentry-sdk not installed — error tracking disabled")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def scrub_sensitive_data(event: dict, hint: dict) -> dict:
    """Remove sensitive fields before sending to Sentry.

    Strips authorization headers, cookies, and API keys from event payloads
    to comply with GDPR and prevent credential leakage.
    """
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = {"authorization", "cookie", "x-api-key", "x-webhook-secret"}
        for key in sensitive_headers:
            if key in headers:
                headers[key] = "[REDACTED]"

    # Strip query string parameters that may contain tokens
    if "request" in event and "query_string" in event["request"]:
        qs = event["request"].get("query_string", "")
        if "token" in qs.lower() or "key" in qs.lower():
            event["request"]["query_string"] = "[REDACTED]"

    return event
