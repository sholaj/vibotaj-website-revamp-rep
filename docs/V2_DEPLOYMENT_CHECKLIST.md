# TraceHub v2 — Full Deployment Checklist

## Context

TraceHub v2 code is built (22/25 PRDs done) but needs external accounts created, credentials injected, and infrastructure deployed before going live. This checklist covers everything needed to get v2 running — from account sign-ups through DNS cutover.

---

## Step 1: Create External Accounts (~30 min)

| # | Service | URL | Status | What to Do |
|---|---------|-----|--------|-----------|
| 1 | **Supabase** | supabase.com | **Done** | Project: `tracehub` · Ref: `kwwzdfiyvxhvklutoltm` · URL: `https://kwwzdfiyvxhvklutoltm.supabase.co` |
| 2 | **PropelAuth** | propelauth.com | **Done** | Project: `tracehub` · Auth URL: `https://7545259.propelauthtest.com` (test) · 6 roles configured · API Key + Verifier Key obtained · **Pre-launch:** Click "Go Live" for prod URL + new keys, update Railway/Vercel env vars |
| 3 | **Railway** | railway.app | Pending | Sign up → connect GitHub repo → create project from `tracehub/backend/` |
| 4 | **Vercel** | vercel.com | Pending | Sign up → connect GitHub repo → set root to `v2/frontend/` |
| 5 | **Sentry** | sentry.io | Pending | Create org `vibotaj` → 2 projects: `tracehub-backend` (Python) + `tracehub-frontend` (JavaScript) → note DSNs + Auth Token |
| 6 | **Resend** | resend.com | Pending | Sign up → verify `vibotaj.com` domain → note API Key |
| 7 | **Stripe** | stripe.com | Deferred | Not needed for launch (PRD-022 not built yet) |

**Reuse from v1:** JSONCargo API key, Anthropic API key, GitHub repo access.

---

## Step 2: Run Supabase Migrations

Apply the 13 migration files in `v2/supabase/migrations/` in order:

| Migration | Purpose |
|-----------|---------|
| 001_create_enums.sql | UserRole, ShipmentStatus, DocumentType enums |
| 002_create_organizations.sql | Organizations table |
| 003_create_users.sql | Users table (organization_id FK) |
| 004_create_memberships_invitations.sql | Membership + invitation tables |
| 005_create_shipments.sql | Shipments (org_id + buyer_org_id) |
| 006_create_documents.sql | Documents table |
| 007_create_document_contents.sql | Document contents |
| 008_create_compliance_results.sql | Compliance results |
| 009_create_events_notifications.sql | Container events + notifications |
| 010_create_origins_products_registry_audit.sql | Origins, products, registry, audit logs |
| **011_enable_rls.sql** | **RLS on all 15 tables + security policies** |
| 012_create_indexes.sql | Performance indexes |
| 013_create_storage_buckets.sql | Supabase Storage buckets |

Run via Supabase dashboard SQL editor or `supabase db push`.

**Critical:** Use direct connection (port **5432**), NOT PgBouncer (6543) — SQLAlchemy prepared statements break on transaction-mode pooling.

---

## Step 3: Configure Railway (Backend)

Set these environment variables in Railway dashboard:

### Core
```
APP_NAME=TraceHub
DEBUG=false
ENVIRONMENT=production
```

### Database (from Supabase Step 1)
```
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

### Auth
```
PROPELAUTH_AUTH_URL=https://[your-org].propelauth.com
PROPELAUTH_API_KEY=[from PropelAuth dashboard]
JWT_SECRET=[generate 64-char random hex]
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Supabase Storage
```
STORAGE_BACKEND=supabase
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_SERVICE_KEY=[service-role-key]
MAX_UPLOAD_SIZE_MB=50
```

### External APIs (reuse v1 keys)
```
JSONCARGO_API_KEY=[v1 key]
JSONCARGO_API_URL=https://api.jsoncargo.com/api/v1
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=[v1 key]
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.70
```

### Email
```
EMAIL_PROVIDER=resend
EMAIL_ENABLED=true
RESEND_API_KEY=[from Resend]
EMAIL_FROM_ADDRESS=notifications@tracehub.vibotaj.com
EMAIL_FROM_NAME=TraceHub
```

### Monitoring
```
SENTRY_DSN=[backend DSN from Sentry]
```

### CORS
```
CORS_ORIGINS=["https://tracehub.vibotaj.com","https://tracehub-v2.vercel.app"]
```

### Integrations (mock until API access obtained)
```
CUSTOMS_PROVIDER=mock
CUSTOMS_ENABLED=false
BANKING_PROVIDER=mock
BANKING_ENABLED=false
```

### Other
```
FRONTEND_URL=https://tracehub.vibotaj.com
WEBHOOK_SECRET=[generate random HMAC secret]
ENABLE_DEMO_CREDENTIALS=false
OCR_ENABLED=true
OCR_DPI=300
OCR_TIMEOUT=30
OCR_LANGUAGE=eng
```

Railway auto-detects `railway.toml` → builds with nixpacks → starts uvicorn on `$PORT`.

