# TraceHub Product Roadmap

## Phase 2: From POC to Production-Ready Platform

**Document Version:** 1.0
**Date:** January 2026
**Status:** Planning

---

## Executive Summary

TraceHub has successfully completed its MVP/POC phase (Sprints 1-5), delivering a functional container tracking and documentation compliance platform. This roadmap outlines the next 3-4 sprints (6-8 weeks) to transform the POC into a production-ready platform that can satisfy German buyer requirements, support African suppliers, and lay the groundwork for SaaS expansion.

### Current State Assessment

**Completed Features (Sprints 1-5):**
- Backend foundation with FastAPI, PostgreSQL, Docker
- Document upload, validation, and workflow engine
- Role-based access control (RBAC) with 5 user roles
- In-app notification system
- EUDR compliance module with risk assessment
- Analytics dashboard with metrics
- Audit pack generation (ZIP with PDF summary)
- JSONCargo API integration for container tracking
- Rate limiting and request middleware

**Outstanding POC Success Criteria:**
1. "Where is my container now and when will it arrive?" - Partially met (tracking exists but not fully live)
2. "Do you have all required documents and are there any compliance gaps?" - Met
3. Single-screen visibility with audit-ready bundle export - Met

---

## Strategic Priorities

### Priority Matrix (Business Value vs. Effort)

```
                          HIGH BUSINESS VALUE
                                |
    +-----------+---------------+---------------+-----------+
    |           |               |               |           |
    |  QUICK    |   DO FIRST    |   DO FIRST    |  MAJOR    |
    |  WINS     |   (Sprint 6)  |   (Sprint 7)  |  PROJECTS |
    |           |               |               |           |
    |  Mobile   |  Live Vizion  |    Email      |   Multi-  |
    |  Respons. |  Tracking     |    Notifs     |   tenant  |
    |           |               |               |           |
LOW |  Audit    |  Enhanced     |    AI Doc     |   Full    | HIGH
EFFORT          |  Pack PDF     |    Validate   |   Platform| EFFORT
    |           |               |               |           |
    |           |               |               |           |
    |  CI/CD    |   Buyer       |   Supplier    |   Mobile  |
    |  Setup    |   Portal      |   Portal      |   App     |
    |           |               |               |           |
    +-----------+---------------+---------------+-----------+
                                |
                          LOW BUSINESS VALUE
```

---

## Feature Backlog (MoSCoW Prioritization)

### MUST HAVE (Sprint 6-7)

| ID | Feature | Description | Business Value | Effort | Sprint |
|----|---------|-------------|----------------|--------|--------|
| M1 | **Enhanced Container Tracking** | Enhance JSONCargo integration with real-time webhook-based tracking. Add dual-provider support for redundancy. | Very High | Medium | 6 |
| M2 | **Email Notifications** | Send critical notifications via email (shipment departed, arrived, documents missing, compliance alerts). | High | Medium | 6 |
| M3 | **Mobile Responsive UI** | Ensure frontend works well on tablets and phones for field suppliers and traveling buyers. | High | Low | 6 |
| M4 | **Buyer Dashboard View** | Simplified read-only view for German buyers showing shipments, ETA, and document completeness at a glance. | High | Medium | 7 |
| M5 | **Supplier Document Checklist** | Clear view for suppliers of what documents are missing/pending per shipment with upload CTAs. | High | Medium | 7 |
| M6 | **Enhanced Audit Pack PDF** | Add EUDR compliance section, origin data, and digital signature placeholder to audit pack. | Medium | Low | 7 |

### SHOULD HAVE (Sprint 7-8)

| ID | Feature | Description | Business Value | Effort | Sprint |
|----|---------|-------------|----------------|--------|--------|
| S1 | **AI Document Validation (Phase 1)** | LLM-powered validation to check document completeness, extract key fields, detect discrepancies. | High | High | 8 |
| S2 | **Document OCR & Extraction** | Extract text/data from uploaded PDFs using OCR for auto-filling metadata fields. | High | High | 8 |
| S3 | **Shipment Summary Generator** | AI-generated human-readable summary for buyers (e.g., "Shipment complete, ETA Feb 12, no compliance flags"). | Medium | Medium | 8 |
| S4 | **Bulk Document Upload** | Allow suppliers to upload multiple documents at once with auto-classification. | Medium | Medium | 8 |
| S5 | **Document Version Control** | Track document revisions, maintain history, allow rollback. | Medium | Medium | 8 |

### COULD HAVE (Sprint 9+)

