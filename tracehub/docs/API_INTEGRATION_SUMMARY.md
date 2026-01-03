# TraceHub API Integration - Quick Reference

## Sprint Roadmap

```
Sprint 3 (20 pts)     Sprint 4 (26 pts)     Sprint 5 (19 pts)
|                     |                     |
| Vizion Subscribe    | AI Completeness     | Digital Signatures
| Webhook Logging     | AI Discrepancies    | RFC 3161 Timestamps
| Email SMTP Setup    | AI Summaries        | Email Preferences
| DB Migrations       | Tracking Polling    | Digest Emails
|                     |                     | Integration Tests
v                     v                     v
[Foundation]          [Intelligence]        [Compliance]
```

## New Endpoints Summary

### Feature 1: Container Tracking (18 pts)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/tracking/subscribe/{shipment_id}` | Subscribe container to Vizion |
| DELETE | `/api/tracking/unsubscribe/{shipment_id}` | Cancel tracking subscription |
| GET | `/api/tracking/subscriptions` | List active subscriptions |
| POST | `/api/tracking/poll/{shipment_id}` | Manual tracking refresh |
| GET | `/api/tracking/carriers` | List supported carriers |
| GET | `/api/webhooks/logs` | View webhook history |
| POST | `/api/webhooks/replay/{event_id}` | Replay failed webhook |

### Feature 2: Audit Pack (8 pts)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/shipments/{id}/audit-pack/preview` | Preview audit pack contents |
| POST | `/api/shipments/{id}/audit-pack/generate` | Generate signed audit pack |
| GET | `/api/shipments/{id}/audit-pack/verify` | Verify pack integrity |
| GET | `/api/audit-packs` | List generated audit packs |

### Feature 3: AI Workflows (21 pts)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/ai/analyze/shipment/{id}` | Full AI analysis |
| POST | `/api/ai/analyze/document/{id}` | Single document analysis |
| POST | `/api/ai/check/completeness/{id}` | Document completeness check |
| POST | `/api/ai/check/discrepancies/{id}` | Cross-document consistency |
| POST | `/api/ai/generate/summary/{id}` | Human-readable summary |
| GET | `/api/ai/analyses` | Analysis history |
| GET | `/api/ai/usage` | Token usage stats |

### Feature 4: Email Notifications (8 pts)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/notifications/email/send` | Send templated email |
| POST | `/api/notifications/email/test` | Test email config |
| GET | `/api/notifications/email/templates` | List templates |
| GET | `/api/notifications/email/logs` | Email delivery logs |
| GET | `/api/notifications/preferences` | Get user preferences |
| PUT | `/api/notifications/preferences` | Update preferences |

## New Data Models

```
TrackingSubscription    - Vizion subscription state
WebhookLog              - Webhook processing history
AuditPack               - Generated audit pack metadata
AIAnalysis              - AI analysis results cache
AIUsageLog              - Token usage tracking
EmailLog                - Email delivery history
UserNotificationPreferences - Per-user notification settings
```

## External Services Required

| Service | Provider | Purpose | Config Key |
|---------|----------|---------|------------|
| Container Tracking | Vizion | Real-time updates | `VIZION_API_KEY` |
| Container Tracking | JSONCargo | Backup/polling | `JSONCARGO_API_KEY` |
| AI/LLM | Anthropic | Document analysis | `ANTHROPIC_API_KEY` |
| Email | SendGrid/SMTP | Notifications | `SMTP_*` |
| Timestamping | DigiCert TSA | Audit pack signing | `TSA_URL` |

## Configuration Additions

```python
# Add to .env

# AI Configuration
ANTHROPIC_API_KEY=sk-ant-xxx
AI_MODEL=claude-3-haiku
AI_MAX_TOKENS=4096
AI_RATE_LIMIT=60

# Email Configuration
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxx
EMAIL_FROM_ADDRESS=notifications@tracehub.vibotaj.com
EMAIL_FROM_NAME=TraceHub

# Timestamping
TSA_URL=http://timestamp.digicert.com
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `SUBSCRIPTION_EXISTS` | 409 | Container already subscribed |
| `CARRIER_NOT_SUPPORTED` | 400 | Unknown carrier code |
| `VIZION_API_ERROR` | 502 | Upstream API failure |
| `ANALYSIS_TIMEOUT` | 504 | AI response timeout |
| `QUOTA_EXCEEDED` | 429 | Rate/usage limit reached |
| `SMTP_ERROR` | 502 | Email delivery failed |
| `SIGNING_FAILED` | 500 | Digital signature error |

## Testing Checklist

- [ ] Vizion subscribe/unsubscribe flow
- [ ] Webhook signature verification
- [ ] AI analysis with real documents
- [ ] Email template rendering
- [ ] Audit pack generation < 60s
- [ ] Digital signature verification
- [ ] User preference persistence
- [ ] Rate limiting enforcement

## Files Created

```
tracehub/docs/
  API_INTEGRATION_PLAN.md      - Full architecture document
  API_INTEGRATION_SUMMARY.md   - This quick reference
  openapi/
    tracking.yaml              - Tracking API spec
    ai.yaml                    - AI Analysis API spec
    notifications.yaml         - Notifications API spec
```