**Verify:** `GET https://[railway-url]/health` returns 200.

---

## Step 4: Configure Vercel (Frontend)

Set these environment variables in Vercel dashboard for `v2/frontend/`:

```
NEXT_PUBLIC_API_URL=https://[railway-url]
NEXT_PUBLIC_PROPELAUTH_URL=https://[your-org].propelauth.com
PROPELAUTH_API_KEY=[api-key]
PROPELAUTH_VERIFIER_KEY=[verifier-key from PropelAuth]
NEXT_PUBLIC_SENTRY_DSN=[frontend DSN from Sentry]
SENTRY_AUTH_TOKEN=[auth token from Sentry]
SENTRY_ORG=vibotaj
SENTRY_PROJECT=tracehub-frontend
NEXT_PUBLIC_ENVIRONMENT=production
```

Vercel auto-detects `vercel.json` → builds Next.js → deploys.

**Verify:** `https://[vercel-url]` loads the app.

---

## Step 5: Migrate v1 Data

### 5a. Database (Hostinger → Supabase)
```bash
# Export from v1
ssh root@82.198.225.150
docker exec tracehub-db pg_dump -U tracehub -d tracehub > tracehub_v1_dump.sql

# Import to Supabase (after running v2 migrations)
psql "postgresql://postgres.[ref]:[pwd]@[host]:5432/postgres" < tracehub_v1_dump.sql
```

### 5b. Users (v1 JWT → PropelAuth)
- Script reads v1 users table → creates accounts in PropelAuth via Management API
- **Forces password reset** (v1 bcrypt hashes can't be imported)
- Maps existing roles to PropelAuth org roles
- Notify users in advance about password reset

### 5c. Files (local uploads → Supabase Storage)
- Scan `tracehub/uploads/` on Hostinger
- Upload each file to appropriate Supabase Storage bucket
- Update document records with new storage URLs

---

## Step 6: DNS Cutover

Update DNS records at your registrar:

| Record | Name | Value | Purpose |
|--------|------|-------|---------|
| CNAME | tracehub.vibotaj.com | cname.vercel-dns.com | Frontend |
| CNAME | api.tracehub.vibotaj.com | [railway-url] | Backend API |

**Or** if Railway provides an IP, use an A record.

Update `CORS_ORIGINS` on Railway and `NEXT_PUBLIC_API_URL` on Vercel to use the final domain names.

---

## Step 7: Post-Deploy Validation

### Smoke Tests
- [ ] Homepage loads at tracehub.vibotaj.com
- [ ] PropelAuth login flow works
- [ ] Create a test shipment (verifies DB + RLS + auth)
- [ ] Upload a document (verifies Supabase Storage)
- [ ] Check compliance status (verifies business logic)
- [ ] Trigger email notification (verifies Resend)
- [ ] Check Sentry for any errors

### Security Checks
- [ ] HTTPS enforced on both domains
- [ ] CORS headers correct (no `*` in production)
- [ ] `ENABLE_DEMO_CREDENTIALS=false`
- [ ] RLS policies blocking cross-tenant access
- [ ] No secrets in logs

### Multi-Tenancy Verification
- [ ] Org A user cannot see Org B shipments
- [ ] Buyer org can view (read-only) shipments where they're the buyer
- [ ] `organization_id` always derived from auth token, never frontend

---

## Step 8: Decommission v1

After **2-week monitoring period** with no issues:

1. Take final v1 database backup
2. Verify all data migrated correctly
3. Shut down Docker containers on Hostinger
4. Cancel Hostinger VPS (82.198.225.150)

---

## Credentials Summary

| Service | Credentials Needed | Count |
|---------|-------------------|-------|
| Supabase | Project URL (**have**), Service Key (**need**), Anon Key (**have**), DB URL (**need**) | 4 |
| PropelAuth | Auth URL (**have**), API Key (**have**), Verifier Key (**have**) | 3 |
| Sentry | Backend DSN, Frontend DSN, Auth Token | 3 |
| Resend | API Key | 1 |
| Stripe | Publishable Key, Secret Key | 2 |
| JSONCargo | API Key (reuse v1) | 1 |
| Anthropic | API Key (reuse v1) | 1 |
| JWT | Secret (generate new) | 1 |
| Webhook | HMAC Secret (generate new) | 1 |
| **Total** | | **17 credentials** |

---

## What's Still Needed Before Go-Live

| Item | Status | Blocker? |
|------|--------|----------|
| Account creation (6 services) | **Supabase + PropelAuth done** — 4 remaining | Yes |
| Supabase migrations | Run once | Yes |
| Railway env vars | Manual config | Yes |
| Vercel env vars | Manual config | Yes |
| PRD-022 (Stripe billing) | Not built | No (can launch without billing) |
| PRD-023 (White-label branding) | Not built | No |
| PRD-025 (Performance optimization) | Not built | No |
| Data migration scripts | Need implementation | Yes (for existing data) |
| User migration script | Need implementation | Yes (for existing users) |
| DNS cutover | Manual | Yes (final step) |
