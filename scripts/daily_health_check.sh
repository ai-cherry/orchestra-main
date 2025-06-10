#!/bin/bash
# 🏥 Orchestra AI Daily Health Check
# Version: 2.0 - Post-Live Verification  
# Last Updated: June 10, 2025

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local url=$1
    local name=$2
    local expected_status=$3
    
    echo -n "  Checking $name... "
    
    response=$(curl -s "$url" 2>/dev/null)
    if [ $? -eq 0 ]; then
        if [ -n "$expected_status" ]; then
            status=$(echo "$response" | jq -r '.status' 2>/dev/null)
            if [ "$status" = "$expected_status" ]; then
                echo -e "${GREEN}✅ HEALTHY${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠️  Status: $status${NC}"
                return 1
            fi
        else
            echo -e "${GREEN}✅ RESPONDING${NC}"
            return 0
        fi
    else
        echo -e "${RED}❌ UNREACHABLE${NC}"
        return 1
    fi
}

# Function to measure response time
measure_response_time() {
    local url=$1
    local name=$2
    
    echo -n "  Response time for $name... "
    response_time=$(curl -w "%{time_total}" -o /dev/null -s "$url" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${CYAN}${response_time}s${NC}"
        
        # Check if response time is good (<0.5s for API, <0.1s for frontend)
        if (( $(echo "$response_time < 0.5" | bc -l) )); then
            echo -e "    ${GREEN}🚀 Excellent performance${NC}"
        elif (( $(echo "$response_time < 1.0" | bc -l) )); then
            echo -e "    ${YELLOW}⚡ Good performance${NC}"
        else
            echo -e "    ${RED}🐌 Slow response${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to measure${NC}"
    fi
}

# Header
echo -e "${BLUE}🏥 Orchestra AI Health Check - $(date)${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Initialize counters
total_checks=0
failed_checks=0

# Zapier MCP Server Health (NEW - Port 80)
echo -e "${CYAN}🔗 Zapier MCP Server Health:${NC}"
((total_checks++))
if ! check_service "http://localhost:80/health" "Zapier MCP Server" "healthy"; then
    ((failed_checks++))
fi
measure_response_time "http://localhost:80/health" "Zapier MCP Server"

# Test Zapier authentication
echo -n "  Zapier authentication... "
auth_response=$(curl -s -H "X-Zapier-API-Key: zap_dev_12345_abcdef_orchestra_ai_cursor" http://localhost:80/api/v1/auth/verify 2>/dev/null)
if [ $? -eq 0 ] && echo "$auth_response" | jq -e '.authenticated == true' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Authenticated${NC}"
else
    echo -e "${RED}❌ Auth Failed${NC}"
    ((failed_checks++))
fi
((total_checks++))
echo ""

# API Server Health
echo -e "${CYAN}🚀 API Server Health:${NC}"
((total_checks++))
if ! check_service "http://localhost:8010/api/system/health" "API Server" "healthy"; then
    ((failed_checks++))
fi
measure_response_time "http://localhost:8010/api/system/health" "API Server"
echo ""

# Personas System Health
echo -e "${CYAN}🎭 Personas System Health:${NC}"
((total_checks++))
if ! check_service "http://localhost:8000/health" "Personas System" "healthy"; then
    ((failed_checks++))
fi
measure_response_time "http://localhost:8000/health" "Personas System"

# Test individual personas
echo "  Testing individual personas:"
for persona in cherry sophia karen; do
    echo -n "    $persona... "
    response=$(curl -s -X POST http://localhost:8000/chat_with_persona \
        -H "Content-Type: application/json" \
        -d "{\"persona\": \"$persona\", \"query\": \"health check\"}" 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | jq -e '.status == "operational"' >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Active${NC}"
    else
        echo -e "${RED}❌ Inactive${NC}"
        ((failed_checks++))
    fi
done
echo ""

# Database Cluster Health
echo -e "${CYAN}🗄️ Database Cluster Health:${NC}"

# PostgreSQL
echo -n "  PostgreSQL... "
if docker exec cherry_ai_postgres_prod pg_isready -U cherry_ai >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ready${NC}"
else
    echo -e "${RED}❌ Not Ready${NC}"
    ((failed_checks++))
fi
((total_checks++))

# Redis
echo -n "  Redis... "
if docker exec cherry_ai_redis_prod redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ Ready${NC}"
else
    echo -e "${RED}❌ Not Ready${NC}"
    ((failed_checks++))
fi
((total_checks++))

# Weaviate
echo -n "  Weaviate... "
((total_checks++))
if ! check_service "http://localhost:8080/v1/.well-known/ready" "Weaviate" ""; then
    ((failed_checks++))
fi
measure_response_time "http://localhost:8080/v1/.well-known/ready" "Weaviate"
echo ""

# Memory Architecture Health
echo -e "${CYAN}🧠 Memory Architecture Health:${NC}"
echo -n "  5-Tier Memory System... "
response=$(curl -s http://localhost:8000/memory_status 2>/dev/null)
if [ $? -eq 0 ] && echo "$response" | jq -e '.status == "all tiers operational"' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ All Tiers Operational${NC}"
    
    # Show compression ratio
    compression=$(echo "$response" | jq -r '.compression.ratio' 2>/dev/null)
    echo "    Compression: $compression"
else
    echo -e "${RED}❌ Memory System Issues${NC}"
    ((failed_checks++))
fi
((total_checks++))
echo ""

# Container Health
echo -e "${CYAN}🐳 Container Health:${NC}"
containers=("cherry_ai_postgres_prod" "cherry_ai_redis_prod" "cherry_ai_weaviate_prod" "cherry_ai_api_hybrid")

for container in "${containers[@]}"; do
    echo -n "  $container... "
    status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)
    if [ "$status" = "healthy" ]; then
        echo -e "${GREEN}✅ Healthy${NC}"
    else
        docker_status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
        if [ "$docker_status" = "running" ]; then
            echo -e "${YELLOW}⚠️  Running (no health check)${NC}"
        else
            echo -e "${RED}❌ $docker_status${NC}"
            ((failed_checks++))
        fi
    fi
    ((total_checks++))
done
echo ""

# System Resources
echo -e "${CYAN}💻 System Resources:${NC}"
echo "  Docker containers resource usage:"
docker stats --no-stream --format "    {{.Name}}: CPU {{.CPUPerc}} | RAM {{.MemUsage}}" 2>/dev/null | head -10
echo ""

# Disk Usage
echo "  Disk usage:"
df -h | grep -E "(/$|/var)" | while read filesystem size used avail percent mount; do
    echo "    $mount: $used/$size ($percent used)"
done
echo ""

# Network Connectivity
echo -e "${CYAN}🌐 Network Connectivity:${NC}"
echo -n "  Internet connectivity... "
if ping -c 1 google.com >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Connected${NC}"
else
    echo -e "${RED}❌ No Internet${NC}"
    ((failed_checks++))
fi
((total_checks++))

# Check if Vercel frontend is accessible (if we have a URL)
if [ -f "QUICK_ACCESS_GUIDE.md" ]; then
    frontend_url=$(grep -o 'https://orchestra-admin-interface-[^.]*\.vercel\.app' QUICK_ACCESS_GUIDE.md | head -1)
    if [ -n "$frontend_url" ]; then
        echo -n "  Frontend accessibility... "
        if curl -s -o /dev/null -w "%{http_code}" "$frontend_url" | grep -q "401\|200"; then
            echo -e "${GREEN}✅ Accessible${NC}"
        else
            echo -e "${RED}❌ Not Accessible${NC}"
            ((failed_checks++))
        fi
        ((total_checks++))
    fi
fi
echo ""

# Security Check
echo -e "${CYAN}🔒 Security Status:${NC}"
echo -n "  Checking for exposed secrets... "
exposed_secrets=$(grep -r "password\|token\|key" . --exclude-dir=node_modules --exclude-dir=venv --exclude="*.log" 2>/dev/null | grep -v ".env" | grep -v "Binary file" | wc -l)
if [ "$exposed_secrets" -eq 0 ]; then
    echo -e "${GREEN}✅ No exposed secrets found${NC}"
else
    echo -e "${YELLOW}⚠️  $exposed_secrets potential secret references found${NC}"
fi
echo ""

# Log File Check
echo -e "${CYAN}📝 Log Status:${NC}"
if [ -f "/tmp/personas_live.log" ]; then
    log_size=$(du -h /tmp/personas_live.log | cut -f1)
    echo "  Personas log size: $log_size"
    
    # Check for recent errors in logs
    error_count=$(tail -100 /tmp/personas_live.log 2>/dev/null | grep -i error | wc -l)
    if [ "$error_count" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠️  $error_count recent errors found in personas log${NC}"
    else
        echo -e "  ${GREEN}✅ No recent errors in personas log${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  Personas log file not found${NC}"
fi
echo ""

# Performance Summary
echo -e "${CYAN}⚡ Performance Summary:${NC}"
echo "  API Response Times (last 5 requests):"
for i in {1..5}; do
    api_time=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8010/api/system/health 2>/dev/null)
    echo "    Request $i: ${api_time}s"
    sleep 1
done
echo ""

# Final Summary
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}📊 Health Check Summary:${NC}"

if [ $failed_checks -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS OPERATIONAL!${NC}"
    echo -e "${GREEN}✅ $total_checks/$total_checks checks passed${NC}"
    exit_code=0
else
    echo -e "${RED}⚠️  ISSUES DETECTED!${NC}"
    echo -e "${RED}❌ $failed_checks/$total_checks checks failed${NC}"
    exit_code=1
fi

echo -e "${BLUE}$(date)${NC}"
echo ""

# Save results to log
{
    echo "$(date): Health check completed - $failed_checks/$total_checks failed"
    if [ $failed_checks -gt 0 ]; then
        echo "Issues detected in health check"
    fi
} >> /tmp/orchestra_health_history.log

# If running in cron, only output if there are issues
if [ -n "$CRON_MODE" ] && [ $failed_checks -eq 0 ]; then
    exit 0
fi

exit $exit_code 