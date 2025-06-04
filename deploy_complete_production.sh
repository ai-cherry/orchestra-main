#!/bin/bash
# Cherry AI Orchestrator - Complete Production Deployment
# This script deploys the entire Cherry AI infrastructure to production

set -e  # Exit on any error

echo "🚀 Cherry AI Orchestrator - Production Deployment"
echo "=================================================="
echo "Server: $(hostname)"
echo "Date: $(date)"
echo "User: $(whoami)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (use sudo)"
fi

# Validate environment variables
required_vars=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "GEMINI_API_KEY"
    "WEAVIATE_URL"
    "WEAVIATE_API_KEY"
    "PINECONE_API_KEY"
    "VULTR_API_KEY"
    "PULUMI_ACCESS_TOKEN"
)

log "Validating environment variables..."
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error "Environment variable $var is not set"
    fi
done

# System update and package installation
log "Updating system packages..."
apt update && apt upgrade -y

log "Installing required packages..."
apt install -y \
    nginx \
    redis-server \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    curl \
    git \
    htop \
    ufw \
    certbot \
    python3-certbot-nginx \
    supervisor

# Configure firewall
log "Configuring firewall..."
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# Create application user
log "Creating application user..."
if ! id "cherry-ai" &>/dev/null; then
    useradd -m -s /bin/bash cherry-ai
    usermod -aG sudo cherry-ai
fi

# Setup application directory
log "Setting up application directory..."
mkdir -p /var/www/cherry-ai
chown -R cherry-ai:cherry-ai /var/www/cherry-ai

# Clone or update repository
log "Cloning/updating repository..."
cd /var/www/cherry-ai
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/ai-cherry/orchestra-main.git .
fi

# Set ownership
chown -R cherry-ai:cherry-ai /var/www/cherry-ai

# Install Python dependencies
log "Installing Python dependencies..."
sudo -u cherry-ai python3 -m venv venv
sudo -u cherry-ai ./venv/bin/pip install --upgrade pip
sudo -u cherry-ai ./venv/bin/pip install -r requirements.txt

# Install Node.js dependencies
log "Installing Node.js dependencies..."
if [ -f "package.json" ]; then
    sudo -u cherry-ai npm install
fi

# Configure PostgreSQL
log "Configuring PostgreSQL..."
sudo -u postgres createuser -D -A -P cherry_ai || true
sudo -u postgres createdb -O cherry_ai cherry_ai_db || true

# Configure Redis
log "Configuring Redis..."
systemctl start redis-server
systemctl enable redis-server

# Create environment file
log "Creating environment configuration..."
cat > /var/www/cherry-ai/.env << EOF
# Cherry AI Production Environment
ENVIRONMENT=production
DEBUG=false

# AI Service APIs
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY:-}

# Vector Databases
WEAVIATE_URL=${WEAVIATE_URL}
WEAVIATE_API_KEY=${WEAVIATE_API_KEY}
PINECONE_API_KEY=${PINECONE_API_KEY}

# Cloud Infrastructure
VULTR_API_KEY=${VULTR_API_KEY}
PULUMI_ACCESS_TOKEN=${PULUMI_ACCESS_TOKEN}
PAPERSPACE_API_KEY=${PAPERSPACE_API_KEY:-}

# Additional Services
NOTION_API_KEY=${NOTION_API_KEY:-}
PORTKEY_API_KEY=${PORTKEY_API_KEY:-}
PORTKEY_CONFIG=${PORTKEY_CONFIG:-}
REDIS_USER_API_KEY=${REDIS_USER_API_KEY:-}
REDIS_ACCOUNT_KEY=${REDIS_ACCOUNT_KEY:-}

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=cherry_ai
POSTGRES_DB=cherry_ai_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application Configuration
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
FLASK_DEBUG=false
EOF

# Set proper permissions for environment file
chown cherry-ai:cherry-ai /var/www/cherry-ai/.env
chmod 600 /var/www/cherry-ai/.env

