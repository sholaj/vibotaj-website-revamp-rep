# PRD-006: Sentry Integration

**Status:** Specified
**Complexity:** Low
**Target:** Week 2
**Dependencies:** PRD-001 (Next.js frontend — for frontend DSN), PRD-004 (FastAPI on Railway — for backend DSN)
**Branch:** `feature/prd-006-sentry-integration`

---

## Problem

v1 has basic Python logging and a custom `ErrorHandlerMiddleware` with `sentry_dsn=None` — the integration point exists but was never connected. No centralized error tracking, no performance monitoring, no session replay. Errors surface only if someone checks server logs via SSH. The middleware at `main.py:253` is already wired to accept a Sentry DSN — this PRD activates it.

## Acceptance Criteria

1. Sentry organization with 2 projects:
   - `tracehub-backend` (Python/FastAPI)
   - `tracehub-frontend` (JavaScript/Next.js)
2. FastAPI: `sentry-sdk[fastapi]` initialized with:
   - Environment tags (`development`, `staging`, `production`)
   - Performance tracing enabled
   - Release tracking (git SHA or version tag)
3. Existing `ErrorHandlerMiddleware` sends exceptions to Sentry
4. Next.js: `@sentry/nextjs` with:
   - Source map uploads for readable stack traces
   - Client-side error boundary integration
   - Server-side error capture (API routes, SSR)
5. Performance sampling: 100% in development, 10% in production
6. `send_default_pii=False` for GDPR compliance
7. Custom tags on all events: `organization_id`, `user_role`, `environment`
8. Alert rules: notify on first occurrence of new error types

## Technical Approach

### 1. Sentry Project Setup

Create Sentry organization `vibotaj` with two projects:
- `tracehub-backend` — platform: Python, framework: FastAPI
- `tracehub-frontend` — platform: JavaScript, framework: Next.js

### 2. FastAPI Backend Integration

```python
# tracehub/backend/app/sentry_setup.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

def init_sentry(dsn: str, environment: str, release: str | None = None):
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
        ],
        traces_sample_rate=1.0 if environment == "development" else 0.1,
        send_default_pii=False,
        before_send=scrub_sensitive_data,
    )

def scrub_sensitive_data(event, hint):
    """Remove sensitive fields before sending to Sentry."""
    # Strip authorization headers, API keys, passwords
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        for key in ["authorization", "cookie", "x-api-key"]:
            if key in headers:
                headers[key] = "[REDACTED]"
    return event
```

### 3. ErrorHandlerMiddleware Connection

Update the existing middleware instantiation in `main.py`:

```python
# Before (v1):
app.add_middleware(ErrorHandlerMiddleware, sentry_dsn=None)

# After (v2):
app.add_middleware(
    ErrorHandlerMiddleware,
    sentry_dsn=settings.SENTRY_DSN,  # From env var
)
```

Also add Sentry context per-request:

```python
@app.middleware("http")
async def sentry_context_middleware(request: Request, call_next):
    user = get_optional_current_user(request)
    if user:
        sentry_sdk.set_user({"id": str(user.id), "email": user.email})
        sentry_sdk.set_tag("organization_id", str(user.organization_id))
        sentry_sdk.set_tag("user_role", user.role.value)
    response = await call_next(request)
    return response
```

### 4. Next.js Frontend Integration

```bash
npx @sentry/wizard@latest -i nextjs
```

This creates:
- `sentry.client.config.ts` — client-side Sentry init
- `sentry.server.config.ts` — server-side Sentry init
- `sentry.edge.config.ts` — edge runtime Sentry init
- `next.config.ts` — updated with Sentry webpack plugin (source maps)

```typescript
// sentry.client.config.ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT,
  tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
  sendDefaultPii: false,
  integrations: [Sentry.replayIntegration({ maskAllText: true })],
  replaysSessionSampleRate: 0,       // Only capture on error
  replaysOnErrorSampleRate: 1.0,     // 100% of error sessions
});
```

### 5. Custom Error Boundary

```typescript
// v2/frontend/src/components/error-boundary.tsx
"use client";
import * as Sentry from "@sentry/nextjs";

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  );
}
```

### 6. Alert Rules

Configure in Sentry dashboard:
- **New issue alert:** Notify on first occurrence of any new error (Slack/email)
- **Regression alert:** Notify when a resolved issue recurs
- **Spike alert:** Notify when error rate exceeds 10x baseline in 5 minutes
- **Performance alert:** Notify when p95 response time exceeds 5 seconds

## Files to Create/Modify

```
tracehub/backend/app/
  sentry_setup.py              # NEW: Sentry initialization + scrubbing
  main.py                      # MODIFY: call init_sentry(), update ErrorHandlerMiddleware
  config.py                    # MODIFY: add SENTRY_DSN field
v2/frontend/
  sentry.client.config.ts      # NEW: Client-side Sentry
  sentry.server.config.ts      # NEW: Server-side Sentry
  sentry.edge.config.ts        # NEW: Edge runtime Sentry
  next.config.ts               # MODIFY: Sentry webpack plugin
  src/app/
    error.tsx                   # NEW: App-level error boundary
    global-error.tsx            # NEW: Root-level error boundary
  .env.example                 # MODIFY: add NEXT_PUBLIC_SENTRY_DSN
```

## v1 Reference Files

| v1 File | What to Reference |
|---------|------------------|
| `tracehub/backend/app/main.py:253` | `ErrorHandlerMiddleware` instantiation with `sentry_dsn=None` |
| `tracehub/backend/app/config.py` | Settings class — add `SENTRY_DSN` field |

## Testing Strategy

- Unit test: `scrub_sensitive_data()` removes authorization headers and API keys
- Unit test: `init_sentry()` configures correct sample rates per environment
- Verify: intentional error in dev → appears in Sentry dashboard within 30 seconds
- Verify: source maps resolve to readable TypeScript stack traces
- Verify: `send_default_pii=False` — no PII in Sentry event payloads
- Verify: performance traces appear for API routes and page loads

## Migration Notes

- v1 `ErrorHandlerMiddleware` is untouched — only the `sentry_dsn` parameter changes from `None` to env var
- Sentry free tier: 5K errors/month, 10K performance transactions — sufficient for dev/staging
- Source maps are uploaded at build time via `@sentry/nextjs` webpack plugin — no runtime overhead
- GDPR: `send_default_pii=False` + `scrub_sensitive_data` before-send hook ensures no personal data leaves the application
- Session replay uses `maskAllText: true` — no user-entered data is recorded
