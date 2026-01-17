#!/bin/bash
# Flush and Reimport Staging Shipments
#
# This script:
# 1. Creates a backup of the staging database
# 2. Flushes shipment-related tables (preserving users, orgs, etc.)
# 3. Re-imports historic shipments using create_historic_shipments.py
#
# Usage: Run this script on the VPS server in the staging directory
#   cd /home/tracehub/staging && bash scripts/flush_and_reimport_staging.sh

set -e

echo "=============================================="
echo "TraceHub Staging - Flush and Reimport"
echo "=============================================="
echo "Date: $(date)"
echo ""

# Configuration
BACKUP_DIR="/home/tracehub/staging/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/staging_backup_before_flush_${TIMESTAMP}.sql"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "[1/5] Creating backup..."
docker exec tracehub-db-staging pg_dump -U tracehub tracehub > "$BACKUP_FILE"
echo "  Backup saved to: $BACKUP_FILE"
echo "  Size: $(ls -lh "$BACKUP_FILE" | awk '{print $5}')"

echo ""
echo "[2/5] Flushing shipment-related data..."
echo "  Tables to clear: shipments, products, documents, document_contents,"
echo "                   origins, tracking_events, containers, compliance_results"

docker exec -i tracehub-db-staging psql -U tracehub tracehub << 'EOF'
BEGIN;

-- Disable foreign key checks temporarily
SET CONSTRAINTS ALL DEFERRED;

-- Clear child tables first (order matters for FK constraints)
DELETE FROM compliance_results;
DELETE FROM document_contents;
DELETE FROM documents;
DELETE FROM tracking_events;
DELETE FROM containers;
DELETE FROM origins;
DELETE FROM products;
DELETE FROM shipments;

-- Reset sequences (optional - for clean IDs)
-- ALTER SEQUENCE shipments_id_seq RESTART WITH 1;

COMMIT;

-- Show remaining row counts
SELECT 'shipments' as table_name, COUNT(*) as count FROM shipments
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'containers', COUNT(*) FROM containers;
EOF

echo "  Done. All shipment data cleared."

echo ""
echo "[3/5] Verifying flush..."
docker exec tracehub-db-staging psql -U tracehub tracehub -c "SELECT 'shipments' as table_name, COUNT(*) FROM shipments;"

echo ""
echo "[4/5] Clearing uploaded document files..."
# Keep directory structure but remove files
find /home/tracehub/staging/uploads -type f -name "*.pdf" -delete 2>/dev/null || true
find /home/tracehub/staging/uploads -type f -name "*.PDF" -delete 2>/dev/null || true
echo "  Document files cleared."

echo ""
echo "[5/5] Re-importing historic shipments..."
docker exec tracehub-backend-staging python scripts/create_historic_shipments.py --env staging

echo ""
echo "=============================================="
echo "FLUSH AND REIMPORT COMPLETE"
echo "=============================================="
echo ""
echo "Summary:"
echo "  - Backup: $BACKUP_FILE"
echo "  - Tables flushed: shipments, documents, products, containers, etc."
echo "  - Historic shipments reimported"
echo ""
echo "To verify, run:"
echo "  docker exec tracehub-db-staging psql -U tracehub tracehub -c 'SELECT reference, status, buyer_organization_id FROM shipments;'"
echo ""
echo "To rollback, run:"
echo "  docker exec -i tracehub-db-staging psql -U tracehub tracehub < $BACKUP_FILE"
