# TraceHub Sprint Backlog

## Detailed Task Breakdown for Sprints 6-9

---

## Sprint 6: Live Tracking & Communication

**Duration:** 2 weeks
**Theme:** Real-time Visibility
**Sprint Goal:** Buyers can track containers in real-time and receive proactive email notifications.

### User Stories & Tasks

---

#### STORY 6.1: Enhanced Container Tracking
**Priority:** MUST HAVE
**Story Points:** 13
**Assignee:** Backend Developer

> As a buyer, I want to see real-time container location updates so that I can plan my operations around accurate arrival times.

**Acceptance Criteria:**
- [ ] Container events appear within 15 minutes of carrier update
- [ ] ETA updates reflect on shipment detail page
- [ ] Historical tracking events are preserved
- [ ] Dual-provider support for redundancy

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T6.1.1: Review JSONCargo API capabilities and rate limits | 2h | TODO |
| T6.1.2: Create `TrackingProvider` abstract interface | 2h | TODO |
| T6.1.3: Refactor existing JSONCargo client to provider pattern | 4h | TODO |
| T6.1.4: Enhance webhook endpoint `/api/webhooks/jsoncargo` | 3h | TODO |
| T6.1.5: Add `TrackingSubscription` model for tracking state | 2h | TODO |
| T6.1.6: Implement subscription management (subscribe/unsubscribe) | 3h | TODO |
| T6.1.7: Improve event mapping to `ContainerEvent` model | 2h | TODO |
| T6.1.8: Update shipment ETA automatically from tracking events | 2h | TODO |
| T6.1.9: Add provider failover logic for redundancy | 3h | TODO |
| T6.1.10: Write integration tests with mock responses | 3h | TODO |
| T6.1.11: Update tracking router to use provider interface | 2h | TODO |
| T6.1.12: Document tracking API configuration | 1h | TODO |

**Technical Notes:**
- Use adapter pattern for provider abstraction
- Store subscription_id in `TrackingSubscription` table
- Webhook security: verify JSONCargo signature header

---

#### STORY 6.2: Email Notifications
**Priority:** MUST HAVE
**Story Points:** 8
**Assignee:** Backend Developer

> As a stakeholder, I want to receive email notifications for critical shipment events so that I stay informed without constantly checking the app.

**Acceptance Criteria:**
- [ ] Users receive emails for: shipment departed, arrived, ETA changed, document rejected, compliance alert
- [ ] Users can opt out of specific notification types
- [ ] Emails include shipment reference and direct link to app
- [ ] Email delivery rate > 95%

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T6.2.1: Set up SendGrid account and API key | 1h | TODO |
| T6.2.2: Create `EmailService` class with SendGrid integration | 3h | TODO |
| T6.2.3: Design HTML email templates (5 notification types) | 4h | TODO |
| T6.2.4: Create `UserNotificationPreferences` model | 2h | TODO |
| T6.2.5: Add preferences API endpoints (GET/PATCH) | 2h | TODO |
| T6.2.6: Integrate email sending with existing notification service | 3h | TODO |
| T6.2.7: Add email sending to shipment status change handlers | 2h | TODO |
| T6.2.8: Implement async email queue (background task) | 3h | TODO |
| T6.2.9: Add email delivery logging and tracking | 2h | TODO |
| T6.2.10: Configure SPF/DKIM for domain verification | 1h | TODO |
| T6.2.11: Write email template tests | 2h | TODO |

**Technical Notes:**
- Use FastAPI BackgroundTasks for async sending
- Template engine: Jinja2
- Consider email queuing with Redis for reliability

---

#### STORY 6.3: Mobile Responsive UI
**Priority:** MUST HAVE
**Story Points:** 5
**Assignee:** Frontend Developer

> As a supplier in the field, I want to access TraceHub on my phone so that I can check shipment status and upload documents from anywhere.

