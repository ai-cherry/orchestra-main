#!/usr/bin/env bash
# Start Orchestra AI: Launch all MCP servers and required services.
# Ensures MongoDB, DragonflyDB, and Weaviate are running (locally or via docker-compose).
# Logs status and provides clear output for troubleshooting.

set -e

echo "=== Orchestra AI Startup ==="

# Activate Python venv if present
if [ -d "venv" ]; then
  source venv/bin/activate
  echo "[OK] Python venv activated."
else
  echo "[WARN] No venv found. Please create and activate a Python 3.10 venv."
fi

# Check for required services (MongoDB, DragonflyDB, Weaviate)
echo "Checking required services..."

function check_service() {
  local name="$1"
  local host="$2"
  local port="$3"
  if nc -z "$host" "$port"; then
    echo "[OK] $name running at $host:$port"
  else
    echo "[FAIL] $name not running at $host:$port"
    return 1
  fi
}

check_service "MongoDB" "localhost" "27017" || echo "Start with: docker compose up -d mongodb"
check_service "DragonflyDB" "localhost" "6379" || echo "Start with: docker compose up -d dragonfly"
check_service "Weaviate" "localhost" "8080" || echo "Start with: docker compose up -d weaviate"

echo "Starting MCP servers..."

# Launch each MCP server in the background
PYTHON=${PYTHON:-python3.10}

$PYTHON mcp_server/servers/memory_mcp_server.py &   MEMORY_PID=$!
echo "[OK] memory_mcp_server.py started (PID $MEMORY_PID)"

$PYTHON mcp_server/servers/tools_server.py &        TOOLS_PID=$!
echo "[OK] tools_server.py started (PID $TOOLS_PID)"

$PYTHON mcp_server/servers/orchestrator_mcp_server.py & ORCH_PID=$!
echo "[OK] orchestrator_mcp_server.py started (PID $ORCH_PID)"

echo "All MCP servers launched."
echo "To stop all servers: kill $MEMORY_PID $TOOLS_PID $ORCH_PID"

echo "=== Orchestra AI is ready! ==="
