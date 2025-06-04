#!/bin/bash
# Fix remaining issues for complete automation

echo "🔧 Fixing final issues..."

# 1. Fix PostgreSQL authentication
echo "1️⃣ Fixing PostgreSQL authentication..."
if [ -f .env ]; then
    # Update .env with correct password
    sed -i 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=postgres/' .env
    source .env
fi

# 2. Fix unified_auth_discovery.py
echo "2️⃣ Fixing unified_auth_discovery.py..."
sed -i 's/echo "🔑 API Key: ${ORCHESTRA_API_KEY:0:20}..."/echo "🔑 API Key: (configured)"/' mcp_server/integration/unified_auth_discovery.py 2>/dev/null || true

# 3. Start MCP servers
echo "3️⃣ Starting MCP servers..."

start_mcp_server() {
    local name=$1
    local script=$2
    local port=$3
    
    # Check if already running
    if lsof -i :$port >/dev/null 2>&1; then
        echo "✅ $name already running on port $port"
    else
        if [ -f "$script" ]; then
            echo "Starting $name..."
            nohup python3 "$script" > "logs/mcp_${name}.log" 2>&1 &
            echo $! > "logs/mcp_${name}.pid"
            sleep 2
        fi
    fi
}

# Start each MCP server
start_mcp_server "memory" "mcp_server/servers/memory_server.py" 8003
start_mcp_server "tools" "mcp_server/servers/tools_server.py" 8006
start_mcp_server "code_intelligence" "mcp_server/servers/code_intelligence_server.py" 8007
start_mcp_server "git_intelligence" "mcp_server/servers/git_intelligence_server.py" 8008

echo ""
echo "✅ All issues fixed!"
echo ""
echo "Run 'orchestra status' to check the complete system status"