**Acceptance Criteria:**
- [ ] All pages render correctly on mobile (375px width)
- [ ] Navigation works via hamburger menu on small screens
- [ ] Document upload works from mobile browser
- [ ] Tables are horizontally scrollable or stacked on mobile

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T6.3.1: Audit current pages for mobile breakpoints | 2h | TODO |
| T6.3.2: Add responsive navigation (hamburger menu) | 3h | TODO |
| T6.3.3: Make Dashboard shipment cards stack on mobile | 2h | TODO |
| T6.3.4: Make Shipment detail page responsive | 3h | TODO |
| T6.3.5: Make document tables scrollable or card-based | 2h | TODO |
| T6.3.6: Test document upload on iOS Safari / Android Chrome | 2h | TODO |
| T6.3.7: Fix any touch interaction issues (buttons, modals) | 2h | TODO |
| T6.3.8: Test Analytics page charts on mobile | 1h | TODO |

**Technical Notes:**
- Use Tailwind `sm:`, `md:`, `lg:` prefixes
- Test on actual devices, not just browser DevTools
- Consider using `react-responsive` for complex conditionals

---

#### STORY 6.4: CI/CD Pipeline Setup
**Priority:** SHOULD HAVE
**Story Points:** 5
**Assignee:** DevOps

> As a developer, I want automated tests and deployments so that we can ship faster with confidence.

**Acceptance Criteria:**
- [ ] PRs run tests and linting automatically
- [ ] Merge to main triggers deployment to staging
- [ ] Deployment notifications in Slack/Teams
- [ ] Rollback procedure documented

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T6.4.1: Create GitHub Actions workflow for backend tests | 2h | TODO |
| T6.4.2: Create GitHub Actions workflow for frontend tests | 2h | TODO |
| T6.4.3: Add ESLint/Prettier checks to frontend workflow | 1h | TODO |
| T6.4.4: Add Python linting (ruff/black) to backend workflow | 1h | TODO |
| T6.4.5: Create deployment workflow (Docker build + push) | 3h | TODO |
| T6.4.6: Set up staging environment on cloud provider | 4h | TODO |
| T6.4.7: Configure environment secrets in GitHub | 1h | TODO |
| T6.4.8: Add deployment status badge to README | 0.5h | TODO |
| T6.4.9: Document rollback procedure | 1h | TODO |

**Technical Notes:**
- Use GitHub Actions matrix for Python 3.11/3.12
- Docker images pushed to GitHub Container Registry or ECR
- Consider using docker-compose for staging

---

### Sprint 6 Capacity Planning

| Role | Available Hours | Allocated Hours | Buffer |
|------|-----------------|-----------------|--------|
| Backend Dev | 80h | 70h | 10h |
| Frontend Dev | 80h | 25h | 55h (carry to Sprint 7) |
| DevOps | 40h | 15h | 25h |

**Total Story Points:** 31
**Velocity Target:** 30-35 points

---

## Sprint 7: Stakeholder Portals

**Duration:** 2 weeks
**Theme:** Role-Optimized Experience
**Sprint Goal:** Buyers and suppliers have tailored views for their specific needs.

### User Stories & Tasks

---

#### STORY 7.1: Buyer Dashboard View
**Priority:** MUST HAVE
**Story Points:** 8
**Assignee:** Frontend Developer

> As a German buyer, I want a simplified dashboard that shows me all my active shipments with ETAs and document status so that I can quickly assess the situation without clicking into each shipment.

**Acceptance Criteria:**
- [ ] Dashboard shows only shipments relevant to buyer
- [ ] Each card shows: reference, container, ETA, doc completion %, EUDR status
- [ ] Cards are sorted by ETA (soonest first)
- [ ] Quick filters: All, In Transit, Arrived, Needs Attention
- [ ] "Needs Attention" highlights compliance issues

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T7.1.1: Create buyer-specific dashboard component | 4h | TODO |
| T7.1.2: Design shipment summary cards (Figma/wireframe) | 2h | TODO |
| T7.1.3: Implement shipment card component | 3h | TODO |
| T7.1.4: Add filter tabs (All, In Transit, etc.) | 2h | TODO |
| T7.1.5: Add backend filter for buyer's shipments only | 2h | TODO |
| T7.1.6: Add EUDR status indicator to cards | 2h | TODO |
| T7.1.7: Add document completion progress bar | 1h | TODO |
| T7.1.8: Sort by ETA with "overdue" highlighting | 1h | TODO |
| T7.1.9: Add role-based route protection | 1h | TODO |

