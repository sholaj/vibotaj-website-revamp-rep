#!/bin/bash
# TraceHub Sprint 8 - Migration Validation Script
# Validates database state after migration

set -euo pipefail

echo "========================================"
echo "TraceHub Migration Validation"
echo "========================================"
echo "Timestamp: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
  echo -e "${GREEN}✓ PASS${NC}: $1"
  ((PASSED++))
}

fail() {
  echo -e "${RED}✗ FAIL${NC}: $1"
  ((FAILED++))
}

warn() {
  echo -e "${YELLOW}⚠ WARN${NC}: $1"
  ((WARNINGS++))
}

# Test 1: Check multi-tenancy tables exist
echo "Test 1: Verify multi-tenancy tables exist"
TABLE_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.tables
  WHERE table_schema = 'public'
    AND table_name IN ('organizations', 'org_memberships', 'invitations');
" 2>/dev/null || echo "0")

if [ "${TABLE_COUNT}" -eq 3 ]; then
  pass "Multi-tenancy tables exist (3/3)"
else
  fail "Multi-tenancy tables missing (${TABLE_COUNT}/3)"
fi

# Test 2: Check organization_id columns
echo ""
echo "Test 2: Verify organization_id columns added"
COLUMN_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE column_name = 'organization_id'
    AND table_schema = 'public';
" 2>/dev/null || echo "0")

if [ "${COLUMN_COUNT}" -eq 9 ]; then
  pass "organization_id columns added (9/9)"
else
  fail "organization_id columns missing (${COLUMN_COUNT}/9)"
fi

# Test 3: Check VIBOTAJ organization
echo ""
echo "Test 3: Verify VIBOTAJ organization exists"
ORG_EXISTS=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*) FROM organizations WHERE slug = 'vibotaj';
" 2>/dev/null || echo "0")

if [ "${ORG_EXISTS}" -eq 1 ]; then
  pass "VIBOTAJ organization exists"
else
  fail "VIBOTAJ organization not found"
fi

# Test 4: Check for NULL organization_id values
echo ""
echo "Test 4: Verify NO NULL organization_id values"
NULL_COUNTS=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT
    (SELECT COUNT(*) FROM users WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM shipments WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM documents WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM products WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM parties WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM origins WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM container_events WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM notifications WHERE organization_id IS NULL) +
    (SELECT COUNT(*) FROM audit_logs WHERE organization_id IS NULL) AS total_nulls;
" 2>/dev/null || echo "999")

if [ "${NULL_COUNTS}" -eq 0 ]; then
  pass "No NULL organization_id values found"
else
  fail "Found ${NULL_COUNTS} NULL organization_id values"
fi

# Test 5: Check foreign key constraints
echo ""
echo "Test 5: Verify foreign key constraints"
FK_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE constraint_type = 'FOREIGN KEY'
    AND constraint_name LIKE 'fk_%_organization_id';
" 2>/dev/null || echo "0")

if [ "${FK_COUNT}" -eq 9 ]; then
  pass "Foreign key constraints added (9/9)"
else
  warn "Foreign key constraints (${FK_COUNT}/9) - Migration 006 may not be complete"
fi

# Test 6: Check NOT NULL constraints
echo ""
echo "Test 6: Verify NOT NULL constraints"
NULLABLE_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE column_name = 'organization_id'
    AND table_schema = 'public'
    AND is_nullable = 'YES';
" 2>/dev/null || echo "9")

if [ "${NULLABLE_COUNT}" -eq 0 ]; then
  pass "All organization_id columns are NOT NULL"
else
  warn "Found ${NULLABLE_COUNT} nullable organization_id columns - Migration 006 may not be complete"
fi

# Test 7: Check composite indexes
echo ""
echo "Test 7: Verify composite indexes created"
INDEX_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM pg_indexes
  WHERE indexname LIKE 'ix_%_organization_id_%';
" 2>/dev/null || echo "0")

if [ "${INDEX_COUNT}" -ge 15 ]; then
  pass "Composite indexes created (${INDEX_COUNT} found)"
elif [ "${INDEX_COUNT}" -gt 0 ]; then
  warn "Partial composite indexes (${INDEX_COUNT} found, expected 16+)"
else
  fail "No composite indexes found"
fi

# Test 8: Check data migration
echo ""
echo "Test 8: Verify data migrated to VIBOTAJ"
USER_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM users
  WHERE organization_id = '00000000-0000-0000-0000-000000000001';
