# TraceHub v2 — Living Plan

## Current Phase
**Phase: 0 — Foundation**
**Focus: Project scaffolding, AI orchestration, migration preparation**

## v1 Status (Sprints 1-14 — Complete)

Production-deployed at https://tracehub.vibotaj.com on Hostinger VPS. 14 sprints delivered:

| Sprint | Theme | Key Deliverables |
|--------|-------|-----------------|
| 1-1.5 | Foundation | FastAPI, PostgreSQL, Docker, JSONCargo tracking |
| 2 | Access Control | 6 roles, RBAC, user management |
| 3 | Document Workflow | Lifecycle states, validation, approval |
| 4 | EUDR Compliance | Compliance tracking, analytics dashboard |
| 5 | Historical Data | Shipment creation, logistics workflow |
| 6 | Live Tracking | Real-time visibility, email notifications |
| 7 | Stakeholder Portals | Buyer dashboard, supplier checklists, AI doc classification |
| 8 | Multi-Tenancy | Organization model, data isolation |
| 9 | Compliance Matrix | EUDR exemptions, Horn & Hoof handling |
| 10-11 | Architecture Cleanup | Schema fixes, UUID FKs, buyer access |
| 12 | Stabilization | DateTime tz, state machine, BoL compliance |
| 13 | Member Management | Invitations, acceptance workflow |
| 14 | Compliance Hardening | EUDR fixes, origin model, PDF reports |

**v1 Test Coverage:** 40+ backend test files, Vitest frontend tests, Playwright E2E
**v1 Known Issues:** See `tracehub/docs/KNOWN_ISSUES.md` (most resolved)

---

## v2 Target Architecture

```
Users → Vercel (Next.js 15 SSR + BFF) → Railway (FastAPI + Celery) → Supabase (Postgres + RLS + Realtime + Storage)
                                       ↕                              ↕
                                  PropelAuth                     Sentry
                               (Auth + Orgs)                  (Monitoring)
```

**Type Bridge:** FastAPI Pydantic models → OpenAPI spec → Hey API → TypeScript client + Zod schemas

---

## Phase 0: Foundation (Current)

- [x] v2 CLAUDE.md — execution rules, stack, git flow
- [x] v2 PLAN.md — living sprint plan with PRD roadmap
- [x] `.claude/rules/` — domain rules (multi-tenancy, compliance, security, API, Pydantic, testing)
- [x] `.claude/skills/` — reusable workflows (new-feature, tdd, review, report, status, deploy, fix-issue)
- [ ] PRD-001: Next.js 15 scaffold + Vercel config
- [ ] PRD-002: Supabase project setup + schema migration
- [ ] PRD-003: PropelAuth integration (replacing custom JWT)

## Phase 1: Infrastructure Migration (Weeks 1-4)

| PRD | Title | Complexity | Target |
|-----|-------|-----------|--------|
| 001 | Next.js 15 scaffold + Vercel deployment | Medium | Week 1 |
| 002 | Supabase setup + PostgreSQL migration + RLS | High | Week 2 |
| 003 | PropelAuth integration (6 roles, orgs, SAML) | High | Week 3 |
| 004 | FastAPI on Railway + Celery workers | Medium | Week 3 |
| 005 | Supabase Storage for document uploads | Low | Week 4 |
| 006 | Sentry integration (backend + frontend) | Low | Week 4 |
| 007 | OpenAPI → Hey API type bridge | Medium | Week 4 |

## Phase 2: Frontend Rebuild (Weeks 5-8)

| PRD | Title | Complexity | Target |
|-----|-------|-----------|--------|
| 008 | Design system (Shadcn + Tailwind tokens from UI spec) | Medium | Week 5 |
| 009 | Auth pages (PropelAuth components + org switcher) | Medium | Week 5 |
| 010 | Dashboard + shipment list (SSR) | Medium | Week 6 |
| 011 | Shipment detail + document management | High | Week 6-7 |
| 012 | Container tracking timeline (Supabase Realtime) | Medium | Week 7 |
| 013 | Analytics dashboard (Recharts + SSR) | Medium | Week 8 |
| 014 | User/org management (PropelAuth admin) | Medium | Week 8 |

## Phase 3: Business Logic Enhancement (Weeks 9-12)

| PRD | Title | Complexity | Target |
|-----|-------|-----------|--------|
| 015 | Enhanced compliance engine (state machine + validation) | High | Week 9 |
| 016 | Audit pack v2 (PDF index + ZIP + Supabase Storage) | Medium | Week 10 |
| 017 | BoL parser + auto-enrichment pipeline | Medium | Week 10 |
| 018 | AI document classification v2 (Claude + OCR) | High | Week 11 |
| 019 | Email notifications (Resend/SendGrid + templates) | Medium | Week 11 |
| 020 | Third-party integrations (customs, banking) | High | Week 12 |

## Phase 4: SaaS Hardening (Weeks 13-16)

