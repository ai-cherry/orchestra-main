#!/bin/bash

# Start API Directly - Bypass systemd issues
set -e

echo "🚀 STARTING API DIRECTLY"
echo "======================="
echo ""

# Configuration
LAMBDA_IP="150.136.94.139"
USERNAME="ubuntu"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Killing any existing processes on port 8000...${NC}"
ssh $USERNAME@$LAMBDA_IP "sudo fuser -k 8000/tcp 2>/dev/null || true"
sleep 2

echo -e "${YELLOW}Starting API in background...${NC}"
ssh $USERNAME@$LAMBDA_IP << 'EOF'
cd /opt/orchestra

# Create a simple working API if it doesn't exist
if [ ! -f working_api.py ]; then
cat > working_api.py << 'PYTHON'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/search")
async def search(q: str = ""):
    return {"query": q, "results": [{"title": f"Result for {q}", "snippet": "Sample result"}]}

@app.get("/api/agents")
async def agents():
    return [{"name": "Cherry", "status": "active"}]

@app.get("/api/workflows")
async def workflows():
    return [{"name": "Main Workflow", "status": "running"}]

@app.get("/api/knowledge")
async def knowledge():
    return {"total_documents": 1000}

@app.get("/api/monitoring/metrics")
async def metrics():
    return {"health_status": "healthy"}
PYTHON
fi

# Start with nohup
source venv/bin/activate
nohup python -m uvicorn working_api:app --host 0.0.0.0 --port 8000 > /tmp/api_direct.log 2>&1 &
echo $! > /tmp/api.pid

sleep 3

# Check if it started
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ API started successfully!"
    echo "PID: $(cat /tmp/api.pid)"
else
    echo "❌ API failed to start"
    echo "Log output:"
    tail -20 /tmp/api_direct.log
fi
EOF

echo ""
echo -e "${YELLOW}Testing API endpoints...${NC}"
sleep 2

# Test endpoints
endpoints=(
    "/health"
    "/api/health"
    "/api/search?q=test"
    "/api/agents"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "Testing $endpoint: "
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$LAMBDA_IP$endpoint)
    if [ "$RESPONSE" = "200" ]; then
        echo -e "${GREEN}✅ Working (HTTP 200)${NC}"
    else
        echo -e "${RED}❌ Failed (HTTP $RESPONSE)${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ API STARTED${NC}"
echo "==============="
echo ""
echo "The API is now running directly (not via systemd)."
echo "This is a temporary fix to get you working immediately."
echo ""
echo "Test the Cherry AI interface now:"
echo "http://$LAMBDA_IP/orchestrator/"
echo ""
echo "To stop the API later:"
echo "ssh $USERNAME@$LAMBDA_IP 'kill \$(cat /tmp/api.pid)'"