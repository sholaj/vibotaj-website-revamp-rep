#!/bin/bash
# TraceHub Sprint 8 - Migration Execution Script
# Runs all multi-tenancy migrations with validation

set -euo pipefail

echo "========================================"
echo "TraceHub Sprint 8 Migration"
echo "Multi-Tenancy Database Upgrade"
echo "========================================"
echo "Start time: $(date)"
echo ""

# Check if running in correct directory
if [ ! -f "alembic.ini" ]; then
  echo "Error: alembic.ini not found. Please run from backend directory."
  exit 1
fi

# Check database connection
echo "Checking database connection..."
if ! docker exec tracehub-db pg_isready -U tracehub > /dev/null 2>&1; then
  echo "Error: Database is not ready"
  exit 1
fi
echo "✓ Database connection OK"

# Get current Alembic version
CURRENT_VERSION=$(alembic current | grep -oP '\w+' | tail -1)
echo "Current Alembic version: ${CURRENT_VERSION}"

# Confirm migration
read -p "Ready to run Sprint 8 migrations (003 -> 006)? (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
  echo "Migration cancelled."
  exit 0
fi

echo ""
echo "========================================"
echo "Starting migration sequence..."
echo "========================================"

# =================================================================
# Migration 003: Create multi-tenancy tables
# =================================================================
echo ""
echo "Migration 003: Create multi-tenancy tables"
echo "Expected time: 1-2 seconds"
echo "----------------------------------------"
alembic upgrade 003

# Verify tables created
TABLE_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.tables
  WHERE table_schema = 'public'
    AND table_name IN ('organizations', 'org_memberships', 'invitations');
")

if [ "${TABLE_COUNT}" -eq 3 ]; then
  echo "✓ Migration 003 completed successfully"
else
  echo "✗ Migration 003 failed: Expected 3 tables, found ${TABLE_COUNT}"
  exit 1
fi

# =================================================================
# Migration 004: Add organization_id columns
# =================================================================
echo ""
echo "Migration 004: Add organization_id columns"
echo "Expected time: 5-10 seconds"
echo "----------------------------------------"
alembic upgrade 004

# Verify columns added
COLUMN_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE column_name = 'organization_id' AND table_schema = 'public';
")

if [ "${COLUMN_COUNT}" -eq 9 ]; then
  echo "✓ Migration 004 completed successfully (9 columns added)"
else
  echo "✗ Migration 004 failed: Expected 9 columns, found ${COLUMN_COUNT}"
  exit 1
fi

# =================================================================
# Migration 005: Data migration to VIBOTAJ
# =================================================================
echo ""
echo "Migration 005: Data migration to VIBOTAJ organization"
echo "Expected time: 10-15 minutes (depends on data volume)"
echo "----------------------------------------"
echo "⚠ This is the CRITICAL data migration step"
echo ""

# Show current data counts
echo "Current data counts:"
docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT 'Users: ' || COUNT(*) FROM users
  UNION ALL
  SELECT 'Shipments: ' || COUNT(*) FROM shipments
  UNION ALL
  SELECT 'Documents: ' || COUNT(*) FROM documents;
"

echo ""
read -p "Proceed with data migration? (yes/no): " CONFIRM_DATA
if [ "${CONFIRM_DATA}" != "yes" ]; then
  echo "Migration paused. Rollback with: alembic downgrade 004"
  exit 0
fi

# Run data migration
alembic upgrade 005

# Verify data migration
echo ""
echo "Verifying data migration..."
NULL_USERS=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*) FROM users WHERE organization_id IS NULL;
")
NULL_SHIPMENTS=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*) FROM shipments WHERE organization_id IS NULL;
")

if [ "${NULL_USERS}" -eq 0 ] && [ "${NULL_SHIPMENTS}" -eq 0 ]; then
  echo "✓ Migration 005 completed successfully"
  echo "✓ All users and shipments migrated to VIBOTAJ organization"
else
  echo "✗ Migration 005 failed: Found NULL organization_id values"
  echo "  Users with NULL: ${NULL_USERS}"
  echo "  Shipments with NULL: ${NULL_SHIPMENTS}"
  echo "Rolling back..."
  alembic downgrade 004
  exit 1
fi

# =================================================================
# Migration 006: Add constraints and indexes
# =================================================================
echo ""
echo "Migration 006: Add constraints and indexes"
echo "Expected time: 5-10 seconds"
echo "----------------------------------------"
alembic upgrade 006

# Verify constraints
FK_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE constraint_type = 'FOREIGN KEY'
    AND constraint_name LIKE 'fk_%_organization_id';
")

if [ "${FK_COUNT}" -eq 9 ]; then
  echo "✓ Migration 006 completed successfully"
else
  echo "⚠ Warning: Expected 9 foreign keys, found ${FK_COUNT}"
fi

# =================================================================
# Final Verification
# =================================================================
echo ""
echo "========================================"
echo "Final Verification"
echo "========================================"

# Check current version
FINAL_VERSION=$(alembic current | grep -oP '\w+' | tail -1)
echo "Final Alembic version: ${FINAL_VERSION}"

# Show organization summary
echo ""
echo "Organization Summary:"
docker exec tracehub-db psql -U tracehub -d tracehub -c "
  SELECT
    o.name AS organization,
    COUNT(DISTINCT u.id) AS users,
    COUNT(DISTINCT s.id) AS shipments,
    COUNT(DISTINCT d.id) AS documents
  FROM organizations o
  LEFT JOIN users u ON u.organization_id = o.id
  LEFT JOIN shipments s ON s.organization_id = o.id
  LEFT JOIN documents d ON d.organization_id = o.id
  GROUP BY o.name;
"

# Check for orphaned records
echo ""
echo "Checking for orphaned records..."
ORPHANED=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*) FROM users WHERE organization_id NOT IN (SELECT id FROM organizations)
  UNION ALL
  SELECT COUNT(*) FROM shipments WHERE organization_id NOT IN (SELECT id FROM organizations);
" | awk '{s+=$1} END {print s}')

if [ "${ORPHANED}" -eq 0 ]; then
  echo "✓ No orphaned records found"
else
  echo "⚠ Warning: Found ${ORPHANED} orphaned records"
fi

echo ""
echo "========================================"
echo "✓ Sprint 8 Migration Completed!"
echo "========================================"
echo "End time: $(date)"
echo ""
echo "Next steps:"
echo "1. Restart application: docker-compose restart backend"
echo "2. Run smoke tests: pytest tests/integration/test_multitenancy_smoke.py"
echo "3. Monitor logs: docker logs -f tracehub-backend"
echo "4. Verify API: curl http://localhost:8000/api/v1/organizations"
echo ""
echo "To rollback: alembic downgrade 002"
echo ""
