#!/bin/bash
# Orchestra AI - Complete Lambda Labs Deployment Script

set -e

# Configuration
PRODUCTION_HOST="150.136.94.139"
DEV_HOST="192.9.142.8"
SSH_USER="ubuntu"
SSH_KEY_PATH="~/.ssh/lambda_labs_key"
GITHUB_REPO="https://github.com/ai-cherry/orchestra-main.git"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Orchestra AI Lambda Labs Deployment ===${NC}\n"

# Function to deploy to a specific host
deploy_to_host() {
    local HOST=$1
    local ENV_NAME=$2
    
    echo -e "${YELLOW}Deploying to $ENV_NAME ($HOST)...${NC}"
    
    # Test SSH connection
    echo -e "${YELLOW}Testing SSH connection...${NC}"
    if ! ssh -o ConnectTimeout=10 -i $SSH_KEY_PATH $SSH_USER@$HOST "echo 'SSH connection successful'"; then
        echo -e "${RED}❌ Cannot connect to $HOST. Check SSH key and permissions.${NC}"
        return 1
    fi
    
    # Deploy via SSH
    ssh -i $SSH_KEY_PATH $SSH_USER@$HOST << 'ENDSSH'
set -e

# Colors for remote output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting deployment on $(hostname)...${NC}"

# Step 1: Stop existing services
echo -e "${YELLOW}Stopping existing services...${NC}"
if command -v docker-compose &> /dev/null; then
    cd ~/orchestra-main 2>/dev/null && docker-compose down || true
fi
pkill -f "uvicorn" || true
pkill -f "orchestra" || true

# Step 2: Update system packages
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    docker.io docker-compose \
    python3.11 python3.11-venv python3.11-dev \
    nginx redis-server postgresql-client \
    git curl jq

# Step 3: Clone or update repository
echo -e "${YELLOW}Updating repository...${NC}"
cd ~
if [ -d "orchestra-main" ]; then
    cd orchestra-main
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    git clone https://github.com/ai-cherry/orchestra-main.git
    cd orchestra-main
fi

# Step 4: Apply critical fixes
echo -e "${YELLOW}Applying critical fixes...${NC}"

# Fix 1: Ensure api/database directories exist
mkdir -p api/database

# Fix 2: Create proper api/database/models.py if empty
if [ ! -s "api/database/models.py" ] || [ $(wc -c < "api/database/models.py") -le 1 ]; then
    echo -e "${YELLOW}Fixing empty models.py...${NC}"
    cat > api/database/models.py << 'EOF'
# Re-export models from the root database directory
from database.models import *

# This allows imports like:
# from api.database.models import User, Persona, etc.
EOF
fi

# Fix 3: Create proper api/database/connection.py
echo -e "${YELLOW}Fixing connection.py...${NC}"
cat > api/database/connection.py << 'EOF'
"""
Database connection proxy for API module
Re-exports from root database module for backward compatibility
"""

# Re-export everything from the root database module
from database.connection import *

# This allows the API to use:
# from api.database.connection import init_database, close_database, get_db, db_manager
EOF

# Fix 4: Create __init__.py files
touch api/__init__.py
touch api/database/__init__.py
touch database/__init__.py

# Step 5: Set up Python virtual environment
echo -e "${YELLOW}Setting up Python environment...${NC}"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Step 6: Create .env file with proper configuration
echo -e "${YELLOW}Creating environment configuration...${NC}"
cat > .env << EOF
# Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://orchestra:orchestra123@localhost:5432/orchestra_ai

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# External Services (if needed)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
EOF

# Step 7: Set up PostgreSQL database
echo -e "${YELLOW}Setting up PostgreSQL...${NC}"
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw orchestra_ai; then
    sudo -u postgres createuser -s orchestra || true
    sudo -u postgres createdb -O orchestra orchestra_ai || true
    sudo -u postgres psql -c "ALTER USER orchestra WITH PASSWORD 'orchestra123';" || true
fi

# Step 8: Set up Redis
echo -e "${YELLOW}Starting Redis...${NC}"
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Step 9: Test local imports
echo -e "${YELLOW}Testing Python imports...${NC}"
python -c "
try:
    from api.database.connection import init_database, db_manager
    from api.database.models import User, Persona
    print('✅ Import test passed!')
except Exception as e:
    print(f'❌ Import test failed: {e}')
    exit(1)
"

# Step 10: Start services with Docker Compose (if available)
if [ -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}Starting services with Docker Compose...${NC}"
    docker-compose up -d
else
    # Fallback: Start services manually
    echo -e "${YELLOW}Starting services manually...${NC}"
    
    # Start API service
    nohup python -m uvicorn main_api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
    
    # Start MCP service if exists
    if [ -f "start_mcp_memory.py" ]; then
        nohup python start_mcp_memory.py > mcp.log 2>&1 &
    fi
fi

# Step 11: Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/orchestra << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Step 12: Verify deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
sleep 5

# Check API health
if curl -s http://localhost:8000/health | jq -e '.status == "healthy"' > /dev/null; then
    echo -e "${GREEN}✅ API is healthy!${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    echo "API logs:"
    tail -n 50 api.log || true
fi

# Check external access
if curl -s http://$(hostname -I | awk '{print $1}'):80/health | jq -e '.status == "healthy"' > /dev/null; then
    echo -e "${GREEN}✅ External access working!${NC}"
else
    echo -e "${YELLOW}⚠️  External access may need firewall configuration${NC}"
fi

echo -e "${GREEN}Deployment complete on $(hostname)!${NC}"

ENDSSH
}

# Main deployment logic
echo -e "${BLUE}Select deployment target:${NC}"
echo "1) Production (${PRODUCTION_HOST})"
echo "2) Development (${DEV_HOST})"
echo "3) Both"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        deploy_to_host $PRODUCTION_HOST "Production"
        ;;
    2)
        deploy_to_host $DEV_HOST "Development"
        ;;
    3)
        deploy_to_host $PRODUCTION_HOST "Production"
        echo
        deploy_to_host $DEV_HOST "Development"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}=== Deployment Summary ===${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update Vercel to point to the correct backend:"
echo "   - Production: http://${PRODUCTION_HOST}/api"
echo "   - Development: http://${DEV_HOST}/api"
echo ""
echo "2. Test the endpoints:"
echo "   curl http://${PRODUCTION_HOST}/health"
echo "   curl http://${DEV_HOST}/health"
echo ""
echo "3. Deploy frontend to Vercel:"
echo "   vercel --prod"
echo ""
echo -e "${GREEN}Deployment script complete!${NC}" 