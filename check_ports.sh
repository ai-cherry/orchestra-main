#!/bin/bash

# Orchestra AI Port Availability Checker
# Checks all critical ports and provides recommendations

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Port definitions (parallel arrays)
SERVICE_NAMES=(
    "PostgreSQL"
    "Redis"
    "Weaviate"
    "API Server"
    "MCP Conductor"
    "MCP Memory"
    "MCP Tools"
    "MCP Weaviate Bridge"
    "Nginx HTTP"
    "Nginx HTTPS"
    "Admin Interface"
    "Grafana"
    "Prometheus"
    "Fluentd"
)

SERVICE_PORTS=(
    5432
    6379
    8080
    8000
    8002
    8003
    8006
    8001
    80
    443
    3000
    3001
    9090
    24224
)

# Alternative ports
ALT_SERVICE_NAMES=(
    "PostgreSQL"
    "Redis"
    "Weaviate"
    "API Server"
    "Admin Interface"
)

ALT_PORTS=(
    5433
    6380
    8081
    8010
    3002
)

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    
    # Check using lsof (most reliable)
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i :$port >/dev/null 2>&1; then
            return 1
        fi
    # Fallback to netstat
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an 2>/dev/null | grep -q ":$port.*LISTEN"; then
            return 1
        fi
    # Last resort: try to bind to the port
    else
        if ! nc -z localhost $port 2>/dev/null; then
            return 0
        else
            return 1
        fi
    fi
    
    return 0
}

# Function to get process using port
get_port_process() {
    local port=$1
    
    if command -v lsof >/dev/null 2>&1; then
        lsof -i :$port 2>/dev/null | grep LISTEN | awk '{print $1, $2}' | tail -1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tlnp 2>/dev/null | grep ":$port" | awk '{print $7}' | cut -d'/' -f2
    else
        echo "Unknown"
    fi
}

# Function to get alternative port for a service
get_alternative_port() {
    local service_name=$1
    local i
    
    for i in "${!ALT_SERVICE_NAMES[@]}"; do
        if [[ "${ALT_SERVICE_NAMES[$i]}" == "$service_name" ]]; then
            echo "${ALT_PORTS[$i]}"
            return
        fi
    done
    
    echo ""
}

# Function to suggest alternative port
suggest_alternative() {
    local service=$1
    local base_port=$2
    
    # Check if we have a predefined alternative
    local alt_port=$(get_alternative_port "$service")
    if [[ -n "$alt_port" ]]; then
        echo "$alt_port"
        return
    fi
    
    # Otherwise, find next available port
    local offset
    for offset in {1..10}; do
        local port=$((base_port + offset))
        if check_port $port "$service (alt)"; then
            echo $port
            return
        fi
    done
    
    echo "none"
}

# Main checking logic
echo -e "${BLUE}🔍 Orchestra AI Port Availability Check${NC}"
echo -e "${BLUE}=====================================>${NC}\n"

conflicts=0
available=0

# Check each service port
for i in "${!SERVICE_NAMES[@]}"; do
    service="${SERVICE_NAMES[$i]}"
    port="${SERVICE_PORTS[$i]}"
    
    if check_port $port "$service"; then
        echo -e "${GREEN}✅ Port $port${NC} ($service): Available"
        ((available++))
    else
        process=$(get_port_process $port)
        echo -e "${RED}❌ Port $port${NC} ($service): In use by ${YELLOW}$process${NC}"
        
        # Suggest alternative
        alt_port=$(suggest_alternative "$service" $port)
        if [[ "$alt_port" != "none" ]]; then
            echo -e "   ${BLUE}→ Suggested alternative: Port $alt_port${NC}"
        fi
        
        ((conflicts++))
    fi
done

echo -e "\n${BLUE}📊 Summary${NC}"
echo -e "${BLUE}----------${NC}"
echo -e "Total ports checked: $((available + conflicts))"
echo -e "${GREEN}Available: $available${NC}"
echo -e "${RED}Conflicts: $conflicts${NC}"

# Provide recommendations based on conflicts
if [[ $conflicts -gt 0 ]]; then
    echo -e "\n${YELLOW}⚠️  Recommendations:${NC}"
    echo -e "${YELLOW}-------------------${NC}"
    
    # Check for specific conflict scenarios
    if ! check_port 8000 "API"; then
        echo -e "• ${YELLOW}Port 8000 conflict detected${NC}"
        echo -e "  Consider using deployment mode:"
        echo -e "  - ${BLUE}docker-only${NC}: API on 8000, MCP disabled"
        echo -e "  - ${BLUE}mcp-only${NC}: MCP on 8000, Docker API on 8010"
        echo -e "  - ${BLUE}hybrid${NC}: Load balancer on 80, services on different ports"
    fi
    
    if ! check_port 5432 "PostgreSQL"; then
        echo -e "• ${YELLOW}PostgreSQL port conflict${NC}"
        echo -e "  - Use external port mapping: -p 5433:5432"
        echo -e "  - Or connect to existing PostgreSQL instance"
    fi
    
    if ! check_port 6379 "Redis"; then
        echo -e "• ${YELLOW}Redis port conflict${NC}"
        echo -e "  - Use external port mapping: -p 6380:6379"
        echo -e "  - Or connect to existing Redis instance"
    fi
    
    echo -e "\n${BLUE}To resolve conflicts:${NC}"
    echo -e "1. Stop conflicting services: ${YELLOW}sudo systemctl stop <service>${NC}"
    echo -e "2. Use Docker port mapping: ${YELLOW}-p <external>:<internal>${NC}"
    echo -e "3. Update .env file with alternative ports"
    echo -e "4. Use deployment modes (docker-only, mcp-only, hybrid)"
fi

# Export results for scripting
if [[ $conflicts -eq 0 ]]; then
    echo -e "\n${GREEN}✅ All ports are available! Ready for deployment.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Port conflicts detected. Please resolve before deployment.${NC}"
    exit 1
fi 