| ID | Feature | Description | Business Value | Effort | Sprint |
|----|---------|-------------|----------------|--------|--------|
| C1 | **Multi-tenant Architecture** | Isolate data by organization, support multiple exporters on shared infrastructure. | High (future) | Very High | 9+ |
| C2 | **White-label Branding** | Allow tenant-specific logos, colors, and domain customization. | Medium | Medium | 9+ |
| C3 | **Native Mobile App** | iOS/Android app for offline document capture and push notifications. | Medium | Very High | 10+ |
| C4 | **Third-party Integrations** | Integrate with customs systems, banking (LC), and insurance platforms. | High | Very High | 10+ |
| C5 | **Advanced Analytics & Reporting** | Historical trend analysis, predictive ETA, compliance scoring over time. | Medium | High | 9+ |

### WON'T HAVE (This Phase)

| ID | Feature | Reason |
|----|---------|--------|
| W1 | Blockchain traceability | Over-engineered for current scale; revisit post-SaaS |
| W2 | Full ERP integration | Requires customer-specific work; defer to enterprise tier |
| W3 | Customs pre-clearance automation | Complex regulatory landscape; future roadmap |
| W4 | Real-time chat support | In-app notifications sufficient for POC/MVP |

---

## Sprint Themes & Goals

### Sprint 6: Live Tracking & Communication (2 weeks)
**Theme:** "Real-time Visibility"

**Goal:** Buyers can answer "Where is my container?" with live data, and all stakeholders receive proactive email alerts for critical events.

**Features:**
- M1: Live Container Tracking (Vizion API integration)
- M2: Email Notifications (SMTP/SendGrid integration)
- M3: Mobile Responsive UI
- CI/CD pipeline setup (GitHub Actions)

**Success Metrics:**
| Metric | Target |
|--------|--------|
| Container tracking latency | < 15 min from carrier event |
| Email delivery rate | > 95% |
| Mobile usability score (manual test) | Pass all critical flows |
| Deployment frequency | 2+ per sprint |

**Dependencies:**
- Vizion API credentials and contract
- SendGrid/SMTP account setup
- Domain verification for email

**Risks:**
| Risk | Impact | Mitigation |
|------|--------|------------|
| Tracking API reliability | Medium | Dual-provider architecture with JSONCargo primary |
| Email deliverability issues | Medium | Use established ESP (SendGrid); implement SPF/DKIM |
| Mobile layout breaks | Low | Test early with Tailwind responsive utilities |

**Resource Needs:**
- 1 Full-stack developer (primary)
- 0.5 DevOps engineer (CI/CD)
- JSONCargo API access + SendGrid account

---

### Sprint 7: Stakeholder Portals (2 weeks)
**Theme:** "Role-Optimized Experience"

**Goal:** Buyers and suppliers have dedicated views tailored to their needs, reducing cognitive load and improving task completion.

**Features:**
- M4: Buyer Dashboard View
- M5: Supplier Document Checklist
- M6: Enhanced Audit Pack PDF
- Improved onboarding flow for new users

**Success Metrics:**
| Metric | Target |
|--------|--------|
| Buyer time-to-answer (usability test) | < 30 seconds |
| Supplier document upload completion rate | > 90% |
| Audit pack downloads per shipment | Track baseline |
| User satisfaction (feedback survey) | > 4/5 |

**Dependencies:**
- Sprint 6 features complete
- Feedback from pilot buyers (WITATRADE)

**Risks:**
| Risk | Impact | Mitigation |
|------|--------|------------|
| Feature scope creep | Medium | Strict MoSCoW adherence; time-box design |
| Buyer requirements unclear | Medium | Early stakeholder review at Sprint 6 end |
| PDF generation performance | Low | Async generation with download link |

**Resource Needs:**
- 1 Full-stack developer
- 0.5 UX designer (wireframes/review)
- Pilot buyer for UAT

---

### Sprint 8: AI-Augmented Workflows (2 weeks)
**Theme:** "Intelligent Automation"

**Goal:** Reduce manual document review effort by 50% through AI-powered validation and summary generation.

**Features:**
- S1: AI Document Validation (Phase 1)
- S2: Document OCR & Extraction (optional, if time)
- S3: Shipment Summary Generator
- S4: Bulk Document Upload

**Success Metrics:**
| Metric | Target |
|--------|--------|
| AI validation accuracy (precision) | > 85% |
| Time saved per document review | > 40% |
| Summary generation latency | < 5 seconds |
| AI-flagged issues caught (recall) | > 70% |

**Dependencies:**
- OpenAI/Claude API access
- OCR service (AWS Textract or Tesseract)
- Sprint 7 document workflow stable

**Risks:**
| Risk | Impact | Mitigation |
|------|--------|------------|
| AI hallucinations/errors | High | Human-in-the-loop for all AI outputs; confidence scores |
| LLM API costs | Medium | Batch processing; cache common validations |
| OCR accuracy on poor scans | Medium | Provide upload guidance; reject unreadable files |

**Resource Needs:**
- 1 ML/AI-focused developer
- 1 Full-stack developer
- OpenAI API budget ($200-500/month estimate)
- OCR service budget

