#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Orchestra AI - Docker Development Environment${NC}"
echo "================================================"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running!${NC}"
        echo "Please start Docker Desktop or Docker daemon"
        exit 1
    fi
}

# Function to show the menu
show_menu() {
    echo ""
    echo -e "${GREEN}What would you like to do?${NC}"
    echo "1) Start everything (recommended)"
    echo "2) Start backend only"
    echo "3) Start with fresh database"
    echo "4) Shell into main container"
    echo "5) View logs"
    echo "6) Stop everything"
    echo "7) Clean everything (nuclear option)"
    echo "8) Run tests"
    echo "9) Exit"
}

# Main logic
check_docker

case "${1:-menu}" in
    "up"|"start"|"1")
        echo -e "${GREEN}🚀 Starting all services...${NC}"
        docker compose up -d
        echo ""
        echo -e "${GREEN}✅ Everything is running!${NC}"
        echo ""
        echo "📍 Services available at:"
        echo "   - FastAPI:    http://localhost:8000"
        echo "   - Admin UI:   http://localhost:3001"
        echo "   - MCP:        http://localhost:8002"
        echo "   - Redis:      localhost:6379"
        echo "   - PostgreSQL: localhost:5432"
        echo ""
        echo -e "${YELLOW}💡 To get a shell: ./start.sh shell${NC}"
        ;;
        
    "shell"|"4")
        echo -e "${GREEN}🐚 Opening shell in main container...${NC}"
        docker compose exec orchestra-dev /bin/bash
        ;;
        
    "logs"|"5")
        echo -e "${GREEN}📋 Showing logs (Ctrl+C to exit)...${NC}"
        docker compose logs -f
        ;;
        
    "stop"|"down"|"6")
        echo -e "${YELLOW}🛑 Stopping all services...${NC}"
        docker compose down
        echo -e "${GREEN}✅ All services stopped${NC}"
        ;;
        
    "clean"|"nuke"|"7")
        echo -e "${RED}⚠️  This will delete all containers, volumes, and data!${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v --remove-orphans
            docker system prune -f
            echo -e "${GREEN}✅ Everything cleaned${NC}"
        fi
        ;;
        
    "test"|"8")
        echo -e "${GREEN}🧪 Running tests...${NC}"
        docker compose exec orchestra-dev poetry run pytest
        ;;
        
    "menu"|*)
        while true; do
            show_menu
            read -p "Select option: " choice
            case $choice in
                1) $0 up ;;
                2) docker compose up -d orchestra-dev redis postgres ;;
                3) docker compose down -v && docker compose up -d ;;
                4) $0 shell ;;
                5) $0 logs ;;
                6) $0 stop ;;
                7) $0 clean ;;
                8) $0 test ;;
                9) exit 0 ;;
                *) echo -e "${RED}Invalid option${NC}" ;;
            esac
        done
        ;;
esac 