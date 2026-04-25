#!/bin/bash
# Docker startup script for VAPT Toolkit
# Usage: ./docker-start.sh [up|down|restart|logs]

set -e

COMMAND=${1:-up}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}VAPT Toolkit Docker Manager${NC}"
echo -e "${YELLOW}Command: $COMMAND${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    exit 1
fi

# Ensure .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${GREEN}.env created. Please edit it with your configuration.${NC}"
fi

cd "$PROJECT_DIR"

case "$COMMAND" in
    up)
        echo -e "${GREEN}Starting VAPT Toolkit services...${NC}"
        docker compose up -d --build
        
        echo ""
        echo -e "${GREEN}Services started!${NC}"
        sleep 3
        docker compose ps
        
        echo ""
        echo -e "${GREEN}Access VAPT Toolkit:${NC}"
        echo -e "  API:      ${YELLOW}http://localhost:8000${NC}"
        echo -e "  Docs:     ${YELLOW}http://localhost:8000/docs${NC}"
        echo -e "  Frontend: ${YELLOW}http://localhost:3000${NC}"
        echo -e "  Health:   ${YELLOW}http://localhost:8000/health${NC}"
        ;;
    
    down)
        echo -e "${GREEN}Stopping VAPT Toolkit services...${NC}"
        docker compose down
        echo -e "${GREEN}Services stopped.${NC}"
        ;;
    
    restart)
        echo -e "${GREEN}Restarting VAPT Toolkit services...${NC}"
        docker compose restart
        sleep 2
        docker compose ps
        ;;
    
    logs)
        echo -e "${GREEN}Showing logs (press Ctrl+C to exit)...${NC}"
        docker compose logs -f
        ;;
    
    clean)
        echo -e "${RED}WARNING: This will remove all containers and volumes!${NC}"
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v
            echo -e "${GREEN}Cleaned up.${NC}"
        fi
        ;;
    
    ps)
        echo -e "${GREEN}Container status:${NC}"
        docker compose ps
        ;;
    
    build)
        echo -e "${GREEN}Building images...${NC}"
        docker compose build --no-cache
        echo -e "${GREEN}Build complete.${NC}"
        ;;
    
    shell-web)
        echo -e "${GREEN}Opening shell in vapt-web container...${NC}"
        docker compose exec vapt-web /bin/bash
        ;;
    
    shell-frontend)
        echo -e "${GREEN}Opening shell in vapt-frontend container...${NC}"
        docker compose exec vapt-frontend /bin/sh
        ;;
    
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        echo "Usage: $0 {up|down|restart|logs|clean|ps|build|shell-web|shell-frontend}"
        echo ""
        echo "Commands:"
        echo "  up              Start all services"
        echo "  down            Stop all services"
        echo "  restart         Restart all services"
        echo "  logs            Show live logs (Ctrl+C to exit)"
        echo "  clean           Remove containers and volumes (destructive!)"
        echo "  ps              Show container status"
        echo "  build           Rebuild images"
        echo "  shell-web       Open shell in API container"
        echo "  shell-frontend  Open shell in frontend container"
        exit 1
        ;;
esac

exit 0
