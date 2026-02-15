// TraceHub v2 — Sentry server-side configuration
// Captures SSR errors and API route errors on the Node.js runtime.

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT ?? "development",

  // Performance: 100% in dev, 10% in prod
  tracesSampleRate:
    process.env.NEXT_PUBLIC_ENVIRONMENT === "production" ? 0.1 : 1.0,

  // GDPR: never send PII
  sendDefaultPii: false,
});