**Technical Notes:**
- Filter shipments by `buyer_id` matching current user's party
- Consider caching buyer dashboard data (changes less frequently)

---

#### STORY 7.2: Supplier Document Checklist
**Priority:** MUST HAVE
**Story Points:** 8
**Assignee:** Frontend Developer

> As a supplier, I want a clear checklist showing which documents I need to upload for each shipment so that I can ensure all requirements are met before shipment.

**Acceptance Criteria:**
- [ ] Supplier sees only their shipments
- [ ] Each shipment shows required vs. uploaded documents
- [ ] Missing documents have prominent upload CTAs
- [ ] Upload status shows: missing, uploaded, pending validation, approved, rejected
- [ ] Rejected documents show rejection reason

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T7.2.1: Create supplier dashboard component | 4h | TODO |
| T7.2.2: Build document checklist component | 3h | TODO |
| T7.2.3: Add status icons (missing, pending, approved, rejected) | 2h | TODO |
| T7.2.4: Integrate quick-upload button per document type | 2h | TODO |
| T7.2.5: Show rejection reason inline with rejected docs | 1h | TODO |
| T7.2.6: Add backend filter for supplier's shipments | 2h | TODO |
| T7.2.7: Add notification badge for pending validations | 1h | TODO |
| T7.2.8: Add "All Documents Complete" success state | 1h | TODO |

**Technical Notes:**
- Filter shipments by `supplier_id` matching current user's party
- Use existing document workflow status colors

---

#### STORY 7.3: Enhanced Audit Pack PDF
**Priority:** MUST HAVE
**Story Points:** 5
**Assignee:** Backend Developer

> As a compliance officer, I want audit packs to include EUDR compliance details and origin data so that the pack is sufficient for regulatory audits.

**Acceptance Criteria:**
- [ ] PDF includes EUDR compliance status section
- [ ] PDF includes origin data (geolocation, production dates)
- [ ] PDF includes risk assessment summary
- [ ] PDF has placeholder for digital signature
- [ ] PDF includes generation timestamp and user

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T7.3.1: Add EUDR compliance section to PDF template | 3h | TODO |
| T7.3.2: Add origin data section with geolocation | 2h | TODO |
| T7.3.3: Add risk assessment summary table | 2h | TODO |
| T7.3.4: Add digital signature placeholder | 1h | TODO |
| T7.3.5: Include generator info (user, timestamp) in footer | 1h | TODO |
| T7.3.6: Add EUDR report as separate PDF in ZIP | 2h | TODO |
| T7.3.7: Update tests for new PDF sections | 2h | TODO |

**Technical Notes:**
- Reuse EUDR report generation logic
- Keep PDF under 5 pages for usability

---

#### STORY 7.4: User Onboarding Flow
**Priority:** SHOULD HAVE
**Story Points:** 5
**Assignee:** Frontend Developer

> As a new user, I want a guided introduction to TraceHub so that I can quickly understand how to complete my tasks.

**Acceptance Criteria:**
- [ ] First-time users see welcome modal with role-specific tips
- [ ] Buyers see guide to tracking and document status
- [ ] Suppliers see guide to document upload workflow
- [ ] User can dismiss and access again from help menu

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T7.4.1: Create onboarding modal component | 2h | TODO |
| T7.4.2: Design onboarding content (3-4 steps) | 2h | TODO |
| T7.4.3: Add role-specific content variations | 2h | TODO |
| T7.4.4: Track first-login state in localStorage or user model | 1h | TODO |
| T7.4.5: Add "Help" link in header to re-trigger onboarding | 1h | TODO |
| T7.4.6: Test flow for each role | 1h | TODO |

**Technical Notes:**
- Use react-joyride or similar for tour functionality
- Store `has_seen_onboarding` flag

---

### Sprint 7 Capacity Planning

| Role | Available Hours | Allocated Hours | Buffer |
|------|-----------------|-----------------|--------|
| Backend Dev | 80h | 20h | 60h |
| Frontend Dev | 80h | 65h | 15h |
| UX Designer | 40h | 15h | 25h |

**Total Story Points:** 26
**Velocity Target:** 25-30 points

---

## Sprint 8: AI-Augmented Workflows

