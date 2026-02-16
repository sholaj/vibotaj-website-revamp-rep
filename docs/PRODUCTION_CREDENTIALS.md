# Production Credentials Checklist

Everything needed to take TraceHub v2 from localhost to `tracehub.vibotaj.com`.

---

## Required Services (show-stoppers if missing)

### 1. Supabase — Database + Storage + Realtime

| | |
|---|---|
| **Sign up** | [supabase.com](https://supabase.com) |
| **Free tier** | Yes (500 MB database, 1 GB storage) |
| **Used for** | PostgreSQL + RLS + file storage + realtime subscriptions |

**Env vars:**

```bash
# Backend
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_KEY=eyJ...   # service_role key (never expose to frontend)

# Frontend
NEXT_PUBLIC_SUPABASE_URL=https://[project].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...   # anon/public key
```

**Setup steps:**
1. Create a new Supabase project
2. Run the migration SQL from `tracehub/backend/alembic/` (or connect Alembic to the Supabase DB URL)
3. Enable RLS on all tenant-scoped tables (see `.claude/rules/multi-tenancy.md`)
4. Create a Storage bucket for document uploads

---

### 2. PropelAuth — Authentication + Organizations + Roles

| | |
|---|---|
| **Sign up** | [propelauth.com](https://propelauth.com) |
| **Free tier** | Yes (1,000 MAU) |
| **Used for** | Login, signup, org management, 6 roles, SAML/SCIM |

**Env vars:**

```bash
# Backend
PROPELAUTH_AUTH_URL=https://[your-project].propelauthtest.com
PROPELAUTH_API_KEY=sk-...
PROPELAUTH_VERIFIER_KEY=-----BEGIN PUBLIC KEY-----...

# Frontend
NEXT_PUBLIC_PROPELAUTH_URL=https://[your-project].propelauthtest.com
```

**Setup steps:**
1. Create a PropelAuth project
2. Configure the 6 roles: `admin`, `compliance_officer`, `logistics`, `buyer`, `supplier`, `viewer`
3. Enable organizations (multi-tenant mode)
4. Set the frontend integration URL to `https://tracehub.vibotaj.com`
5. Set the backend integration URL to `https://api.tracehub.vibotaj.com`
6. Copy the API key, verifier key, and auth URL

---

### 3. Vercel — Frontend Hosting

| | |
|---|---|
| **Sign up** | [vercel.com](https://vercel.com) |
| **Free tier** | Yes (Hobby plan) |
| **Used for** | Next.js hosting, CDN, edge functions |

**Setup steps:**
1. Link GitHub repo (`sholaj/vibotaj-website-revamp-rep`)
2. Set root directory to `v2/frontend`
3. Add all `NEXT_PUBLIC_*` and `PROPELAUTH_*` env vars in project settings
4. Add `SENTRY_AUTH_TOKEN` for source map uploads
5. Deploy — Vercel auto-builds on push to `main`

---

### 4. Railway — Backend Hosting

| | |
|---|---|
| **Sign up** | [railway.app](https://railway.app) |
| **Cost** | $5/mo (Pro plan) |
| **Used for** | FastAPI backend, background workers |

**Setup steps:**
1. Link GitHub repo
2. Set root directory to `tracehub/backend` (or use a Dockerfile)
3. Add all backend env vars (DATABASE_URL, PROPELAUTH_*, ANTHROPIC_API_KEY, etc.)
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configure health check on `GET /health`

---

### 5. Sentry — Error Tracking + Performance

| | |
|---|---|
| **Sign up** | [sentry.io](https://sentry.io) |
| **Free tier** | Yes (5K errors/mo, 10K transactions/mo) |
| **Used for** | Error tracking, performance monitoring, release tracking |

**Env vars:**

```bash
# Backend
SENTRY_DSN=https://[key]@o[org-id].ingest.sentry.io/[project-id]

# Frontend
NEXT_PUBLIC_SENTRY_DSN=https://[key]@o[org-id].ingest.sentry.io/[project-id]
SENTRY_AUTH_TOKEN=sntrys_...   # for source map uploads
SENTRY_ORG=vibotaj
SENTRY_PROJECT=tracehub-frontend
```

**Setup steps:**
1. Create two Sentry projects: `tracehub-frontend` (Next.js) and `tracehub-backend` (Python)
2. Copy DSNs to env vars
3. Create an auth token for source map uploads

---

### 6. JSONCargo — Container Tracking

| | |
|---|---|
| **Sign up** | [jsoncargo.com](https://jsoncargo.com) |
| **Cost** | ~$10-30/mo (existing v1 account) |
| **Used for** | Container tracking data, vessel schedules |

**Env vars:**

```bash
JSONCARGO_API_KEY=jc_...
```

---

### 7. Anthropic — AI Document Classification

| | |
|---|---|
| **Sign up** | [console.anthropic.com](https://console.anthropic.com) |
| **Cost** | Pay-per-use (~$0.80/M input tokens with Haiku) |
| **Used for** | Document OCR classification, BoL parsing, compliance checks |

**Env vars:**

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Optional Services (degrade gracefully)

### 8. Resend — Email Notifications

| | |
|---|---|
| **Sign up** | [resend.com](https://resend.com) |
| **Free tier** | Yes (3,000 emails/mo) |
| **Used for** | Shipment alerts, compliance notifications, invitations |

**Env vars:**

```bash
EMAIL_PROVIDER=resend            # or "console" for dev
RESEND_API_KEY=re_...
EMAIL_FROM=notifications@tracehub.vibotaj.com
```

**DNS required:** SPF + DKIM records for `tracehub.vibotaj.com` (Resend provides these during domain verification).

---

### 9. Customs APIs — Pre-Clearance

Not yet integrated. Use the mock provider:

```bash
CUSTOMS_PROVIDER=mock
```

---

### 10. Banking APIs — LC + Payments + Forex

Not yet integrated. Use the mock provider:

```bash
BANKING_PROVIDER=mock
```

---

### 11. Stripe — Billing (PRD-022, not built yet)

Will be needed in Phase 4.

---

## Additional Production Config

```bash
# Security
JWT_SECRET=<strong-random-string-64-chars>
WEBHOOK_SECRET=<strong-random-string-32-chars>

# CORS
CORS_ORIGINS=https://tracehub.vibotaj.com

# Email links
FRONTEND_URL=https://tracehub.vibotaj.com
```

---

## DNS Configuration

| Record | Type | Value |
|--------|------|-------|
| `tracehub.vibotaj.com` | CNAME | `cname.vercel-dns.com` (or Vercel-assigned) |
| `api.tracehub.vibotaj.com` | CNAME | Railway-provided domain |
| Resend SPF/DKIM | TXT | Provided by Resend during domain verification |

---

## Estimated Monthly Cost

| Service | Cost |
|---------|------|
| Supabase | $0 (free tier) |
| PropelAuth | $0 (free tier) |
| Vercel | $0 (hobby) |
| Railway | $5 |
| Sentry | $0 (free tier) |
| JSONCargo | ~$10-30 |
| Anthropic | ~$10-50 |
| Resend | $0 (free tier) |
| **Total** | **~$25-85/mo** |

---

## Quick Start: Signup Order

1. **Supabase** — create project, get DATABASE_URL (everything depends on this)
2. **PropelAuth** — create project, configure roles + orgs, get keys
3. **Sentry** — create projects, get DSNs
4. **Anthropic** — create API key (if not already from v1)
5. **Resend** — create account, verify domain
6. **Vercel** — link repo, add env vars, deploy frontend
7. **Railway** — link repo, add env vars, deploy backend
8. **DNS** — point domains, add Resend SPF/DKIM records
