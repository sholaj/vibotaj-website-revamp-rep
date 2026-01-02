# Phase 2: Customer Portal Development

**Start Date:** December 30, 2025  
**Target Duration:** 8-12 weeks  
**Previous Phase:** ✅ Phase 1 Complete (Infrastructure)

---

## 📋 Phase 2 Overview

Phase 2 focuses on building the **Customer Portal** - a React-based frontend that integrates with the existing WordPress/WooCommerce backend. This will transform VIBOTAJ from a static website into an interactive platform where customers can track shipments, manage documents, and request quotes.

---

## 🎯 Phase 2 Objectives

| # | Objective | Business Value |
|---|-----------|----------------|
| 1 | Customer Authentication | Secure access to personal data |
| 2 | Order/Shipment Tracking | Real-time visibility, reduced support calls |
| 3 | Document Management | Centralized access to shipping docs |
| 4 | Quote Request System | Automated lead capture |
| 5 | Email Notifications | Proactive customer communication |

---

## 🏗️ Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2 ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   FRONTEND (New)              BACKEND (Existing WordPress)      │
│   ┌──────────────────┐        ┌──────────────────────────────┐ │
│   │  React Portal    │◄──────►│  WordPress REST API          │ │
│   │  ├─ Auth         │  JWT   │  ├─ WooCommerce              │ │
│   │  ├─ Dashboard    │        │  ├─ Custom Endpoints         │ │
│   │  ├─ Tracking     │        │  └─ Maersk Integration       │ │
│   │  ├─ Documents    │        └──────────────────────────────┘ │
│   │  └─ Quotes       │                                         │
│   └──────────────────┘        ┌──────────────────────────────┐ │
│           │                   │  External APIs               │ │
│           └──────────────────►│  ├─ Maersk Track & Trace     │ │
│                               │  ├─ SendGrid (Email)         │ │
│                               │  └─ S3/Cloudinary (Storage)  │ │
│                               └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Deliverables Breakdown

### Sprint 1: Foundation (Weeks 1-2)

#### 1.1 Project Setup
- [ ] Initialize React 18 + TypeScript project
- [ ] Configure Tailwind CSS
- [ ] Set up project structure
- [ ] Configure ESLint + Prettier
- [ ] Create development environment

#### 1.2 WordPress API Preparation
- [ ] Create custom plugin `vibotaj-core`
- [ ] Set up JWT authentication (wp-jwt-auth)
- [ ] Create custom REST endpoints
- [ ] Configure CORS for React frontend

**Deliverables:**
```
src/
├── frontend/                    # React App
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/           # API calls
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
└── backend/                     # WordPress Plugin
    └── vibotaj-core/
        ├── includes/
        │   ├── class-api.php
        │   ├── class-auth.php
        │   └── class-tracking.php
        └── vibotaj-core.php
```

---

### Sprint 2: Authentication (Weeks 3-4)

#### 2.1 User Registration & Login
- [ ] Registration form with email verification
- [ ] Login form with JWT token handling
- [ ] Password reset flow
- [ ] Remember me functionality
- [ ] Session management

#### 2.2 User Profile
- [ ] Company information
- [ ] Contact details
- [ ] Shipping addresses
- [ ] Communication preferences

**API Endpoints:**
```
POST /wp-json/vibotaj/v1/auth/register    → Create account
POST /wp-json/vibotaj/v1/auth/login       → Get JWT token
POST /wp-json/vibotaj/v1/auth/refresh     → Refresh token
POST /wp-json/vibotaj/v1/auth/forgot      → Password reset
GET  /wp-json/vibotaj/v1/profile          → Get user profile
PUT  /wp-json/vibotaj/v1/profile          → Update profile
```

---

### Sprint 3: Order Tracking (Weeks 5-6)

#### 3.1 Dashboard
- [ ] Overview of active orders
- [ ] Recent shipments
- [ ] Quick actions
- [ ] Notification center

#### 3.2 Maersk API Integration
- [ ] Container tracking by BL number
- [ ] Real-time status updates
- [ ] ETA calculations
- [ ] Vessel information
- [ ] Port-to-port tracking

#### 3.3 Tracking UI
- [ ] Visual timeline of milestones
- [ ] Map view (optional)
- [ ] Status filters
- [ ] Search and sort

**Tracking Milestones:**
```
🟡 Order Confirmed
🔵 Logistics Coordinated
🟢 Loading in Progress
🟣 Departed Lagos
🟠 In Transit
🔴 Arrived at Destination
⚪ Customs Clearance
✅ Delivered
```

**Maersk API Endpoints:**
```
GET /tracking/v2.2/tracking           → Track by BL/Container
GET /vessel-schedules/v1/schedules    → Vessel info
```

---

### Sprint 4: Document Management (Weeks 7-8)

#### 4.1 Document Upload System
- [ ] Drag-and-drop file upload
- [ ] Multi-file support
- [ ] File type validation
- [ ] Progress indicators

#### 4.2 Document Organization
- [ ] Categorization by type
- [ ] Association with orders
- [ ] Version control
- [ ] Download/preview

#### 4.3 Document Types to Support
```
Pre-Shipment:
├── FPIS Certificate
├── Certificate of Origin (NACCIMA)
├── Health Certificate
├── Fumigation Certificate
└── Product Declaration

Shipping:
├── Bill of Lading
├── Commercial Invoice
├── Packing List
└── Customs Documentation

Evidence:
├── Loading Photos
├── Loading Videos
└── Weight Certificates
```

