#!/bin/bash
# 🚀 Orchestra AI One-Click Deployment Script
# Version: 2.0 - Post-Live Verification
# Last Updated: June 10, 2025

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji constants
ROCKET="🚀"
DATABASE="🗄️"
CLOCK="⏳"
PERSONAS="🎭"
FRONTEND="🌐"
CHECK="✅"
PARTY="🎉"
WARNING="⚠️"

echo -e "${CYAN}${ROCKET} Orchestra AI One-Click Deployment${NC}"
echo -e "${CYAN}==================================${NC}"
echo -e "$(date)"
echo ""

# Parse command line arguments
VERIFY_ONLY=false
SKIP_FRONTEND=false
SKIP_PERSONAS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --skip-personas)
            SKIP_PERSONAS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --verify-only     Only run verification checks"
            echo "  --skip-frontend   Skip frontend deployment"
            echo "  --skip-personas   Skip personas deployment"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}${CLOCK} Waiting for $name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}${CHECK} $name is ready!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}${WARNING} $name failed to start within timeout${NC}"
    return 1
}

# Verification function
verify_deployment() {
    echo -e "${BLUE}${CHECK} Running deployment verification...${NC}"
    echo ""
    
    # Zapier MCP Health
    echo -e "${BLUE}🔗 Testing Zapier MCP Server:${NC}"
    if curl -s http://localhost:80/health | jq -e '.status == "healthy"' >/dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} Zapier MCP Server: HEALTHY${NC}"
    else
        echo -e "${RED}❌ Zapier MCP Server: UNHEALTHY${NC}"
        return 1
    fi
    
    # API Health
    echo -e "${BLUE}${ROCKET} Testing API Server:${NC}"
    if curl -s http://localhost:8010/api/system/health | jq -e '.status == "healthy"' >/dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} API Server: HEALTHY${NC}"
    else
        echo -e "${RED}❌ API Server: UNHEALTHY${NC}"
        return 1
    fi
    
    # Personas Health
    echo -e "${BLUE}${PERSONAS} Testing Personas System:${NC}"
    if curl -s http://localhost:8000/health | jq -e '.status == "healthy"' >/dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} Personas System: HEALTHY${NC}"
    else
        echo -e "${RED}❌ Personas System: UNHEALTHY${NC}"
        return 1
    fi
    
    # Database Health
    echo -e "${BLUE}${DATABASE} Testing Database Cluster:${NC}"
    if docker exec cherry_ai_postgres_prod pg_isready -U cherry_ai >/dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} PostgreSQL: READY${NC}"
    else
        echo -e "${RED}❌ PostgreSQL: NOT READY${NC}"
        return 1
    fi
    
    if docker exec cherry_ai_redis_prod redis-cli ping | grep -q "PONG"; then
        echo -e "${GREEN}${CHECK} Redis: READY${NC}"
    else
        echo -e "${RED}❌ Redis: NOT READY${NC}"
        return 1
    fi
    
    if curl -s http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} Weaviate: READY${NC}"
    else
        echo -e "${RED}❌ Weaviate: NOT READY${NC}"
        return 1
    fi
    
    # Performance test
    echo -e "${BLUE}⚡ Testing Performance:${NC}"
    API_TIME=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8010/api/system/health)
    echo -e "${GREEN}${CHECK} API Response Time: ${API_TIME}s${NC}"
    
    return 0
}

# If verify-only mode, run verification and exit
if [ "$VERIFY_ONLY" = true ]; then
    verify_deployment
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}${PARTY} All systems verified operational!${NC}"
        exit 0
    else
        echo -e "${RED}${WARNING} Verification failed!${NC}"
        exit 1
    fi
fi

# Check required tools
echo -e "${BLUE}🔧 Checking required tools...${NC}"

if ! command_exists docker; then
    echo -e "${RED}${WARNING} Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! command_exists jq; then
    echo -e "${RED}${WARNING} jq is not installed. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y jq
fi

if [ "$SKIP_FRONTEND" = false ] && ! command_exists vercel; then
    echo -e "${RED}${WARNING} Vercel CLI is not installed${NC}"
    echo "Install with: npm i -g vercel"
    exit 1
fi

# Environment check
echo -e "${BLUE}🔍 Checking environment...${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}${WARNING} .env file not found, using defaults${NC}"
else
    source .env
    echo -e "${GREEN}${CHECK} Environment loaded from .env${NC}"
fi

# Ensure we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}${WARNING} docker-compose.production.yml not found${NC}"
    echo "Please run this script from the orchestra-main directory"
    exit 1
fi

