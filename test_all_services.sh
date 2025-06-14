#!/bin/bash

# Orchestra AI - Test All Service Endpoints
echo "🧪 Testing Orchestra AI Service Endpoints"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✅ $name - OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ $name - Failed (HTTP $response, expected $expected)${NC}"
        return 1
    fi
}

# Test all services
echo "Testing Service Endpoints:"
echo "-------------------------"

test_endpoint "API Health" "http://localhost:8000/api/health" "200"
test_endpoint "API Root" "http://localhost:8000/" "200"

test_endpoint "Context Service Health" "http://localhost:8005/health" "200"
test_endpoint "Context Data" "http://localhost:8005/context" "200"

test_endpoint "Portkey MCP Health" "http://localhost:8004/health" "200"
test_endpoint "Portkey MCP Stats" "http://localhost:8004/stats" "200"

test_endpoint "Frontend" "http://localhost:3000/" "200"

# Try MCP Memory on both 8003 and 8020
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    test_endpoint "MCP Memory Health" "http://localhost:8003/health" "200"
elif curl -s http://localhost:8020/health > /dev/null 2>&1; then
    test_endpoint "MCP Memory Health (alt port)" "http://localhost:8020/health" "200"
else
    echo -e "${RED}❌ MCP Memory Server - Not running${NC}"
fi

echo ""
echo "Service Summary:"
echo "---------------"
echo "API:             http://localhost:8000"
echo "Frontend:        http://localhost:3000"  
echo "Context Service: http://localhost:8005"
echo "Portkey MCP:     http://localhost:8004"

# Check for MCP Memory port
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "MCP Memory:      http://localhost:8003"
elif curl -s http://localhost:8020/health > /dev/null 2>&1; then
    echo "MCP Memory:      http://localhost:8020 (alternate port)"
fi 