#!/bin/bash
# Start Orchestra AI System on DigitalOcean Droplet

set -e

echo "🚀 Starting Orchestra AI System..."

# Check if we're in the right directory
if [ ! -f "/opt/orchestra/agent/app/main.py" ]; then
    echo "❌ Error: Orchestra code not found at /opt/orchestra/"
    exit 1
fi

cd /opt/orchestra

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="/opt/orchestra:$PYTHONPATH"
export ORCHESTRA_ENV="production"
export DATABASE_URL="postgresql://orchestrator:dev-password-123@localhost/orchestrator"
export WEAVIATE_URL="http://localhost:8080"
export DRAGONFLY_URI="${DRAGONFLY_URI:-rediss://qpwj3s2ae.dragonflydb.cloud:6385}"

# Check if Weaviate is running
echo "🔍 Checking Weaviate..."
if ! curl -s http://localhost:8080/v1/.well-known/ready > /dev/null; then
    echo "❌ Weaviate is not running. Starting it..."
    cd /opt && docker-compose -f weaviate-compose.yml up -d
    sleep 10
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL..."
if ! sudo -u postgres psql -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Starting it..."
    systemctl start postgresql
fi

# Create logs directory
mkdir -p /var/log/orchestra

# Start MCP servers in background
echo "🔧 Starting MCP servers..."
cd /opt/orchestra/mcp_server
python main.py > /var/log/orchestra/mcp.log 2>&1 &
MCP_PID=$!
echo "MCP Server started with PID: $MCP_PID"

# Start main API server (using agent app)
echo "🌐 Starting Orchestra API..."
cd /opt/orchestra
python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000 --reload > /var/log/orchestra/api.log 2>&1 &
API_PID=$!
echo "API Server started with PID: $API_PID"

# Save PIDs
echo $MCP_PID > /var/run/orchestra-mcp.pid
echo $API_PID > /var/run/orchestra-api.pid

echo "✅ Orchestra AI System started successfully!"
echo ""
echo "Services running:"
echo "- API: http://${APP_IP}:8000"
echo "- Weaviate: http://${APP_IP}:8080"
echo "- MCP Server: Running on internal ports"
echo ""
echo "Logs available at:"
echo "- API: /var/log/orchestra/api.log"
echo "- MCP: /var/log/orchestra/mcp.log"
echo ""
echo "To stop: ./stop_orchestra_on_droplet.sh"
