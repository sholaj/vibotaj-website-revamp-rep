#!/bin/bash
# TraceHub Deployment Script
# This script handles deployment to staging or production environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="staging"
SKIP_BACKUP=false
SKIP_MIGRATIONS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --skip-backup)
      SKIP_BACKUP=true
      shift
      ;;
    --skip-migrations)
      SKIP_MIGRATIONS=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  -e, --environment ENV    Environment to deploy to (staging|production) [default: staging]"
      echo "  --skip-backup           Skip database backup before deployment"
      echo "  --skip-migrations       Skip running database migrations"
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

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TraceHub Deployment Script${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Production safety check
if [[ "$ENVIRONMENT" == "production" ]]; then
  echo -e "${YELLOW}WARNING: You are about to deploy to PRODUCTION!${NC}"
  read -p "Are you sure you want to continue? (yes/no): " -r
  echo
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Deployment cancelled."
    exit 1
  fi
fi

# Check if .env file exists
if [[ ! -f .env ]]; then
  echo -e "${RED}Error: .env file not found${NC}"
  echo "Please create .env file from .env.example and configure it"
  exit 1
fi

# Source environment variables
set -a
source .env
set +a

# Check required environment variables
REQUIRED_VARS=("DB_PASSWORD" "JWT_SECRET")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var}" || "${!var}" == *"change-this"* || "${!var}" == *"your-"* ]]; then
    MISSING_VARS+=("$var")
  fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
  echo -e "${RED}Error: The following required environment variables are not set or contain default values:${NC}"
  for var in "${MISSING_VARS[@]}"; do
    echo "  - $var"
  done
  exit 1
fi

# Create backup (unless skipped)
if [[ "$SKIP_BACKUP" != true ]]; then
  echo -e "${GREEN}Creating database backup...${NC}"
  mkdir -p ./backups
  BACKUP_FILE="./backups/backup_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql"

  if docker-compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" || {
      echo -e "${YELLOW}Warning: Failed to create backup (database may not be running yet)${NC}"
    }
    if [[ -f "$BACKUP_FILE" ]]; then
      echo -e "${GREEN}Backup created: $BACKUP_FILE${NC}"
    fi
  else
    echo -e "${YELLOW}Skipping backup: Database not running${NC}"
  fi
  echo ""
fi

# Pull latest code
echo -e "${GREEN}Pulling latest code...${NC}"
git pull origin main || {
  echo -e "${YELLOW}Warning: Git pull failed. Continuing with local changes.${NC}"
}
echo ""

# Build images
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache
echo ""

# Stop existing containers
echo -e "${GREEN}Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down
echo ""

# Start new containers
echo -e "${GREEN}Starting new containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d
echo ""

# Wait for services to be healthy
echo -e "${GREEN}Waiting for services to be healthy...${NC}"
MAX_WAIT=120
WAIT_TIME=0

while [[ $WAIT_TIME -lt $MAX_WAIT ]]; do
  if docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
    echo -e "${GREEN}Services are healthy!${NC}"
    break
  fi
  echo "Waiting for services... ($WAIT_TIME/$MAX_WAIT seconds)"
  sleep 5
  WAIT_TIME=$((WAIT_TIME + 5))
done

if [[ $WAIT_TIME -ge $MAX_WAIT ]]; then
  echo -e "${YELLOW}Warning: Services did not become healthy within $MAX_WAIT seconds${NC}"
  echo "Checking service status:"
  docker-compose -f docker-compose.prod.yml ps
fi
echo ""

# Run database migrations (unless skipped)
if [[ "$SKIP_MIGRATIONS" != true ]]; then
  echo -e "${GREEN}Running database migrations...${NC}"
  docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || {
    echo -e "${RED}Error: Database migrations failed${NC}"
    echo "Rolling back deployment..."
    docker-compose -f docker-compose.prod.yml down
    exit 1
  }
  echo ""
fi

# Health check
echo -e "${GREEN}Performing health checks...${NC}"
HEALTH_CHECK_FAILED=false

# Check backend
if curl -sf http://localhost/api/health > /dev/null; then
  echo -e "${GREEN}✓ Backend is healthy${NC}"
else
  echo -e "${RED}✗ Backend health check failed${NC}"
  HEALTH_CHECK_FAILED=true
fi

# Check frontend
if curl -sf http://localhost/health > /dev/null; then
  echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
  echo -e "${RED}✗ Frontend health check failed${NC}"
  HEALTH_CHECK_FAILED=true
fi

echo ""

if [[ "$HEALTH_CHECK_FAILED" == true ]]; then
  echo -e "${YELLOW}Warning: Some health checks failed${NC}"
  echo "Please check the logs: docker-compose -f docker-compose.prod.yml logs"
  exit 1
fi

# Show running containers
echo -e "${GREEN}Running containers:${NC}"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Clean up old images
echo -e "${GREEN}Cleaning up old Docker images...${NC}"
docker image prune -f
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Application is running at:"
echo "  Frontend: http://localhost"
echo "  Backend:  http://localhost/api"
echo "  API Docs: http://localhost/api/docs"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To rollback (if needed):"
echo "  docker-compose -f docker-compose.prod.yml down"
echo "  # Restore from backup: $BACKUP_FILE"
echo ""
