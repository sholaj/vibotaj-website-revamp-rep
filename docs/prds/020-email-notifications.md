# PRD-020: Email Notifications

## Problem Statement

TraceHub has in-app notifications (v1 `NotificationService` with 7 event triggers) but zero email delivery. The invitation service explicitly stubs email with `[EMAIL PLACEHOLDER]` log messages. Users miss critical shipment events — document approvals, compliance alerts, status changes — because they must actively check the app. Email notifications are table-stakes for a compliance SaaS where missed deadlines have real regulatory consequences.

## Solution

Build a provider-agnostic email notification system using the same Protocol pattern as `LLMBackend` and `StorageBackend`. Default provider: **Resend** (modern API, React Email-style templates, 3k/month free tier). Simple synchronous sending with 3x retry — no Celery/queue infrastructure needed at current volume.

## Architecture

```
EmailBackend (Protocol)
├── ResendBackend      ← default provider
├── ConsoleBackend     ← dev/test (logs to stdout)
└── [future backends]  ← SendGrid, Postmark, SMTP via config swap

EmailTemplateEngine
├── Base HTML layout (per-org branding: logo, colors)
├── document_uploaded / approved / rejected
├── shipment_status_change
├── compliance_alert
├── invitation_sent / accepted
└── expiry_warning
```

## Acceptance Criteria

### Backend
- [ ] `EmailBackend` Protocol with `send()`, `send_batch()`, `is_available()`, `get_provider_name()`, `get_status()`
- [ ] `ResendBackend` implementation using `resend` Python SDK
- [ ] `ConsoleBackend` for dev/test (prints email to stdout, tracks calls)
- [ ] `get_email_backend()` factory (singleton, reads `email_provider` from Settings)
- [ ] `EmailTemplateEngine` renders HTML emails with org branding (logo_url, primary_color, org_name)
- [ ] `NotificationEmailService` orchestrates: check user preferences → render template → send via backend
- [ ] 8 email event handlers: `document_uploaded`, `document_approved`, `document_rejected`, `shipment_status_change`, `compliance_alert`, `invitation_sent`, `invitation_accepted`, `expiry_warning`
- [ ] User notification preferences: per-event opt-in/out stored in DB
- [ ] Config: `email_provider`, `resend_api_key` (SecretStr), `email_from_address`, `email_from_name`, `email_enabled`
- [ ] Retry logic: 3 attempts with exponential backoff (1s, 4s, 16s)
- [ ] Replace `[EMAIL PLACEHOLDER]` stubs in invitation.py with real sends
- [ ] All emails include unsubscribe link and org context

### Frontend
- [ ] Notification preferences page at `/settings/notifications`
- [ ] Toggle per event type (document, shipment, compliance, invitation)
- [ ] React Query hooks: `useNotificationPreferences()`, `useUpdateNotificationPreferences()`

### API Endpoints
- [ ] `GET /api/users/me/notification-preferences` — get current preferences
- [ ] `PUT /api/users/me/notification-preferences` — update preferences
- [ ] `POST /api/admin/notifications/test` — send test email (admin only)

## Database Changes

### New table: `notification_preferences`
```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- matches NotificationType enum
    email_enabled BOOLEAN NOT NULL DEFAULT true,
    in_app_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, organization_id, event_type)
);
```

### New table: `email_log`
```sql
CREATE TABLE email_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    recipient_email VARCHAR(320) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, sent, failed
    provider VARCHAR(50) NOT NULL,
    provider_message_id VARCHAR(255),
    error_message TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Config Changes (`config.py`)

```python
# Email (PRD-020)
email_provider: str = "console"  # "resend", "console"
email_enabled: bool = False
resend_api_key: SecretStr = SecretStr("")
email_from_address: str = "notifications@tracehub.vibotaj.com"
email_from_name: str = "TraceHub"
```

## Frontend Changes

### New page: `/settings/notifications`
- Table of event types with email toggle + in-app toggle per row
- Grouped by category: Documents, Shipments, Compliance, Team
- Save button with optimistic update

### New files
- `v2/frontend/src/app/settings/notifications/page.tsx`
- `v2/frontend/src/lib/api/notification-types.ts`
- `v2/frontend/src/lib/api/notifications.ts`
- `v2/frontend/src/components/settings/notification-preferences.tsx`

## Email Template Structure

All emails share a base layout:
- Organization logo (from org settings, fallback to TraceHub logo)
- Primary color accent (from org settings, fallback to TraceHub blue)
- Footer: "Sent by TraceHub on behalf of {org_name}" + unsubscribe link

### Template: Document Status
- Subject: "[TraceHub] {doc_type} has been {action}"
- Body: document name, action taken, by whom, link to shipment

### Template: Shipment Status
- Subject: "[TraceHub] Shipment {ref} status: {status}"
- Body: shipment reference, old → new status, link to shipment

### Template: Compliance Alert
- Subject: "[TraceHub] Compliance alert: {shipment_ref}"
- Body: alert type, severity, affected documents, link to shipment

### Template: Invitation
- Subject: "You've been invited to {org_name} on TraceHub"
- Body: inviter name, role, accept button (link)

## Compliance Impact

None. Email notifications are operational, not compliance-affecting. No EUDR impact. Checked against `docs/COMPLIANCE_MATRIX.md`.

## Dependencies

- PRD-015 (User/Org Management) — user preferences need user + org context
- PRD-016 (Compliance Engine) — compliance alert triggers

## Non-Goals (v1)

- Real-time push notifications (WebSocket/SSE) — future PRD
- SMS notifications — future PRD
- Daily/weekly digest emails — future PRD
- Email analytics (open rates, click tracking) — future PRD
