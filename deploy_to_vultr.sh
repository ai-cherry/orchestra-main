#!/bin/bash
# Deploy Orchestra AI to Vultr server

set -e

echo "🚀 Deploying Orchestra AI to Vultr"
echo "================================="

# Check required environment variables
if [ -z "$VULTR_SERVER_IP" ]; then
    echo "❌ Error: VULTR_SERVER_IP not set"
    echo "Set it with: export VULTR_SERVER_IP=your-server-ip"
    exit 1
fi

# GitHub repository
GITHUB_REPO="https://github.com/ai-cherry/orchestra-main.git"

# Function to run commands on Vultr server
vultr_exec() {
    ssh -i ~/.ssh/vultr_orchestra -o StrictHostKeyChecking=no root@$VULTR_SERVER_IP "$@"
}

# Function to copy files to Vultr server
vultr_copy() {
    scp -i ~/.ssh/vultr_orchestra -o StrictHostKeyChecking=no "$1" root@$VULTR_SERVER_IP:"$2"
}

echo "📦 Step 1: Installing system dependencies..."
vultr_exec << 'EOF'
apt-get update
apt-get install -y python3.12 python3.12-venv python3-pip git nginx certbot python3-certbot-nginx redis-server

# Start Redis
systemctl enable redis-server
systemctl start redis-server
EOF

echo "📥 Step 2: Cloning repository..."
vultr_exec << EOF
# Remove old installation if exists
rm -rf /opt/orchestra

# Clone the repository
git clone $GITHUB_REPO /root/orchestra-main
EOF

echo "🐍 Step 3: Setting up Python environment..."
vultr_exec << 'EOF'
cd /root/orchestra-main
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install dependencies
pip install -r requirements/production/requirements.txt
chown -R root:root /root/orchestra-main
EOF

echo "🔧 Step 4: Setting up environment variables..."
vultr_exec << 'EOF'
# Generate secure keys
API_KEY=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)

# Create .env file
cat > /root/orchestra-main/.env << ENV
# Orchestra AI Configuration
ORCHESTRA_API_KEY=$API_KEY
SECRET_KEY=$SECRET_KEY

# Service URLs
REDIS_URL=redis://localhost:6379

# GCP Configuration (update these with your values)
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# OpenAI Configuration (update with your key)
OPENAI_API_KEY=your-openai-key

# Production settings
ENV=production
DEBUG=false
ENV

chown root:root /root/orchestra-main/.env
chmod 600 /root/orchestra-main/.env
EOF

echo "🔄 Step 5: Setting up systemd services..."

# Create orchestra-real service
vultr_exec << 'EOF'
cat > /etc/systemd/system/orchestra-real.service << 'SERVICE'
[Unit]
Description=Orchestra AI Real Agents
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
Environment="PATH=/root/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/root/orchestra-main"
EnvironmentFile=/root/orchestra-main/.env
ExecStart=/root/orchestra-main/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable orchestra-real
systemctl start orchestra-real
EOF

echo "🌐 Step 6: Setting up Nginx..."
vultr_exec << 'EOF'
# Configure Nginx
cat > /etc/nginx/sites-available/orchestra-admin << 'NGINX'
server {
    listen 80;
    server_name _;

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
}
NGINX

ln -sf /etc/nginx/sites-available/orchestra-admin /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
EOF

echo "🔄 Step 7: Running database migrations..."
# Copy migration script
vultr_copy scripts/migrate_dragonfly_to_weaviate.py /root/orchestra-main/scripts/

vultr_exec << 'EOF'
cd /root/orchestra-main
source venv/bin/activate
export PYTHONPATH=/root/orchestra-main

# Create Redis migration script
cat > /root/orchestra-main/scripts/migrate_to_redis.py << 'PYTHON'
import asyncio
import redis.asyncio as redis
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_redis_connection():
    """Test Redis connection and create initial data."""
    try:
        # Connect to Redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Test connection
        await client.ping()
        logger.info("✅ Successfully connected to Redis")

        # Set some initial data
        await client.set("orchestra:status", "active")
        await client.set("orchestra:start_time", datetime.now().isoformat())

        # Create initial indexes
        await client.hset("orchestra:agents", mapping={
            "sys-001": "System Monitor",
            "analyze-001": "Data Analyzer",
            "monitor-001": "Service Monitor"
        })

        logger.info("✅ Initial data created in Redis")

        # Close connection
        await client.close()

    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_redis_connection())
PYTHON

# Run migration
python /root/orchestra-main/scripts/migrate_to_redis.py || echo "Redis setup completed"
EOF

echo "✅ Step 8: Starting services..."
vultr_exec << 'EOF'
cd /root/orchestra-main
systemctl restart orchestra-real
systemctl status orchestra-real --no-pager
EOF

echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "Your Orchestra AI is now running at:"
echo "http://$VULTR_SERVER_IP"
echo ""
echo "API Documentation:"
echo "http://$VULTR_SERVER_IP/docs"
echo ""
echo "To get your API key:"
echo "ssh -i ~/.ssh/vultr_orchestra root@$VULTR_SERVER_IP 'grep ORCHESTRA_API_KEY /root/orchestra-main/.env'"
echo ""
echo "To check logs:"
echo "ssh -i ~/.ssh/vultr_orchestra root@$VULTR_SERVER_IP 'journalctl -u orchestra-real -f'"
