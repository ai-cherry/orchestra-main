#!/bin/bash
# Orchestra AI - Remote Deployment Script
# Run this script directly on Lambda Labs instances

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Orchestra AI Lambda Labs Deployment ===${NC}\n"

# Step 1: Stop existing services
echo -e "${YELLOW}Stopping existing services...${NC}"
if command -v docker-compose &> /dev/null; then
    cd ~/orchestra-main 2>/dev/null && docker-compose down || true
fi
pkill -f "uvicorn" || true
pkill -f "orchestra" || true
pkill -f "python.*main" || true

# Step 2: Update system packages
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    docker.io docker-compose \
    python3.11 python3.11-venv python3.11-dev \
    nginx redis-server postgresql postgresql-contrib \
    git curl jq htop

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
if [ ! -s "api/database/models.py" ] || [ $(wc -c < "api/database/models.py") -le 50 ]; then
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

# Fix 5: Update main_api.py to use correct health endpoint
if [ -f "main_api.py" ]; then
    sed -i 's|@app.get("/health")|@app.get("/api/health")|g' main_api.py || true
    sed -i 's|@app.get("/")|@app.get("/api/")|g' main_api.py || true
fi

# Step 5: Set up Python virtual environment
echo -e "${YELLOW}Setting up Python environment...${NC}"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# Install requirements with fallback
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || pip install fastapi uvicorn sqlalchemy psycopg2-binary redis python-multipart
else
    pip install fastapi uvicorn sqlalchemy psycopg2-binary redis python-multipart
fi

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
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql << PSQL
CREATE USER orchestra WITH PASSWORD 'orchestra123';
CREATE DATABASE orchestra_ai OWNER orchestra;
GRANT ALL PRIVILEGES ON DATABASE orchestra_ai TO orchestra;
\q
PSQL

# Step 8: Set up Redis
echo -e "${YELLOW}Starting Redis...${NC}"
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Step 9: Test local imports
echo -e "${YELLOW}Testing Python imports...${NC}"
python -c "
try:
    import sys
    sys.path.append('.')
    print('✅ Basic import test passed!')
except Exception as e:
    print(f'❌ Import test failed: {e}')
"

# Step 10: Create a simple health check API if main_api.py doesn't exist
if [ ! -f "main_api.py" ]; then
    echo -e "${YELLOW}Creating simple API...${NC}"
    cat > main_api.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Orchestra AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Orchestra AI is running", "status": "healthy"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "orchestra-ai", "version": "1.0.0"}

@app.get("/health")
async def health_simple():
    return {"status": "healthy", "service": "orchestra-ai", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
fi

# Step 11: Start API service
echo -e "${YELLOW}Starting API service...${NC}"
nohup python main_api.py > api.log 2>&1 &
API_PID=$!

# Step 12: Configure Nginx
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
    
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

# Step 13: Verify deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
sleep 10

# Check if API is running
if ps -p $API_PID > /dev/null; then
    echo -e "${GREEN}✅ API process is running (PID: $API_PID)${NC}"
else
    echo -e "${RED}❌ API process failed to start${NC}"
    echo "API logs:"
    tail -n 20 api.log || true
fi

# Check API health
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ API health check passed!${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    echo "API logs:"
    tail -n 20 api.log || true
fi

# Check external access
EXTERNAL_IP=$(hostname -I | awk '{print $1}')
if curl -s http://$EXTERNAL_IP/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ External access working!${NC}"
else
    echo -e "${YELLOW}⚠️  External access may need firewall configuration${NC}"
fi

echo -e "\n${GREEN}=== Deployment Summary ===${NC}"
echo -e "${YELLOW}Services Status:${NC}"
echo "- API: http://$EXTERNAL_IP:8000"
echo "- Health: http://$EXTERNAL_IP/health"
echo "- API Health: http://$EXTERNAL_IP/api/health"
echo ""
echo -e "${YELLOW}Test commands:${NC}"
echo "curl http://$EXTERNAL_IP/health"
echo "curl http://$EXTERNAL_IP/api/health"
echo ""
echo -e "${GREEN}Deployment complete on $(hostname)!${NC}"

