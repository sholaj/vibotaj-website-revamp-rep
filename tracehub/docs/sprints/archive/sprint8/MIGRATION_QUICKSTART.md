# TraceHub Sprint 8 Migration - Quick Start Guide

**Version:** 1.0
**Date:** 2026-01-05
**Estimated Time:** 20-30 minutes
**Risk Level:** LOW (with rollback available)

---

## Pre-Flight Checklist

Before starting the migration, ensure:

- [ ] Database backup created (see Backup section)
- [ ] All users notified of maintenance window
- [ ] Git repository is on `main` branch and up-to-date
- [ ] Docker containers are running
- [ ] You have database access credentials
- [ ] Rollback script tested in development

---

## Quick Migration Steps

### 1. Create Backup (5 minutes)

```bash
cd /opt/tracehub
./scripts/backup_pre_migration.sh
```

Expected output:
```
✓ Backup created: /backup/tracehub/tracehub_pre_sprint8_YYYYMMDD_HHMMSS.dump
✓ Backup verified successfully
```

### 2. Run Migrations (15-20 minutes)

```bash
cd /opt/tracehub/backend
./scripts/run_migration_sprint8.sh
```

The script will:
- Migration 003: Create multi-tenancy tables (2 seconds)
- Migration 004: Add organization_id columns (10 seconds)
- Migration 005: Migrate data to VIBOTAJ (10-15 minutes)
- Migration 006: Add constraints and indexes (10 seconds)

### 3. Restart Application (2 minutes)

```bash
cd /opt/tracehub
docker-compose restart backend
docker-compose restart frontend
```

### 4. Verify Migration (3 minutes)

```bash
# Check database
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT o.name, COUNT(s.id) AS shipments
  FROM organizations o
  LEFT JOIN shipments s ON s.organization_id = o.id
  GROUP BY o.name;
"

# Check API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/organizations
```

Expected: VIBOTAJ organization with all shipments

---

## Rollback (if needed)

### Quick Rollback (5 minutes)

```bash
cd /opt/tracehub/backend
alembic downgrade 002
docker-compose restart backend
```

### Full Restore from Backup (10 minutes)

```bash
cd /opt/tracehub
./scripts/restore_from_backup.sh /backup/tracehub/tracehub_pre_sprint8_YYYYMMDD_HHMMSS.dump
```

---

## Post-Migration Validation

### Automated Tests
```bash
cd /opt/tracehub/backend
pytest tests/integration/test_multitenancy_smoke.py -v
```

### Manual Checks
1. Log in as admin user
2. View shipments list (should show all shipments)
3. Create new shipment (should auto-assign to VIBOTAJ)
4. Check notifications (should work as before)
5. View documents (should display correctly)

---

## Troubleshooting

### Problem: Migration 005 fails with NULL values
**Solution:**
```bash
# Check which tables have NULL organization_id
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT 'users' AS table, COUNT(*) FROM users WHERE organization_id IS NULL
  UNION ALL
  SELECT 'shipments', COUNT(*) FROM shipments WHERE organization_id IS NULL;
"

# Rollback and investigate
alembic downgrade 004
```

### Problem: Foreign key constraint violation
**Solution:**
```bash
# This means Migration 005 didn't complete properly
# Rollback to 004 and re-run 005
alembic downgrade 004
alembic upgrade 005
```

### Problem: Application won't start after migration
**Solution:**
```bash
# Check logs
docker logs tracehub-backend

# Common causes:
# 1. Code not updated to use organization context
# 2. Missing environment variables
# 3. Database connection issues

# Quick fix: Restart containers
docker-compose restart
```

### Problem: Performance degradation
**Solution:**
```bash
# Check if indexes were created
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT tablename, indexname
  FROM pg_indexes
  WHERE indexname LIKE '%organization_id%';
"

# Expected: ~25 indexes with organization_id

# If missing, re-run migration 006
alembic downgrade 005
alembic upgrade 006
```

---

## Migration File Locations

```
tracehub/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       ├── 20260106_0003_create_multitenancy_tables.py
│   │       ├── 20260106_0004_add_organization_id_columns.py
│   │       ├── 20260106_0005_migrate_data_to_vibotaj_org.py
│   │       └── 20260106_0006_add_multitenancy_constraints.py
│   └── scripts/
│       └── run_migration_sprint8.sh
├── scripts/
│   ├── backup_pre_migration.sh
│   └── restore_from_backup.sh
├── MIGRATION_PLAN_SPRINT8.md (Full documentation)
└── MIGRATION_QUICKSTART.md (This file)
```

---

## Key Commands Reference

```bash
# Backup
./scripts/backup_pre_migration.sh

# Run migration
cd backend && ./scripts/run_migration_sprint8.sh

# Check current version
alembic current

# Rollback to specific version
alembic downgrade 002

# Full restore
./scripts/restore_from_backup.sh /backup/path/to/file.dump

# Verify data
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT name, type FROM organizations;
"

# Check for NULL values
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT COUNT(*) FROM shipments WHERE organization_id IS NULL;
"
```

---

## Success Criteria

Migration is successful when:
- [x] All tables have `organization_id` column
- [x] VIBOTAJ organization exists
- [x] All users belong to VIBOTAJ organization
- [x] All shipments have `organization_id = VIBOTAJ`
- [x] NO NULL `organization_id` values
- [x] Foreign key constraints in place
- [x] Composite indexes created
- [x] Application starts without errors
- [x] Users can log in and view shipments
- [x] New shipments are created with organization context

---

## Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Pre-migration | 10 min | Backup + verification |
| Migration 003 | 2 sec | Create tables |
| Migration 004 | 10 sec | Add columns |
| Migration 005 | 10-15 min | Data migration |
| Migration 006 | 10 sec | Add constraints |
| Application restart | 2 min | Restart containers |
| Validation | 5 min | Smoke tests |
| **Total** | **20-30 min** | End-to-end |

---

## Support Contacts

- **DevOps Lead:** devops@vibotaj.com
- **On-Call Engineer:** +49 XXX XXXXXXX
- **Slack Channel:** #tracehub-migration
- **Documentation:** See MIGRATION_PLAN_SPRINT8.md

---

## Additional Resources

- **Full Migration Plan:** `/tracehub/MIGRATION_PLAN_SPRINT8.md`
- **Architecture Docs:** `/tracehub/docs/architecture/multi-tenancy.md`
- **API Changes:** `/tracehub/docs/api/v1.3-changes.md`
- **Testing Guide:** `/tracehub/tests/integration/README.md`

---

**Last Updated:** 2026-01-05
**Next Review:** After first production deployment
