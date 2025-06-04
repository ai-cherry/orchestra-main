#!/bin/bash
# Orchestra Complete Setup and Automation
# Fixes all issues and starts intelligent automation

set -e

echo "🎼 Orchestra Complete Setup & Automation"
echo "======================================"

# 1. Fix Weaviate by using simpler configuration
echo "1️⃣ Fixing Weaviate configuration..."

# Create a fixed docker-compose for Weaviate
cat > docker-compose.weaviate-fix.yml << 'EOF'
version: '3.8'

services:
  weaviate:
    image: semitechnologies/weaviate:1.19.6
    container_name: cherry_ai_weaviate
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/v1/.well-known/ready"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  weaviate_data:
    external: true

networks:
  default:
    name: cherry_ai_network
    external: true
EOF

# Stop and remove the problematic Weaviate
docker-compose -f docker-compose.production.yml stop weaviate
docker-compose -f docker-compose.production.yml rm -f weaviate

# Start the fixed Weaviate
docker-compose -f docker-compose.weaviate-fix.yml up -d

echo "✅ Weaviate fixed and restarted"

# 2. Wait for services to be healthy
echo ""
echo "2️⃣ Waiting for services to be healthy..."

check_health() {
    local service=$1
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        health=$(docker inspect cherry_ai_$service --format='{{.State.Health.Status}}' 2>/dev/null || echo "not_found")
        
        if [ "$health" = "healthy" ]; then
            echo "✅ $service is healthy"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo "⚠️  $service failed to become healthy"
    return 1
}

# Check each service
for service in postgres redis weaviate; do
    check_health $service || true
done

# 3. Create systemd service for automation
echo ""
echo "3️⃣ Creating systemd service for automation..."

# Create the automation daemon script
cat > scripts/orchestra_daemon.py << 'EOF'
#!/usr/bin/env python3
"""Orchestra Automation Daemon - Simple and Reliable"""

import asyncio
import subprocess
import logging
import json
import os
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestra_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OrchestraDaemon:
    def __init__(self):
        self.running = True
        self.services = ["postgres", "redis", "weaviate"]
        self.mcp_servers = {
            "memory": {"script": "mcp_server/servers/memory_server.py", "port": 8003},
            "tools": {"script": "mcp_server/servers/tools_server.py", "port": 8006}
        }
        
    async def run(self):
        logger.info("🚀 Orchestra Daemon Started")
        
        while self.running:
            try:
                # Check Docker services
                for service in self.services:
                    await self.check_docker_service(service)
                
                # Check MCP servers
                for name, config in self.mcp_servers.items():
                    await self.check_mcp_server(name, config)
                
                # Wait before next check
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Daemon error: {e}")
                await asyncio.sleep(60)
    
    async def check_docker_service(self, service):
        """Check and heal Docker service"""
        try:
            result = subprocess.run(
                ["docker", "inspect", f"cherry_ai_{service}", "--format", "{{.State.Health.Status}}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 or result.stdout.strip() != "healthy":
                logger.warning(f"Service {service} unhealthy, restarting...")
                
                if service == "weaviate":
                    subprocess.run(["docker-compose", "-f", "docker-compose.weaviate-fix.yml", "restart", service])
                else:
                    subprocess.run(["docker-compose", "-f", "docker-compose.production.yml", "restart", service])
                    
        except Exception as e:
            logger.error(f"Error checking {service}: {e}")
    
    async def check_mcp_server(self, name, config):
        """Check and start MCP server if needed"""
        try:
            # Check if port is in use
            result = subprocess.run(
                ["lsof", "-i", f":{config['port']}"],
                capture_output=True
            )
            
            if result.returncode != 0 and Path(config['script']).exists():
                logger.info(f"Starting MCP {name} server...")
                subprocess.Popen(
                    ["python3", config['script']],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            logger.error(f"Error checking MCP {name}: {e}")


if __name__ == "__main__":
    daemon = OrchestraDaemon()
    asyncio.run(daemon.run())
EOF

chmod +x scripts/orchestra_daemon.py

# Create systemd service
sudo tee /etc/systemd/system/orchestra.service > /dev/null << EOF
[Unit]
Description=Orchestra Automation System
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which python3) $(pwd)/scripts/orchestra_daemon.py
Restart=always
RestartSec=30
StandardOutput=append:$(pwd)/logs/orchestra_daemon.log
StandardError=append:$(pwd)/logs/orchestra_daemon.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable orchestra.service
sudo systemctl start orchestra.service

echo "✅ Automation service installed and started"

# 4. Create convenience commands
echo ""
echo "4️⃣ Creating convenience commands..."

# Create orchestra command
cat > /tmp/orchestra << 'EOF'
#!/bin/bash
# Orchestra command-line interface

case "$1" in
    status)
        echo "🎼 Orchestra Status"
        echo "=================="
        echo ""
        echo "Services:"
        docker-compose -f docker-compose.production.yml ps
        echo ""
        echo "Automation:"
        sudo systemctl status orchestra.service --no-pager
        ;;
    logs)
        tail -f logs/orchestra_daemon.log
        ;;
    restart)
        sudo systemctl restart orchestra.service
        echo "✅ Orchestra restarted"
        ;;
    stop)
        sudo systemctl stop orchestra.service
        echo "✅ Orchestra stopped"
        ;;
    start)
        sudo systemctl start orchestra.service
        echo "✅ Orchestra started"
        ;;
    *)
        echo "Usage: orchestra {status|logs|restart|stop|start}"
        ;;
esac
EOF

sudo mv /tmp/orchestra /usr/local/bin/orchestra
sudo chmod +x /usr/local/bin/orchestra

echo "✅ Orchestra command installed"

# 5. Final status check
echo ""
echo "5️⃣ Final Status Check..."
echo ""

# Show service status
docker-compose -f docker-compose.production.yml ps
echo ""

# Show automation status
sudo systemctl status orchestra.service --no-pager || true

echo ""
echo "======================================"
echo "✅ Orchestra Setup Complete!"
echo "======================================"
echo ""
echo "The system is now:"
echo "  • Self-monitoring every 60 seconds"
echo "  • Auto-healing unhealthy services"
echo "  • Starting MCP servers automatically"
echo "  • Running as a system service"
echo ""
echo "Commands:"
echo "  orchestra status  - Check system status"
echo "  orchestra logs    - View automation logs"
echo "  orchestra restart - Restart automation"
echo ""
echo "The automation will:"
echo "  • Start automatically on boot"
echo "  • Restart failed services"
echo "  • Maintain system health"
echo "  • Require zero maintenance"
echo ""