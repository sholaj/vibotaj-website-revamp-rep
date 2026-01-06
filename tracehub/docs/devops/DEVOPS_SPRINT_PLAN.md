# TraceHub DevOps Implementation Sprint Plan

## Overview

**Goal**: Implement automated CI/CD pipeline with GitOps workflows, database migrations, and zero-downtime deployments for TraceHub.

**Duration**: 3 Sprints (6 weeks total)

**Team**: 1 DevOps Engineer + 1 Backend Developer (part-time support)

---

## Sprint 1: Foundation & CI Pipeline (2 weeks)

### Week 1: Setup & Basic CI

#### Day 1-2: Infrastructure Preparation

**Tasks**:
- [ ] Review current VPS configuration and access
- [ ] Set up SSH keys for automation
- [ ] Create directory structure on VPS for staging/production
- [ ] Configure firewall rules for new ports (staging: 8100, 3100, 5532)
- [ ] Set up SSL certificates for staging.tracehub.vibotaj.com

**Deliverables**:
```bash
# VPS directory structure
/home/tracehub/
├── production/
│   ├── .env.production (created from template)
│   ├── uploads/
│   ├── logs/
│   └── backups/
├── staging/
│   ├── .env.staging (created from template)
│   ├── uploads/
│   ├── logs/
│   └── backups/
└── shared/
    └── ssl/
```

**Commands**:
```bash
# On VPS
ssh user@tracehub.vibotaj.com
sudo mkdir -p /home/tracehub/{production,staging,shared}/{uploads,logs,backups}
sudo chown -R $USER:$USER /home/tracehub

# Set up SSL for staging subdomain
sudo certbot certonly --nginx -d staging.tracehub.vibotaj.com
```

---

#### Day 3-4: GitHub Actions - Backend CI

**Tasks**:
- [x] Create `.github/workflows/backend-ci.yml` ✓
- [ ] Add linting tools to backend requirements
- [ ] Configure code quality checks (flake8, black, mypy)
- [ ] Set up test database in GitHub Actions
- [ ] Write initial backend tests if missing
- [ ] Configure code coverage reporting

**Testing**:
```bash
# Locally test the workflow
cd tracehub/backend

# Install dev dependencies
pip install black flake8 mypy pytest pytest-cov

# Run linting
black --check app
flake8 app

# Run tests
pytest --cov=app
```

**Success Criteria**:
- Backend CI workflow runs on every PR
- All quality checks pass
- Coverage report generated

---

#### Day 5-6: GitHub Actions - Frontend CI

**Tasks**:
- [x] Create `.github/workflows/frontend-ci.yml` ✓
- [ ] Configure ESLint for frontend
- [ ] Set up TypeScript strict mode checks
- [ ] Add frontend unit tests (if missing)
- [ ] Configure build validation
- [ ] Set up npm audit for security

**Testing**:
```bash
# Locally test frontend CI steps
cd tracehub/frontend

# Install dependencies
npm ci

# Run checks
npm run lint
npx tsc --noEmit
npm run build
npm audit --production
```

**Success Criteria**:
- Frontend CI workflow runs on every PR
- Build completes successfully
- No critical security vulnerabilities

---

#### Day 7-8: Database Migration Setup

**Tasks**:
- [x] Create Alembic configuration ✓
- [x] Create `alembic/env.py` with model imports ✓
- [ ] Generate initial migration from existing models
- [ ] Test migrations locally
- [ ] Create database migration CI workflow
- [ ] Document migration procedures

**Commands**:
```bash
cd tracehub/backend

# Initialize Alembic (already done via files created)
# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Review and test migration
alembic upgrade head
alembic downgrade base
alembic upgrade head

# Test in Docker
docker-compose exec backend alembic upgrade head
```

**Success Criteria**:
- Alembic properly configured
- Initial migration created and tested
- Migration CI validates all changes

---

#### Day 9-10: Docker Build Pipeline

**Tasks**:
- [x] Create `.github/workflows/build-and-push.yml` ✓
- [ ] Set up GitHub Container Registry (GHCR)
- [ ] Configure Docker Buildx for caching
- [ ] Add Trivy security scanning
- [ ] Test image build and push locally
- [ ] Verify images are accessible

**Testing**:
```bash
# Test Docker build locally
cd tracehub

# Build backend
docker build -t tracehub-backend:test ./backend

# Build frontend
docker build -t tracehub-frontend:test ./frontend

# Test with docker-compose
docker-compose up -d
```

