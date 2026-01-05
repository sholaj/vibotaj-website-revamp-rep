#!/bin/bash
# TraceHub Sprint 8 - Pre-Migration Backup Script
# Creates full database backup and verifies integrity

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/backup/tracehub}"
BACKUP_FILE="${BACKUP_DIR}/tracehub_pre_sprint8_${TIMESTAMP}.dump"

echo "========================================"
echo "TraceHub Pre-Migration Backup"
echo "========================================"
echo "Timestamp: $(date)"
echo "Backup location: ${BACKUP_FILE}"
echo ""

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Dump database
echo "Creating database backup..."
docker exec tracehub-db pg_dump -U tracehub -Fc tracehub > "${BACKUP_FILE}"

# Verify backup
if [ -f "${BACKUP_FILE}" ]; then
  SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
  echo "✓ Backup created: ${BACKUP_FILE} (${SIZE})"

  # Test restore to temporary database
  echo "Verifying backup integrity..."
  docker exec tracehub-db psql -U tracehub -c "CREATE DATABASE tracehub_verify;" 2>/dev/null || true
  docker exec -i tracehub-db pg_restore -U tracehub -d tracehub_verify < "${BACKUP_FILE}" 2>&1 | grep -v "already exists" || true

  # Check restored data
  RESTORED_SHIPMENTS=$(docker exec tracehub-db psql -U tracehub -d tracehub_verify -tAc "SELECT COUNT(*) FROM shipments;" 2>/dev/null || echo "0")

  # Cleanup verify database
  docker exec tracehub-db psql -U tracehub -c "DROP DATABASE IF EXISTS tracehub_verify;"

  if [ "${RESTORED_SHIPMENTS}" -gt 0 ]; then
    echo "✓ Backup verified successfully (${RESTORED_SHIPMENTS} shipments restored)"
  else
    echo "⚠ Warning: Backup verification failed or no data found"
  fi
else
  echo "✗ Backup failed!"
  exit 1
fi

# Backup application config
echo "Backing up configuration files..."
if [ -f /opt/tracehub/.env ]; then
  cp /opt/tracehub/.env "${BACKUP_DIR}/.env.${TIMESTAMP}"
  echo "✓ Backed up .env"
fi

if [ -f /opt/tracehub/docker-compose.yml ]; then
  cp /opt/tracehub/docker-compose.yml "${BACKUP_DIR}/docker-compose.yml.${TIMESTAMP}"
  echo "✓ Backed up docker-compose.yml"
fi

# Create backup manifest
echo "Creating backup manifest..."
cat > "${BACKUP_DIR}/manifest_${TIMESTAMP}.txt" <<EOF
============================================
TraceHub Pre-Sprint8 Backup Manifest
============================================

Backup Date: $(date)
Backup File: ${BACKUP_FILE}
Backup Size: $(du -h "${BACKUP_FILE}" | cut -f1)

Database Information:
--------------------
Database Version: $(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "SELECT version();" 2>/dev/null | head -1)
Alembic Version: $(docker exec tracehub-backend alembic current 2>/dev/null || echo "N/A")

Git Information:
---------------
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")
Git Tag: $(git describe --tags --always 2>/dev/null || echo "N/A")
Git Branch: $(git branch --show-current 2>/dev/null || echo "N/A")

Table Counts:
-------------
$(docker exec tracehub-db psql -U tracehub -d tracehub -tAc "
  SELECT 'users: ' || COUNT(*) FROM users
  UNION ALL
  SELECT 'shipments: ' || COUNT(*) FROM shipments
  UNION ALL
  SELECT 'documents: ' || COUNT(*) FROM documents
  UNION ALL
  SELECT 'products: ' || COUNT(*) FROM products
  UNION ALL
  SELECT 'parties: ' || COUNT(*) FROM parties
  UNION ALL
  SELECT 'origins: ' || COUNT(*) FROM origins
  UNION ALL
  SELECT 'container_events: ' || COUNT(*) FROM container_events
  UNION ALL
  SELECT 'notifications: ' || COUNT(*) FROM notifications
  UNION ALL
  SELECT 'audit_logs: ' || COUNT(*) FROM audit_logs;
" 2>/dev/null || echo "Error retrieving table counts")

============================================
EOF

echo "✓ Backup manifest created"

# Display manifest
cat "${BACKUP_DIR}/manifest_${TIMESTAMP}.txt"

echo ""
echo "========================================"
echo "✓ Backup completed successfully!"
echo "========================================"
echo "Backup location: ${BACKUP_FILE}"
echo "Manifest: ${BACKUP_DIR}/manifest_${TIMESTAMP}.txt"
echo ""
echo "To restore from this backup, run:"
echo "  ./scripts/restore_from_backup.sh ${BACKUP_FILE}"
echo ""
