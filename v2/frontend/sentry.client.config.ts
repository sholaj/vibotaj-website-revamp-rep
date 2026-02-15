// TraceHub v2 — Sentry client-side configuration
// Captures browser errors, performance traces, and session replays on error.

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT ?? "development",

  // Performance: 100% in dev, 10% in prod
  tracesSampleRate:
    process.env.NEXT_PUBLIC_ENVIRONMENT === "production" ? 0.1 : 1.0,

  // Session replay — only on errors (no recording of normal sessions)
  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  replaysSessionSampleRate: 0,
  replaysOnErrorSampleRate: 1.0,

  // GDPR: never send PII
  sendDefaultPii: false,
});