---

### Sprint 9: Production Hardening & SaaS Prep (2 weeks)
**Theme:** "Scale & Stability"

**Goal:** Platform is production-ready for pilot customers and architecturally prepared for multi-tenancy.

**Features:**
- C1: Multi-tenant data model (schema per tenant or tenant_id column)
- S5: Document Version Control
- Database backup automation
- Performance optimization (query tuning, caching)
- Security audit and penetration testing
- SLA monitoring and alerting

**Success Metrics:**
| Metric | Target |
|--------|--------|
| P99 API latency | < 500ms |
| Uptime (during pilot) | > 99.5% |
| Security vulnerabilities (critical) | 0 |
| Data isolation test (multi-tenant) | 100% pass |

**Dependencies:**
- Infrastructure budget for prod environment
- Security consultant (optional)
- Pilot customer commitment

**Risks:**
| Risk | Impact | Mitigation |
|------|--------|------------|
| Multi-tenant complexity | High | Start with tenant_id column; defer full isolation |
| Performance bottlenecks | Medium | Load testing before launch |
| Security gaps | Critical | Engage security review; OWASP checklist |

**Resource Needs:**
- 1 Senior backend developer
- 0.5 DevOps/SRE engineer
- Security consultant (1-2 days)
- AWS/cloud budget increase

---

## Technical Architecture Decisions

### Sprint 6 Architecture Updates

```
                    +------------------+
                    |   German Buyer   |
                    |   (Browser/Mobile)|
                    +--------+---------+
                             |
                    +--------v---------+
                    |    Cloudflare    |
                    |   (CDN/WAF)      |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v----+  +------v------+ +-----v------+
     |   React     |  |   FastAPI   | |  Webhook   |
     |   Frontend  |  |   Backend   | |  Handler   |
     +--------+----+  +------+------+ +-----+------+
              |              |              |
              +------+-------+------+-------+
                     |              |
              +------v------+ +-----v------+
              | PostgreSQL  | |   Redis    |
              |  (Primary)  | |  (Cache)   |
              +-------------+ +------------+
                     |
              +------v------+
              |  JSONCargo  |     +------------+
              |  Webhooks   |<----| JSONCargo  |
              +-------------+     +------------+
                                       |
              +-------------+     +----v-------+
              |  SendGrid   |<----| Email Svc  |
              +-------------+     +------------+
```

### Data Model Extensions

**Sprint 6: Add to existing models**
```python
# New: Email notification preferences
class UserNotificationPreferences(Base):
    user_id = Column(UUID, ForeignKey("users.id"))
    email_enabled = Column(Boolean, default=True)
    email_on_shipment_departed = Column(Boolean, default=True)
    email_on_shipment_arrived = Column(Boolean, default=True)
    email_on_document_rejected = Column(Boolean, default=True)
    email_on_compliance_alert = Column(Boolean, default=True)

# New: Tracking subscription status
class TrackingSubscription(Base):
    shipment_id = Column(UUID, ForeignKey("shipments.id"))
    provider = Column(String)  # "vizion", "jsoncargo"
    subscription_id = Column(String)  # Provider's reference
    status = Column(String)  # "active", "inactive", "error"
    last_event_at = Column(DateTime)
```

**Sprint 9: Multi-tenant support**
```python
# Add to all models
class TenantMixin:
    tenant_id = Column(UUID, ForeignKey("tenants.id"), index=True)

class Tenant(Base):
    id = Column(UUID, primary_key=True)
    name = Column(String)
    slug = Column(String, unique=True)  # e.g., "vibotaj", "acme-exports"
    settings = Column(JSON)  # branding, features, limits
    subscription_tier = Column(String)  # "starter", "professional", "enterprise"
    created_at = Column(DateTime)
```

---

## Resource & Budget Summary

### Team Allocation (per sprint)

| Role | Sprint 6 | Sprint 7 | Sprint 8 | Sprint 9 |
|------|----------|----------|----------|----------|
| Full-stack Dev | 1.0 FTE | 1.0 FTE | 1.5 FTE | 1.0 FTE |
| DevOps/SRE | 0.5 FTE | 0.25 FTE | 0.25 FTE | 0.5 FTE |
| UX Designer | 0.25 FTE | 0.5 FTE | 0.25 FTE | 0.25 FTE |
| ML Engineer | - | - | 0.5 FTE | - |
| Security | - | - | - | 0.25 FTE |

### External Costs (Monthly Estimates)

| Service | Sprint 6 | Sprint 7 | Sprint 8 | Sprint 9 |
|---------|----------|----------|----------|----------|
| JSONCargo API | $200 | $200 | $200 | $200 |
| SendGrid | $20 | $20 | $20 | $20 |
| OpenAI API | - | - | $300 | $200 |
| AWS Textract | - | - | $100 | $100 |
| AWS (infra) | $150 | $150 | $200 | $300 |
| **Total** | **$370** | **$370** | **$820** | **$820** |

