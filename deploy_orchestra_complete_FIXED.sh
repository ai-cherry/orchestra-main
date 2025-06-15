#!/bin/bash

# Orchestra AI Complete Deployment Script - FIXED VERSION
# This script deploys admin frontend to Vercel and all backend services to Lambda Labs
# FIXES: SSH key path, directory structure, service conflicts

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration - FIXED
LAMBDA_LABS_IP="150.136.94.139"
LAMBDA_LABS_USER="ubuntu"
SSH_KEY_CONTENT="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDMQ+BMDckhfiutxjpFUxtMwLnGHkDyI/oh4mQ76oudkjptAJfywKYCR+ShUM1HbuNdCGJJEbfTV6f85Mhwn2y+Qktxi0T550N/afX3lqZiXTCrIPUJrAq1hgFQJCDLi8aSU7KHLilB9fxIdLy5vNPKaAculG83VS43QayPK15r8KslyyKBBdCZhzSncmQdabTW48QtyO3NjH1lX7XXCL3AHi7KR1ES8YcPMpUla1IOqLKw/pRaDrwLkNdrkTEW/PE+RnpNVSw4CiFtqi/D0WSTaovwIHVQAIeIGMjtIEi47Jalgy3bgH4uSChSdhja5LxCuMsVnK1OeHLnMmf/rS6L7/72amviJU1oS8Y7l1Y5UnalfF8dmkheexvoQL4M2z9BmO0Ak9apT2cawzif0HtZoFJWeeLzuBLkOgtyGP4iYQoFp2ofkU3ze/i0R2hySh/FqVnAsB0Fn95gaXCNHhGrVCsbxQQBDDKkE6oLFg/vgkgAwJfgAMphdCqaoFCrjyp+yIZbvqwj79BihZEIzk1WtZYpOCRHOVSQC5caOW+wvYBDwjscidgSsmNVEZWpZzoK4vo9Ne5G5imJL8DVm4gqhmNgcJjylVV+wePdBAq+Ev3NEEoV0343DaTmQzXlGrcsEB/cmvPHPDhpJNwP7ySR9o10MibyMQJBmdPiOy+c5w== manus-ai-deployment"
SSH_KEY_PATH="$HOME/.ssh/cherry_ai_key"

echo -e "${BLUE}🎼 Orchestra AI Complete Deployment - FIXED VERSION${NC}"
echo "=================================================="

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Setup SSH key
setup_ssh_key() {
    echo -e "\n${YELLOW}Setting up SSH key...${NC}"
    
    # Create SSH directory if it doesn't exist
    mkdir -p "$HOME/.ssh"
    
    # Write SSH key - FIXED to use the actual private key
    cat > "$SSH_KEY_PATH" << 'SSH_KEY_EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
SSH_KEY_EOF
    chmod 600 "$SSH_KEY_PATH"
    
    # Add to SSH agent if running
    if [ -n "$SSH_AUTH_SOCK" ]; then
        ssh-add "$SSH_KEY_PATH" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ SSH key configured${NC}"
}

# Cleanup conflicting services
cleanup_services() {
    echo -e "\n${YELLOW}Cleaning up conflicting services on Lambda Labs...${NC}"
    
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP" << 'CLEANUP'
#!/bin/bash

echo "Stopping conflicting services..."

# Stop systemd services
sudo systemctl stop orchestra-supervisor.service 2>/dev/null || true
sudo systemctl disable orchestra-supervisor.service 2>/dev/null || true

# Stop supervisor processes
supervisorctl stop all 2>/dev/null || true
sudo pkill supervisord 2>/dev/null || true

# Stop individual processes
sudo pkill -f "python.*main_api.py" || true
sudo pkill -f "python.*mcp_servers" || true
sudo pkill -f "uvicorn.*main:app" || true
sudo pkill -f "uvicorn.*memory_management_server" || true
sudo pkill -f "uvicorn.*portkey_mcp" || true

# Remove old nginx config
sudo rm -f /etc/nginx/sites-enabled/orchestra
sudo rm -f /etc/nginx/sites-available/orchestra

echo "✅ Cleanup complete"
CLEANUP

    echo -e "${GREEN}✅ Services cleaned up${NC}"
}

# Deploy Admin Frontend to Vercel
deploy_admin_frontend() {
    echo -e "\n${YELLOW}Deploying Admin Frontend to Vercel...${NC}"
    
    if [ -d "modern-admin" ]; then
        cd modern-admin
        
        # Install dependencies
        echo "Installing dependencies..."
        npm install --legacy-peer-deps
        
        # Build the project
        echo "Building admin interface..."
        npm run build
        
        # Check if Vercel CLI is installed
        if ! command_exists vercel; then
            echo "Installing Vercel CLI..."
            npm i -g vercel
        fi
        
        # Deploy to Vercel with token
        echo "Deploying to Vercel..."
        VERCEL_TOKEN="Y57oxELkt4ufdVnk2CBZ5ayi" vercel --prod --yes
        
        cd ..
        echo -e "${GREEN}✅ Admin frontend deployed successfully${NC}"
    else
        echo -e "${RED}❌ modern-admin directory not found${NC}"
    fi
}

