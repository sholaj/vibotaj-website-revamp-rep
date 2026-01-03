#!/bin/bash
# TraceHub Health Check Script
# Checks the health of all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TraceHub Health Check${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

COMPOSE_FILE="${1:-docker-compose.yml}"
ALL_HEALTHY=true

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}✗ Docker is not running${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check if containers are running
echo ""
echo -e "${GREEN}Container Status:${NC}"
if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
  echo -e "${RED}✗ No containers are running${NC}"
  echo "Start them with: docker-compose -f $COMPOSE_FILE up -d"
  exit 1
fi

docker-compose -f "$COMPOSE_FILE" ps
echo ""

# Check database
echo -e "${GREEN}Database Health:${NC}"
if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U tracehub > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Database is ready${NC}"

  # Check database connection
  if docker-compose -f "$COMPOSE_FILE" exec -T db psql -U tracehub -d tracehub -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
  else
    echo -e "${RED}✗ Database connection failed${NC}"
    ALL_HEALTHY=false
  fi
else
  echo -e "${RED}✗ Database is not ready${NC}"
  ALL_HEALTHY=false
fi
echo ""

# Check backend
echo -e "${GREEN}Backend Health:${NC}"
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  BACKEND_RESPONSE=$(curl -s http://localhost:8000/health)
  echo -e "${GREEN}✓ Backend is healthy${NC}"
  echo "  Response: $BACKEND_RESPONSE"
else
  echo -e "${RED}✗ Backend health check failed${NC}"
  echo "  Checking backend logs:"
  docker-compose -f "$COMPOSE_FILE" logs --tail=20 backend
  ALL_HEALTHY=false
fi
echo ""

# Check frontend
echo -e "${GREEN}Frontend Health:${NC}"
if curl -sf http://localhost:80/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
  echo -e "${RED}✗ Frontend health check failed${NC}"
  echo "  Checking frontend logs:"
  docker-compose -f "$COMPOSE_FILE" logs --tail=20 frontend
  ALL_HEALTHY=false
fi
echo ""

# Check API endpoint
echo -e "${GREEN}API Endpoint:${NC}"
if curl -sf http://localhost/api/health > /dev/null 2>&1; then
  API_RESPONSE=$(curl -s http://localhost/api/health)
  echo -e "${GREEN}✓ API is accessible via frontend proxy${NC}"
  echo "  Response: $API_RESPONSE"
else
  echo -e "${RED}✗ API not accessible via frontend proxy${NC}"
  ALL_HEALTHY=false
fi
echo ""

# Check disk space
echo -e "${GREEN}Disk Space:${NC}"
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_USAGE -gt 90 ]]; then
  echo -e "${RED}✗ Disk usage is at ${DISK_USAGE}%${NC}"
  ALL_HEALTHY=false
elif [[ $DISK_USAGE -gt 80 ]]; then
  echo -e "${YELLOW}! Disk usage is at ${DISK_USAGE}%${NC}"
else
  echo -e "${GREEN}✓ Disk usage is at ${DISK_USAGE}%${NC}"
fi
echo ""

# Check Docker resources
echo -e "${GREEN}Docker Resources:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo ""

# Check volumes
echo -e "${GREEN}Volumes:${NC}"
docker volume ls | grep tracehub || echo "No TraceHub volumes found"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
if [[ "$ALL_HEALTHY" == true ]]; then
  echo -e "${GREEN}All Systems Healthy ✓${NC}"
  echo -e "${GREEN}========================================${NC}"
  exit 0
else
  echo -e "${RED}Some Systems Unhealthy ✗${NC}"
  echo -e "${RED}========================================${NC}"
  echo ""
  echo "To view logs:"
  echo "  docker-compose -f $COMPOSE_FILE logs -f"
  echo ""
  echo "To restart services:"
  echo "  docker-compose -f $COMPOSE_FILE restart"
  exit 1
fi