---

## Success Criteria & KPIs

### Phase 2 Exit Criteria

1. **Buyer Satisfaction:** Pilot buyer (WITATRADE) can track all active shipments and download audit packs without support requests.

2. **Supplier Adoption:** TEMIRA can independently upload all required documents with < 5% rejection rate.

3. **System Reliability:** 99.5% uptime over 4-week pilot period.

4. **Compliance Coverage:** 100% of Germany-bound shipments have EUDR compliance status visible.

5. **Audit Readiness:** Generated audit packs contain all required documents, origin data, and tracking history.

### Key Performance Indicators

| KPI | Current | Sprint 6 Target | Sprint 9 Target |
|-----|---------|-----------------|-----------------|
| Container tracking delay | N/A | < 15 min | < 5 min |
| Document upload to validation | Manual | < 2 hours | < 30 min (AI-assisted) |
| Buyer query resolution time | N/A | < 30 sec (self-service) | < 15 sec |
| Mobile usability | Not tested | Functional | Optimized |
| Audit pack generation time | ~5 sec | ~3 sec | ~2 sec |
| Email notification delivery | N/A | > 95% | > 99% |

---

## Risks & Mitigations

### Program-Level Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| Tracking API changes | Medium | Medium | Modular tracking service architecture |
| AI features underperform | Medium | Medium | Human oversight; gradual rollout; feedback loop |
| Buyer adoption resistance | Low | High | Early engagement; training; feedback incorporation |
| Resource constraints | Medium | Medium | Prioritize MUST-HAVE; defer COULD-HAVE |
| Scope creep | High | Medium | Strict MoSCoW; sprint retrospectives |
| Data migration issues | Low | Medium | Schema versioning; rollback procedures |

### Technical Debt Management

| Area | Current State | Target (Sprint 9) | Action |
|------|---------------|-------------------|--------|
| Test coverage | < 30% | > 70% | Add tests with each feature |
| API documentation | OpenAPI basic | Full examples | Enhance Swagger docs |
| Error handling | Inconsistent | Standardized | Error handling middleware |
| Logging | Basic | Structured (JSON) | Implement structured logging |
| Monitoring | Health checks | Full APM | Add Sentry/Datadog |

---

## Appendix

### A. Competitive Landscape

| Competitor | Strengths | Weaknesses | TraceHub Differentiation |
|------------|-----------|------------|--------------------------|
| ShipsGo | Easy tracking | No document mgmt | Full doc + tracking |
| CargoSmart | Enterprise-grade | Complex, expensive | SME-focused, affordable |
| project44 | Real-time visibility | No compliance | EUDR-first compliance |
| Flexport | End-to-end | Lock-in, US-centric | Africa-Europe focus |

### B. User Personas

**Hans (German Buyer - WITATRADE)**
- Needs: Real-time ETA, document completeness, audit trail
- Pain: "I spend hours chasing suppliers for documents"
- Goal: Self-service visibility, reduce email volume

**Adaeze (Nigerian Supplier - TEMIRA)**
- Needs: Clear document requirements, upload status, rejection feedback
- Pain: "I don't know which documents are still missing"
- Goal: Single checklist view, mobile-friendly upload

**Chidi (VIBOTAJ Compliance Officer)**
- Needs: Validation queue, EUDR compliance status, alerts
- Pain: "Manual checking is error-prone and slow"
- Goal: AI-assisted validation, automated flags

### C. Integration Specifications

**JSONCargo API Integration (Active)**
```
Endpoints:
- POST /api/tracking/subscribe/{shipment_id} - Start tracking
- POST /api/webhooks/jsoncargo - Receive events
- GET /api/shipments/{id}/events - Container event history

Event Types:
- container_loaded
- vessel_departed
- vessel_arrived
- container_discharged
- container_delivered

Webhook Payload:
{
  "event_id": "evt_xxx",
  "container_number": "MRSU3452572",
  "event_type": "vessel_departed",
  "event_datetime": "2026-01-15T08:30:00Z",
  "location": {
    "port_code": "NGAPP",
    "port_name": "Apapa, Lagos"
  },
  "vessel": {
    "name": "RHINE MAERSK",
    "imo": "9778819"
  },
  "eta": "2026-02-12T14:00:00Z"
}
```

**Email Notification Templates (Sprint 6)**
- Shipment Departed
- Shipment Arrived
- ETA Changed
- Document Rejected
- Compliance Alert
- Weekly Digest (Sprint 8)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Product Strategy | Initial roadmap |

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Tech Lead | | | |
| Business Sponsor | | | |