| PRD | Title | Complexity | Target |
|-----|-------|-----------|--------|
| 021 | Stripe billing integration | High | Week 13 |
| 022 | White-label branding (per-org logos, colors, domains) | Medium | Week 14 |
| 023 | Self-service onboarding flow | Medium | Week 15 |
| 024 | Performance optimization (edge caching, ISR, lazy loading) | Medium | Week 16 |

---

## In Progress
_Phase 0 foundation_

## Blocked
_None_

---

## Decisions Made

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-15 | Super Pack over Azure | Azure over-engineered for current stage; $75-125/mo vs $500-800/mo |
| 2026-02-15 | Keep FastAPI + add Next.js BFF | Preserves 14 sprints of business logic; Python for OCR/PDF/compliance |
| 2026-02-15 | Supabase for database + RLS | Multi-tenancy via RLS + Realtime for tracking + Storage for docs — all in one |
| 2026-02-15 | PropelAuth over Clerk | 6+ custom roles, org-level RBAC, SAML/SCIM, official FastAPI SDK |
| 2026-02-15 | Vercel for Next.js hosting | Optimized for Next.js; preview deploys, edge caching, ISR |
| 2026-02-15 | Railway for FastAPI hosting | Managed containers, per-minute billing, one-click databases |
| 2026-02-15 | OpenAPI → Hey API for type bridge | Pydantic stays source of truth; auto-gen TS client from OpenAPI spec |
| 2026-02-15 | Shared DB + RLS for multi-tenancy | Defense-in-depth: application-level org_id filtering + database-level RLS |
| 2026-02-15 | PRD-driven feature branches (iMaintain pattern) | Each feature = numbered PRD + feature branch + TDD + validation + commit |
| 2026-02-15 | Sentry over Application Insights | Standard for SaaS; error tracking + performance + session replay |
| Previous | Horn & Hoof (0506/0507) NOT EUDR-covered | Regulatory fact — NEVER add geolocation/deforestation fields |
| Previous | Custom JWT auth (v1) | Sufficient for POC; replaced by PropelAuth in v2 |
| Previous | Hostinger VPS (v1) | Cheapest option for POC; replaced by Vercel + Railway in v2 |
| Previous | SQLAlchemy + Alembic (v1) | Standard ORM; maintained in v2 backend alongside Supabase |

---

## Key Metrics

### v1 (Current)
- Production: 14 sprints delivered, live at tracehub.vibotaj.com
- Backend: 40+ test files, 12 routers, 15+ services
- Frontend: 7 pages, 20+ components
- Users: 6 roles across 2+ organizations (VIBOTAJ, HAGES)
- Real shipments: Nigeria (Apapa, Lagos) → Germany (Hamburg)

### v2 (Target)
- Open PRDs: 24 (001-024)
- Phase 0: Foundation complete
- Phase 1: Infrastructure migration (Weeks 1-4)
- Phase 2: Frontend rebuild (Weeks 5-8)
- Phase 3: Business logic enhancement (Weeks 9-12)
- Phase 4: SaaS hardening (Weeks 13-16)

---

## Migration Strategy

**Principle: Zero downtime. v1 runs until v2 is ready.**

1. **Phase 0-1:** Build v2 infrastructure alongside v1. v1 stays live on Hostinger.
2. **Phase 2:** Rebuild frontend on Next.js. Backend stays FastAPI — no rewrite.
3. **Phase 3:** Enhance business logic with Supabase features (Realtime, Storage, RLS).
4. **Cutover:** DNS switch from Hostinger to Vercel. FastAPI moves to Railway. Database migrates to Supabase.
5. **Decommission:** Shut down Hostinger VPS after 2-week validation period.

**Data migration:** Use Supabase CLI + pg_dump/pg_restore. Schema preserved — same PostgreSQL. Add RLS policies on top.

---

## External Dependencies

| Dependency | Status | Used In |
|-----------|--------|---------|
| JSONCargo API | Integrated (v1) | Container tracking |
| Anthropic Claude API | Integrated (v1) | Document classification |
| SendGrid | Configured (v1) | Email notifications |
| PropelAuth | New (v2) | Auth + organizations |
| Supabase | New (v2) | Database + Realtime + Storage |
| Vercel | New (v2) | Frontend hosting |
| Railway | New (v2) | Backend hosting |
| Sentry | New (v2) | Monitoring |
| Stripe | Planned (v2 Phase 4) | Billing |

---

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) — AI execution rules and project context
- [COMPLIANCE_MATRIX.md](./COMPLIANCE_MATRIX.md) — HS codes & required documents
- [tracehub/ROADMAP.md](../tracehub/ROADMAP.md) — v1 sprint history
- [tracehub/CHANGELOG.md](../tracehub/CHANGELOG.md) — v1 feature log
- [tracehub/docs/KNOWN_ISSUES.md](../tracehub/docs/KNOWN_ISSUES.md) — Tech debt
- [tracehub/docs/architecture/ARCHITECTURE.md](../tracehub/docs/architecture/ARCHITECTURE.md) — v1 system architecture
