#!/bin/bash
# 🚀 Cherry AI Lambda Labs Production Setup Script
# This script sets up the complete Cherry AI environment on Lambda Labs

set -e

echo "🚀 Cherry AI Lambda Labs Production Setup"
echo "========================================="
echo "📍 Server: $(hostname) ($(hostname -I | awk '{print $1}'))"
echo "🖥️  System: $(uname -a)"
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt-get install -y \
    python3.10 python3.10-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    certbot python3-certbot-nginx \
    git curl wget \
    build-essential \
    libssl-dev libffi-dev \
    supervisor

# Install Docker for Weaviate
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Clone Cherry AI repository
echo "📥 Cloning Cherry AI repository..."
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/ai-cherry/orchestra-main.git cherry-ai
sudo chown -R ubuntu:ubuntu /opt/cherry-ai
cd /opt/cherry-ai

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
python3.10 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup PostgreSQL
echo "🐘 Setting up PostgreSQL..."
sudo -u postgres psql << EOF
CREATE USER cherry_ai WITH PASSWORD 'CherryAI2024!';
CREATE DATABASE cherry_ai_production OWNER cherry_ai;
GRANT ALL PRIVILEGES ON DATABASE cherry_ai_production TO cherry_ai;
EOF

# Configure Redis
echo "🔴 Configuring Redis..."
sudo sed -i 's/^# bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
sudo sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf
sudo systemctl restart redis-server

# Setup Weaviate with Docker
echo "🔮 Setting up Weaviate..."
docker run -d \
  --name weaviate \
  --restart always \
  -p 8080:8080 \
  -e QUERY_DEFAULTS_LIMIT=100 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  semitechnologies/weaviate:latest

# Create systemd service for Cherry AI
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/cherry-ai.service > /dev/null << EOF
[Unit]
Description=Cherry AI Production Service
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cherry-ai
Environment="PATH=/opt/cherry-ai/venv/bin"
ExecStart=/opt/cherry-ai/venv/bin/python /opt/cherry-ai/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for collaboration bridge
sudo tee /etc/systemd/system/cherry-ai-bridge.service > /dev/null << EOF
[Unit]
Description=Cherry AI Collaboration Bridge
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cherry-ai
Environment="PATH=/opt/cherry-ai/venv/bin"
ExecStart=/opt/cherry-ai/venv/bin/python /opt/cherry-ai/cherry_ai_live_collaboration_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/cherry-ai > /dev/null << 'EOF'
server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me 150.136.94.139;

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

    location /ws {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/cherry-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 8765/tcp
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 6379/tcp  # Redis
sudo ufw allow 8080/tcp  # Weaviate
sudo ufw --force enable

# Enable and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable cherry-ai.service
sudo systemctl enable cherry-ai-bridge.service
sudo systemctl start cherry-ai.service
sudo systemctl start cherry-ai-bridge.service

# Create admin user
echo "👤 Creating admin user..."
cd /opt/cherry-ai
source venv/bin/activate
python << EOF
import os
os.environ['DATABASE_URL'] = 'postgresql://cherry_ai:CherryAI2024!@localhost/cherry_ai_production'
# Add admin user creation logic here if needed
EOF

# Display status
echo ""
echo "✅ Cherry AI Lambda Labs Setup Complete!"
echo "========================================"
echo ""
echo "🌐 URLs:"
echo "   Main App: http://150.136.94.139"
echo "   WebSocket: ws://150.136.94.139:8765"
echo ""
echo "📊 Services Status:"
sudo systemctl status cherry-ai --no-pager | head -n 5
echo ""
sudo systemctl status cherry-ai-bridge --no-pager | head -n 5
echo ""
echo "🔍 Check logs with:"
echo "   sudo journalctl -u cherry-ai -f"
echo "   sudo journalctl -u cherry-ai-bridge -f"
echo ""
echo "🚀 Next steps:"
echo "1. Update DNS to point cherry-ai.me → 150.136.94.139"
echo "2. Run: sudo certbot --nginx -d cherry-ai.me -d www.cherry-ai.me"
echo "3. Access Cherry AI at https://cherry-ai.me" 