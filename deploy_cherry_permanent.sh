#!/bin/bash
# Permanent deployment script for cherry-ai.me
# Ensures site is always running with latest version and no cache issues

set -e

echo "🚀 Deploying Cherry AI for 24/7 Operation"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1 successful${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

# 1. Build frontend with cache-busting
echo -e "\n${YELLOW}Step 1: Building frontend with cache-busting...${NC}"
cd /root/orchestra-main/admin-ui

# Add timestamp to build for cache busting
export VITE_BUILD_TIME=$(date +%s)
echo "Build timestamp: $VITE_BUILD_TIME"

# Clean install and build
rm -rf node_modules dist
npm install
npm run build
check_success "Frontend build"

# 2. Add cache-busting to index.html
echo -e "\n${YELLOW}Step 2: Adding cache-busting headers...${NC}"

# Add version query parameter to all assets
cd dist
TIMESTAMP=$(date +%s)
sed -i "s/\.js\"/\.js?v=$TIMESTAMP\"/g" index.html
sed -i "s/\.css\"/\.css?v=$TIMESTAMP\"/g" index.html
check_success "Cache-busting added"

# 3. Deploy frontend with proper headers
echo -e "\n${YELLOW}Step 3: Deploying frontend...${NC}"

# Find nginx root
NGINX_ROOT="/var/www/html"
if [ -f "/etc/nginx/sites-available/default" ]; then
    NGINX_ROOT=$(grep -E "^\s*root" /etc/nginx/sites-available/default | head -1 | awk '{print $2}' | tr -d ';' || echo "/var/www/html")
fi

# Clear old files completely
sudo rm -rf "$NGINX_ROOT"/*
sudo rm -rf "$NGINX_ROOT"/.* 2>/dev/null || true

# Copy new files
sudo cp -r * "$NGINX_ROOT/"
sudo chown -R www-data:www-data "$NGINX_ROOT"
check_success "Frontend deployment"

# 4. Configure nginx with aggressive no-cache headers
echo -e "\n${YELLOW}Step 4: Configuring nginx for no-cache...${NC}"

cat > /tmp/cherry-ai-nginx << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name cherry-ai.me www.cherry-ai.me;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Root directory
    root /var/www/html;
    index index.html;
    
    # Aggressive cache prevention for HTML
    location / {
        try_files $uri $uri/ /index.html;
        
        # No cache for HTML files
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Force refresh
        if_modified_since off;
        expires off;
        etag off;
    }
    
    # Cache static assets but with version control
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # But if there's a version parameter, respect it
        if ($args ~* "v=") {
            add_header Cache-Control "public, max-age=31536000, immutable";
        }
    }
    
    # API proxy with no cache
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
        
        # No cache for API
        proxy_no_cache 1;
        proxy_cache_bypass 1;
        add_header Cache-Control "no-store, no-cache, must-revalidate" always;
        
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
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'; img-src 'self' https: data: blob:;" always;
}
EOF

# Install new nginx config
sudo cp /tmp/cherry-ai-nginx /etc/nginx/sites-available/cherry-ai
sudo ln -sf /etc/nginx/sites-available/cherry-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t
check_success "Nginx configuration"

# 5. Set up backend with auto-restart
echo -e "\n${YELLOW}Step 5: Setting up backend for 24/7 operation...${NC}"

# Create comprehensive environment file
cat > /etc/orchestra.env << 'EOF'
# Orchestra AI Backend Environment
ENVIRONMENT=production

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=720

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=OrchAI_Admin2024!
ADMIN_EMAIL=admin@orchestra.ai

# Database
DATABASE_URL=postgresql://orchestra:orchestra@localhost/orchestra

# Redis
REDIS_URL=redis://localhost:6379

# CORS - Allow your domain
CORS_ORIGINS=["https://cherry-ai.me", "https://www.cherry-ai.me"]

# Monitoring
METRICS_ENABLED=true
PROMETHEUS_PORT=9090

# Add your LLM API keys here
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# PORTKEY_API_KEY=...
# OPENROUTER_API_KEY=...
EOF

# Create systemd service with auto-restart
cat > /etc/systemd/system/orchestra-backend.service << 'EOF'
[Unit]
Description=Orchestra AI Backend API
After=network.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
EnvironmentFile=/etc/orchestra.env
ExecStartPre=/bin/bash -c 'cd /root/orchestra-main && source venv/bin/activate && pip install -r requirements.txt'
ExecStart=/root/orchestra-main/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=orchestra-backend

# Restart conditions
RestartPreventExitStatus=0
SuccessExitStatus=0 143

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

# 6. Create health check script
echo -e "\n${YELLOW}Step 6: Setting up health monitoring...${NC}"

cat > /usr/local/bin/orchestra-health-check.sh << 'EOF'
#!/bin/bash
# Health check and auto-recovery script

# Check if backend is responding
if ! curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend health check failed, restarting..."
    systemctl restart orchestra-backend
    sleep 10
fi

# Check if nginx is responding
if ! curl -f -s -k https://localhost > /dev/null 2>&1; then
    echo "Nginx health check failed, restarting..."
    systemctl restart nginx
fi

# Clear nginx cache if needed
if [ -d /var/cache/nginx ]; then
    find /var/cache/nginx -type f -delete
fi
EOF

chmod +x /usr/local/bin/orchestra-health-check.sh

# Add to crontab for regular checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/orchestra-health-check.sh") | crontab -

# 7. Set up log rotation
echo -e "\n${YELLOW}Step 7: Configuring log rotation...${NC}"

cat > /etc/logrotate.d/orchestra << 'EOF'
/var/log/orchestra/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload orchestra-backend > /dev/null 2>&1 || true
    endscript
}
EOF

# 8. Start all services
echo -e "\n${YELLOW}Step 8: Starting all services...${NC}"

# Create log directory
mkdir -p /var/log/orchestra

# Reload systemd
systemctl daemon-reload

# Enable and start services
systemctl enable orchestra-backend
systemctl restart orchestra-backend
check_success "Backend service start"

systemctl restart nginx
check_success "Nginx restart"

# 9. Clear all caches
echo -e "\n${YELLOW}Step 9: Clearing all caches...${NC}"

# Clear nginx cache
if [ -d /var/cache/nginx ]; then
    rm -rf /var/cache/nginx/*
fi

# Clear any CDN cache (if using Cloudflare)
if command -v curl &> /dev/null; then
    echo "If using Cloudflare, run this command with your API credentials:"
    echo 'curl -X POST "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID/purge_cache" \
         -H "X-Auth-Email: your-email@example.com" \
         -H "X-Auth-Key: your-api-key" \
         -H "Content-Type: application/json" \
         --data "{\"purge_everything\":true}"'
fi

# 10. Verify deployment
echo -e "\n${YELLOW}Step 10: Verifying deployment...${NC}"

sleep 5

# Check services
echo -e "\n${BLUE}Service Status:${NC}"
systemctl is-active orchestra-backend && echo -e "${GREEN}✓ Backend is running${NC}" || echo -e "${RED}✗ Backend failed${NC}"
systemctl is-active nginx && echo -e "${GREEN}✓ Nginx is running${NC}" || echo -e "${RED}✗ Nginx failed${NC}"

# Test endpoints
echo -e "\n${BLUE}Endpoint Tests:${NC}"
curl -s -o /dev/null -w "Frontend HTTPS: %{http_code}\n" https://cherry-ai.me || echo "Frontend test failed"
curl -s -o /dev/null -w "API Health: %{http_code}\n" http://localhost:8000/health || echo "API test failed"

# Final summary
echo -e "\n${GREEN}========================================"
echo "✅ Deployment Complete!"
echo "========================================${NC}"
echo ""
echo "🌐 Your site is now:"
echo "   - Always running (auto-restart on failure)"
echo "   - Always serving the latest version"
echo "   - No browser cache issues"
echo "   - Health checks every 5 minutes"
echo ""
echo "📋 Access your site:"
echo "   URL: https://cherry-ai.me"
echo "   Login: admin / OrchAI_Admin2024!"
echo ""
echo "⚠️  IMPORTANT: Add your LLM API keys to /etc/orchestra.env"
echo "   Then run: systemctl restart orchestra-backend"
echo ""
echo "📊 Monitor services:"
echo "   - Logs: journalctl -u orchestra-backend -f"
echo "   - Status: systemctl status orchestra-backend"
echo "   - Health: tail -f /var/log/syslog | grep orchestra-health"