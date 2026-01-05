# TraceHub Migration Scripts

This directory contains scripts for database backup, migration, restore, and validation.

## Scripts Overview

| Script | Purpose | Usage | Estimated Time |
|--------|---------|-------|----------------|
| `backup_pre_migration.sh` | Create pre-migration backup with verification | `./backup_pre_migration.sh` | 2-5 minutes |
| `restore_from_backup.sh` | Restore database from backup file | `./restore_from_backup.sh /path/to/backup.dump` | 10-15 minutes |
| `run_migration_sprint8.sh` | Execute Sprint 8 migrations (003-006) | `cd ../backend && ./scripts/run_migration_sprint8.sh` | 15-20 minutes |
| `validate_migration.sh` | Validate migration completion | `./validate_migration.sh` | 1 minute |

---

## Quick Start

### 1. Create Backup Before Migration

```bash
cd /opt/tracehub/scripts
./backup_pre_migration.sh
```

**Output:**
```
✓ Backup created: /backup/tracehub/tracehub_pre_sprint8_20260106_140000.dump (15M)
✓ Backup verified successfully (23 shipments restored)
✓ Backup manifest created
```

**Files Created:**
- `/backup/tracehub/tracehub_pre_sprint8_YYYYMMDD_HHMMSS.dump` - Database backup
- `/backup/tracehub/.env.YYYYMMDD_HHMMSS` - Environment config backup
- `/backup/tracehub/docker-compose.yml.YYYYMMDD_HHMMSS` - Docker config backup
- `/backup/tracehub/manifest_YYYYMMDD_HHMMSS.txt` - Backup manifest with table counts

---

### 2. Run Migration

```bash
cd /opt/tracehub/backend
./scripts/run_migration_sprint8.sh
```

**Interactive Steps:**
1. Confirms database connection
2. Shows current Alembic version
3. Prompts for confirmation before each major step
4. Runs migrations 003 → 004 → 005 → 006
5. Validates data at each step
6. Shows final summary

**Output Example:**
```
========================================
TraceHub Sprint 8 Migration
========================================
Current Alembic version: 002
Ready to run Sprint 8 migrations (003 -> 006)? (yes/no): yes

Migration 003: Create multi-tenancy tables
✓ Migration 003 completed successfully

Migration 004: Add organization_id columns
✓ Migration 004 completed successfully (9 columns added)

Migration 005: Data migration to VIBOTAJ organization
Step 1/11: Creating VIBOTAJ organization...
✓ Created VIBOTAJ organization (ID: 00000000-0000-0000-0000-000000000001)
[... data migration steps ...]
✓ Migration 005 completed successfully

Migration 006: Add constraints and indexes
✓ Migration 006 completed successfully

✓ Sprint 8 Migration Completed!
```

---

### 3. Validate Migration

```bash
cd /opt/tracehub/scripts
./validate_migration.sh
```

**Runs 12 validation tests:**
1. Multi-tenancy tables exist
2. organization_id columns added
3. VIBOTAJ organization exists
4. No NULL organization_id values
5. Foreign key constraints
6. NOT NULL constraints
7. Composite indexes
8. Data migrated to VIBOTAJ
9. Organization memberships
10. No orphaned records
11. Alembic version
12. Unique constraints

**Output Example:**
```
✓ PASS: Multi-tenancy tables exist (3/3)
✓ PASS: organization_id columns added (9/9)
✓ PASS: VIBOTAJ organization exists
✓ PASS: No NULL organization_id values found
✓ PASS: Foreign key constraints added (9/9)
...
========================================
Validation Summary
========================================
Passed:   12
Warnings: 0
Failed:   0

✓ All tests passed! Migration successful.
```

---

### 4. Restore from Backup (if needed)

```bash
cd /opt/tracehub/scripts
./restore_from_backup.sh /backup/tracehub/tracehub_pre_sprint8_20260106_140000.dump
```

**Interactive Steps:**
1. Confirms backup file exists
2. Prompts for confirmation (destructive operation)
3. Stops application
4. Creates safety backup of current state
5. Drops and recreates database
6. Restores from backup
7. Verifies restore
8. Restarts application

**Output Example:**
```
⚠ WARNING: This will OVERWRITE the current database. Continue? (yes/no): yes

Step 1/7: Stopping application...
✓ Application stopped

Step 2/7: Starting database...
✓ Database is ready

Step 3/7: Creating safety backup...
✓ Safety backup created: /backup/tracehub/tracehub_before_restore_20260106_150000.dump

[... restore steps ...]

✓ Restore completed successfully!
Restored from: /backup/tracehub/tracehub_pre_sprint8_20260106_140000.dump
Users: 45 (was 45)
Shipments: 23 (was 23)
```

---

## Script Details

### backup_pre_migration.sh

**Purpose:** Create comprehensive backup before migration

**Features:**
- Creates PostgreSQL custom format dump (compressed)
- Verifies backup by restoring to temporary database
- Backs up configuration files (.env, docker-compose.yml)
- Creates manifest with table counts and git info
- Prints summary with restore instructions

**Environment Variables:**
- `BACKUP_DIR` - Backup directory (default: `/backup/tracehub`)

**Exit Codes:**
- `0` - Success
- `1` - Backup failed or verification failed

**Example Usage:**
```bash
# Default backup location
./backup_pre_migration.sh

# Custom backup location
BACKUP_DIR=/mnt/backups ./backup_pre_migration.sh
```

---

### restore_from_backup.sh

**Purpose:** Restore database from backup with safety checks

