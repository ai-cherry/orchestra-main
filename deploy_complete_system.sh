#!/bin/bash

# Orchestra AI Complete System Deployment
# Deploys admin frontend to Vercel and all backend services to Lambda Labs

set -e

echo "🎼 Orchestra AI Complete System Deployment"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
LAMBDA_LABS_IP="150.136.94.139"
LAMBDA_LABS_USER="ubuntu"
SSH_KEY="~/.ssh/orchestra_lambda"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Deploy Admin Frontend to Vercel
deploy_admin_frontend() {
    echo -e "\n${BLUE}=== Deploying Admin Frontend to Vercel ===${NC}"
    cd modern-admin
    
    # Check if Vercel CLI is installed
    if ! command_exists vercel; then
        echo "Installing Vercel CLI..."
        npm i -g vercel
    fi
    
    # Build the admin interface
    echo "Building admin interface..."
    npm install
    npm run build
    
    # Deploy to Vercel
    echo "Deploying to Vercel..."
    vercel --prod --yes
    
    cd ..
    echo -e "${GREEN}✅ Admin frontend deployed to Vercel${NC}"
}

# Deploy Backend to Lambda Labs
deploy_backend() {
    echo -e "\n${BLUE}=== Deploying Backend to Lambda Labs ===${NC}"
    
    # Create deployment package
    echo "Creating deployment package..."
    cat > deploy_package.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
# This script runs on the Lambda Labs instance

cd /home/ubuntu/orchestra-dev

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip nginx supervisor

# Create virtual environment
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service for Orchestra Supervisor
echo "Creating systemd service..."
sudo tee /etc/systemd/system/orchestra-supervisor.service > /dev/null << 'SERVICE'
[Unit]
Description=Orchestra AI Supervisor
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/orchestra-dev
Environment="PATH=/home/ubuntu/orchestra-dev/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api"
ExecStart=/home/ubuntu/orchestra-dev/venv/bin/python /home/ubuntu/orchestra-dev/orchestra_supervisor_enhanced.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/orchestra-dev/logs/supervisor.log
StandardError=append:/home/ubuntu/orchestra-dev/logs/supervisor_error.log

[Install]
WantedBy=multi-user.target
SERVICE

# Create logs directory
mkdir -p /home/ubuntu/orchestra-dev/logs

# Configure Nginx as reverse proxy
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/orchestra > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;
    
    # API Server
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Admin Interface
    location /admin {
        proxy_pass http://localhost:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # MCP Memory Server
    location /mcp/memory {
        proxy_pass http://localhost:8003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Portkey MCP Server
    location /mcp/portkey {
        proxy_pass http://localhost:8004;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # AI Context Service
    location /context {
        proxy_pass http://localhost:8005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Health check endpoint
    location /health {
        return 200 "Orchestra AI System Healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINX

# Enable Nginx site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# Enable and start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable orchestra-supervisor.service
sudo systemctl restart orchestra-supervisor.service

# Setup firewall
echo "Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000:8005/tcp
sudo ufw --force enable

echo "✅ Backend deployment complete!"
DEPLOY_SCRIPT

    # Copy deployment script to Lambda Labs
    echo "Copying deployment script to Lambda Labs..."
    scp -i "$SSH_KEY" deploy_package.sh "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP:/tmp/"
    
    # Execute deployment on Lambda Labs
    echo "Executing deployment on Lambda Labs..."
    ssh -i "$SSH_KEY" "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP" "chmod +x /tmp/deploy_package.sh && /tmp/deploy_package.sh"
    
    # Clean up
    rm -f deploy_package.sh
    
    echo -e "${GREEN}✅ Backend deployed to Lambda Labs${NC}"
}

# Verify deployment
verify_deployment() {
    echo -e "\n${BLUE}=== Verifying Deployment ===${NC}"
    
    # Check backend health
    echo "Checking backend services..."
    
    if curl -s "http://$LAMBDA_LABS_IP/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend system healthy${NC}"
    else
        echo -e "${RED}❌ Backend system health check failed${NC}"
    fi
    
    # Check individual services
    echo -e "\nChecking individual services:"
    
    services=(
        "/api/health:API Server"
        "/mcp/memory/health:MCP Memory Server"
        "/mcp/portkey/health:Portkey MCP Server"
        "/context/health:AI Context Service"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r endpoint name <<< "$service"
        if curl -s "http://$LAMBDA_LABS_IP$endpoint" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ $name${NC}"
        else
            echo -e "  ${RED}❌ $name${NC}"
        fi
    done
    
    echo -e "\n${GREEN}🎉 Deployment Summary:${NC}"
    echo "  - Admin Frontend: Deployed to Vercel"
    echo "  - Backend API: http://$LAMBDA_LABS_IP/api"
    echo "  - MCP Memory: http://$LAMBDA_LABS_IP/mcp/memory"
    echo "  - MCP Portkey: http://$LAMBDA_LABS_IP/mcp/portkey"
    echo "  - AI Context: http://$LAMBDA_LABS_IP/context"
    echo "  - Services: Running via systemd (auto-restart on failure)"
}

# Main deployment process
main() {
    echo "Starting complete system deployment..."
    
    # Deploy admin frontend
    deploy_admin_frontend
    
    # Deploy backend services
    deploy_backend
    
    # Verify deployment
    verify_deployment
    
    echo -e "\n${GREEN}✅ Complete system deployment finished!${NC}"
}

# Run main
main 