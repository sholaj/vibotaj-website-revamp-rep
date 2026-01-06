# TraceHub Deployment Documentation

This directory contains all deployment-related documentation for TraceHub.

## Quick Navigation

### For Quick Operations
- **[DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md)** - One-page reference for common deployment commands
  - Local development commands
  - Testing commands  
  - Production deployment commands
  - Troubleshooting quick fixes

### For Complete Deployments
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
  - Infrastructure overview (Hostinger VPS)
  - DNS configuration
  - Firewall setup
  - Directory structure
  - Docker deployment

- **[DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md)** - Detailed setup procedures
  - Prerequisites
  - Development deployment
  - Production deployment
  - Environment configuration
  - SSL/HTTPS setup
  - Database backups
  - Monitoring and logs

- **[README.deployment.md](README.deployment.md)** - Alternative deployment guide
  - Docker and Docker Compose deployment
  - Step-by-step instructions

### For Sprint 8 Migration
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Sprint 8 deployment checklist
  - Pre-deployment tasks (24 hours before)
  - Migration execution steps
  - Post-deployment validation
  - Rollback procedures

## Common Tasks

### Start Local Development
```bash
cd tracehub
make dev              # Start local environment
make dev-logs         # View logs
make health           # Check service health
```

### Deploy to Production
1. Review [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
2. Follow [DEPLOYMENT.md](DEPLOYMENT.md) for infrastructure setup
3. Use [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md) for commands

## Infrastructure Details

- **Provider:** Hostinger VPS (ID: 1243111)
- **Domain:** tracehub.vibotaj.com
- **IP:** 82.198.225.150
- **OS:** Ubuntu 24.04 with Docker

For complete infrastructure details, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Related Documentation

- [DevOps Documentation](../devops/) - CI/CD, GitOps, monitoring
- [Architecture](../architecture/) - System architecture and design
- [Sprint Archives](../sprints/archive/) - Historical sprint documentation
