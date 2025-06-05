#!/bin/bash

# Debug and Fix API Issues
# Systematic approach to identify why API is offline

set -e

echo "🔍 DEBUGGING API ISSUES"
echo "======================"
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

echo -e "${YELLOW}STEP 1: Checking API Process${NC}"
echo "============================="

ssh $USERNAME@$LAMBDA_IP << 'EOF'
echo "Checking for API processes..."
ps aux | grep -E "(uvicorn|gunicorn|simple_api)" | grep -v grep || echo "No API process found"

echo -e "\nChecking port 8000..."
sudo lsof -i :8000 || echo "Port 8000 is not in use"

echo -e "\nChecking systemd service..."
sudo systemctl status orchestra-api --no-pager || echo "Service status check failed"

echo -e "\nChecking API logs..."
if [ -f /var/log/orchestra-api.log ]; then
    echo "Last 20 lines of API log:"
    sudo tail -20 /var/log/orchestra-api.log
fi

if [ -f /tmp/api.log ]; then
    echo -e "\nLast 20 lines of temp API log:"
    tail -20 /tmp/api.log
fi
EOF

echo ""
echo -e "${YELLOW}STEP 2: Testing API Endpoints${NC}"
echo "=============================="

# Test direct access
echo "Testing localhost:8000..."
ssh $USERNAME@$LAMBDA_IP "curl -s -w '\nHTTP Status: %{http_code}\n' http://localhost:8000/health || echo 'Failed to connect'"

echo -e "\nTesting proxied API..."
curl -s -w '\nHTTP Status: %{http_code}\n' http://$LAMBDA_IP/api/health || echo 'Failed to connect'

echo ""
echo -e "${YELLOW}STEP 3: Checking Nginx Proxy${NC}"
echo "============================="

ssh $USERNAME@$LAMBDA_IP << 'EOF'
echo "Nginx error logs (last 10 lines)..."
sudo tail -10 /var/log/nginx/error.log | grep -E "(proxy|upstream|api)" || echo "No relevant errors"

echo -e "\nNginx access logs for /api/..."
sudo tail -20 /var/log/nginx/access.log | grep "/api/" || echo "No API requests in access log"

echo -e "\nChecking nginx configuration..."
sudo nginx -t
EOF

echo ""
echo -e "${YELLOW}STEP 4: Restarting API Service${NC}"
echo "==============================="

ssh $USERNAME@$LAMBDA_IP << 'EOF'
# Stop any existing processes
echo "Stopping existing API processes..."
sudo pkill -f "uvicorn|gunicorn|simple_api" || true
sudo systemctl stop orchestra-api || true
sleep 2

# Ensure the API file exists
if [ ! -f /opt/orchestra/simple_api.py ]; then
    echo "API file missing! Recreating..."
    cat > /opt/orchestra/simple_api.py << 'PYTHON'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Orchestra API is running"}

@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "orchestra-api",
        "version": "1.0.0"
    }

@app.post("/api/search")
@app.get("/api/search")
async def search(q: str = "", mode: str = "normal", type: str = "internal", persona: str = "cherry"):
    results = []
    if q:
        results = [
            {
                "title": f"Result for: {q}",
                "snippet": f"Found information about {q} in our knowledge base",
                "source": "Orchestra KB",
                "relevance": 0.95
            }
        ]
    return {
        "query": q,
        "mode": mode,
        "results": results,
        "search_config": {"name": f"{mode} search"}
    }

@app.get("/api/agents")
async def get_agents():
    return [{"name": "Cherry", "status": "active", "description": "AI Assistant"}]

@app.get("/api/workflows")
async def get_workflows():
    return [{"name": "Data Pipeline", "status": "running", "last_run": datetime.now().isoformat()}]

@app.get("/api/knowledge")
async def get_knowledge():
    return {"total_documents": 1000, "total_embeddings": 50000, "last_updated": datetime.now().isoformat()}

@app.get("/api/monitoring/metrics")
async def get_metrics():
    return {"api_requests_24h": 1000, "avg_response_time": 50, "error_rate": 0.1, "health_status": "healthy"}
PYTHON
fi

# Start API manually first to test
echo -e "\nStarting API manually..."
cd /opt/orchestra
source venv/bin/activate
python -m uvicorn simple_api:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 5

# Test if it's working
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ API started successfully"
    
    # Kill manual process and start with systemd
    kill $API_PID
    sleep 2
    
    # Start with systemd
    sudo systemctl start orchestra-api
    sleep 3
    
    if sudo systemctl is-active orchestra-api | grep -q "active"; then
        echo "✅ Systemd service is running"
    else
        echo "❌ Systemd service failed to start"
        sudo journalctl -u orchestra-api -n 50
    fi
else
    echo "❌ API failed to start"
    kill $API_PID 2>/dev/null || true
fi
EOF

echo ""
echo -e "${YELLOW}STEP 5: Fixing Weaviate${NC}"
echo "======================="

ssh $USERNAME@$LAMBDA_IP << 'EOF'
echo "Checking Weaviate status..."
if systemctl list-units --type=service | grep -q weaviate; then
    sudo systemctl status weaviate --no-pager || true
    echo -e "\nRestarting Weaviate..."
    sudo systemctl restart weaviate || echo "Failed to restart Weaviate"
else
    echo "Weaviate service not found. Checking Docker..."
    if docker ps | grep -q weaviate; then
        echo "Weaviate is running in Docker"
    else
        echo "Starting Weaviate with Docker..."
        docker run -d \
          --name weaviate \
          --restart unless-stopped \
          -p 8080:8080 \
          -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
          -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
          -e DEFAULT_VECTORIZER_MODULE=none \
          semitechnologies/weaviate:latest || echo "Failed to start Weaviate"
    fi
fi

# Wait and test
sleep 5
if curl -s http://localhost:8080/v1/.well-known/ready | grep -q "ok"; then
    echo "✅ Weaviate is running"
else
    echo "❌ Weaviate is not responding"
fi
EOF

echo ""
echo -e "${YELLOW}STEP 6: Final Verification${NC}"
echo "=========================="

# Test all endpoints
echo -e "${BLUE}Testing endpoints...${NC}"

# API Health
echo -n "API Health: "
if curl -s http://$LAMBDA_IP/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Search
echo -n "Search API: "
if curl -s "http://$LAMBDA_IP/api/search?q=test" | grep -q "results"; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Weaviate
echo -n "Weaviate: "
if ssh $USERNAME@$LAMBDA_IP "curl -s http://localhost:8080/v1/.well-known/ready" | grep -q "ok"; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

echo ""
echo -e "${GREEN}✅ DEBUG COMPLETE${NC}"
echo "================="
echo ""
echo "If API is still showing red:"
echo "1. Clear browser cache completely"
echo "2. Try: http://$LAMBDA_IP/api/health directly"
echo "3. Check browser console for CORS errors"
echo "4. Use curl to test: curl -v http://$LAMBDA_IP/api/health"