# Configure Nginx
log "Configuring Nginx..."
cat > /etc/nginx/sites-available/cherry-ai.me << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name cherry-ai.me www.cherry-ai.me;
    
    root /var/www/cherry-ai/admin-interface;
    index index.html enhanced-production-interface.html;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    location / {
        try_files $uri $uri/ /enhanced-production-interface.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /mcp/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/cherry-ai.me /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t && systemctl reload nginx

# Configure Supervisor for application services
log "Configuring Supervisor..."
cat > /etc/supervisor/conf.d/cherry-ai.conf << EOF
[group:cherry-ai]
programs=cherry-ai-api,cherry-ai-mcp-codebase,cherry-ai-mcp-infrastructure

[program:cherry-ai-api]
command=/var/www/cherry-ai/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
directory=/var/www/cherry-ai
user=cherry-ai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cherry-ai-api.log
environment=PATH="/var/www/cherry-ai/venv/bin"

[program:cherry-ai-mcp-codebase]
command=/var/www/cherry-ai/venv/bin/python mcp_server/servers/enhanced_codebase_server.py
directory=/var/www/cherry-ai
user=cherry-ai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cherry-ai-mcp-codebase.log
environment=PATH="/var/www/cherry-ai/venv/bin",PYTHONPATH="/var/www/cherry-ai"

[program:cherry-ai-mcp-infrastructure]
command=/var/www/cherry-ai/venv/bin/python mcp_server/servers/infrastructure_manager.py
directory=/var/www/cherry-ai
user=cherry-ai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cherry-ai-mcp-infrastructure.log
environment=PATH="/var/www/cherry-ai/venv/bin",PYTHONPATH="/var/www/cherry-ai"
EOF

# Reload supervisor
supervisorctl reread
supervisorctl update

# Start services
log "Starting services..."
systemctl start nginx postgresql redis-server supervisor
systemctl enable nginx postgresql redis-server supervisor

# Setup SSL certificate (Let's Encrypt)
log "Setting up SSL certificate..."
certbot --nginx -d cherry-ai.me -d www.cherry-ai.me --non-interactive --agree-tos --email admin@cherry-ai.me || warn "SSL setup failed, continuing without HTTPS"

# Create systemd service for health monitoring
log "Setting up health monitoring..."
cat > /etc/systemd/system/cherry-ai-health.service << EOF
[Unit]
Description=Cherry AI Health Monitor
After=network.target

[Service]
Type=simple
User=cherry-ai
WorkingDirectory=/var/www/cherry-ai
ExecStart=/var/www/cherry-ai/venv/bin/python scripts/health_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cherry-ai-health
systemctl start cherry-ai-health

# Setup log rotation
log "Configuring log rotation..."
cat > /etc/logrotate.d/cherry-ai << EOF
/var/log/cherry-ai*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 cherry-ai cherry-ai
    postrotate
        supervisorctl restart cherry-ai:*
    endscript
}
EOF

# Create backup script
log "Setting up backup system..."
cat > /usr/local/bin/cherry-ai-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/cherry-ai"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump cherry_ai_db > $BACKUP_DIR/database_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz -C /var/www cherry-ai

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/nginx/sites-available/cherry-ai.me /etc/supervisor/conf.d/cherry-ai.conf

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/cherry-ai-backup.sh

# Setup cron job for backups
echo "0 2 * * * root /usr/local/bin/cherry-ai-backup.sh" > /etc/cron.d/cherry-ai-backup

# Final health check
log "Performing final health check..."
sleep 10

# Check services
services=("nginx" "postgresql" "redis-server" "supervisor")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        log "✅ $service is running"
    else
        error "❌ $service is not running"
    fi
done

# Check website
if curl -f http://localhost > /dev/null 2>&1; then
    log "✅ Website is responding"
else
    warn "⚠️ Website may not be responding correctly"
fi

# Display final status
echo ""
echo "🎉 Cherry AI Orchestrator Deployment Complete!"
echo "=============================================="
echo "🌐 Website: http://cherry-ai.me"
echo "🔒 HTTPS: https://cherry-ai.me (if SSL setup succeeded)"
echo "📊 Admin Interface: Enhanced production interface active"
echo "🤖 MCP Servers: Running on ports 8001+"
echo "📈 Monitoring: Health checks active"
echo "💾 Backups: Daily at 2 AM"
echo ""
echo "📋 Service Status:"
for service in "${services[@]}"; do
    status=$(systemctl is-active $service)
    echo "   $service: $status"
done
echo ""
echo "📁 Important Paths:"
echo "   Application: /var/www/cherry-ai"
echo "   Logs: /var/log/cherry-ai*.log"
echo "   Backups: /var/backups/cherry-ai"
echo "   Config: /etc/nginx/sites-available/cherry-ai.me"
echo ""
echo "🔧 Management Commands:"
echo "   Restart services: supervisorctl restart cherry-ai:*"
echo "   View logs: tail -f /var/log/cherry-ai*.log"
echo "   Manual backup: /usr/local/bin/cherry-ai-backup.sh"
echo ""
echo "✅ Your Cherry AI Orchestrator is now live and operational!"