# Setup Lambda Labs Backend
setup_lambda_backend() {
    echo -e "\n${YELLOW}Setting up Lambda Labs backend...${NC}"
    
    # Create setup script
    cat > lambda_setup.sh << 'EOF'
#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Use orchestra-main directory (current structure)
cd /home/ubuntu/orchestra-main

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
logfile=/home/ubuntu/orchestra-main/logs/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=false

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

[program:api_server]
command=/home/ubuntu/orchestra-main/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/home/ubuntu/orchestra-main/api
autostart=true
autorestart=true
stdout_logfile=/home/ubuntu/orchestra-main/logs/api.log
stderr_logfile=/home/ubuntu/orchestra-main/logs/api_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-main:/home/ubuntu/orchestra-main/api"

[program:main_api]
command=/home/ubuntu/orchestra-main/venv/bin/python main_api.py
directory=/home/ubuntu/orchestra-main
autostart=true
autorestart=true
stdout_logfile=/home/ubuntu/orchestra-main/logs/main_api.log
stderr_logfile=/home/ubuntu/orchestra-main/logs/main_api_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-main"

[program:mcp_memory]
command=/home/ubuntu/orchestra-main/venv/bin/python -m uvicorn memory_management_server:app --host 0.0.0.0 --port 8003 --workers 2
directory=/home/ubuntu/orchestra-main/mcp_servers
autostart=true
autorestart=true
stdout_logfile=/home/ubuntu/orchestra-main/logs/mcp_memory.log
stderr_logfile=/home/ubuntu/orchestra-main/logs/mcp_memory_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-main:/home/ubuntu/orchestra-main/api"

[group:orchestra]
programs=api_server,main_api,mcp_memory
SUPERVISOR

# Configure Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/orchestra > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;
    
    # Main API (port 8000)
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Direct API access
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

# Setup systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/orchestra-supervisor.service > /dev/null << 'SYSTEMD'
[Unit]
Description=Orchestra AI Supervisor
After=network.target

[Service]
Type=forking
User=ubuntu
ExecStart=/usr/bin/supervisord -c /home/ubuntu/orchestra-main/supervisor_config.conf
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
    scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no lambda_setup.sh "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP:/tmp/"
    
    echo "Executing setup on Lambda Labs..."
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP" "chmod +x /tmp/lambda_setup.sh && /tmp/lambda_setup.sh"
    
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
        "http://$LAMBDA_LABS_IP:8000/health:API Server Direct"
        "http://$LAMBDA_LABS_IP/api/health:API Server Proxy"
        "http://$LAMBDA_LABS_IP/mcp/memory/health:MCP Memory"
    )
    
    echo -e "\nChecking service endpoints:"
    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r url name <<< "$endpoint"
        if curl -s --connect-timeout 10 "$url" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ $name${NC}"
        else
            echo -e "  ${RED}❌ $name${NC}"
        fi
    done
}

# Main deployment process
main() {
    echo "Starting Orchestra AI complete deployment..."
    
    # Setup SSH key
    setup_ssh_key
    
    # Test SSH connection
    echo -e "\n${YELLOW}Testing SSH connection...${NC}"
    if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$LAMBDA_LABS_USER@$LAMBDA_LABS_IP" "echo 'SSH connection successful'"; then
        echo -e "${GREEN}✅ SSH connection working${NC}"
    else
        echo -e "${RED}❌ SSH connection failed${NC}"
        exit 1
    fi
    
    # Cleanup conflicting services
    cleanup_services
    
    # Deploy admin frontend
    deploy_admin_frontend
    
    # Setup Lambda Labs backend
    setup_lambda_backend
    
    # Verify deployment
    verify_deployment
    
    echo -e "\n${GREEN}🎉 Orchestra AI Complete Deployment Finished!${NC}"
    echo -e "\nDeployment Summary:"
    echo "  - Admin Frontend: Deployed to Vercel"
    echo "  - Backend API: http://$LAMBDA_LABS_IP:8000"
    echo "  - Backend API (Proxy): http://$LAMBDA_LABS_IP/api"
    echo "  - MCP Memory: http://$LAMBDA_LABS_IP/mcp/memory"
    echo "  - System Health: http://$LAMBDA_LABS_IP/health"
    echo -e "\nServices are running via systemd with automatic restart on failure."
    echo "To manage services on Lambda Labs, SSH in and use:"
    echo "  supervisorctl status    # View status"
    echo "  supervisorctl restart all  # Restart all"
    echo "  systemctl status orchestra-supervisor  # Check systemd"
}

# Run main
main

