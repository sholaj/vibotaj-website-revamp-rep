# TraceHub Sprint 8 Deployment Checklist

**Migration:** Multi-Tenancy Platform
**Version:** 1.3.0
**Target Date:** TBD
**Deployment Type:** Blue-Green (Zero Downtime)

---

## Pre-Deployment (24 Hours Before)

### Team Readiness
- [ ] DevOps team briefed on deployment procedure
- [ ] Database team on-call and available
- [ ] Technical lead available for decision-making
- [ ] Emergency contacts verified and reachable
- [ ] Rollback team designated and trained

### Documentation
- [ ] Migration plan reviewed by all stakeholders
- [ ] Rollback procedure documented and tested
- [ ] Backup/restore scripts tested in staging
- [ ] Validation queries prepared
- [ ] Communication templates ready

### Environment Preparation
- [ ] Staging migration completed successfully
- [ ] Staging validation passed all tests
- [ ] Production database credentials verified
- [ ] Backup storage space verified (50GB+ free)
- [ ] Monitoring dashboards configured

### Stakeholder Communication
- [ ] VIBOTAJ team notified (24h notice)
- [ ] Maintenance window communicated (if not using blue-green)
- [ ] Support team briefed on expected changes
- [ ] Status page prepared for updates

---

## Pre-Deployment (1 Hour Before)

### System Health Check
- [ ] All production services running normally
- [ ] Database connections stable
- [ ] Disk space > 20% free
- [ ] CPU usage < 70%
- [ ] Memory usage < 80%
- [ ] No active incidents

### Code Preparation
- [ ] Git repository on `main` branch
- [ ] Latest code pulled to production server
- [ ] Migration files present (003-006)
- [ ] Scripts executable (`chmod +x scripts/*.sh`)
- [ ] Docker images built

### Backup Verification
- [ ] Latest automated backup exists (< 24h old)
- [ ] Automated backup verified restorable
- [ ] Backup retention policy confirmed

---

## Deployment Phase 1: Backup (15 minutes)

**Time:** T-15 minutes

- [ ] Start deployment log: `deployment_$(date +%Y%m%d_%H%M%S).log`
- [ ] Record deployment start time
- [ ] Create pre-migration backup:
  ```bash
  cd /opt/tracehub/scripts
  ./backup_pre_migration.sh | tee -a ../deployment.log
  ```
- [ ] Verify backup created successfully
- [ ] Verify backup size reasonable (> 1MB)
- [ ] Backup manifest generated
- [ ] Record backup file location
- [ ] Test backup integrity (verification step in script)

**Rollback Trigger:** If backup fails, STOP deployment

---

## Deployment Phase 2: Migration Execution (20 minutes)

**Time:** T-0 minutes

### Migration 003: Create Multi-Tenancy Tables (2 seconds)

- [ ] Run: `alembic upgrade 003`
- [ ] Verify tables created:
  ```bash
  docker exec tracehub-db psql -U tracehub -d tracehub -c "
    SELECT table_name FROM information_schema.tables
    WHERE table_name IN ('organizations', 'org_memberships', 'invitations');
  "
  ```
- [ ] Expected: 3 rows
- [ ] Record execution time

**Rollback Trigger:** If migration fails, run `alembic downgrade 002`

### Migration 004: Add organization_id Columns (10 seconds)

- [ ] Run: `alembic upgrade 004`
- [ ] Verify columns added:
  ```bash
  docker exec tracehub-db psql -U tracehub -d tracehub -c "
    SELECT COUNT(*) FROM information_schema.columns
    WHERE column_name = 'organization_id';
  "
  ```
- [ ] Expected: 9 columns
- [ ] All columns nullable: YES
- [ ] Record execution time

**Rollback Trigger:** If migration fails, run `alembic downgrade 003`

### Migration 005: Data Migration (10-15 minutes)

**CRITICAL STEP - Monitor Closely**

- [ ] Run: `alembic upgrade 005`
- [ ] Monitor migration output for:
  - VIBOTAJ organization created
  - User count migrated
  - Shipment count migrated
  - No error messages
- [ ] Verify data migration:
  ```bash
  docker exec tracehub-db psql -U tracehub -d tracehub -c "
    SELECT
      (SELECT COUNT(*) FROM users WHERE organization_id IS NULL) AS users_null,
      (SELECT COUNT(*) FROM shipments WHERE organization_id IS NULL) AS shipments_null;
  "
  ```
