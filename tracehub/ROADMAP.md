# TraceHub Roadmap

**Last Updated:** 2026-01-11
**Status:** Phase 3 - Production Stabilization

---

## Overview

TraceHub is a container tracking and documentation compliance platform for VIBOTAJ agro-exports. This roadmap tracks completed work (Sprints 1-11) and upcoming features (Sprints 12+).

---

## Completed Sprints (1-11)

| Sprint | Theme | Key Deliverables | Status |
|--------|-------|------------------|--------|
| 1 | Backend Foundation | FastAPI, PostgreSQL, Docker, document upload | ✅ Done |
| 1.5 | Tracking Integration | JSONCargo API, webhook support, event history | ✅ Done |
| 2 | Access Control | 6 user roles, RBAC, user management | ✅ Done |
| 3 | Document Workflow | Lifecycle states, validation, approval flow | ✅ Done |
| 4 | EUDR Compliance | Compliance tracking, analytics dashboard | ✅ Done |
| 5 | Historical Data | Shipment creation, logistics agent workflow | ✅ Done |
| 6 | Live Tracking | Real-time visibility, email notifications | ✅ Done |
| 7 | Stakeholder Portals | Buyer dashboard, supplier checklists | ✅ Done |
| 8 | Multi-Tenancy | Organization model, data isolation, RBAC | ✅ Done |
| 9 | Compliance Matrix | EUDR exemptions, Horn & Hoof handling | ✅ Done |
| 10 | Architecture Cleanup | Deprecate legacy schemas, Party table removal | ✅ Done |
| 11 | Schema Fixes | UUID FK constraints, buyer access control | ✅ Done |

See [CHANGELOG.md](./CHANGELOG.md) for detailed feature list.

---

## Current Sprint (12)

### Sprint 12: Final Stabilization
**Theme:** Production Hardening
**Duration:** 1-2 weeks

**Goals:**
- Standardize DateTime timezone handling across all models
- Add shipment status transition validation
- Add EUDR compliance tests

**Features:**
| Feature | Priority | Status |
|---------|----------|--------|
| DateTime timezone standardization | SHOULD | Planned |
| Shipment status state machine | SHOULD | Planned |
| EUDR compliance tests | SHOULD | Planned |

---

## Future Considerations (Sprint 13+)

| Feature | Description | Priority |
|---------|-------------|----------|
| White-label branding | Tenant-specific logos, colors, domains | Medium |
| Native mobile app | iOS/Android with offline document capture | Medium |
| Third-party integrations | Customs, banking (LC), insurance | High |
| Advanced analytics | Predictive ETA, compliance scoring trends | Medium |
| Blockchain traceability | Deferred - revisit post-SaaS | Low |

---

## Priority Framework (MoSCoW)

- **MUST HAVE:** Required for next release
- **SHOULD HAVE:** Important but not blocking
- **COULD HAVE:** Nice to have if time permits
- **WON'T HAVE:** Explicitly deferred

---

## External Dependencies

| Dependency | Sprint | Status |
|------------|--------|--------|
| JSONCargo API | Active | ✅ Integrated |
| SendGrid account | Sprint 6 | ✅ Configured |
| Anthropic Claude API | Sprint 7+ | ✅ Integrated |
| PostgreSQL | Active | ✅ Running |

---

## How to Resume Work

To continue development from where we left off:

1. Check current sprint status in this file
2. Review [CHANGELOG.md](./CHANGELOG.md) for completed features
3. See [docs/KNOWN_ISSUES.md](./docs/KNOWN_ISSUES.md) for remaining tech debt
4. Check git log for recent changes: `git log --oneline -20`

**Current State:** Sprints 1-11 complete, Sprint 12 in progress.

---

## Related Documentation

- [CHANGELOG.md](./CHANGELOG.md) - Completed features by version
- [docs/KNOWN_ISSUES.md](./docs/KNOWN_ISSUES.md) - Known issues and tech debt
- [docs/architecture/ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md) - System architecture
- [README.md](./README.md) - Quick start and API reference
