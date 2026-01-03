#!/bin/bash
# TraceHub Backup Script
# Creates backups of the database and uploads directory

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse arguments
BACKUP_NAME="${1:-auto}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TraceHub Backup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if .env file exists
if [[ ! -f .env ]]; then
  echo -e "${YELLOW}Warning: .env file not found, using defaults${NC}"
  DB_USER="tracehub"
  DB_NAME="tracehub"
else
  set -a
  source .env
  set +a
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if database is running
if ! docker-compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
  echo "Error: Database container is not running"
  echo "Start it with: docker-compose -f docker-compose.prod.yml up -d db"
  exit 1
fi

# Create database backup
echo -e "${GREEN}Creating database backup...${NC}"
DB_BACKUP_FILE="${BACKUP_DIR}/db_${BACKUP_NAME}_${TIMESTAMP}.sql"
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$DB_BACKUP_FILE"

if [[ -f "$DB_BACKUP_FILE" ]]; then
  DB_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
  echo -e "${GREEN}✓ Database backup created: $DB_BACKUP_FILE ($DB_SIZE)${NC}"
else
  echo "Error: Failed to create database backup"
  exit 1
fi

# Create uploads backup
if [[ -d "./uploads" ]] && [[ -n "$(ls -A ./uploads)" ]]; then
  echo -e "${GREEN}Creating uploads backup...${NC}"
  UPLOADS_BACKUP_FILE="${BACKUP_DIR}/uploads_${BACKUP_NAME}_${TIMESTAMP}.tar.gz"
  tar -czf "$UPLOADS_BACKUP_FILE" ./uploads

  if [[ -f "$UPLOADS_BACKUP_FILE" ]]; then
    UPLOADS_SIZE=$(du -h "$UPLOADS_BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Uploads backup created: $UPLOADS_BACKUP_FILE ($UPLOADS_SIZE)${NC}"
  else
    echo -e "${YELLOW}Warning: Failed to create uploads backup${NC}"
  fi
else
  echo -e "${YELLOW}Skipping uploads backup (directory empty or doesn't exist)${NC}"
fi

# Create metadata file
METADATA_FILE="${BACKUP_DIR}/backup_${BACKUP_NAME}_${TIMESTAMP}.meta"
cat > "$METADATA_FILE" << EOF
Backup Information
==================
Timestamp: $(date)
Name: $BACKUP_NAME
Database: $DB_NAME
Database File: $(basename "$DB_BACKUP_FILE")
Uploads File: $(basename "${UPLOADS_BACKUP_FILE:-none}")

Environment:
$(docker-compose -f docker-compose.prod.yml version)

Containers:
$(docker-compose -f docker-compose.prod.yml ps)
EOF

echo -e "${GREEN}✓ Metadata saved: $METADATA_FILE${NC}"
echo ""

# Clean old backups
echo -e "${GREEN}Cleaning old backups (older than $RETENTION_DAYS days)...${NC}"
DELETED_COUNT=$(find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete -print | wc -l)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.meta" -mtime +$RETENTION_DAYS -delete

if [[ $DELETED_COUNT -gt 0 ]]; then
  echo -e "${GREEN}✓ Deleted $DELETED_COUNT old backup files${NC}"
else
  echo "No old backups to delete"
fi
echo ""

# List recent backups
echo -e "${GREEN}Recent backups:${NC}"
ls -lh "$BACKUP_DIR" | grep "backup_\|db_\|uploads_" | tail -n 10
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Backup files:"
echo "  Database: $DB_BACKUP_FILE"
if [[ -f "${UPLOADS_BACKUP_FILE:-}" ]]; then
  echo "  Uploads:  $UPLOADS_BACKUP_FILE"
fi
echo "  Metadata: $METADATA_FILE"
echo ""
echo "To restore:"
echo "  Database: docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER $DB_NAME < $DB_BACKUP_FILE"
if [[ -f "${UPLOADS_BACKUP_FILE:-}" ]]; then
  echo "  Uploads:  tar -xzf $UPLOADS_BACKUP_FILE"
fi
echo ""