**Features:**
- Safety backup of current database before restore
- Verification of restored data
- Automatic fallback to safety backup if restore fails
- Database recreation (clean restore)
- Application restart with health check

**Arguments:**
- `$1` - Path to backup file (required)

**Exit Codes:**
- `0` - Success
- `1` - No backup file specified, file not found, or restore failed

**Example Usage:**
```bash
# List available backups
ls -lh /backup/tracehub/*.dump

# Restore specific backup
./restore_from_backup.sh /backup/tracehub/tracehub_pre_sprint8_20260106_140000.dump
```

---

### run_migration_sprint8.sh

**Purpose:** Execute Sprint 8 migrations with validation

**Features:**
- Pre-flight checks (database connection, Alembic setup)
- Interactive confirmation prompts
- Step-by-step migration execution
- Data validation at each step
- Final summary with organization stats
- Automatic rollback on validation failure

**Requirements:**
- Must be run from `/opt/tracehub/backend` directory
- Database must be accessible
- Alembic must be configured

**Exit Codes:**
- `0` - Success
- `1` - Pre-flight check failed, migration failed, or validation failed

**Example Usage:**
```bash
cd /opt/tracehub/backend
./scripts/run_migration_sprint8.sh
```

---

### validate_migration.sh

**Purpose:** Validate migration state after completion

**Features:**
- 12 comprehensive validation tests
- Color-coded output (green=pass, yellow=warn, red=fail)
- Detailed failure messages
- Summary with pass/warn/fail counts
- Non-zero exit code on failure (CI/CD friendly)

**Exit Codes:**
- `0` - All tests passed (or only warnings)
- `1` - One or more tests failed

**Example Usage:**
```bash
# Run validation
./validate_migration.sh

# Use in CI/CD
if ./validate_migration.sh; then
  echo "Migration validated successfully"
else
  echo "Migration validation failed - rolling back"
  alembic downgrade 002
fi
```

---

## Troubleshooting

### Problem: backup_pre_migration.sh fails with permission denied

**Solution:**
```bash
# Make script executable
chmod +x /opt/tracehub/scripts/*.sh

# Or run with bash
bash /opt/tracehub/scripts/backup_pre_migration.sh
```

### Problem: Backup verification fails

**Solution:**
```bash
# Check if database is running
docker ps | grep tracehub-db

# Check database logs
docker logs tracehub-db

# Test database connection
docker exec tracehub-db psql -U tracehub -d tracehub -c "SELECT 1;"
```

### Problem: Migration script hangs during Migration 005

**Solution:**
```bash
# Check backend logs
docker logs -f tracehub-backend

# Check database queries
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT pid, query, state, wait_event_type
  FROM pg_stat_activity
  WHERE datname = 'tracehub';
"

# If stuck, cancel migration and rollback
# Press Ctrl+C, then:
alembic downgrade 004
```

### Problem: restore_from_backup.sh fails with "relation already exists"

**Solution:**
```bash
# These warnings are normal during restore
# Restore uses DROP DATABASE / CREATE DATABASE to ensure clean restore
# Warnings like "relation already exists" are informational only

# If restore truly fails, check the safety backup was created:
ls -lh /backup/tracehub/tracehub_before_restore_*.dump
```

### Problem: validate_migration.sh shows warnings

**Solution:**
```bash
# Warnings typically mean migration is incomplete
# Check Alembic version:
docker exec tracehub-backend alembic current

# If not at version 006, continue migration:
docker exec tracehub-backend alembic upgrade head

# Re-run validation
./validate_migration.sh
```

---

## Best Practices

1. **Always create backup before migration**
   ```bash
   ./backup_pre_migration.sh
   ```

2. **Test restore procedure before production migration**
   ```bash
   # In staging environment
   ./restore_from_backup.sh /backup/latest.dump
   ```

3. **Validate migration after completion**
   ```bash
   ./validate_migration.sh
   ```

4. **Keep backups for 30 days**
   ```bash
   # Add to crontab
   0 2 * * * find /backup/tracehub -name "*.dump" -mtime +30 -delete
   ```

5. **Monitor migration progress**
   ```bash
   # In separate terminal
   docker logs -f tracehub-backend
   ```

6. **Document migration execution**
   ```bash
   # Save migration output
   ./run_migration_sprint8.sh 2>&1 | tee migration_$(date +%Y%m%d_%H%M%S).log
   ```

---

## Maintenance

### Scheduled Backups

Add to crontab for automated backups:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/tracehub/scripts/backup_pre_migration.sh >> /var/log/tracehub-backup.log 2>&1

# Weekly backup with retention (keep 4 weeks)
0 3 * * 0 /opt/tracehub/scripts/backup_pre_migration.sh && find /backup/tracehub -name "*.dump" -mtime +28 -delete
```

### Backup Rotation

```bash
#!/bin/bash
# keep-recent-backups.sh
# Keeps only the 10 most recent backups

cd /backup/tracehub
ls -t tracehub_*.dump | tail -n +11 | xargs -r rm
```

---

## See Also

- **Full Migration Plan:** `/tracehub/MIGRATION_PLAN_SPRINT8.md`
- **Quick Start Guide:** `/tracehub/MIGRATION_QUICKSTART.md`
- **Executive Summary:** `/tracehub/SPRINT8_MIGRATION_SUMMARY.md`
- **Alembic Migrations:** `/tracehub/backend/alembic/versions/`

---

**Last Updated:** 2026-01-05
**Maintained By:** DevOps Team
