#!/bin/bash
# Orchestra AI - Unified Deployment Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
print_header() {
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}======================================${NC}"
}

print_error() {
    echo -e "${RED}❌ Error: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check command
if [ $# -eq 0 ]; then
    echo "Orchestra AI Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  local      - Run services locally with Docker Compose"
    echo "  vercel     - Deploy frontend to Vercel"
    echo "  aws        - Deploy to AWS using Pulumi"
    echo "  status     - Check deployment status"
    echo "  clean      - Clean up resources"
    exit 1
fi

case "$1" in
    local)
        print_header "Starting Local Development Environment"
        
        # Check prerequisites
        print_info "Checking prerequisites..."
        
        # Check Docker
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed"
            exit 1
        fi
        
        # Check Docker Compose
        if ! command -v docker-compose &> /dev/null; then
            print_error "Docker Compose is not installed"
            exit 1
        fi
        
        # Start Redis if not running
        if ! redis-cli ping > /dev/null 2>&1; then
            print_info "Starting Redis..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                brew services start redis
            else
                sudo service redis-server start
            fi
        fi
        
        # Build and start services
        print_info "Building Docker images..."
        docker-compose -f docker-compose.dev.yml build
        
        print_info "Starting services..."
        docker-compose -f docker-compose.dev.yml up -d
        
        # Wait for services to be healthy
        print_info "Waiting for services to be healthy..."
        sleep 5
        
        # Check service health
        if curl -s http://localhost/health > /dev/null; then
            print_success "Nginx is healthy"
        fi
        
        if curl -s http://localhost:8000/health > /dev/null; then
            print_success "API is healthy"
        fi
        
        if curl -s http://localhost:8003/health > /dev/null; then
            print_success "MCP Memory is healthy"
        fi
        
        print_success "Local environment is running!"
        echo ""
        echo "🔗 Service URLs:"
        echo "   Main:     http://localhost"
        echo "   API:      http://localhost/api"
        echo "   Admin:    http://localhost"
        echo "   MCP:      http://localhost/mcp"
        echo ""
        echo "📊 View logs:"
        echo "   docker-compose -f docker-compose.dev.yml logs -f"
        ;;
        
    vercel)
        print_header "Deploying to Vercel"
        
        # Check if we're in the right directory
        if [ ! -f "vercel.json" ]; then
            print_error "vercel.json not found. Are you in the project root?"
            exit 1
        fi
        
        # Fix any authentication issues
        print_info "Checking Vercel authentication..."
        vercel whoami || vercel login
        
        # Deploy
        print_info "Starting deployment..."
        vercel --prod --yes
        
        print_success "Deployment initiated!"
        echo ""
        echo "Check deployment status with: vercel ls"
        ;;
        
    aws)
        print_header "Deploying to AWS with Pulumi"
        
        # Check Pulumi
        if ! command -v pulumi &> /dev/null; then
            print_error "Pulumi is not installed"
            echo "Install from: https://www.pulumi.com/docs/get-started/install/"
            exit 1
        fi
        
        # Navigate to Pulumi directory
        cd pulumi
        
        # Install dependencies
        print_info "Installing Pulumi dependencies..."
        pip3 install -r requirements.txt
        
        # Run Pulumi
        print_info "Deploying infrastructure..."
        pulumi up
        
        print_success "AWS deployment complete!"
        ;;
        
    status)
        print_header "Deployment Status"
        
        echo -e "\n${YELLOW}Local Services:${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f docker-compose.dev.yml ps
        else
            echo "Docker Compose not installed"
        fi
        
        echo -e "\n${YELLOW}Vercel Deployments:${NC}"
        if command -v vercel &> /dev/null; then
            vercel ls | head -10
        else
            echo "Vercel CLI not installed"
        fi
        
        echo -e "\n${YELLOW}Backend Health:${NC}"
        curl -s http://150.136.94.139:8000/health | jq . || echo "Backend not reachable"
        ;;
        
    clean)
        print_header "Cleaning Up Resources"
        
        # Stop Docker containers
        if [ -f "docker-compose.dev.yml" ]; then
            print_info "Stopping Docker containers..."
            docker-compose -f docker-compose.dev.yml down -v
        fi
        
        # Clean build artifacts
        print_info "Cleaning build artifacts..."
        rm -rf modern-admin/dist
        rm -rf modern-admin/node_modules
        rm -rf __pycache__
        find . -name "*.pyc" -delete
        
        print_success "Cleanup complete!"
        ;;
        
    *)
        print_error "Unknown command: $1"
        exit 1
        ;;
esac 