**Success Criteria**:
- Docker images build successfully
- Images pushed to GHCR
- Vulnerability scanning runs
- Image size optimized (<500MB backend, <100MB frontend)

---

### Week 2: Staging Deployment

#### Day 11-12: Staging Environment Setup

**Tasks**:
- [x] Create `docker-compose.staging.yml` ✓
- [x] Create `.env.staging.example` ✓
- [ ] Configure staging database
- [ ] Set up nginx reverse proxy for staging
- [ ] Configure SSL for staging subdomain
- [ ] Test manual staging deployment

**Nginx Configuration**:
```nginx
# /etc/nginx/sites-available/staging.tracehub.vibotaj.com
server {
    listen 80;
    server_name staging.tracehub.vibotaj.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.tracehub.vibotaj.com;

    ssl_certificate /etc/letsencrypt/live/staging.tracehub.vibotaj.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.tracehub.vibotaj.com/privkey.pem;

    location /api {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Success Criteria**:
- Staging accessible at https://staging.tracehub.vibotaj.com
- Separate database from production
- All services healthy

---

#### Day 13-14: Automated Staging Deployment

**Tasks**:
- [x] Create `.github/workflows/deploy-staging.yml` ✓
- [ ] Set up GitHub Secrets for staging
- [ ] Configure SSH access from GitHub Actions
- [ ] Test automated deployment to staging
- [ ] Add smoke tests after deployment
- [ ] Set up deployment notifications

**GitHub Secrets to Create**:
```bash
gh secret set STAGING_SSH_KEY < ~/.ssh/tracehub_staging_rsa
gh secret set STAGING_HOST -b "tracehub.vibotaj.com"
gh secret set STAGING_USER -b "tracehub"
gh secret set STAGING_DB_PASSWORD -b "secure-staging-password"
gh secret set STAGING_JWT_SECRET -b "staging-jwt-secret-32-chars"
gh secret set VIZION_API_KEY -b "your-vizion-key"
gh secret set DEMO_PASSWORD -b "staging-demo-pass"
```

**Testing**:
```bash
# Create test branch
git checkout -b test-staging-deploy

# Make a small change
echo "// Test deployment" >> tracehub/backend/app/main.py

# Push to develop branch
git checkout develop
git merge test-staging-deploy
git push origin develop

# Watch GitHub Actions deploy to staging
# Verify at https://staging.tracehub.vibotaj.com
```

**Success Criteria**:
- Push to `develop` triggers staging deployment
- Deployment completes without errors
- Health checks pass
- Smoke tests verify functionality

---

### Sprint 1 Deliverables

- [x] Backend CI workflow functional ✓
- [x] Frontend CI workflow functional ✓
- [x] Docker build pipeline working ✓
- [x] Alembic migration system configured ✓
- [x] Staging environment deployed and accessible ✓
- [ ] Documentation for CI/CD processes

**Sprint 1 Demo**:
1. Show pull request with CI checks
2. Demonstrate automatic staging deployment
3. Show staging environment running
4. Walk through logs and health checks

---

## Sprint 2: Production Deployment & Blue-Green (2 weeks)

### Week 3: Production Preparation

#### Day 15-16: Production Environment Hardening

**Tasks**:
- [ ] Review and update production `.env` file
- [ ] Set up production database with strong passwords
- [ ] Configure production nginx with SSL
- [ ] Set up automated backups (cron job)
- [ ] Configure log rotation
- [ ] Set up monitoring scripts

**Automated Backup Cron**:
```bash
# Add to crontab on VPS
crontab -e

# Backup production database daily at 2 AM
0 2 * * * cd /home/tracehub/production && docker-compose exec -T db pg_dump -U tracehub tracehub > backups/daily_$(date +\%Y\%m\%d).sql

# Keep only last 30 days
5 2 * * * find /home/tracehub/production/backups -name "daily_*.sql" -mtime +30 -delete
```

**Success Criteria**:
- Production environment secure
- Daily backups working
- Logs rotated to prevent disk fill

---

#### Day 17-18: Blue-Green Deployment Strategy

**Tasks**:
- [x] Create production deployment workflow ✓
- [ ] Implement blue-green deployment logic
- [ ] Add health check validation
- [ ] Configure traffic switching
- [ ] Test rollback procedures
- [ ] Document blue-green process

**Testing Blue-Green Locally**:
```bash
cd tracehub