**API Endpoints:**
```
POST /wp-json/vibotaj/v1/documents      → Upload document
GET  /wp-json/vibotaj/v1/documents      → List documents
GET  /wp-json/vibotaj/v1/documents/:id  → Get document
DELETE /wp-json/vibotaj/v1/documents/:id → Delete document
```

---

### Sprint 5: Quote System & Notifications (Weeks 9-10)

#### 5.1 Quote Request Form
- [ ] Product selection
- [ ] Quantity specification
- [ ] Destination details
- [ ] Special requirements
- [ ] File attachments (specifications)

#### 5.2 Quote Management
- [ ] View submitted quotes
- [ ] Quote status tracking
- [ ] Accept/decline quotes
- [ ] Quote to order conversion

#### 5.3 Email Notifications
- [ ] SendGrid/Mailgun integration
- [ ] Email templates
- [ ] Trigger automation

**Notification Types:**
```
1. Order Received Confirmation
2. Order Accepted by VIBOTAJ
3. Container IDs Assigned
4. Loading Started (with photos)
5. Departed Lagos Port
6. Weekly In Transit Updates
7. Arrived at Destination
8. Customs Cleared
9. Delivered Successfully
10. Payment Reminders
```

---

### Sprint 6: Testing & Launch (Weeks 11-12)

#### 6.1 Testing
- [ ] Unit tests (Jest/Vitest)
- [ ] Integration tests
- [ ] E2E tests (Playwright/Cypress)
- [ ] Performance testing
- [ ] Security audit

#### 6.2 Deployment
- [ ] Build optimization
- [ ] Deploy to Hostinger
- [ ] SSL verification
- [ ] CDN configuration
- [ ] Monitoring setup

#### 6.3 Documentation
- [ ] User guide
- [ ] Admin guide
- [ ] API documentation
- [ ] Deployment runbook

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + TypeScript | SPA framework |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Build** | Vite | Fast builds, HMR |
| **State** | TanStack Query | Server state management |
| **Forms** | React Hook Form + Zod | Form handling & validation |
| **Backend** | WordPress + PHP 8.1 | CMS & API |
| **Auth** | JWT (wp-jwt-auth) | Token-based auth |
| **API** | WP REST API | Data layer |
| **Tracking** | Maersk Track API | Container tracking |
| **Email** | SendGrid | Transactional emails |
| **Storage** | AWS S3 / Cloudinary | Document storage |

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Portal Adoption | 50% of customers use portal | GA4 tracking |
| Support Ticket Reduction | 40% decrease | Help desk analytics |
| Quote Response Time | < 4 hours | CRM tracking |
| Customer Satisfaction | > 4.5/5 rating | In-app surveys |
| Page Load Time | < 2 seconds | Lighthouse score |

---

## 💰 Estimated Costs

| Item | One-Time | Monthly |
|------|----------|---------|
| Development (in-house) | - | - |
| SendGrid (Email) | - | $20 |
| AWS S3 (Storage) | - | $50 |
| Maersk API | Free tier | $0 |
| Additional Plugins | $200 | - |
| **Total** | **$200** | **$70/month** |

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Maersk API access delays | High | Early application, backup manual entry |
| Hostinger performance | Medium | CDN, code optimization, consider upgrade |
| Scope creep | High | Strict MVP focus, defer nice-to-haves |
| Security vulnerabilities | Critical | JWT best practices, security audit |

---

## 📅 Week-by-Week Schedule

```
Week 1-2:   Project Setup, WP Plugin, React Scaffold
Week 3-4:   Authentication System
Week 5-6:   Order Tracking + Maersk Integration
Week 7-8:   Document Management
Week 9-10:  Quote System + Email Notifications
Week 11-12: Testing, Bug Fixes, Launch
```

---

## 🚀 Getting Started Checklist

Before coding begins:

- [ ] **Maersk API Access** - Apply at developer.maersk.com
- [ ] **SendGrid Account** - Create and verify sender domain
- [ ] **AWS S3 Bucket** - Create bucket for document storage
- [ ] **Development Environment** - Node 20+, PHP 8.1+, local WordPress
- [ ] **Git Repository** - Create `feature/customer-portal` branch

---

## 📁 File Structure (Final)

```
vibotaj-website-revamp-rep/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── tracking/
│   │   │   ├── documents/
│   │   │   ├── quotes/
│   │   │   └── ui/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Tracking.tsx
│   │   │   ├── Documents.tsx
│   │   │   └── Quotes.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useTracking.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   └── maersk.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── backend/
│   └── vibotaj-core/
│       ├── includes/
│       │   ├── class-api.php
│       │   ├── class-auth.php
│       │   ├── class-documents.php
│       │   ├── class-quotes.php
│       │   └── class-tracking.php
│       ├── templates/
│       │   └── email/
│       └── vibotaj-core.php
│
├── docs/
│   ├── api/
│   │   └── endpoints.md
│   └── deployment/
│       └── hostinger-deploy.md
│
└── PHASE2_PLAN.md (this file)
```

---

## Next Steps

1. **Review and approve** this plan
2. **Apply for Maersk API access** (can take 1-2 weeks)
3. **Set up development environment**
4. **Start Sprint 1: Foundation**

---

*Created: December 30, 2025*  
*Last Updated: December 30, 2025*
