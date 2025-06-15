#!/bin/bash

# Orchestra AI Complete Deployment Script
# This script deploys admin frontend to Vercel and all backend services to Lambda Labs

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
LAMBDA_LABS_IP="150.136.94.139"
LAMBDA_LABS_USER="ubuntu"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"

echo -e "${BLUE}🎼 Orchestra AI Complete Deployment${NC}"
echo "===================================="

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Deploy Admin Frontend to Vercel
deploy_admin_frontend() {
    echo -e "\n${YELLOW}Deploying Admin Frontend to Vercel...${NC}"
    
    if [ -d "modern-admin" ]; then
        cd modern-admin
        
        # Install dependencies
        echo "Installing dependencies..."
        npm install
        
        # Build the project
        echo "Building admin interface..."
        npm run build
        
        # Check if Vercel CLI is installed
        if ! command_exists vercel; then
            echo "Installing Vercel CLI..."
            npm i -g vercel
        fi
        
        # Deploy to Vercel
        echo "Deploying to Vercel..."
        vercel --prod --yes
        
        cd ..
        echo -e "${GREEN}✅ Admin frontend deployed successfully${NC}"
    else
        echo -e "${RED}❌ modern-admin directory not found${NC}"
    fi
}

# Setup Lambda Labs Backend
setup_lambda_backend() {
    echo -e "\n${YELLOW}Setting up Lambda Labs backend...${NC}"
    
    # Ensure SSH key path is expanded
    SSH_KEY_EXPANDED=$(eval echo "$SSH_KEY")
    
    # Create setup script
    cat > lambda_setup.sh << 'EOF'
#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /home/ubuntu/orchestra-dev

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip nginx supervisor redis-server

# Setup Python environment
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create supervisor configuration
echo "Creating supervisor configuration..."
cat > supervisor_config.conf << 'SUPERVISOR'
[unix_http_server]
file=/tmp/supervisor.sock

[supervisord]
logfile=/home/ubuntu/orchestra-dev/logs/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=false

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

[program:mcp_memory]
command=/home/ubuntu/orchestra-dev/venv/bin/python -m uvicorn memory_management_server:app --host 0.0.0.0 --port 8003 --workers 2
directory=/home/ubuntu/orchestra-dev/mcp_servers
autostart=true
autorestart=true
stdout_logfile=/home/ubuntu/orchestra-dev/logs/mcp_memory.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/mcp_memory_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api"

[program:mcp_portkey]
command=/home/ubuntu/orchestra-dev/venv/bin/python -m uvicorn portkey_mcp:app --host 0.0.0.0 --port 8004 --workers 2
directory=/home/ubuntu/orchestra-dev/packages/mcp-enhanced
autostart=true
autorestart=true
stdout_logfile=/home/ubuntu/orchestra-dev/logs/mcp_portkey.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/mcp_portkey_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api"

[program:api_server]
command=/home/ubuntu/orchestra-dev/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/home/ubuntu/orchestra-dev/api
autostart=true
autorestart=true
stdout_logfile=/home/ubuntu/orchestra-dev/logs/api.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/api_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api"

[program:ai_context]
command=/home/ubuntu/orchestra-dev/venv/bin/python context_service.py
directory=/home/ubuntu/orchestra-dev/.ai-context
autostart=true
autorestart=true
stdout_logfile=/home/ubuntu/orchestra-dev/logs/context_service.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/context_service_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev"

[group:orchestra]
programs=mcp_memory,mcp_portkey,api_server,ai_context
SUPERVISOR

# Configure Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/orchestra > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /mcp/memory {
        proxy_pass http://localhost:8003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /mcp/portkey {
        proxy_pass http://localhost:8004;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /context {
        proxy_pass http://localhost:8005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
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

# Setup systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/orchestra-supervisor.service > /dev/null << 'SYSTEMD'
[Unit]
Description=Orchestra AI Supervisor
After=network.target

[Service]
Type=forking
User=ubuntu
ExecStart=/usr/bin/supervisord -c /home/ubuntu/orchestra-dev/supervisor_config.conf
ExecStop=/usr/bin/supervisorctl shutdown
ExecReload=/usr/bin/supervisorctl reload
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
SYSTEMD

# Enable and start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable orchestra-supervisor.service
sudo systemctl restart orchestra-supervisor.service

# Check status
sleep 5
supervisorctl status

echo -e "${GREEN}✅ Backend deployment complete!${NC}"
EOF

    # Copy and execute setup script on Lambda Labs
    echo "Copying setup script to Lambda Labs..."
    scp -i "$SSH_KEY_EXPANDED" lambda_setup.sh "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP:/tmp/"
    
    echo "Executing setup on Lambda Labs..."
    ssh -i "$SSH_KEY_EXPANDED" "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP" "chmod +x /tmp/lambda_setup.sh && /tmp/lambda_setup.sh"
    
    # Clean up
    rm -f lambda_setup.sh
    
    echo -e "${GREEN}✅ Lambda Labs backend setup complete${NC}"
}

# Verify deployment
verify_deployment() {
    echo -e "\n${YELLOW}Verifying deployment...${NC}"
    
    # Test endpoints
    endpoints=(
        "http://$LAMBDA_LABS_IP/health:System Health"
        "http://$LAMBDA_LABS_IP/api/health:API Server"
        "http://$LAMBDA_LABS_IP/mcp/memory/health:MCP Memory"
        "http://$LAMBDA_LABS_IP/mcp/portkey/health:MCP Portkey"
        "http://$LAMBDA_LABS_IP/context/health:AI Context"
    )
    
    echo -e "\nChecking service endpoints:"
    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r url name <<< "$endpoint"
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ $name${NC}"
        else
            echo -e "  ${RED}❌ $name${NC}"
        fi
    done
}

# Main deployment process
main() {
    echo "Starting Orchestra AI complete deployment..."
    
    # Check SSH key exists
    SSH_KEY_EXPANDED=$(eval echo "$SSH_KEY")
    if [ ! -f "$SSH_KEY_EXPANDED" ]; then
        echo -e "${RED}❌ SSH key not found at $SSH_KEY_EXPANDED${NC}"
        echo "Please ensure you have the Lambda Labs SSH key configured."
        exit 1
    fi
    
    # Deploy admin frontend
    deploy_admin_frontend
    
    # Setup Lambda Labs backend
    setup_lambda_backend
    
    # Verify deployment
    verify_deployment
    
    echo -e "\n${GREEN}🎉 Orchestra AI Complete Deployment Finished!${NC}"
    echo -e "\nDeployment Summary:"
    echo "  - Admin Frontend: Deployed to Vercel"
    echo "  - Backend API: http://$LAMBDA_LABS_IP/api"
    echo "  - MCP Memory: http://$LAMBDA_LABS_IP/mcp/memory"
    echo "  - MCP Portkey: http://$LAMBDA_LABS_IP/mcp/portkey"
    echo "  - AI Context: http://$LAMBDA_LABS_IP/context"
    echo -e "\nServices are running via systemd with automatic restart on failure."
    echo "To manage services on Lambda Labs, SSH in and use:"
    echo "  supervisorctl status    # View status"
    echo "  supervisorctl restart all  # Restart all"
    echo "  systemctl status orchestra-supervisor  # Check systemd"
}

# Run main
main 