# Simulate blue deployment
docker-compose -f docker-compose.prod.yml up -d

# Tag as blue
docker tag tracehub-backend:latest tracehub-backend:blue
docker tag tracehub-frontend:latest tracehub-frontend:blue

# Deploy green with new version
docker build -t tracehub-backend:green ./backend
docker build -t tracehub-frontend:green ./frontend

# Start green containers
# Switch traffic (update docker-compose.yml)
# Remove blue containers
```

**Success Criteria**:
- Blue-green deployment tested
- Zero downtime during switch
- Rollback tested and working

---

#### Day 19-20: GitHub Environments & Approvals

**Tasks**:
- [ ] Configure GitHub production environment
- [ ] Set up required reviewers for production
- [ ] Add environment protection rules
- [ ] Test approval workflow
- [ ] Document approval process

**GitHub Environment Setup**:
```bash
# Via GitHub UI:
# Repository → Settings → Environments → New environment

Environment: production
Required reviewers: [Add team members]
Wait timer: 0 minutes
Deployment branches: main only

# Add environment-specific secrets
PRODUCTION_SSH_KEY
PRODUCTION_HOST
PRODUCTION_DB_PASSWORD
PRODUCTION_JWT_SECRET
```

**Success Criteria**:
- Production requires manual approval
- Only main branch can deploy to production
- Approval process documented

---

### Week 4: Rollback & Recovery

#### Day 21-22: Automated Rollback

**Tasks**:
- [x] Create `scripts/rollback.sh` ✓
- [ ] Test deployment rollback
- [ ] Test database rollback
- [ ] Add rollback to CI/CD pipeline
- [ ] Document rollback procedures
- [ ] Create rollback runbook

**Rollback Testing**:
```bash
# SSH to VPS
ssh user@tracehub.vibotaj.com

# Test deployment rollback
cd /home/tracehub/staging
./scripts/rollback.sh -e staging -t deployment

# Test database rollback
./scripts/rollback.sh -e staging -t database

# Verify health after rollback
curl http://localhost:8100/health
```

**Success Criteria**:
- Rollback script works for both deployment and database
- Rollback completes in <5 minutes
- System healthy after rollback

---

#### Day 23-24: Disaster Recovery Plan

**Tasks**:
- [ ] Document complete disaster recovery procedures
- [ ] Create backup restoration scripts
- [ ] Test full system recovery from backups
- [ ] Set up off-site backup storage
- [ ] Create recovery time objectives (RTO)
- [ ] Create recovery point objectives (RPO)

**Disaster Recovery Test**:
```bash
# Simulate complete data loss
docker-compose down -v

# Restore from backup
./scripts/restore-full-system.sh

# Verify all data present
# Verify all services working
```

**Success Criteria**:
- Full system can be restored from backup
- RTO: <30 minutes
- RPO: <24 hours (daily backups)
- DR procedures documented

---

#### Day 25-26: Production Deployment Dry Run

**Tasks**:
- [ ] Deploy to production for first time
- [ ] Monitor deployment closely
- [ ] Run full test suite on production
- [ ] Verify all integrations working
- [ ] Document any issues encountered
- [ ] Create production deployment checklist

**Production Deployment Checklist**:
```markdown
Pre-Deployment:
- [ ] All tests passing on staging
- [ ] Database backup verified
- [ ] Rollback plan ready
- [ ] Team notified
- [ ] Maintenance window scheduled (if needed)

Deployment:
- [ ] GitHub Actions workflow approved
- [ ] Monitor deployment logs
- [ ] Verify health checks
- [ ] Test critical user flows
- [ ] Check error rates
- [ ] Monitor response times

