# TraceHub Roadmap

**Last Updated:** 2026-01-03
**Status:** Phase 2 Planning

---

## Overview

TraceHub is a container tracking and documentation compliance platform for VIBOTAJ agro-exports. This roadmap outlines completed work (Sprints 1-5) and upcoming features (Sprints 6-9).

---

## Completed Sprints (1-5)

| Sprint | Theme | Key Deliverables | Status |
|--------|-------|------------------|--------|
| 1 | Backend Foundation | FastAPI, PostgreSQL, Docker, document upload | Done |
| 1.5 | Tracking Integration | JSONCargo API, webhook support, event history | Done |
| 2 | Access Control | 6 user roles, RBAC, user management | Done |
| 3 | Document Workflow | Lifecycle states, validation, approval flow | Done |
| 4 | EUDR Compliance | Compliance tracking, analytics dashboard | Done |
| 5 | Historical Data | Shipment creation, logistics agent workflow | Done |

See [CHANGELOG.md](./CHANGELOG.md) for detailed feature list.

---

## Upcoming Sprints (6-9)

### Sprint 6: Live Tracking & Communication
**Theme:** Real-time Visibility
**Duration:** 2 weeks

**Goals:**
- Buyers can answer "Where is my container?" with live data
- Stakeholders receive proactive email alerts

**Features:**
| Feature | Priority | Status |
|---------|----------|--------|
| Enhanced container tracking (dual-provider) | MUST | Planned |
| Email notifications (SendGrid) | MUST | Planned |
| Mobile responsive UI | MUST | Planned |
| CI/CD pipeline (GitHub Actions) | SHOULD | Planned |

**Success Metrics:**
- Container tracking latency < 15 min
- Email delivery rate > 95%
- Mobile usability pass

---

### Sprint 7: Stakeholder Portals
**Theme:** Role-Optimized Experience
**Duration:** 2 weeks

**Goals:**
- Buyers have simplified dashboard showing ETAs and document status
- Suppliers have clear document checklists with upload CTAs

**Features:**
| Feature | Priority | Status |
|---------|----------|--------|
| Buyer dashboard view | MUST | Planned |
| Supplier document checklist | MUST | Planned |
| Enhanced audit pack PDF (EUDR section) | MUST | Planned |
| User onboarding flow | SHOULD | Planned |

**Success Metrics:**
- Buyer time-to-answer < 30 seconds
- Supplier upload completion > 90%

---

### Sprint 8: AI-Augmented Workflows
**Theme:** Intelligent Automation
**Duration:** 2 weeks

**Goals:**
- Reduce document review time by 50% through AI validation
- Auto-generate shipment summaries for buyers

**Features:**
| Feature | Priority | Status |
|---------|----------|--------|
| AI document validation (LLM) | SHOULD | Planned |
| Shipment summary generator | SHOULD | Planned |
| Bulk document upload | SHOULD | Planned |
| Document OCR & extraction | COULD | Planned |

**Success Metrics:**
- AI validation accuracy > 85%
- Time saved per review > 40%

---

### Sprint 9: Production Hardening & SaaS Prep
**Theme:** Scale & Stability
**Duration:** 2 weeks

**Goals:**
- Platform is production-ready for pilot customers
- Architecture supports multi-tenancy for future SaaS

**Features:**
| Feature | Priority | Status |
|---------|----------|--------|
| Multi-tenant data model | COULD | Planned |
| Document version control | SHOULD | Planned |
| Performance optimization | MUST | Planned |
| Security hardening | MUST | Planned |

**Success Metrics:**
- P99 API latency < 500ms
- Uptime > 99.5%
- Zero critical security vulnerabilities

---

## Future Considerations (Sprint 10+)

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
| JSONCargo API | Active | Integrated |
| SendGrid account | Sprint 6 | Needed |
| OpenAI/Claude API | Sprint 8 | Needed |
| Security consultant | Sprint 9 | Needed |

---

## How to Resume Work

To continue development from where we left off:

1. Check current sprint status in this file
2. Review [CHANGELOG.md](./CHANGELOG.md) for completed features
3. See [SPRINT_BACKLOG.md](./SPRINT_BACKLOG.md) for detailed task breakdown
4. Check git log for recent changes: `git log --oneline -20`

**Current State:** Sprints 1-5 complete, Sprint 6 ready to start.

---

## Related Documentation

- [CHANGELOG.md](./CHANGELOG.md) - Completed features by version
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [README.md](./README.md) - Quick start and API reference
- [SPRINT_BACKLOG.md](./SPRINT_BACKLOG.md) - Detailed task breakdown
- [PRODUCT_ROADMAP.md](./PRODUCT_ROADMAP.md) - Full product strategy (detailed)