- [ ] Expected: 0 NULL values
- [ ] Record execution time
- [ ] Record migrated counts

**Rollback Trigger:** If data validation fails, run `alembic downgrade 004`

### Migration 006: Add Constraints & Indexes (10 seconds)

- [ ] Run: `alembic upgrade 006`
- [ ] Verify constraints:
  ```bash
  docker exec tracehub-db psql -U tracehub -d tracehub -c "
    SELECT COUNT(*) FROM information_schema.table_constraints
    WHERE constraint_name LIKE 'fk_%_organization_id';
  "
  ```
- [ ] Expected: 9 foreign keys
- [ ] Verify indexes created (25+ indexes)
- [ ] Record execution time

**Rollback Trigger:** If constraint addition fails, run `alembic downgrade 005`

---

## Deployment Phase 3: Application Deployment (10 minutes)

**Time:** T+20 minutes

### Blue-Green Switch (Recommended)

- [ ] Build new Docker images (green environment)
- [ ] Start green containers (port 8001)
- [ ] Wait for green health check:
  ```bash
  for i in {1..30}; do
    if curl -f http://localhost:8001/health; then
      echo "Green is healthy"
      break
    fi
    sleep 2
  done
  ```
- [ ] Run smoke tests on green:
  ```bash
  pytest tests/integration/test_multitenancy_smoke.py --base-url=http://localhost:8001
  ```
- [ ] Switch load balancer to green
- [ ] Monitor for 5 minutes
- [ ] Verify no errors in logs

**Alternative: Rolling Restart**

- [ ] Restart backend:
  ```bash
  docker-compose restart backend
  ```
- [ ] Wait for health check
- [ ] Restart frontend:
  ```bash
  docker-compose restart frontend
  ```
- [ ] Verify services running

---

## Deployment Phase 4: Validation (10 minutes)

**Time:** T+30 minutes

### Automated Validation

- [ ] Run validation script:
  ```bash
  cd /opt/tracehub/scripts
  ./validate_migration.sh | tee -a ../deployment.log
  ```
- [ ] All tests passed or acceptable warnings
- [ ] No critical failures

### Manual Validation

- [ ] Admin user can log in
- [ ] Shipment list displays correctly
- [ ] Create new test shipment
- [ ] Upload test document
- [ ] View container events
- [ ] Check notifications
- [ ] Verify EUDR compliance card

### Performance Validation

- [ ] Response time < baseline + 20%
- [ ] Database CPU < 80%
- [ ] Memory usage normal
- [ ] No slow queries (> 1000ms)

### API Validation

- [ ] Test organization endpoint:
  ```bash
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/organizations
  ```
- [ ] Expected: VIBOTAJ organization returned
- [ ] Test shipments endpoint (verify organization_id in response)

---

## Deployment Phase 5: Post-Deployment (30 minutes)

**Time:** T+40 minutes

### Monitoring Setup

- [ ] Configure alerts for:
  - Error rate > 1%
  - Response time > baseline + 50%
  - Database CPU > 90%
  - Failed queries
- [ ] Enable detailed logging for 24 hours
- [ ] Set up dashboard for organization queries

### Documentation

- [ ] Record deployment completion time
- [ ] Document any issues encountered
- [ ] Note any manual fixes applied
- [ ] Update runbook with lessons learned
- [ ] Create post-deployment summary

### Cleanup

- [ ] Keep blue environment for 24 hours (rollback option)
- [ ] Create post-migration backup:
  ```bash
  ./backup_pre_migration.sh  # Creates timestamped backup
  ```
- [ ] Verify backup completed
- [ ] Archive deployment logs

### Communication

- [ ] Notify stakeholders of successful deployment
- [ ] Update status page
- [ ] Send summary email to team
- [ ] Update project management board

---

## Post-Deployment Monitoring (24 Hours)

### Hour 1
- [ ] Monitor error logs every 5 minutes
- [ ] Check database performance metrics
- [ ] Verify user login success rate
- [ ] Confirm new shipments being created

### Hour 4
- [ ] Review slow query log
- [ ] Check index usage statistics
- [ ] Verify all API endpoints working
- [ ] Monitor database connection pool