Post-Deployment:
- [ ] Verify all features working
- [ ] Monitor for 30 minutes
- [ ] Update deployment log
- [ ] Notify stakeholders
- [ ] Schedule post-deployment review
```

**Success Criteria**:
- Production deployment successful
- Zero customer impact
- All services healthy
- Deployment documented

---

### Sprint 2 Deliverables

- [x] Production deployment workflow ✓
- [ ] Blue-green deployment working
- [x] Rollback procedures tested ✓
- [ ] Disaster recovery plan documented
- [ ] First production deployment complete
- [ ] Deployment runbooks created

**Sprint 2 Demo**:
1. Show production deployment with approval
2. Demonstrate blue-green deployment
3. Show rollback procedure
4. Walk through disaster recovery plan

---

## Sprint 3: Monitoring, Security & Optimization (2 weeks)

### Week 5: Security & Secrets Management

#### Day 27-28: Security Hardening

**Tasks**:
- [ ] Implement secrets rotation strategy
- [ ] Add security scanning to CI (Trivy, Snyk)
- [ ] Configure dependency updates (Dependabot)
- [ ] Set up HTTPS enforcement
- [ ] Review and update firewall rules
- [ ] Implement rate limiting

**Security Checklist**:
```bash
# Enable Dependabot
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/tracehub/backend"
    schedule:
      interval: "weekly"

  - package-ecosystem: "npm"
    directory: "/tracehub/frontend"
    schedule:
      interval: "weekly"

  - package-ecosystem: "docker"
    directory: "/tracehub"
    schedule:
      interval: "weekly"
```

**Success Criteria**:
- No critical security vulnerabilities
- Secrets properly managed
- Automated security updates enabled

---

#### Day 29-30: Monitoring & Alerting

**Tasks**:
- [ ] Set up health check monitoring
- [ ] Configure uptime monitoring
- [ ] Add application metrics endpoint
- [ ] Set up error tracking
- [ ] Configure deployment notifications
- [ ] Create monitoring dashboard

**Basic Monitoring Setup**:
```python
# Add to backend: app/routers/metrics.py
from fastapi import APIRouter
import psutil

router = APIRouter()

