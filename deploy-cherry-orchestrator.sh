#!/bin/bash

# Cherry AI Orchestrator Deployment Script
# Production deployment with blue-green strategy

set -euo pipefail

# Configuration
DEPLOY_DIR="/var/www/cherry-ai-orchestrator"
BACKUP_DIR="/var/backups/cherry-ai"
NGINX_CONFIG="/etc/nginx/sites-available/cherry-ai-orchestrator"
DOMAIN="cherry-ai.me"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🍒 Cherry AI Orchestrator Deployment${NC}"
echo "=================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-deployment checks
echo -e "${BLUE}Running pre-deployment checks...${NC}"

if ! command_exists nginx; then
    echo -e "${RED}Error: nginx is not installed${NC}"
    exit 1
fi

if ! command_exists rsync; then
    echo -e "${RED}Error: rsync is not installed${NC}"
    exit 1
fi

# Create directories if they don't exist
echo -e "${BLUE}Setting up directories...${NC}"
sudo mkdir -p "$DEPLOY_DIR"
sudo mkdir -p "$BACKUP_DIR"
sudo mkdir -p "${DEPLOY_DIR}.blue"
sudo mkdir -p "${DEPLOY_DIR}.green"

# Determine current active deployment
if [ -L "$DEPLOY_DIR" ]; then
    CURRENT=$(readlink "$DEPLOY_DIR" | grep -o '\.(blue|green)$' | tr -d '.')
    if [ "$CURRENT" = "blue" ]; then
        NEW="green"
    else
        NEW="blue"
    fi
else
    # First deployment
    CURRENT="none"
    NEW="blue"
fi

echo -e "${BLUE}Current deployment: ${CURRENT}${NC}"
echo -e "${BLUE}New deployment: ${NEW}${NC}"

# Backup current deployment
if [ "$CURRENT" != "none" ]; then
    echo -e "${BLUE}Backing up current deployment...${NC}"
    sudo tar -czf "${BACKUP_DIR}/cherry-ai-orchestrator-${CURRENT}-${TIMESTAMP}.tar.gz" -C "${DEPLOY_DIR}.${CURRENT}" .
fi

# Deploy new version
echo -e "${BLUE}Deploying new version to ${NEW} environment...${NC}"
DEPLOY_TARGET="${DEPLOY_DIR}.${NEW}"

# Copy files
sudo rsync -av --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.env' \
    cherry-ai-orchestrator-final.html \
    cherry-ai-orchestrator.js \
    "$DEPLOY_TARGET/"

# Set permissions
sudo chown -R www-data:www-data "$DEPLOY_TARGET"
sudo chmod -R 755 "$DEPLOY_TARGET"

# Create nginx configuration
echo -e "${BLUE}Configuring nginx...${NC}"
sudo tee "$NGINX_CONFIG" > /dev/null <<EOF
server {
    listen 80;
    server_name orchestrator.${DOMAIN} www.orchestrator.${DOMAIN};
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name orchestrator.${DOMAIN} www.orchestrator.${DOMAIN};
    
    # SSL configuration (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
    
    # Root directory
    root ${DEPLOY_DIR};
    index cherry-ai-orchestrator-final.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy (if needed)
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Default location
    location / {
        try_files \$uri \$uri/ /cherry-ai-orchestrator-final.html;
    }
}
EOF

# Test nginx configuration
echo -e "${BLUE}Testing nginx configuration...${NC}"
sudo nginx -t

if [ $? -ne 0 ]; then
    echo -e "${RED}Nginx configuration test failed!${NC}"
    exit 1
fi

# Enable site if not already enabled
if [ ! -L "/etc/nginx/sites-enabled/cherry-ai-orchestrator" ]; then
    sudo ln -s "$NGINX_CONFIG" "/etc/nginx/sites-enabled/cherry-ai-orchestrator"
fi

# Health check on new deployment
echo -e "${BLUE}Running health check on new deployment...${NC}"
# Add your health check logic here
# For now, just check if files exist
if [ ! -f "${DEPLOY_TARGET}/cherry-ai-orchestrator-final.html" ] || [ ! -f "${DEPLOY_TARGET}/cherry-ai-orchestrator.js" ]; then
    echo -e "${RED}Health check failed: Required files not found${NC}"
    exit 1
fi

# Switch symlink (blue-green deployment)
echo -e "${BLUE}Switching to new deployment...${NC}"
sudo ln -sfn "$DEPLOY_TARGET" "$DEPLOY_DIR"

# Reload nginx
echo -e "${BLUE}Reloading nginx...${NC}"
sudo systemctl reload nginx

# Post-deployment verification
echo -e "${BLUE}Verifying deployment...${NC}"
sleep 2

# Check if site is accessible
if command_exists curl; then
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/" || echo "000")
    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
        echo -e "${GREEN}✓ Site is accessible (HTTP ${HTTP_STATUS})${NC}"
    else
        echo -e "${RED}✗ Site returned HTTP ${HTTP_STATUS}${NC}"
        echo -e "${RED}Rolling back...${NC}"
        
        # Rollback
        if [ "$CURRENT" != "none" ]; then
            sudo ln -sfn "${DEPLOY_DIR}.${CURRENT}" "$DEPLOY_DIR"
            sudo systemctl reload nginx
            echo -e "${RED}Rollback completed${NC}"
        fi
        exit 1
    fi
fi

# Cleanup old deployment after successful switch
if [ "$CURRENT" != "none" ] && [ "$CURRENT" != "$NEW" ]; then
    echo -e "${BLUE}Deployment successful! Old ${CURRENT} environment kept for rollback.${NC}"
    echo -e "${BLUE}To remove old deployment, run: sudo rm -rf ${DEPLOY_DIR}.${CURRENT}${NC}"
fi

echo -e "${GREEN}✅ Cherry AI Orchestrator deployed successfully!${NC}"
echo -e "${GREEN}Access at: https://orchestrator.${DOMAIN}${NC}"

# Create rollback script
cat > rollback-cherry-orchestrator.sh << 'ROLLBACK'
#!/bin/bash
# Rollback Cherry AI Orchestrator

DEPLOY_DIR="/var/www/cherry-ai-orchestrator"
CURRENT=$(readlink "$DEPLOY_DIR" | grep -o '\.(blue|green)$' | tr -d '.')

if [ "$CURRENT" = "blue" ]; then
    OLD="green"
else
    OLD="blue"
fi

if [ -d "${DEPLOY_DIR}.${OLD}" ]; then
    echo "Rolling back from ${CURRENT} to ${OLD}..."
    sudo ln -sfn "${DEPLOY_DIR}.${OLD}" "$DEPLOY_DIR"
    sudo systemctl reload nginx
    echo "Rollback completed!"
else
    echo "No previous deployment found to rollback to"
    exit 1
fi
ROLLBACK

chmod +x rollback-cherry-orchestrator.sh
echo -e "${BLUE}Rollback script created: ./rollback-cherry-orchestrator.sh${NC}"