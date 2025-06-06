#!/bin/bash
# FINAL CONSOLIDATED DEPLOYMENT SCRIPT FOR CHERRY-AI.ME
# This replaces ALL other deployment scripts - use ONLY this one
set -e

echo "🚀 Cherry AI Production Deployment to cherry-ai.me"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Environment variables (set these before running)
DOMAIN=${DOMAIN:-cherry-ai.me}
SECRET_KEY=${SECRET_KEY:-$(openssl rand -base64 32)}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -base64 16)}

echo -e "${BLUE}Domain: $DOMAIN${NC}"
echo -e "${BLUE}Secret Key: ${SECRET_KEY:0:10}...${NC}"

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        exit 1
    fi
}

# Function to create directories
create_directories() {
    echo -e "${YELLOW}📁 Creating required directories...${NC}"
    mkdir -p logs/nginx
    mkdir -p nginx/ssl
    mkdir -p fluentd
    chmod 755 logs logs/nginx
}

# Function to generate SSL certificates (self-signed for dev)
generate_ssl() {
    echo -e "${YELLOW}🔐 Generating SSL certificates...${NC}"
    
    if [ ! -f "nginx/ssl/cherry-ai.me.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/cherry-ai.me.key \
            -out nginx/ssl/cherry-ai.me.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        
        echo -e "${GREEN}✅ SSL certificates generated${NC}"
        echo -e "${YELLOW}⚠️  For production, replace with real certificates:${NC}"
        echo -e "${YELLOW}   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN${NC}"
    else
        echo -e "${GREEN}✅ SSL certificates already exist${NC}"
    fi
}

# Function to create environment file
create_env() {
    echo -e "${YELLOW}📝 Creating environment configuration...${NC}"
    
    cat > .env.production << EOF
# Cherry AI Production Environment
DOMAIN=$DOMAIN
SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Database settings
DATABASE_URL=postgresql://cherry_ai:$POSTGRES_PASSWORD@postgres:5432/cherry_ai
REDIS_URL=redis://redis:6379/0
WEAVIATE_URL=http://weaviate:8080

# Environment
CHERRY_AI_ENV=production
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

# Bridge settings
BRIDGE_HOST=0.0.0.0
BRIDGE_PORT=8765

# Monitoring (optional)
# SLACK_WEBHOOK=https://hooks.slack.com/services/...
# EMAIL_ALERTS=admin@$DOMAIN

# Health monitoring
MONITOR_INTERVAL=30
EOF
    
    echo -e "${GREEN}✅ Environment file created${NC}"
}

# Function to create fluentd config
create_fluentd_config() {
    echo -e "${YELLOW}📊 Creating logging configuration...${NC}"
    
    cat > fluentd/fluent.conf << 'EOF'
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match cherry_ai.**>
  @type file
  path /logs/cherry_ai
  append true
  time_slice_format %Y%m%d
  time_slice_wait 10m
  time_format %Y%m%dT%H%M%S%z
  format json
</match>
EOF
    
    echo -e "${GREEN}✅ Logging configuration created${NC}"
}

# Function to stop old deployments
cleanup_old_deployments() {
    echo -e "${YELLOW}🧹 Cleaning up old deployments...${NC}"
    
    # Stop any existing cherry AI containers
    docker ps -a | grep cherry_ai | awk '{print $1}' | xargs -r docker stop
    docker ps -a | grep cherry_ai | awk '{print $1}' | xargs -r docker rm
    
    # Stop dev deployment if running
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Cleaned up old deployments${NC}"
}

# Function to start production deployment
start_production() {
    echo -e "${YELLOW}🚀 Starting production deployment...${NC}"
    
    # Build and start services using the correct env file
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d --build
    
    echo -e "${GREEN}✅ Production services started${NC}"
}

# Function to wait for services
wait_for_services() {
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    
    # Wait for database
    echo -n "Waiting for database..."
    for i in {1..30}; do
        if docker exec cherry_ai_postgres_prod pg_isready -U cherry_ai -d cherry_ai >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    
    # Wait for API
    echo -n "Waiting for API..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/system/health >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    
    # Wait for Bridge
    echo -n "Waiting for AI Bridge..."
    for i in {1..20}; do
        if curl -f http://localhost:8765/health >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
}

# Function to test deployment
test_deployment() {
    echo -e "${YELLOW}🧪 Testing deployment...${NC}"
    
    # Test API health
    if curl -f http://localhost:8000/api/system/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API is healthy${NC}"
    else
        echo -e "${RED}❌ API health check failed${NC}"
    fi
    
    # Test AI Bridge
    if curl -f http://localhost:8765/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ AI Bridge is healthy${NC}"
    else
        echo -e "${RED}❌ AI Bridge health check failed${NC}"
    fi
    
    # Test Nginx
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Nginx is healthy${NC}"
    else
        echo -e "${RED}❌ Nginx health check failed${NC}"
    fi
}

# Function to show final status
show_final_status() {
    echo ""
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}===========================================${NC}"
    echo ""
    echo -e "${BLUE}🌐 Website:${NC} https://$DOMAIN"
    echo -e "${BLUE}🔗 API:${NC} https://$DOMAIN/api"
    echo -e "${BLUE}📚 API Docs:${NC} https://$DOMAIN/api/docs"
    echo -e "${BLUE}🤖 AI Bridge:${NC} wss://$DOMAIN/bridge/ws"
    echo ""
    echo -e "${YELLOW}📊 Service Status:${NC}"
    docker-compose -f docker-compose.production.yml --env-file .env.production ps
    echo ""
    echo -e "${YELLOW}🔑 Connect your Manus AI Coder:${NC}"
    echo -e "${BLUE}   WebSocket URL:${NC} wss://$DOMAIN/bridge/ws"
    echo -e "${BLUE}   API Key:${NC} manus-key-2024"
    echo ""
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    echo "1. Point your DNS to this server's IP"
    echo "2. Get real SSL certificates: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
    echo "3. Connect your AI coders to the bridge"
    echo "4. Monitor logs: docker-compose -f docker-compose.production.yml --env-file .env.production logs -f"
    echo ""
    echo -e "${GREEN}✨ Cherry AI is now live on $DOMAIN! ✨${NC}"
}

# Main execution
main() {
    # Prerequisites check
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    check_command "docker"
    check_command "docker-compose"
    check_command "openssl"
    check_command "curl"
    
    # Deployment steps
    create_directories
    generate_ssl
    create_env
    create_fluentd_config
    cleanup_old_deployments
    start_production
    wait_for_services
    test_deployment
    show_final_status
}

# Run main function
main "$@" 