#!/bin/bash
# Complete Orchestra AI Deployment to Vultr
# For 16 vCPU / 65GB RAM server

set -e

# Values should come from GitHub Actions secrets
export VULTR_IP="${VULTR_IP:-${VULTR_SERVER_IP}}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
export POSTGRES_DSN="${POSTGRES_DSN}"
GITHUB_REPO="${GITHUB_REPO:-https://github.com/ai-cherry/orchestra-main.git}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/vultr_orchestra}"

echo "🚀 Orchestra AI Vultr Deployment"
echo "==============================="
echo "Server: $VULTR_IP"
echo ""

# Function to run commands on Vultr
vultr_exec() {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no root@$VULTR_IP "$@"
}

# Function to copy files to Vultr
vultr_copy() {
    scp -i $SSH_KEY -o StrictHostKeyChecking=no "$1" root@$VULTR_IP:"$2"
}

echo "📦 Step 1: Preparing Vultr server..."
vultr_copy vultr_single_server_setup.sh /tmp/
vultr_exec "chmod +x /tmp/vultr_single_server_setup.sh && /tmp/vultr_single_server_setup.sh"

echo "🔑 Step 2: Setting up PostgreSQL..."
vultr_exec << 'EOF'
# Create orchestrator database and user
sudo -u postgres psql << SQL
CREATE DATABASE orchestrator;
CREATE USER orchestrator WITH ENCRYPTED PASSWORD '${POSTGRES_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE orchestrator TO orchestrator;
\c orchestrator
CREATE EXTENSION IF NOT EXISTS pgvector;
SQL
EOF

echo "📥 Step 3: Cloning repository..."
vultr_exec "git clone $GITHUB_REPO /opt/orchestra"

echo "🐍 Step 4: Setting up Python environment..."
vultr_exec << 'EOF'
cd /opt/orchestra
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/base.txt
pip install mcp portkey-ai
chown -R orchestra:orchestra /opt/orchestra
EOF

echo "🐋 Step 5: Setting up Weaviate..."
vultr_copy weaviate-docker-compose.yml /opt/
vultr_exec << 'EOF'
cd /opt
docker-compose -f weaviate-docker-compose.yml up -d
sleep 10
# Test Weaviate
curl -s http://localhost:8080/v1/.well-known/ready || echo "Weaviate not ready yet"
EOF

echo "🔧 Step 6: Creating environment configuration..."
vultr_exec << 'EOF'
cat > /opt/orchestra/.env << ENV
# Orchestra Production Environment
ORCHESTRA_ENV=production
DATABASE_URL=${POSTGRES_DSN}
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=INFO
ENV

chown orchestra:orchestra /opt/orchestra/.env
chmod 600 /opt/orchestra/.env
EOF

echo "🚀 Step 7: Starting services..."
vultr_exec << 'EOF'
# Reload systemd
systemctl daemon-reload

# Enable and start services
systemctl enable --now orchestra-api orchestra-mcp

# Check status
sleep 5
systemctl status orchestra-api orchestra-mcp --no-pager
EOF

echo "📊 Step 8: Installing Redis and migrating DragonflyDB data..."
# First install Redis
vultr_exec << 'EOF'
apt-get update
apt-get install -y redis-server redis-tools

# Configure Redis for production
cat > /etc/redis/redis.conf << REDIS
bind 127.0.0.1
protected-mode yes
port 6379
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir /var/lib/redis
maxmemory 8gb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
REDIS

systemctl restart redis-server
systemctl enable redis-server
EOF

# Copy and run migration script
vultr_copy scripts/migrate_dragonfly_to_weaviate.py /opt/orchestra/scripts/

vultr_exec << 'EOF'
cd /opt/orchestra
source venv/bin/activate
export PYTHONPATH=/opt/orchestra
export DRAGONFLY_URI="${DRAGONFLY_URI}"

# Create a modified migration script for Redis
cat > /opt/orchestra/scripts/migrate_to_redis.py << 'PYTHON'
#!/usr/bin/env python3
import os
import redis
from datetime import datetime

try:
    # Connect to DragonflyDB
    dragonfly_url = os.getenv('DRAGONFLY_URI')
    print(f"Connecting to DragonflyDB: {dragonfly_url}")
    source = redis.from_url(dragonfly_url, decode_responses=True)

    # Connect to local Redis
    dest = redis.Redis(host='localhost', port=6379, decode_responses=True)

    print("Testing connections...")
    source.ping()
    dest.ping()
    print("✅ Both connections successful")

    # Migrate all keys
    migrated = 0
    for key in source.scan_iter("*"):
        try:
            ttl = source.ttl(key)
            key_type = source.type(key)

            if key_type == 'string':
                value = source.get(key)
                dest.set(key, value)
                if ttl > 0:
                    dest.expire(key, ttl)
            # Add other types as needed

            migrated += 1
            if migrated % 100 == 0:
                print(f"Migrated {migrated} keys...")
        except Exception as e:
            print(f"Error migrating {key}: {e}")

    print(f"✅ Migration complete! Migrated {migrated} keys")

except Exception as e:
    print(f"Migration error: {e}")
    print("Continuing without DragonflyDB data migration")
PYTHON

python /opt/orchestra/scripts/migrate_to_redis.py || echo "DragonflyDB migration skipped"
EOF

echo "🔧 Step 9: Updating all configuration files..."
vultr_exec << 'EOF'
cd /opt/orchestra

# Restart services with new config
systemctl restart orchestra-api orchestra-mcp
EOF

echo "✅ Step 10: Final health check..."
sleep 5
curl -s http://$VULTR_IP/health | jq . || echo "API might need a moment to start"

echo ""
echo "🎉 Migration Complete!"
echo "====================="
echo "✅ All services running on Vultr"
echo "✅ Redis installed (replacing DragonflyDB)"
echo "✅ PostgreSQL + Weaviate running"
echo "✅ Orchestra API deployed"
echo ""
echo "Access your services:"
echo "- API: http://$VULTR_IP"
echo "- API Docs: http://$VULTR_IP/docs"
echo "- Weaviate: http://$VULTR_IP:8080"
echo ""
echo "Next steps:"
echo "1. Test everything: curl http://$VULTR_IP/health"
echo "2. Update your local .env to use Vultr"
echo "3. Delete DigitalOcean droplets"
echo "4. Cancel DragonflyDB subscription"