" 2>/dev/null || echo "0")

SHIPMENT_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM shipments
  WHERE organization_id = '00000000-0000-0000-0000-000000000001';
" 2>/dev/null || echo "0")

if [ "${USER_COUNT}" -gt 0 ] && [ "${SHIPMENT_COUNT}" -gt 0 ]; then
  pass "Data migrated to VIBOTAJ (${USER_COUNT} users, ${SHIPMENT_COUNT} shipments)"
elif [ "${USER_COUNT}" -eq 0 ] && [ "${SHIPMENT_COUNT}" -eq 0 ]; then
  warn "No data in VIBOTAJ organization (fresh database?)"
else
  fail "Partial data migration (${USER_COUNT} users, ${SHIPMENT_COUNT} shipments)"
fi

# Test 9: Check org_memberships
echo ""
echo "Test 9: Verify organization memberships"
MEMBERSHIP_COUNT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM org_memberships
  WHERE organization_id = '00000000-0000-0000-0000-000000000001';
" 2>/dev/null || echo "0")

if [ "${MEMBERSHIP_COUNT}" -eq "${USER_COUNT}" ]; then
  pass "Organization memberships created (${MEMBERSHIP_COUNT} memberships)"
elif [ "${MEMBERSHIP_COUNT}" -gt 0 ]; then
  warn "Partial memberships (${MEMBERSHIP_COUNT} memberships, ${USER_COUNT} users)"
else
  warn "No organization memberships found"
fi

# Test 10: Check for orphaned records
echo ""
echo "Test 10: Check for orphaned records"
ORPHANED=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT
    (SELECT COUNT(*) FROM users WHERE organization_id NOT IN (SELECT id FROM organizations)) +
    (SELECT COUNT(*) FROM shipments WHERE organization_id NOT IN (SELECT id FROM organizations)) AS total;
" 2>/dev/null || echo "999")

if [ "${ORPHANED}" -eq 0 ]; then
  pass "No orphaned records found"
else
  fail "Found ${ORPHANED} orphaned records"
fi

# Test 11: Check Alembic version
echo ""
echo "Test 11: Verify Alembic version"
ALEMBIC_VERSION=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT version_num FROM alembic_version;
" 2>/dev/null || echo "unknown")

if [ "${ALEMBIC_VERSION}" = "006" ]; then
  pass "Alembic at version 006 (migrations complete)"
elif [ "${ALEMBIC_VERSION}" = "005" ]; then
  warn "Alembic at version 005 (Migration 006 not applied)"
elif [ "${ALEMBIC_VERSION}" = "004" ]; then
  warn "Alembic at version 004 (Migrations 005-006 not applied)"
elif [ "${ALEMBIC_VERSION}" = "003" ]; then
  warn "Alembic at version 003 (Migrations 004-006 not applied)"
else
  fail "Alembic at version ${ALEMBIC_VERSION} (expected 006)"
fi

# Test 12: Check unique constraints
echo ""
echo "Test 12: Verify unique constraints"
UNIQUE_CONSTRAINT=$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE constraint_type = 'UNIQUE'
    AND constraint_name = 'uq_shipments_organization_reference';
" 2>/dev/null || echo "0")

if [ "${UNIQUE_CONSTRAINT}" -eq 1 ]; then
  pass "Unique constraint on shipment reference exists"
else
  warn "Unique constraint on shipment reference not found"
fi

# Summary
echo ""
echo "========================================"
echo "Validation Summary"
echo "========================================"
echo -e "${GREEN}Passed:${NC}   ${PASSED}"
echo -e "${YELLOW}Warnings:${NC} ${WARNINGS}"
echo -e "${RED}Failed:${NC}   ${FAILED}"
echo ""

if [ "${FAILED}" -eq 0 ] && [ "${WARNINGS}" -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed! Migration successful.${NC}"
  exit 0
elif [ "${FAILED}" -eq 0 ]; then
  echo -e "${YELLOW}⚠ All tests passed with warnings. Review warnings above.${NC}"
  exit 0
else
  echo -e "${RED}✗ Some tests failed. Migration incomplete or rolled back.${NC}"
  echo ""
  echo "Next steps:"
  echo "1. Check Alembic version: alembic current"
  echo "2. Review migration logs"
  echo "3. Consider rollback: alembic downgrade 002"
  exit 1
fi
