# VIBOTAJ TraceHub

> Container tracking and documentation compliance platform for agro-export operations, designed to give German buyers and African suppliers complete shipment visibility and audit-ready records.

[![Project Status](https://img.shields.io/badge/status-POC%20Development-yellow)]()
[![Phase](https://img.shields.io/badge/phase-Single%20Shipment%20POC-blue)]()

---

## Table of Contents

- [About](#about)
- [Three Pillars](#three-pillars)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Roadmap](#roadmap)
- [Team](#team)

---

## About

**VIBOTAJ Global Nigeria Ltd** (EU TRACES: RC1479592) is an established agro-export company specializing in horn and hoof processing for European markets. TraceHub is our platform for solving the core pain points identified by our German buyers and African suppliers:

| Problem | Impact |
|---------|--------|
| **Documentation gaps** | Missing or incomplete export documentation delays shipments |
| **Inconsistent visibility** | Buyers can't track container status in real-time |
| **Audit-readiness** | No consolidated, EUDR-compliant record bundles for regulatory review |

**TraceHub Solution**: A decoupled platform that provides real-time container tracking linked to complete document sets, enabling anyone to answer "Where is my container?" and "Are all documents complete?" within 30 seconds.

---

## Three Pillars

```
+------------------------------------------------------------------+
|                        VIBOTAJ TraceHub                           |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------------+  +-------------------+  +------------------+ |
|  |   REAL-TIME     |  |    DOCUMENT       |  |  BUYER/SUPPLIER  | |
|  |   CONTAINER     |  |    LIFECYCLE &    |  |  EXPERIENCE      | |
|  |   TRACKING      |  |    COMPLIANCE     |  |                  | |
|  +-----------------+  +-------------------+  +------------------+ |
|  | - Carrier API   |  | - State machine   |  | - Role-based     | |
|  |   integration   |  | - EUDR compliance |  |   dashboards     | |
|  | - Event ingest  |  | - Metadata model  |  | - Upload portal  | |
|  | - ETD/ETA       |  | - Audit bundles   |  | - Doc status     | |
|  | - Port events   |  | - Validation      |  | - Tracking view  | |
|  +-----------------+  +-------------------+  +------------------+ |
|                                                                   |
+------------------------------------------------------------------+
```

### 1. Real-Time Container Tracking
- Integration with carrier-agnostic tracking APIs (ShipsGo/Vizion)
- Standardized container events: loaded, departed, arrived, discharged, delivered
- Live status linked directly to documentation set

### 2. Document Lifecycle & Compliance
- State machine: Draft -> Uploaded -> Validated -> Compliance Check -> Linked -> Archived
- EUDR-compliant metadata: farm/plot IDs, geolocation, production dates
- Required document matrix by product type and destination

### 3. Buyer & Supplier Experience
- WordPress as public portal/UI layer (decoupled from core logic)
- Buyers: see live containers + complete doc packs per shipment
- Suppliers: see required docs, upload status, missing items
- One-click "Download Audit Pack" for regulatory review

---

## Project Structure

```
vibotaj-website-revamp-rep/
├── README.md                           # This file
├── claude.md                           # CEO's directional task request
├── HOSTINGER_CONFIG.md                 # Hostinger API configuration
├── VIBOTAJ_TECHNICAL_AUDIT_REPORT.md   # Technical audit findings
│
├── docs/
│   ├── architecture/
│   │   └── tracehub-architecture.md    # Full architecture document (5-7 pages)
│   ├── strategy/
│   │   └── tracehub-poc-plan.md        # POC implementation plan
│   ├── design/
│   │   └── design-system.md            # Brand colors, typography, components
│   ├── infrastructure/
│   │   ├── ssl-configuration.md        # SSL/TLS setup
│   │   ├── dns-configuration.md        # DNS records & CNAME
│   │   └── backup-strategy.md          # Backup procedures
│   └── _archive/
│       └── pre-tracehub/               # Previous phase documentation
│
├── .claude/
│   ├── agents/                         # AI agent role definitions
│   └── skills/                         # Skill configurations
│
├── scripts/
│   └── deploy-phase1.sh                # Deployment automation
│
├── src/
│   └── config/
│       └── .htaccess.template          # Apache configuration
│
├── .secrets/                           # Environment credentials (git-ignored)
└── backups/                            # Local backup storage
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture/tracehub-architecture.md) | Full system architecture, data model, API design, lifecycle diagrams |
| [POC Plan](docs/strategy/tracehub-poc-plan.md) | Single-shipment POC implementation plan |
| [Design System](docs/design/design-system.md) | Brand colors, typography, components |
| [CEO Vision](claude.md) | Directional task request from leadership |

### Key Architecture Concepts

**Decoupled Design**:
- WordPress = UI shell (customer portal, login, dashboards)
- TraceHub Core = separate backend service (Node.js/Python + PostgreSQL)
- Integration layer for container tracking APIs

**Data Model Entities**:
- `Shipment`: container, BL, vessel, ETD/ETA, ports, incoterms
- `Product`: HS code, quantities, packaging, batch/lot
- `Origin`: farm/plot ID, geolocation, EUDR compliance fields
- `Document`: type, state, file, validation status
- `ContainerEvent`: tracking events from carrier APIs
- `Party`: buyers, suppliers, agents

**Lifecycle States**:
- Documents: Draft -> Uploaded -> Validated -> Compliance_OK/Fail -> Linked -> Archived
- Shipments: Created -> Docs_Pending -> Docs_Complete -> In_Transit -> Arrived -> Delivered -> Closed

---

## Getting Started

### Prerequisites

- Node.js 20+ or Python 3.11+
- PostgreSQL 15+
- WordPress 6.x (for portal UI)
- Container tracking API key (ShipsGo or Vizion)

### POC Development Setup

```bash
# Clone repository
git clone https://github.com/vibotaj/vibotaj-website-revamp-rep.git
cd vibotaj-website-revamp-rep

# Backend setup (when implemented)
cd backend
npm install  # or pip install -r requirements.txt
cp .env.example .env
# Edit .env with credentials
npm run dev

# Database
docker run -d --name tracehub-db \
  -e POSTGRES_DB=tracehub \
  -e POSTGRES_USER=tracehub \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:15
```

---

## Development Workflow

### Branch Strategy

```bash
# Main branch: stable, production-ready
# Feature branches: feature/<task-name>
# Current: feature/security-setup

git checkout main
git pull origin main
git checkout -b feature/tracehub-backend
```

### Commit Convention

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `chore:` Build/config changes

---

## Roadmap

### Current Phase: Single-Shipment POC

**Objective**: Demonstrate end-to-end TraceHub concept with ONE real shipment to Germany.

| Sprint | Focus | Deliverables |
|--------|-------|--------------|
| **Sprint 1** | Data & Backend | PostgreSQL schema, core entities, basic APIs |
| **Sprint 2** | Tracking Integration | ShipsGo/Vizion API, event persistence, webhooks |
| **Sprint 3** | UI & Documents | WordPress integration, buyer dashboard, document upload |
| **Sprint 4** | Polish & Delivery | Audit pack export, testing, documentation |

**Success Criteria**:
- [ ] Single shipment visible with all metadata
- [ ] Live container tracking displayed
- [ ] Documents with complete/missing indicators
- [ ] "Download Audit Pack" exports ZIP with PDF index
- [ ] Non-technical user answers key questions in <30 seconds

### Future Phases

| Phase | Description |
|-------|-------------|
| **Full VIBOTAJ Rollout** | All shipments on TraceHub, all products |
| **AI Enhancement** | Document OCR, discrepancy detection, auto-summaries |
| **Multi-Tenant SaaS** | Onboard other exporters, subscription model |

---

## Team

**Project Stakeholders**
- **Shola** - CEO, VIBOTAJ Global
- **Bolaji Jibodu** - COO, VIBOTAJ Global (bolaji@vibotaj.com)

**AI Agent Roles**
| Agent | Responsibility |
|-------|----------------|
| Product Strategist | Requirements, roadmap, prioritization |
| Microservices Architect | System design, APIs, data model |
| Full-Stack Developer | Frontend & backend implementation |
| DevOps Engineer | Infrastructure, CI/CD, deployment |
| API Designer | API specifications, integrations |
| UI/UX Designer | Design system, user experience |

---

## Infrastructure

**Current Setup**:
- Domain Management: Squarespace DNS
- Web Hosting: Hostinger
- CMS: WordPress 6.4.7 + WooCommerce 8.7.2
- PHP: 8.1.33

**TraceHub Backend** (POC):
- Runtime: Node.js 20 or Python 3.11
- Database: PostgreSQL 15
- Container Tracking: ShipsGo API
- File Storage: Local (POC) / S3 (Production)

---

## License

This project is proprietary and confidential.
Copyright 2025-2026 VIBOTAJ Global Nigeria Ltd. All rights reserved.

---

## Contact

**VIBOTAJ Global Nigeria Ltd**
EU TRACES NUMBER: RC1479592
Website: https://vibotaj.com

---

**Last Updated:** January 2, 2026
**Current Branch:** `feature/security-setup`