# Database deployment
echo -e "${BLUE}${DATABASE} Deploying database cluster...${NC}"
docker-compose -f docker-compose.production.yml up -d \
    cherry_ai_postgres_prod cherry_ai_redis_prod cherry_ai_weaviate_prod

# Wait for databases to be ready
echo -e "${YELLOW}${CLOCK} Waiting for databases to initialize...${NC}"
sleep 30

# Check database health
wait_for_service "http://localhost:8080/v1/.well-known/ready" "Weaviate"

# API deployment
echo -e "${BLUE}${ROCKET} Deploying API server...${NC}"
docker-compose -f docker-compose.production.yml up -d cherry_ai_api_hybrid

# Wait for API to be ready
wait_for_service "http://localhost:8010/api/system/health" "API Server"

# Zapier MCP Server deployment (NEW)
echo -e "${BLUE}🔗 Deploying Zapier MCP Server...${NC}"
cd zapier-mcp

# Stop existing Zapier MCP process
sudo pkill -f "node.*server.js" 2>/dev/null || true
sleep 3

# Start Zapier MCP server on port 80
sudo MCP_SERVER_PORT=80 node server.js &
sleep 5

# Wait for Zapier MCP to be ready
wait_for_service "http://localhost:80/health" "Zapier MCP Server"

cd ..

# Personas deployment
if [ "$SKIP_PERSONAS" = false ]; then
    echo -e "${BLUE}${PERSONAS} Deploying personas system...${NC}"
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}${CHECK} Virtual environment activated${NC}"
    else
        echo -e "${YELLOW}${WARNING} Virtual environment not found, using system Python${NC}"
    fi
    
    # Stop existing personas process
    pkill -f personas_server.py 2>/dev/null || true
    sleep 5
    
    # Start personas server
    export ENABLE_ADVANCED_MEMORY=true
    export PERSONA_SYSTEM=enabled
    export CROSS_DOMAIN_ROUTING=enabled
    
    nohup python3 personas_server.py > /tmp/personas_live.log 2>&1 &
    
    # Wait for personas to be ready
    wait_for_service "http://localhost:8000/health" "Personas System"
fi

# Frontend deployment
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${BLUE}${FRONTEND} Deploying frontend...${NC}"
    
    if [ -z "$VERCEL_TOKEN" ]; then
        echo -e "${RED}${WARNING} VERCEL_TOKEN not set${NC}"
        echo "Please set VERCEL_TOKEN in your .env file or environment"
        exit 1
    fi
    
    cd admin-interface
    
    echo -e "${BLUE}🚀 Starting Vercel deployment...${NC}"
    vercel --prod --yes --token "$VERCEL_TOKEN"
    
    cd ..
    
    echo -e "${GREEN}${CHECK} Frontend deployment initiated${NC}"
    echo -e "${BLUE}💡 Check Vercel dashboard for deployment URL${NC}"
fi

# Final verification
echo -e "${BLUE}${CHECK} Running final verification...${NC}"
sleep 10

verify_deployment

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}${PARTY}${PARTY}${PARTY} DEPLOYMENT COMPLETE! ${PARTY}${PARTY}${PARTY}${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${CYAN}📊 System Status:${NC}"
    echo -e "${GREEN}${CHECK} Zapier MCP Server: http://localhost:80${NC}"
    echo -e "${GREEN}${CHECK} API Server: http://localhost:8010${NC}"
    echo -e "${GREEN}${CHECK} Personas: http://localhost:8000${NC}"
    echo -e "${GREEN}${CHECK} Database Cluster: Operational${NC}"
    echo ""
    echo -e "${CYAN}🔗 Quick Links:${NC}"
    echo -e "${BLUE}• Zapier MCP Health: http://localhost:80/health${NC}"
    echo -e "${BLUE}• Zapier API Docs: http://localhost:80/api/v1/docs${NC}"
    echo -e "${BLUE}• API Documentation: http://localhost:8010/docs${NC}"
    echo -e "${BLUE}• Personas Health: http://localhost:8000/health${NC}"
    echo -e "${BLUE}• System Health: http://localhost:8010/api/system/health${NC}"
    echo ""
    echo -e "${CYAN}🎭 Your Orchestra AI is ready to revolutionize your workflow!${NC}"
else
    echo -e "${RED}${WARNING} Deployment verification failed!${NC}"
    echo -e "${YELLOW}💡 Check logs for more details:${NC}"
    echo -e "${YELLOW}• API Logs: docker logs cherry_ai_api_hybrid${NC}"
    echo -e "${YELLOW}• Personas Logs: tail -f /tmp/personas_live.log${NC}"
    exit 1
fi 