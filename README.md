# VIBOTAJ Global - Website Revamp & Customer Portal

> Transform your agro-export business with an AI-powered customer portal featuring real-time container tracking, automated document management, and intelligent features.

[![Project Status](https://img.shields.io/badge/status-in%20development-yellow)]()
[![WordPress](https://img.shields.io/badge/WordPress-6.4.7-blue)]()
[![WooCommerce](https://img.shields.io/badge/WooCommerce-8.7.2-purple)]()
[![PHP](https://img.shields.io/badge/PHP-8.1.33-blue)]()
[![React](https://img.shields.io/badge/React-18.x-blue)]()

---

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Sub-Agent Architecture](#sub-agent-architecture)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 About

VIBOTAJ Global Nigeria Ltd (EU TRACES: RC1479592) is an established agro-export company specializing in horn and hoof processing for European markets. This project aims to transform the company's static website into a dynamic, AI-powered customer portal.

**Business Challenge:**
- Manual order tracking and document sharing
- Time-consuming customer support
- Inefficient communication processes
- Lack of real-time visibility for customers

**Solution:**
A comprehensive customer portal with:
- Real-time container tracking via Maersk API
- Automated document management
- AI-powered features (OCR, chatbot, predictive analytics)
- Multi-language support (English, German, French)
- Mobile-first responsive design

---

## ✨ Features

### Core Features (Phase 3 - MVP)
- 🔐 **Secure Authentication** - Role-based access control for different user types
- 📦 **Order Management** - Complete order lifecycle tracking
- 🚢 **Container Tracking** - Real-time tracking integration with Maersk API
- 📄 **Document Management** - Centralized document library with categorization
- 📧 **Email Notifications** - Automated status updates at every milestone
- 📊 **Dashboard** - Personalized dashboard for each user role
- 📱 **Mobile Responsive** - Optimized for mobile devices

### Advanced Features (Phase 4)
- 🤖 **AI Document OCR** - Automatic data extraction from certificates
- 💬 **Customer Support Chatbot** - 24/7 automated support
- 📈 **Predictive Analytics** - ETA predictions and demand forecasting
- 🌍 **Multi-language** - English, German, French support
- 🔗 **CRM Integration** - HubSpot/Zoho integration

### Infrastructure & Security
- 🛡️ **Security Hardening** - Wordfence, 2FA, security headers
- ⚡ **Performance Optimization** - CDN, caching, image optimization
- 🔄 **Automated Backups** - Daily backups with off-site storage
- 📊 **Analytics** - Google Analytics 4 integration
- 🔍 **SEO Optimized** - Structured data, XML sitemaps

---

## 🏗️ Project Structure

```
vibotaj-website-revamp/
├── README.md
├── claude.md                 # AI agent task breakdown
├── TECHNICAL_AUDIT_REPORT.md # Comprehensive audit findings
├── docs/                     # All documentation
│   ├── requirements/
│   ├── architecture/
│   ├── infrastructure/
│   ├── database/
│   ├── portal/
│   ├── security/
│   ├── testing/
│   └── deployment/
├── designs/                  # UI/UX designs
│   ├── portal/
│   └── assets/
├── src/                      # Source code
│   ├── frontend/            # React frontend
│   └── backend/             # WordPress plugin
├── integrations/            # Third-party integrations
│   ├── maersk/
│   ├── crm/
│   └── email-service/
├── ai/                      # AI/ML features
│   ├── ocr/
│   ├── chatbot/
│   └── analytics/
├── templates/               # Email & PDF templates
├── tests/                   # Test suites
├── tools/                   # Utility scripts
└── languages/               # Translation files
```

---

## 🚀 Getting Started

### Prerequisites

- **Local Development:**
  - PHP 8.1+
  - MySQL 5.7+
  - Node.js 18+
  - npm or yarn
  - WordPress 6.4+
  
- **Recommended Tools:**
  - Local by Flywheel (WordPress local dev)
  - VS Code with extensions
  - Git
  - Postman (API testing)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vibotaj/vibotaj-website-revamp.git
   cd vibotaj-website-revamp
   ```

2. **Set up WordPress locally:**
   - Install Local by Flywheel or XAMPP
   - Create new WordPress site
   - Import existing vibotaj.com database (if available)

3. **Install dependencies:**
   ```bash
   # Frontend dependencies
   cd src/frontend
   npm install
   
   # Backend - install WordPress plugins manually
   ```

4. **Configure environment:**
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env with your local settings
   ```

5. **Run development server:**
   ```bash
   # Frontend
   cd src/frontend
   npm run dev
   
   # Backend - use Local by Flywheel server
   ```

6. **Access the site:**
   - Frontend: http://localhost:3000
   - WordPress Admin: http://localhost/wp-admin

---

## 🔄 Development Workflow

### 1. Pick a Task
- Review [`claude.md`](claude.md) for task breakdown
- Choose a task assigned to your agent role
- Create a GitHub Issue for the task (if not exists)

### 2. Create Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feature/task-name
```

### 3. Develop & Test
- Write code following project standards
- Write unit tests
- Test locally
- Document your code

### 4. Commit Changes
```bash
git add .
git commit -m "feat: descriptive commit message"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build/config changes

### 5. Create Pull Request
- Push branch to GitHub
- Create Pull Request
- Request review from appropriate agent
- Address review comments

### 6. Merge
- Once approved, merge to main
- Delete feature branch

---

## 🤖 Sub-Agent Architecture

This project uses specialized AI sub-agents for different aspects of development:

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **PROJECT MANAGER AGENT** | Orchestrator | Requirements, planning, coordination |
| **INFRASTRUCTURE AGENT** | DevOps | DNS, hosting, backups, deployments |
| **BACKEND AGENT** | Server-side | API development, integrations |
| **FRONTEND AGENT** | UI/UX | React development, responsive design |
| **DATABASE AGENT** | Data Architecture | Schema design, migrations, optimization |
| **SECURITY AGENT** | Cybersecurity | Security hardening, audits, compliance |
| **QA AGENT** | Testing | Test plans, automation, quality assurance |
| **CONTENT AGENT** | Content & SEO | Analytics, SEO, translations, emails |
| **AI/ML AGENT** | Intelligent Features | OCR, chatbot, predictive analytics |

**See [`claude.md`](claude.md) for detailed task breakdown by agent.**

---

## 🗺️ Roadmap

### Phase 1: Critical Fixes (Week 1) ✅ Ready to Start
- [ ] Fix www subdomain DNS issue
- [ ] Configure 301 redirects
- [ ] Verify SSL certificate
- [ ] Set up automated backups
- [ ] Configure Google Analytics

**Timeline:** 1 week  
**Priority:** 🔴 CRITICAL

---

### Phase 2: Foundation & Security (Weeks 2-4)
- [ ] Security hardening (Wordfence, 2FA)
- [ ] Performance optimization
- [ ] Mobile responsiveness fixes
- [ ] SEO foundation
- [ ] Email system setup

**Timeline:** 3 weeks  
**Priority:** 🟡 HIGH

---

### Phase 3: Customer Portal MVP (Weeks 5-12)
- [ ] Portal UI/UX design
- [ ] Frontend development (React)
- [ ] Backend API development
- [ ] Maersk API integration
- [ ] Document management system
- [ ] Email notifications

**Timeline:** 8 weeks  
**Priority:** 🟡 HIGH

---

### Phase 4: Advanced Features (Weeks 13-16)
- [ ] AI document OCR
- [ ] Customer support chatbot
- [ ] Predictive analytics
- [ ] Multi-language support
- [ ] CRM integration

**Timeline:** 4 weeks  
**Priority:** 🟢 MEDIUM

---

### Phase 5: Launch & Optimization (Weeks 17-20)
- [ ] Pre-launch testing
- [ ] Production deployment
- [ ] Post-launch optimization
- [ ] Continuous improvement

**Timeline:** 4 weeks  
**Priority:** 🟡 HIGH

**Total Project Duration:** 16-20 weeks

---

## 🎨 Design System

### Brand Colors
```css
/* Primary Colors */
--vibotaj-green: #8bc34a;
--vibotaj-dark-green: #6a9739;

/* Neutral Colors */
--vibotaj-dark: #333333;
--vibotaj-light: #f8f6f3;
--vibotaj-white: #ffffff;

/* Accent Colors */
--vibotaj-accent-1: #001524;
--vibotaj-accent-2: #f8f6f3;
```

### Typography
- **Headings:** Merriweather, serif
- **Body:** Open Sans, sans-serif

### Responsive Breakpoints
- Mobile: < 544px
- Tablet: 544px - 921px
- Desktop: > 921px

---

## 🧪 Testing

### Running Tests

```bash
# Backend (PHPUnit)
cd plugins/vibotaj-portal
composer test

# Frontend (Jest)
cd src/frontend
npm test

# E2E (Cypress)
npm run cypress:open
```

### Test Coverage Goals
- Unit Tests: 80%+
- Integration Tests: 70%+
- E2E Tests: Critical user flows

---

## 📚 Documentation

- **[Technical Audit Report](TECHNICAL_AUDIT_REPORT.md)** - Comprehensive findings
- **[Agent Task Breakdown](claude.md)** - Detailed task assignments
- **[Requirements](/docs/requirements/)** - Functional & non-functional requirements
- **[Architecture](/docs/architecture/)** - System architecture & data models
- **[API Documentation](/docs/architecture/api-documentation.md)** - REST API reference
- **[Deployment Guide](/docs/deployment/)** - Deployment procedures

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit changes** (`git commit -m 'feat: Add AmazingFeature'`)
4. **Push to branch** (`git push origin feature/AmazingFeature`)
5. **Open Pull Request**

### Contribution Guidelines
- Follow existing code style
- Write tests for new features
- Update documentation
- Ensure all tests pass
- Request review from appropriate agent

---

## 👥 Team

**Project Stakeholders:**
- **Shola** - CEO, VIBOTAJ Global
- **Bolaji Jibodu** - COO, VIBOTAJ Global (bolaji@vibotaj.com)

**Development Team:**
- Project Manager Agent
- Infrastructure Agent
- Backend Agent
- Frontend Agent
- Database Agent
- Security Agent
- QA Agent
- Content Agent
- AI/ML Agent

---

## 📄 License

This project is proprietary and confidential.  
© 2025 VIBOTAJ Global Nigeria Ltd. All rights reserved.

---

## 📞 Contact

**VIBOTAJ Global Nigeria Ltd**  
EU TRACES NUMBER: RC1479592  
Website: https://vibotaj.com

**Project Repository:**  
https://github.com/vibotaj/vibotaj-website-revamp

**Issues & Questions:**  
https://github.com/vibotaj/vibotaj-website-revamp/issues

---

## 🙏 Acknowledgments

- WordPress & WooCommerce communities
- Astra Theme & Elementor
- React.js community
- All open-source contributors

---

**Built with ❤️ for the future of agro-export**

---

## 📊 Project Status

![Phase 1](https://img.shields.io/badge/Phase%201-Not%20Started-red)
![Phase 2](https://img.shields.io/badge/Phase%202-Not%20Started-red)
![Phase 3](https://img.shields.io/badge/Phase%203-Not%20Started-red)
![Phase 4](https://img.shields.io/badge/Phase%204-Not%20Started-red)
![Phase 5](https://img.shields.io/badge/Phase%205-Not%20Started-red)

**Last Updated:** December 27, 2025  
**Next Review:** January 3, 2026