**Duration:** 2 weeks
**Theme:** Intelligent Automation
**Sprint Goal:** Reduce document review time by 50% through AI-powered validation.

### User Stories & Tasks

---

#### STORY 8.1: AI Document Validation (Phase 1)
**Priority:** SHOULD HAVE
**Story Points:** 13
**Assignee:** ML Engineer + Backend Developer

> As a compliance officer, I want AI to pre-validate documents and flag potential issues so that I can focus on edge cases rather than routine checks.

**Acceptance Criteria:**
- [ ] AI validates document completeness against requirements
- [ ] AI extracts key fields (dates, reference numbers, quantities)
- [ ] AI flags discrepancies between documents (quantity mismatch, etc.)
- [ ] Validation results show confidence scores
- [ ] Human review required for all AI decisions

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T8.1.1: Design AI validation prompt templates | 4h | TODO |
| T8.1.2: Create `AIValidationService` class | 4h | TODO |
| T8.1.3: Integrate OpenAI/Claude API for document analysis | 4h | TODO |
| T8.1.4: Implement field extraction logic | 4h | TODO |
| T8.1.5: Create cross-document validation rules | 4h | TODO |
| T8.1.6: Add validation results to document model | 2h | TODO |
| T8.1.7: Create validation results UI component | 3h | TODO |
| T8.1.8: Add confidence score display | 2h | TODO |
| T8.1.9: Implement human-in-the-loop approval flow | 3h | TODO |
| T8.1.10: Add AI validation to document workflow | 3h | TODO |
| T8.1.11: Create evaluation dataset for testing | 4h | TODO |
| T8.1.12: Measure and log accuracy metrics | 2h | TODO |

**Technical Notes:**
- Use Claude/GPT-4 with structured output (JSON mode)
- Cache common validations to reduce API costs
- Log all AI decisions for audit trail

---

#### STORY 8.2: Shipment Summary Generator
**Priority:** SHOULD HAVE
**Story Points:** 5
**Assignee:** ML Engineer

> As a buyer, I want an AI-generated plain-English summary of each shipment so that I can quickly understand the status without reading multiple data points.

**Acceptance Criteria:**
- [ ] Summary appears at top of shipment detail page
- [ ] Summary includes: current status, ETA, document status, any alerts
- [ ] Summary is regenerated when key data changes
- [ ] Generation takes < 5 seconds

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T8.2.1: Design summary prompt template | 2h | TODO |
| T8.2.2: Create `SummaryGeneratorService` | 3h | TODO |
| T8.2.3: Add summary endpoint to shipment API | 2h | TODO |
| T8.2.4: Create summary display component | 2h | TODO |
| T8.2.5: Implement caching (regenerate on data change) | 2h | TODO |
| T8.2.6: Add loading state and error handling | 1h | TODO |

**Technical Notes:**
- Use GPT-3.5 for cost efficiency (summaries are simple)
- Cache in Redis with shipment hash as key

---

#### STORY 8.3: Bulk Document Upload
**Priority:** SHOULD HAVE
**Story Points:** 5
**Assignee:** Full-stack Developer

> As a supplier, I want to upload multiple documents at once so that I can save time when preparing a shipment.

**Acceptance Criteria:**
- [ ] Drag-and-drop zone accepts multiple files
- [ ] User can assign document type to each file
- [ ] AI suggests document type based on filename/content (optional)
- [ ] Upload progress shows per-file status
- [ ] All files are validated before upload starts

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T8.3.1: Create multi-file dropzone component | 3h | TODO |
| T8.3.2: Add file list with type assignment dropdowns | 2h | TODO |
| T8.3.3: Implement AI document type suggestion | 3h | TODO |
| T8.3.4: Add per-file upload progress tracking | 2h | TODO |
| T8.3.5: Create bulk upload API endpoint | 2h | TODO |
| T8.3.6: Add validation (file size, type, duplicates) | 2h | TODO |
| T8.3.7: Test with 10+ files simultaneously | 1h | TODO |

**Technical Notes:**
- Use react-dropzone for drag-and-drop
- Parallel upload with concurrency limit (3 files at a time)

---

### Sprint 8 Capacity Planning