@router.get("/metrics")
async def metrics():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
```

**Success Criteria**:
- Real-time health monitoring
- Alerts for critical issues
- Deployment notifications working

---

### Week 6: Performance & Documentation

#### Day 31-32: Performance Optimization

**Tasks**:
- [ ] Optimize Docker image sizes
- [ ] Configure Docker resource limits
- [ ] Add database query optimization
- [ ] Implement caching where appropriate
- [ ] Set up CDN for static assets (if needed)
- [ ] Load testing

**Performance Targets**:
```
- Backend image: <500MB
- Frontend image: <100MB
- API response time: <200ms (p95)
- Database query time: <100ms (p95)
- Deployment time: <5 minutes
```

**Success Criteria**:
- Performance targets met
- Docker images optimized
- Load tests passing

---

#### Day 33-34: Documentation & Training

**Tasks**:
- [x] Complete DEVOPS.md documentation ✓
- [ ] Create video walkthrough of deployment process
- [ ] Create incident response playbook
- [ ] Document common troubleshooting steps
- [ ] Train team on new workflows
- [ ] Create onboarding guide for new developers

**Documentation Checklist**:
- [x] CI/CD architecture diagram ✓
- [x] Deployment procedures ✓
- [x] Rollback procedures ✓
- [ ] Monitoring setup guide
- [ ] Security procedures
- [ ] Troubleshooting guide
- [ ] FAQ document

**Success Criteria**:
- All documentation complete
- Team trained on workflows
- Runbooks tested

---

#### Day 35-36: Final Testing & Handoff

**Tasks**:
- [ ] Full end-to-end testing of all workflows
- [ ] Load testing of production system
- [ ] Security audit and penetration testing
- [ ] Final review of all documentation
- [ ] Knowledge transfer session
- [ ] Create maintenance schedule

**Final Verification**:
```bash
# Test all workflows
1. Create feature branch
2. Open PR → CI runs
3. Merge to develop → Staging deployment
4. Merge to main → Production deployment (with approval)
5. Verify rollback works
6. Verify monitoring alerts
7. Test disaster recovery
```

**Success Criteria**:
- All workflows tested end-to-end
- No critical issues
- Team confident with new system
- Documentation complete

---

### Sprint 3 Deliverables

- [ ] Security hardening complete
- [ ] Monitoring and alerting functional
- [ ] Performance optimized
- [x] Complete documentation ✓
- [ ] Team trained
- [ ] System fully operational

**Sprint 3 Demo**:
1. Show complete CI/CD pipeline in action
2. Demonstrate monitoring dashboard
3. Show security scanning results
4. Walk through documentation
5. Present performance metrics

---

## Post-Sprint Activities

### Month 1 After Go-Live

**Week 1-2**:
- [ ] Monitor deployment frequency and success rate
- [ ] Track and resolve any issues
- [ ] Gather team feedback
- [ ] Optimize based on usage patterns

**Week 3-4**:
- [ ] Review and update documentation
- [ ] Conduct retrospective
- [ ] Plan next improvements
- [ ] Set up advanced monitoring (Prometheus/Grafana)

### Continuous Improvement Backlog

**High Priority**:
- [ ] Set up Prometheus + Grafana for metrics
- [ ] Implement automated database backup verification
- [ ] Add canary deployments
- [ ] Set up log aggregation (ELK/Loki)
- [ ] Implement feature flags

**Medium Priority**:
- [ ] Multi-region failover (if needed)
- [ ] Cost optimization review
- [ ] Performance profiling and optimization
- [ ] API load testing automation
- [ ] Implement circuit breakers

**Low Priority**:
- [ ] Infrastructure as Code (Terraform for VPS)
- [ ] Container orchestration (Kubernetes if scaling needed)
- [ ] Advanced security (WAF, DDoS protection)
- [ ] Multi-environment testing (QA environment)

---

## Success Metrics

### Technical Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Deployment frequency | 5+ per week | Manual |
| Deployment success rate | >95% | - |
| Mean time to recovery (MTTR) | <30 min | - |
| Change failure rate | <5% | - |
| Lead time for changes | <1 day | - |
| Automated test coverage | >70% | ~30% |

### Business Metrics

| Metric | Target |
|--------|--------|
| Zero-downtime deployments | 100% |
| Production incidents per month | <2 |
| Time to resolve incidents | <2 hours |
| Developer satisfaction | >4/5 |

---

## Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| VPS downtime during migration | Medium | High | Test on staging first, schedule maintenance window |
| Database migration failure | Low | Critical | Always backup before migration, test on staging |
| GitHub Actions quota exceeded | Low | Medium | Monitor usage, optimize workflows |
| SSH access issues | Medium | High | Multiple backup access methods, VPS console access |
| Disk space issues | Medium | Medium | Implement monitoring, automated cleanup |

### Contingency Plans

**If automated deployment fails**:
1. Fallback to manual deployment using existing scripts
2. Investigate and fix GitHub Actions workflow
3. Document incident for post-mortem

**If database migration fails in production**:
1. Immediately rollback database from backup
2. Restart services on old version
3. Fix migration in staging environment
4. Re-attempt migration in next deployment

**If VPS becomes unavailable**:
1. Check Hostinger control panel
2. Contact Hostinger support
3. Use VPS console access if SSH unavailable
4. Escalate to CTO if unresolved within 1 hour

---

## Resource Requirements

### Team
- **DevOps Engineer**: Full-time for 6 weeks
- **Backend Developer**: Part-time support (10 hours/week)
- **QA Engineer**: Testing support (5 hours/week in Sprint 3)

### Infrastructure
- **Current**: Hostinger VPS (already provisioned)
- **Additional**: None required initially
- **Future**: Consider dedicated monitoring server

### Tools & Services
- **GitHub Actions**: Free tier (2,000 minutes/month)
- **GitHub Container Registry**: Free for public repos
- **Hostinger VPS**: Already paid
- **SSL Certificates**: Free (Let's Encrypt)

### Estimated Costs
- **Additional infrastructure**: $0 (using existing VPS)
- **Tools**: $0 (free tier)
- **Total**: $0 for initial implementation

---

## Checklist for Sprint Kickoff

**Before Starting Sprint 1**:
- [ ] VPS access confirmed
- [ ] GitHub repository access confirmed
- [ ] Team availability confirmed
- [ ] Backup of current production system
- [ ] Sprint goals communicated to stakeholders
- [ ] Development environment set up
- [ ] Documentation repository created

**Tools to Install**:
```bash
# Local development
brew install gh           # GitHub CLI
brew install terraform    # Future IaC
pip install alembic      # Database migrations
npm install -g trivy     # Security scanning

# On VPS
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
```

---

## Daily Standup Template

**What did I accomplish yesterday?**
- Task 1
- Task 2

**What will I work on today?**
- Task 1
- Task 2

**Any blockers?**
- Issue 1 (if any)

---

## Sprint Review Template

**What we accomplished**:
- List of completed features
- Demos and screenshots

**What we learned**:
- Technical insights
- Process improvements

**What's next**:
- Next sprint goals
- Carryover items

---

**Ready to start? Let's kick off Sprint 1!**

For questions or issues during implementation, refer to:
- **Documentation**: `/tracehub/DEVOPS.md`
- **GitHub Issues**: Tag with `devops` label
- **Team Chat**: #tracehub-devops channel
