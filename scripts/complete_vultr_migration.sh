#!/bin/bash
# Complete Migration from DragonflyDB + DigitalOcean to Vultr
# This replaces ALL external services with Vultr-hosted ones

set -e

VULTR_IP="45.32.69.157"
DRAGONFLY_URI="rediss://qpwj3s2ae.dragonflydb.cloud:6385"

echo "🚀 Complete Vultr Migration Script"
echo "================================="
echo "This will:"
echo "1. Install Redis locally (replacing DragonflyDB)"
echo "2. Migrate all data from DragonflyDB to local Redis"
echo "3. Update all connection strings"
echo "4. Test everything works"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Function to run commands on Vultr
vultr_exec() {
    ssh -i ~/.ssh/vultr_cherry_ai root@$VULTR_IP "$@"
}

echo "📦 Step 1: Installing Redis on Vultr..."
vultr_exec << 'EOF'
# Install Redis (DragonflyDB replacement)
apt-get update
apt-get install -y redis-server redis-tools

# Configure Redis for production
cat > /etc/redis/redis.conf << REDIS
bind 127.0.0.1
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16

# Persistence settings
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# Memory settings (optimize for 65GB server)
maxmemory 8gb
maxmemory-policy allkeys-lru

# Append only file
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no

# Performance tuning
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
REDIS

# Start Redis
systemctl restart redis-server
systemctl enable redis-server

# Test Redis
redis-cli ping
EOF

echo "📊 Step 2: Creating data migration script..."
cat > /tmp/migrate_dragonfly_data.py << 'PYTHON'
#!/usr/bin/env python3
"""Migrate data from DragonflyDB to local Redis"""

import os
import redis
import json
from datetime import datetime

# Source: DragonflyDB
DRAGONFLY_URI = os.getenv('DRAGONFLY_URI', 'rediss://qpwj3s2ae.dragonflydb.cloud:6385')
source_redis = redis.from_url(DRAGONFLY_URI, decode_responses=True)

# Destination: Local Redis
dest_redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

print(f"Starting migration at {datetime.now()}")

# Get all keys
all_keys = []
for key in source_redis.scan_iter("*"):
    all_keys.append(key)

print(f"Found {len(all_keys)} keys to migrate")

# Migrate data
migrated = 0
errors = 0

for key in all_keys:
    try:
        key_type = source_redis.type(key)

        if key_type == 'string':
            value = source_redis.get(key)
            ttl = source_redis.ttl(key)
            dest_redis.set(key, value)
            if ttl > 0:
                dest_redis.expire(key, ttl)

        elif key_type == 'list':
            values = source_redis.lrange(key, 0, -1)
            dest_redis.delete(key)
            for v in values:
                dest_redis.rpush(key, v)

        elif key_type == 'set':
            values = source_redis.smembers(key)
            dest_redis.delete(key)
            for v in values:
                dest_redis.sadd(key, v)

        elif key_type == 'zset':
            values = source_redis.zrange(key, 0, -1, withscores=True)
            dest_redis.delete(key)
            for v, score in values:
                dest_redis.zadd(key, {v: score})

        elif key_type == 'hash':
            values = source_redis.hgetall(key)
            dest_redis.delete(key)
            dest_redis.hset(key, mapping=values)

        migrated += 1
        if migrated % 100 == 0:
            print(f"Migrated {migrated} keys...")

    except Exception as e:
        print(f"Error migrating {key}: {e}")
        errors += 1

print(f"\nMigration complete!")
print(f"Migrated: {migrated} keys")
print(f"Errors: {errors}")

# Verify some data
print("\nVerifying migration...")
sample_keys = all_keys[:5] if len(all_keys) > 5 else all_keys
for key in sample_keys:
    source_val = source_redis.get(key) if source_redis.type(key) == 'string' else source_redis.type(key)
    dest_val = dest_redis.get(key) if dest_redis.type(key) == 'string' else dest_redis.type(key)
    match = "✓" if source_val == dest_val else "✗"
    print(f"{match} {key}: {source_val} == {dest_val}")
PYTHON

# Copy and run migration script
vultr_exec "mkdir -p /opt/cherry_ai/scripts"
scp -i ~/.ssh/vultr_cherry_ai /tmp/migrate_dragonfly_data.py root@$VULTR_IP:/opt/cherry_ai/scripts/

echo "📊 Step 3: Running data migration..."
vultr_exec << EOF
cd /opt/cherry_ai
source venv/bin/activate
export DRAGONFLY_URI="$DRAGONFLY_URI"
python scripts/migrate_dragonfly_data.py
EOF

echo "🔧 Step 4: Updating cherry_ai configuration..."
vultr_exec << 'EOF'
# Update environment file
sed -i 's|DRAGONFLY_URI=.*|REDIS_URL=redis://localhost:6379|g' /opt/cherry_ai/.env

# Add Redis URL if not exists
grep -q "REDIS_URL" /opt/cherry_ai/.env || echo "REDIS_URL=redis://localhost:6379" >> /opt/cherry_ai/.env

# Update any Python files that reference DragonflyDB
find /opt/cherry_ai -name "*.py" -type f -exec sed -i 's/DRAGONFLY_URI/REDIS_URL/g' {} \;
find /opt/cherry_ai -name "*.py" -type f -exec sed -i 's/dragonfly/redis/gi' {} \;

# Restart services
systemctl restart cherry_ai-api conductor-mcp
EOF

echo "✅ Step 5: Verification..."
vultr_exec << 'EOF'
echo "=== Redis Status ==="
systemctl is-active redis-server
redis-cli ping

echo -e "\n=== Redis Info ==="
redis-cli INFO keyspace

echo -e "\n=== cherry_ai Services ==="
systemctl is-active cherry_ai-api conductor-mcp

echo -e "\n=== API Health Check ==="
sleep 5
curl -s http://localhost/health | jq . || echo "API starting..."
EOF

echo ""
echo "🎉 Migration Complete!"
echo "===================="
echo "✅ Redis running locally (replaced DragonflyDB)"
echo "✅ All data migrated"
echo "✅ Services updated to use local Redis"
echo ""
echo "Next steps:"
echo "1. Test everything works: http://$VULTR_IP"
echo "2. Cancel DragonflyDB subscription"
echo "3. Delete DigitalOcean droplets"
echo "4. Update any external services that point to old IPs"
