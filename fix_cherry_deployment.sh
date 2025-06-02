#!/bin/bash
# Comprehensive fix for cherry-ai.me deployment
# This script fixes frontend version issues and backend API problems

set -e  # Exit on error

echo "🚀 Starting Cherry AI Deployment Fix..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1 successful${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

# 1. Build the latest frontend
echo -e "\n${YELLOW}Step 1: Building latest frontend...${NC}"
cd /root/orchestra-main/admin-ui

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    check_success "npm install"
fi

# Build the frontend
echo "Building production frontend..."
npm run build
check_success "Frontend build"

# 2. Find nginx root directory
echo -e "\n${YELLOW}Step 2: Locating nginx configuration...${NC}"
NGINX_ROOT=""

# Check common nginx config locations
if [ -f "/etc/nginx/sites-available/default" ]; then
    NGINX_ROOT=$(grep -E "^\s*root" /etc/nginx/sites-available/default | head -1 | awk '{print $2}' | tr -d ';')
elif [ -f "/etc/nginx/nginx.conf" ]; then
    NGINX_ROOT=$(grep -E "^\s*root" /etc/nginx/nginx.conf | head -1 | awk '{print $2}' | tr -d ';')
fi

# Default to common location if not found
if [ -z "$NGINX_ROOT" ]; then
    NGINX_ROOT="/var/www/html"
fi

echo "Nginx root directory: $NGINX_ROOT"

# 3. Backup old files and deploy new frontend
echo -e "\n${YELLOW}Step 3: Deploying new frontend...${NC}"

# Create backup
if [ -d "$NGINX_ROOT" ]; then
    BACKUP_DIR="/root/nginx_backup_$(date +%Y%m%d_%H%M%S)"
    echo "Creating backup at $BACKUP_DIR..."
    sudo cp -r "$NGINX_ROOT" "$BACKUP_DIR"
    check_success "Backup creation"
fi

# Clear old files and copy new build
echo "Clearing old frontend files..."
sudo rm -rf "$NGINX_ROOT"/*
check_success "Clear old files"

echo "Copying new frontend build..."
sudo cp -r /root/orchestra-main/admin-ui/dist/* "$NGINX_ROOT/"
check_success "Deploy new frontend"

# Set proper permissions
sudo chown -R www-data:www-data "$NGINX_ROOT"
sudo chmod -R 755 "$NGINX_ROOT"

# 4. Create environment configuration for backend
echo -e "\n${YELLOW}Step 4: Setting up backend environment...${NC}"

# Create environment file
cat > /etc/orchestra.env << 'EOF'
# Orchestra AI Backend Environment Configuration
ENVIRONMENT=production

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=720

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=OrchAI_Admin2024!
ADMIN_EMAIL=admin@orchestra.ai

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://orchestra:orchestra@localhost/orchestra

# Redis (if using)
REDIS_URL=redis://localhost:6379

# LLM API Keys (add your actual keys here)
# PORTKEY_API_KEY=your-portkey-api-key
# OPENROUTER_API_KEY=your-openrouter-api-key
# OPENAI_API_KEY=your-openai-api-key
# ANTHROPIC_API_KEY=your-anthropic-api-key

# Monitoring
METRICS_ENABLED=true
PROMETHEUS_PORT=9090

# CORS
CORS_ORIGINS=["https://cherry-ai.me", "http://localhost:3000"]
EOF

check_success "Environment file creation"

# 5. Create Python virtual environment if it doesn't exist
echo -e "\n${YELLOW}Step 5: Setting up Python environment...${NC}"
cd /root/orchestra-main

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    check_success "Virtual environment creation"
fi

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
check_success "Python dependencies installation"

# 6. Create systemd service for backend
echo -e "\n${YELLOW}Step 6: Creating systemd service for backend...${NC}"

cat > /etc/systemd/system/orchestra-backend.service << 'EOF'
[Unit]
Description=Orchestra AI Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
EnvironmentFile=/etc/orchestra.env
ExecStart=/root/orchestra-main/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

check_success "Systemd service creation"

# 7. Update nginx configuration
echo -e "\n${YELLOW}Step 7: Updating nginx configuration...${NC}"

# Create nginx config for cherry-ai.me
cat > /etc/nginx/sites-available/cherry-ai << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # SSL configuration (update paths if needed)
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;
    
    # Root directory
    root /var/www/html;
    index index.html;
    
    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
    
    # Metrics endpoint (optional)
    location /metrics {
        proxy_pass http://127.0.0.1:9090/metrics;
        allow 127.0.0.1;
        deny all;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/cherry-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t
check_success "Nginx configuration test"

# 8. Start/restart services
echo -e "\n${YELLOW}Step 8: Starting services...${NC}"

# Reload systemd
sudo systemctl daemon-reload

# Enable and start backend
sudo systemctl enable orchestra-backend
sudo systemctl restart orchestra-backend
check_success "Backend service start"

# Restart nginx
sudo systemctl restart nginx
check_success "Nginx restart"

# 9. Clear any CDN/browser caches
echo -e "\n${YELLOW}Step 9: Cache clearing instructions...${NC}"
echo "If you're using Cloudflare or another CDN:"
echo "1. Log into your CDN dashboard"
echo "2. Purge/clear the cache for cherry-ai.me"
echo "3. Wait 2-3 minutes for propagation"

# 10. Check service status
echo -e "\n${YELLOW}Step 10: Checking service status...${NC}"

# Check backend status
if systemctl is-active --quiet orchestra-backend; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running${NC}"
    echo "Check logs with: journalctl -u orchestra-backend -f"
fi

# Check nginx status
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx is not running${NC}"
fi

# Test API endpoint
echo -e "\nTesting API endpoint..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$API_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${YELLOW}⚠ API returned status code: $API_RESPONSE${NC}"
    echo "This might be normal if the API requires authentication"
fi

# Final instructions
echo -e "\n${GREEN}======================================"
echo "Deployment fix completed!"
echo "======================================${NC}"
echo ""
echo "📋 Next steps:"
echo "1. Visit https://cherry-ai.me (use incognito mode to avoid cache)"
echo "2. Login with: admin / OrchAI_Admin2024!"
echo "3. If you still see the old version:"
echo "   - Clear your browser cache completely"
echo "   - Clear CDN cache if using one"
echo "   - Check nginx error logs: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "📊 Monitoring commands:"
echo "- Backend logs: journalctl -u orchestra-backend -f"
echo "- Backend status: systemctl status orchestra-backend"
echo "- Nginx logs: tail -f /var/log/nginx/access.log"
echo ""
echo "⚠️  IMPORTANT: Add your LLM API keys to /etc/orchestra.env"
echo "   Then restart the backend: systemctl restart orchestra-backend"