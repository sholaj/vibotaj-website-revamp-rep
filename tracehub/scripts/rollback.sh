#!/bin/bash
# TraceHub Rollback Script
# Rollback to previous deployment or specific backup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
ROLLBACK_TYPE="deployment"  # deployment or database
BACKUP_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -t|--type)
      ROLLBACK_TYPE="$2"
      shift 2
      ;;
    -b|--backup)
      BACKUP_FILE="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  -e, --environment ENV    Environment (staging|production) [default: production]"
      echo "  -t, --type TYPE         Rollback type (deployment|database) [default: deployment]"
      echo "  -b, --backup FILE       Specific backup file to restore (for database rollback)"
      echo "  -h, --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
  echo -e "${RED}Error: Environment must be 'staging' or 'production'${NC}"
  exit 1
fi

# Validate rollback type
if [[ "$ROLLBACK_TYPE" != "deployment" && "$ROLLBACK_TYPE" != "database" ]]; then
  echo -e "${RED}Error: Rollback type must be 'deployment' or 'database'${NC}"
  exit 1
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}TraceHub Rollback Script${NC}"
echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"
echo -e "${YELLOW}Rollback Type: $ROLLBACK_TYPE${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Safety confirmation
echo -e "${RED}WARNING: You are about to rollback $ENVIRONMENT environment!${NC}"
read -p "Are you sure you want to continue? Type 'yes' to confirm: " -r
echo
if [[ ! $REPLY == "yes" ]]; then
  echo "Rollback cancelled."
  exit 1
fi

# Determine compose file
if [[ "$ENVIRONMENT" == "production" ]]; then
  COMPOSE_FILE="docker-compose.prod.yml"
else
  COMPOSE_FILE="docker-compose.staging.yml"
fi

if [[ "$ROLLBACK_TYPE" == "deployment" ]]; then
  echo -e "${GREEN}Rolling back deployment...${NC}"

  # Check if blue deployment exists (from blue-green deployment)
  if [[ -f "docker-compose.blue.yml" ]]; then
    echo -e "${GREEN}Found blue deployment backup. Switching back to blue...${NC}"

    # Stop current deployment
    docker-compose -f "$COMPOSE_FILE" down

    # Start blue deployment
    docker-compose -f docker-compose.blue.yml up -d

    # Wait for health
    echo "Waiting for services to be healthy..."
    sleep 30

    if docker-compose -f docker-compose.blue.yml ps | grep -q healthy; then
      echo -e "${GREEN}Rollback to blue deployment successful!${NC}"

      # Rename blue to production
      mv docker-compose.blue.yml "$COMPOSE_FILE"
    else
      echo -e "${RED}Rollback failed - services not healthy${NC}"
      docker-compose -f docker-compose.blue.yml logs
      exit 1
    fi
  else
    echo -e "${YELLOW}No blue deployment found. You'll need to manually specify which version to deploy.${NC}"
    echo "Use: docker-compose down && docker pull <image:tag> && docker-compose up -d"
    exit 1
  fi

elif [[ "$ROLLBACK_TYPE" == "database" ]]; then
  echo -e "${GREEN}Rolling back database...${NC}"

  # Find latest backup if not specified
  if [[ -z "$BACKUP_FILE" ]]; then
    BACKUP_FILE=$(ls -t ./backups/backup_*.sql 2>/dev/null | head -n1)

    if [[ -z "$BACKUP_FILE" ]]; then
      echo -e "${RED}Error: No backup files found in ./backups/${NC}"
      exit 1
    fi

    echo -e "${YELLOW}Using latest backup: $BACKUP_FILE${NC}"
  fi

  # Validate backup file exists
  if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
  fi

  # Get database container name
  DB_CONTAINER=$(docker-compose -f "$COMPOSE_FILE" ps -q db)

  if [[ -z "$DB_CONTAINER" ]]; then
    echo -e "${RED}Error: Database container not running${NC}"
    exit 1
  fi

  # Create pre-rollback backup
  echo -e "${GREEN}Creating pre-rollback backup...${NC}"
  PRE_ROLLBACK_BACKUP="./backups/pre_rollback_$(date +%Y%m%d_%H%M%S).sql"
  docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$PRE_ROLLBACK_BACKUP"
  echo -e "${GREEN}Pre-rollback backup saved: $PRE_ROLLBACK_BACKUP${NC}"

  # Stop backend to prevent connections during restore
  echo -e "${GREEN}Stopping backend...${NC}"
  docker-compose -f "$COMPOSE_FILE" stop backend

  # Restore database
  echo -e "${GREEN}Restoring database from: $BACKUP_FILE${NC}"
  docker-compose -f "$COMPOSE_FILE" exec -T db psql -U "$DB_USER" "$DB_NAME" < "$BACKUP_FILE"

  if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}Database restored successfully!${NC}"

    # Restart backend
    echo -e "${GREEN}Restarting backend...${NC}"
    docker-compose -f "$COMPOSE_FILE" start backend

    # Wait for health
    sleep 20

    if docker-compose -f "$COMPOSE_FILE" ps | grep backend | grep -q healthy; then
      echo -e "${GREEN}Database rollback complete and backend is healthy!${NC}"
    else
      echo -e "${YELLOW}Warning: Backend may not be healthy after database restore${NC}"
      docker-compose -f "$COMPOSE_FILE" logs backend
    fi
  else
    echo -e "${RED}Database restore failed!${NC}"
    echo "You can try restoring the pre-rollback backup: $PRE_ROLLBACK_BACKUP"
    exit 1
  fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Rollback Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Show status
echo "Current status:"
docker-compose -f "$COMPOSE_FILE" ps
echo ""

# Health check
echo "Running health checks..."
if curl -sf http://localhost/api/health > /dev/null; then
  echo -e "${GREEN}✓ Backend is healthy${NC}"
else
  echo -e "${RED}✗ Backend health check failed${NC}"
fi

if curl -sf http://localhost/ > /dev/null; then
  echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
  echo -e "${RED}✗ Frontend health check failed${NC}"
fi

echo ""
echo "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
echo ""