### Hour 12
- [ ] Review error rate trends
- [ ] Check storage space usage
- [ ] Verify backup jobs running
- [ ] Analyze user feedback (if any)

### Hour 24
- [ ] Final validation check
- [ ] Review 24-hour metrics
- [ ] Decide on blue environment teardown
- [ ] Schedule post-deployment retrospective

---

## Rollback Procedures

### Level 1: Quick Rollback (If caught within 1 hour)

**Trigger:** Application errors, data inconsistencies, performance issues

```bash
# Stop
cd /opt/tracehub/backend
alembic downgrade 002

# Restart
docker-compose restart backend frontend

# Verify
curl http://localhost:8000/health
```

**Time:** 5 minutes
**Data Loss:** None (rollback is clean)

### Level 2: Blue-Green Rollback (If using blue-green)

**Trigger:** Application instability, user complaints

```bash
# Switch load balancer back to blue
sudo cp /etc/nginx/sites-available/tracehub-blue.conf \
        /etc/nginx/sites-enabled/tracehub.conf
sudo systemctl reload nginx

# Verify
curl https://tracehub.vibotaj.com/health
```

**Time:** 2 minutes
**Data Loss:** New data created after migration will be lost

### Level 3: Full Database Restore

**Trigger:** Data corruption, critical database errors

```bash
cd /opt/tracehub/scripts
./restore_from_backup.sh /backup/tracehub/tracehub_pre_sprint8_YYYYMMDD_HHMMSS.dump
```

**Time:** 15 minutes
**Data Loss:** All data created after backup

---

## Rollback Decision Tree

```
Issue Detected
    │
    ├─ Migration failed?
    │   └─ YES → Use Alembic downgrade (Level 1)
    │
    ├─ Application crashes?
    │   └─ YES → Check if blue-green → Switch to blue (Level 2)
    │             Else → Alembic downgrade (Level 1)
    │
    ├─ Data corruption?
    │   └─ YES → Restore from backup (Level 3)
    │
    ├─ Performance issues?
    │   └─ YES → Analyze first, consider indexes
    │             If critical → Rollback (Level 1)
    │
    └─ User complaints?
        └─ YES → Investigate, determine severity
                 If critical → Rollback (Level 2 or 1)
```

---

## Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| DevOps Lead | [Name] | devops@vibotaj.com | 24/7 |
| Technical Lead | [Name] | tech@vibotaj.com | Business hours |
| Database Admin | [Name] | dba@vibotaj.com | On-call |
| Product Owner | [Name] | product@vibotaj.com | Business hours |
| On-Call Engineer | [Name] | +49 XXX XXXXXXX | 24/7 |

**Slack Channels:**
- `#tracehub-deployment` - Deployment coordination
- `#tracehub-alerts` - Critical alerts
- `#tracehub-dev` - Development discussion

---

## Success Criteria

Deployment is successful when:

- [x] All 4 migrations completed without errors
- [x] All validation tests passed
- [x] VIBOTAJ organization contains all data
- [x] No NULL organization_id values
- [x] Application starts and users can log in
- [x] Performance within acceptable range (< baseline + 20%)
- [x] No critical errors in logs
- [x] Post-migration backup created
- [x] Stakeholders notified of success

---

## Final Sign-Off

| Role | Name | Signature | Date/Time |
|------|------|-----------|-----------|
| DevOps Engineer | __________ | __________ | __________ |
| Database Admin | __________ | __________ | __________ |
| Technical Lead | __________ | __________ | __________ |
| Product Owner | __________ | __________ | __________ |

**Deployment Notes:**
```
[Add any notes, issues encountered, or lessons learned here]
```

---

## Appendix: Quick Command Reference

```bash
# Backup
cd /opt/tracehub/scripts
./backup_pre_migration.sh

# Migration
cd /opt/tracehub/backend
./scripts/run_migration_sprint8.sh

# Validation
cd /opt/tracehub/scripts
./validate_migration.sh

# Rollback
cd /opt/tracehub/backend
alembic downgrade 002

# Restore
cd /opt/tracehub/scripts
./restore_from_backup.sh /backup/path/to/file.dump

# Check status
alembic current
docker ps
docker logs tracehub-backend
curl http://localhost:8000/health

# Database queries
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT name, type FROM organizations;
"
```

---

**Checklist Version:** 1.0
**Last Updated:** 2026-01-05
**Next Review:** After deployment completion