| Role | Available Hours | Allocated Hours | Buffer |
|------|-----------------|-----------------|--------|
| ML Engineer | 80h | 55h | 25h |
| Backend Dev | 80h | 30h | 50h |
| Frontend Dev | 80h | 25h | 55h |

**Total Story Points:** 23
**Velocity Target:** 20-25 points

---

## Sprint 9: Production Hardening

**Duration:** 2 weeks
**Theme:** Scale & Stability
**Sprint Goal:** Platform is production-ready and multi-tenant capable.

### User Stories & Tasks

---

#### STORY 9.1: Multi-Tenant Data Model
**Priority:** COULD HAVE (but critical for SaaS)
**Story Points:** 13
**Assignee:** Senior Backend Developer

> As the product owner, I want data isolation between organizations so that we can onboard multiple exporters without data leakage.

**Acceptance Criteria:**
- [ ] All models include `tenant_id` column
- [ ] API queries automatically filter by tenant
- [ ] Cross-tenant data access is impossible
- [ ] Admin can manage multiple tenants
- [ ] Tenant settings control features and limits

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T9.1.1: Create `Tenant` model and migration | 2h | TODO |
| T9.1.2: Add `tenant_id` to all existing models | 3h | TODO |
| T9.1.3: Create database migration with default tenant | 2h | TODO |
| T9.1.4: Implement tenant context middleware | 4h | TODO |
| T9.1.5: Update all queries to include tenant filter | 4h | TODO |
| T9.1.6: Add tenant management API endpoints | 3h | TODO |
| T9.1.7: Create tenant onboarding workflow | 3h | TODO |
| T9.1.8: Add tenant settings (limits, features) | 2h | TODO |
| T9.1.9: Write comprehensive cross-tenant tests | 4h | TODO |
| T9.1.10: Document multi-tenant architecture | 2h | TODO |

**Technical Notes:**
- Use Row-Level Security (RLS) in PostgreSQL for extra safety
- Tenant context from JWT claims
- Consider schema-per-tenant for large customers (future)

---

#### STORY 9.2: Document Version Control
**Priority:** SHOULD HAVE
**Story Points:** 5
**Assignee:** Backend Developer

> As a compliance officer, I want to see document revision history so that I can track changes and access previous versions if needed.

**Acceptance Criteria:**
- [ ] Re-uploading a document creates a new version, not replacement
- [ ] Version history shows uploader, timestamp, status
- [ ] Previous versions are downloadable
- [ ] Current version is clearly indicated

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T9.2.1: Add version tracking to Document model | 2h | TODO |
| T9.2.2: Create DocumentVersion model for history | 2h | TODO |
| T9.2.3: Update upload logic to create versions | 2h | TODO |
| T9.2.4: Add version history API endpoint | 2h | TODO |
| T9.2.5: Create version history UI component | 3h | TODO |
| T9.2.6: Add download link per version | 1h | TODO |
| T9.2.7: Migrate existing documents to v1 | 1h | TODO |

**Technical Notes:**
- Store file paths with version suffix
- Limit versions (keep last 10) to control storage

---

#### STORY 9.3: Performance Optimization
**Priority:** MUST HAVE
**Story Points:** 8
**Assignee:** Backend Developer + DevOps

> As a user, I want the application to respond quickly so that I can complete my tasks efficiently.

**Acceptance Criteria:**
- [ ] P99 API latency < 500ms
- [ ] Dashboard load time < 2 seconds
- [ ] Document list query < 200ms
- [ ] No N+1 query issues

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T9.3.1: Add APM monitoring (Sentry/Datadog) | 3h | TODO |
| T9.3.2: Identify slow queries with query logging | 2h | TODO |
| T9.3.3: Add database indexes for common queries | 3h | TODO |
| T9.3.4: Implement eager loading to fix N+1 | 3h | TODO |
| T9.3.5: Add Redis caching for dashboard stats | 3h | TODO |
| T9.3.6: Optimize shipment list query | 2h | TODO |
| T9.3.7: Add frontend data prefetching | 2h | TODO |
| T9.3.8: Run load tests (100 concurrent users) | 3h | TODO |

**Technical Notes:**
- Use `explain analyze` to identify slow queries
- Consider read replicas for analytics queries (future)

---

