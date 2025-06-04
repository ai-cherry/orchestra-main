#!/bin/bash
# Vultr Single Server Setup for Cherry AI
# Optimized for 4vCPU / 16GB RAM server

set -e

echo "🚀 Cherry AI Single Server Setup"
echo "=================================="

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y \
    python3.12 python3.12-venv python3-pip \
    postgresql-16 postgresql-contrib-16 \
    docker.io docker-compose \
    nginx certbot python3-certbot-nginx \
    htop iotop nethogs \
    git curl wget jq

# Configure PostgreSQL for optimal performance
cat > /etc/postgresql/16/main/conf.d/cherry_ai.conf << EOF
# Optimized for 16GB RAM server
shared_buffers = 2GB
effective_cache_size = 8GB
maintenance_work_mem = 512MB
work_mem = 32MB
max_connections = 100
EOF

systemctl restart postgresql

# Configure Docker for Weaviate
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker

# Create cherry_ai user and directories
useradd -m -s /bin/bash cherry_ai
usermod -aG docker cherry_ai

mkdir -p /opt/cherry_ai
mkdir -p /var/log/cherry_ai
chown -R cherry_ai:cherry_ai /opt/cherry_ai /var/log/cherry_ai

# Configure systemd services for auto-restart
cat > /etc/systemd/system/cherry_ai-api.service << EOF
[Unit]
Description=cherry_ai API Service
After=network.target postgresql.service

[Service]
Type=simple
User=cherry_ai
WorkingDirectory=/opt/cherry_ai
Environment="PYTHONPATH=/opt/cherry_ai"
ExecStart=/opt/cherry_ai/venv/bin/uvicorn agent.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/conductor-mcp.service << EOF
[Unit]
Description=cherry_ai MCP Service
After=network.target

[Service]
Type=simple
User=cherry_ai
WorkingDirectory=/opt/cherry_ai/mcp_server
Environment="PYTHONPATH=/opt/cherry_ai"
ExecStart=/opt/cherry_ai/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx as reverse proxy
cat > /etc/nginx/sites-available/cherry_ai << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /weaviate/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cherry_ai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Performance monitoring script
cat > /usr/local/bin/cherry_ai-monitor << 'EOF'
#!/bin/bash
echo "=== cherry_ai System Monitor ==="
echo "CPU & Memory:"
echo "-------------"
ps aux | grep -E "(postgres|docker|python|uvicorn)" | grep -v grep | awk '{printf "%-20s %5s %5s\n", $11, $3"%", $4"%"}'
echo ""
echo "Disk Usage:"
df -h / /var/lib/docker /var/lib/postgresql
echo ""
echo "Service Status:"
systemctl is-active cherry_ai-api conductor-mcp docker postgresql nginx | paste -d' ' - - - - -
EOF

chmod +x /usr/local/bin/cherry_ai-monitor

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone repository: git clone <your-repo> /opt/cherry_ai"
echo "2. Set up Python venv: cd /opt/cherry_ai && python3.12 -m venv venv"
echo "3. Install dependencies: source venv/bin/activate && pip install -r requirements/base.txt"
echo "4. Configure environment variables in /opt/cherry_ai/.env"
echo "5. Enable services: systemctl enable --now cherry_ai-api conductor-mcp"
echo ""
echo "Monitor performance: cherry_ai-monitor"
