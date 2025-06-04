#!/bin/bash
# Nuclear Fix Script - Complete System Reset and Rebuild
# This will fix EVERYTHING

set -e

echo "🔥 NUCLEAR FIX INITIATED - FIXING THIS SHIT SHOW 🔥"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 1. KILL EVERYTHING
echo -e "\n${RED}PHASE 1: SCORCHED EARTH${NC}"
echo "================================"

# Kill all Docker containers
warning "Killing ALL Docker containers..."
docker kill $(docker ps -q) 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true
status "All containers terminated"

# Remove all Docker volumes
warning "Removing ALL Docker volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || true
status "All volumes removed"

# Clean Docker system
warning "Cleaning Docker system..."
docker system prune -af --volumes
status "Docker system cleaned"

# Kill any lingering processes
warning "Killing any lingering processes..."
pkill -f "mcp_server" || true
pkill -f "uvicorn" || true
pkill -f "orchestrator" || true
pkill -f "cherry" || true
status "All processes killed"

# 2. CREATE SIMPLE, WORKING CONFIG
echo -e "\n${GREEN}PHASE 2: REBUILD FROM SCRATCH${NC}"
echo "================================"

# Create a simple, working docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: orchestra_postgres
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: conductor
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: orchestra_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  weaviate:
    image: semitechnologies/weaviate:1.24.10
    container_name: orchestra_weaviate
    restart: always
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      CLUSTER_HOSTNAME: 'node1'
      STANDALONE_MODE: 'true'
      PERSISTENCE_LSM_ACCESS_STRATEGY: 'mmap'
      LIMIT_RESOURCES: 'true'
      GOMAXPROCS: '2'
      LOG_LEVEL: 'warning'
    volumes:
      - weaviate_data:/var/lib/weaviate
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/v1/.well-known/ready"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  postgres_data:
  redis_data:
  weaviate_data:

networks:
  default:
    name: orchestra_network
EOF
status "Created simple docker-compose.yml"

# 3. START SERVICES ONE BY ONE
echo -e "\n${GREEN}PHASE 3: START SERVICES${NC}"
echo "================================"

# Start PostgreSQL
warning "Starting PostgreSQL..."
docker-compose up -d postgres
sleep 10
docker exec orchestra_postgres pg_isready -U postgres
status "PostgreSQL is running"

# Start Redis
warning "Starting Redis..."
docker-compose up -d redis
sleep 5
docker exec orchestra_redis redis-cli ping
status "Redis is running"

# Start Weaviate
warning "Starting Weaviate..."
docker-compose up -d weaviate
sleep 15

# Wait for Weaviate to be ready
echo "Waiting for Weaviate to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        status "Weaviate is running"
        break
    fi
    echo -n "."
    sleep 2
done

# 4. VERIFY EVERYTHING
echo -e "\n${GREEN}PHASE 4: VERIFICATION${NC}"
echo "================================"

# Check all services
echo "Service Status:"
echo "---------------"

# PostgreSQL
if docker exec orchestra_postgres pg_isready -U postgres > /dev/null 2>&1; then
    status "PostgreSQL: HEALTHY"
else
    error "PostgreSQL: FAILED"
fi

# Redis
if [[ $(docker exec orchestra_redis redis-cli ping) == "PONG" ]]; then
    status "Redis: HEALTHY"
else
    error "Redis: FAILED"
fi

# Weaviate
if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    status "Weaviate: HEALTHY"
else
    error "Weaviate: FAILED"
fi

# 5. CREATE SIMPLE TEST SCRIPT
echo -e "\n${GREEN}PHASE 5: CREATE TEST UTILITIES${NC}"
echo "================================"

# Create a simple test script
cat > test_services.py << 'EOF'
#!/usr/bin/env python3
"""Test all services are working"""

import sys
import psycopg2
import redis
import requests

def test_postgres():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres"
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"PostgreSQL Error: {e}")
        return False

def test_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.set('test', 'value')
        result = r.get('test')
        r.delete('test')
        return result == 'value'
    except Exception as e:
        print(f"Redis Error: {e}")
        return False

def test_weaviate():
    try:
        response = requests.get('http://localhost:8080/v1/.well-known/ready')
        return response.status_code == 200
    except Exception as e:
        print(f"Weaviate Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing services...")
    
    tests = {
        "PostgreSQL": test_postgres(),
        "Redis": test_redis(),
        "Weaviate": test_weaviate()
    }
    
    all_passed = True
    for service, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{service}: {status}")
        if not result:
            all_passed = False
    
    sys.exit(0 if all_passed else 1)
EOF

chmod +x test_services.py
status "Created test script"

# 6. CREATE SIMPLE MCP SERVER STARTER
cat > start_mcp_servers.sh << 'EOF'
#!/bin/bash
# Start MCP servers

cd /root/orchestra-main

# Kill any existing MCP processes
pkill -f "mcp_server" || true

# Create logs directory
mkdir -p logs

# Start basic MCP servers
echo "Starting MCP servers..."

# Memory server
nohup python3 -m mcp_server.servers.memory_server > logs/mcp_memory.log 2>&1 &
echo $! > logs/mcp_memory.pid
echo "Memory server started (PID: $(cat logs/mcp_memory.pid))"

# Tools server
nohup python3 -m mcp_server.servers.tools_server > logs/mcp_tools.log 2>&1 &
echo $! > logs/mcp_tools.pid
echo "Tools server started (PID: $(cat logs/mcp_tools.pid))"

# Orchestrator server
nohup python3 -m mcp_server.servers.orchestrator_server > logs/mcp_orchestrator.log 2>&1 &
echo $! > logs/mcp_orchestrator.pid
echo "Orchestrator server started (PID: $(cat logs/mcp_orchestrator.pid))"

echo "All MCP servers started. Check logs/ directory for output."
EOF

chmod +x start_mcp_servers.sh
status "Created MCP server starter"

# 7. FINAL STATUS
echo -e "\n${GREEN}PHASE 6: FINAL STATUS${NC}"
echo "================================"

# Show running containers
echo -e "\nRunning containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test services
echo -e "\nTesting services..."
python3 test_services.py

echo -e "\n${GREEN}✅ NUCLEAR FIX COMPLETE${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Run './test_services.py' to verify all services"
echo "2. Run './start_mcp_servers.sh' to start MCP servers"
echo "3. Check 'docker logs <container_name>' if any issues"
echo ""
echo "Services available at:"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo "- Weaviate: http://localhost:8080"
echo ""
echo "The system has been completely reset and rebuilt with a simple, working configuration."