#### STORY 9.4: Security Hardening
**Priority:** MUST HAVE
**Story Points:** 8
**Assignee:** Backend Developer + Security Consultant

> As a security-conscious organization, I want the platform to be secure against common attacks so that our data is protected.

**Acceptance Criteria:**
- [ ] OWASP Top 10 vulnerabilities addressed
- [ ] Security headers configured (CSP, HSTS, etc.)
- [ ] Input validation on all endpoints
- [ ] Secrets properly managed (not in code)
- [ ] Audit log captures security events

**Tasks:**

| Task | Estimate | Status |
|------|----------|--------|
| T9.4.1: Run OWASP ZAP scan and fix findings | 4h | TODO |
| T9.4.2: Add security headers middleware | 2h | TODO |
| T9.4.3: Review and harden input validation | 3h | TODO |
| T9.4.4: Implement rate limiting per endpoint | 2h | Already done |
| T9.4.5: Add brute-force protection on login | 2h | TODO |
| T9.4.6: Review secret management | 2h | TODO |
| T9.4.7: Add security events to audit log | 2h | TODO |
| T9.4.8: Create security documentation | 2h | TODO |
| T9.4.9: Conduct penetration test (external) | 8h | TODO |

**Technical Notes:**
- Use `helmet` equivalent for FastAPI
- Consider WAF (Cloudflare/AWS WAF) for additional protection

---

### Sprint 9 Capacity Planning

| Role | Available Hours | Allocated Hours | Buffer |
|------|-----------------|-----------------|--------|
| Senior Backend Dev | 80h | 65h | 15h |
| DevOps/SRE | 80h | 25h | 55h |
| Security Consultant | 16h | 16h | 0h |

**Total Story Points:** 34
**Velocity Target:** 30-35 points

---

## Definition of Done

### Feature Level
- [ ] Code reviewed and approved
- [ ] Unit tests written (>80% coverage for new code)
- [ ] Integration tests passing
- [ ] API documentation updated
- [ ] No critical/high security issues
- [ ] Performance acceptable (<500ms P99)
- [ ] Deployed to staging
- [ ] Product owner acceptance

### Sprint Level
- [ ] All committed stories complete
- [ ] No critical bugs open
- [ ] Sprint demo conducted
- [ ] Retrospective completed
- [ ] Documentation updated
- [ ] Release notes prepared

---

## Velocity Tracking

| Sprint | Planned | Completed | Velocity | Notes |
|--------|---------|-----------|----------|-------|
| 1 | 20 | 22 | 22 | Backend foundation |
| 2 | 25 | 23 | 23 | RBAC implementation |
| 3 | 25 | 26 | 26 | Frontend + notifications |
| 4 | 30 | 28 | 28 | EUDR + analytics |
| 5 | 28 | 27 | 27 | Polish + workflow |
| **Avg** | **25.6** | **25.2** | **25.2** | |
| 6 | 31 | - | - | Tracking + email |
| 7 | 26 | - | - | Portals |
| 8 | 23 | - | - | AI features |
| 9 | 34 | - | - | Production prep |

---

## Sprint Ceremonies Schedule

### Sprint 6 (Week 1-2 of January 2026)

| Ceremony | Day | Time | Duration | Attendees |
|----------|-----|------|----------|-----------|
| Sprint Planning | Mon W1 | 10:00 | 2h | Team + PO |
| Daily Standup | Daily | 09:00 | 15m | Team |
| Backlog Refinement | Wed W1 | 14:00 | 1h | Team + PO |
| Sprint Review | Fri W2 | 14:00 | 1h | Team + Stakeholders |
| Retrospective | Fri W2 | 15:30 | 1h | Team |

---

## Appendix: Story Templates

### User Story Template
```
**As a** [type of user]
**I want** [goal/desire]
**So that** [benefit/value]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Technical Notes:**
- Implementation detail 1
- Dependency or constraint

**Story Points:** X
**Priority:** MUST/SHOULD/COULD
**Assignee:** Role/Name
```

### Task Template
```
| Task ID | Description | Estimate | Status | Notes |
|---------|-------------|----------|--------|-------|
| TX.X.X | Task description | Xh | TODO/IN_PROGRESS/DONE/BLOCKED | Any blockers |
```
