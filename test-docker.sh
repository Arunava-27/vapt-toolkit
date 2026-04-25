#!/bin/bash
# Docker Build and Validation Script for VAPT Toolkit

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}VAPT Toolkit - Docker Build & Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${RED}ERROR: Docker daemon is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker installed and running${NC}"

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    # Try with docker compose (new syntax)
    if docker compose version &> /dev/null; then
        echo -e "${GREEN}✓ Docker Compose available${NC}"
    else
        echo -e "${RED}ERROR: Docker Compose not available${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
fi

# Validate files exist
echo ""
echo -e "${YELLOW}[2/6] Validating configuration files...${NC}"

FILES=(
    "Dockerfile"
    "docker-compose.yml"
    ".dockerignore"
    "requirements.txt"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${RED}ERROR: $file not found${NC}"
        exit 1
    fi
done

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
fi
echo -e "${GREEN}✓ .env configured${NC}"

# Build images
echo ""
echo -e "${YELLOW}[3/6] Building Docker images...${NC}"

if docker compose build --no-cache 2>&1 | grep -q "Successfully tagged"; then
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
else
    echo -e "${YELLOW}Building images (this may take a few minutes)...${NC}"
    docker compose build --no-cache
    echo -e "${GREEN}✓ Docker images built${NC}"
fi

# Start services
echo ""
echo -e "${YELLOW}[4/6] Starting services...${NC}"

docker compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start (30 seconds)...${NC}"
sleep 10

echo ""
echo -e "${YELLOW}[5/6] Verifying service health...${NC}"

# Check container status
if docker compose ps | grep -q "vapt-web"; then
    echo -e "${GREEN}✓ vapt-web container running${NC}"
else
    echo -e "${RED}ERROR: vapt-web container not running${NC}"
    docker compose logs vapt-web
    exit 1
fi

if docker compose ps | grep -q "vapt-frontend"; then
    echo -e "${GREEN}✓ vapt-frontend container running${NC}"
else
    echo -e "${YELLOW}⚠ vapt-frontend may still be building${NC}"
fi

# Test API connectivity
echo ""
echo -e "${YELLOW}Testing API connectivity...${NC}"

API_AVAILABLE=false
for i in {1..5}; do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        API_AVAILABLE=true
        break
    fi
    echo -e "${YELLOW}Attempt $i/5...${NC}"
    sleep 5
done

if [ "$API_AVAILABLE" = true ]; then
    echo -e "${GREEN}✓ API responding at http://localhost:8000${NC}"
else
    echo -e "${RED}ERROR: API not responding${NC}"
    echo -e "${YELLOW}Container logs:${NC}"
    docker compose logs vapt-web
    exit 1
fi

# Test health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"

HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy\|ok\|success"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${YELLOW}Health check response: $HEALTH_RESPONSE${NC}"
fi

# Check volumes
echo ""
echo -e "${YELLOW}[6/6] Verifying volume mounts...${NC}"

if docker volume ls | grep -q "vapt-db-data"; then
    echo -e "${GREEN}✓ Database volume exists${NC}"
else
    echo -e "${RED}ERROR: Database volume not found${NC}"
    exit 1
fi

if docker volume ls | grep -q "vapt-scans"; then
    echo -e "${GREEN}✓ Scans volume exists${NC}"
else
    echo -e "${RED}ERROR: Scans volume not found${NC}"
    exit 1
fi

if docker volume ls | grep -q "vapt-logs"; then
    echo -e "${GREEN}✓ Logs volume exists${NC}"
else
    echo -e "${RED}ERROR: Logs volume not found${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VALIDATION SUCCESSFUL!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}VAPT Toolkit is running:${NC}"
echo -e "  ${BLUE}API Server:${NC}      http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}        http://localhost:8000/docs"
echo -e "  ${BLUE}API Health:${NC}      http://localhost:8000/api/health"
echo -e "  ${BLUE}Frontend:${NC}        http://localhost:3000"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View logs:       docker compose logs -f"
echo -e "  Stop services:   docker compose down"
echo -e "  View containers: docker compose ps"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Open http://localhost:8000/docs to explore API endpoints"
echo -e "  2. Open http://localhost:3000 to access the frontend"
echo -e "  3. See docs/DOCKER_DEPLOYMENT.md for configuration options"
echo ""

exit 0
