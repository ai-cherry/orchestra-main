#!/bin/bash
# Vultr Single Server Setup for Orchestra AI
# Optimized for 4vCPU / 16GB RAM server

set -e

echo "🚀 Orchestra AI Single Server Setup"
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
cat > /etc/postgresql/16/main/conf.d/orchestra.conf << EOF
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

# Create Orchestra user and directories
useradd -m -s /bin/bash orchestra
usermod -aG docker orchestra

mkdir -p /opt/orchestra
mkdir -p /var/log/orchestra
chown -R orchestra:orchestra /opt/orchestra /var/log/orchestra

# Configure systemd services for auto-restart
cat > /etc/systemd/system/orchestra-api.service << EOF
[Unit]
Description=Orchestra API Service
After=network.target postgresql.service

[Service]
Type=simple
User=orchestra
WorkingDirectory=/opt/orchestra
Environment="PYTHONPATH=/opt/orchestra"
ExecStart=/opt/orchestra/venv/bin/uvicorn agent.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/orchestra-mcp.service << EOF
[Unit]
Description=Orchestra MCP Service
After=network.target

[Service]
Type=simple
User=orchestra
WorkingDirectory=/opt/orchestra/mcp_server
Environment="PYTHONPATH=/opt/orchestra"
ExecStart=/opt/orchestra/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx as reverse proxy
cat > /etc/nginx/sites-available/orchestra << EOF
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

ln -sf /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Performance monitoring script
cat > /usr/local/bin/orchestra-monitor << 'EOF'
#!/bin/bash
echo "=== Orchestra System Monitor ==="
echo "CPU & Memory:"
echo "-------------"
ps aux | grep -E "(postgres|docker|python|uvicorn)" | grep -v grep | awk '{printf "%-20s %5s %5s\n", $11, $3"%", $4"%"}'
echo ""
echo "Disk Usage:"
df -h / /var/lib/docker /var/lib/postgresql
echo ""
echo "Service Status:"
systemctl is-active orchestra-api orchestra-mcp docker postgresql nginx | paste -d' ' - - - - -
EOF

chmod +x /usr/local/bin/orchestra-monitor

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone repository: git clone <your-repo> /opt/orchestra"
echo "2. Set up Python venv: cd /opt/orchestra && python3.12 -m venv venv"
echo "3. Install dependencies: source venv/bin/activate && pip install -r requirements/base.txt"
echo "4. Configure environment variables in /opt/orchestra/.env"
echo "5. Enable services: systemctl enable --now orchestra-api orchestra-mcp"
echo ""
echo "Monitor performance: orchestra-monitor"
