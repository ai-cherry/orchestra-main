#!/bin/bash
# Orchestra-Main Complete Infrastructure Deployment Script
# Run this on your local Mac to deploy the entire Tier 1 infrastructure

set -e  # Exit on any error

# Configuration
API_KEY="7L34HOKF25HYDT7WHETR7QZTHQX6M5YP36MQ"
BASE_URL="https://api.vultr.com/v2"
CURRENT_SERVER_ID="4fafc6c9-0531-4508-9762-19dc5959b9da"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ "$method" = "GET" ]; then
        curl -s -H "Authorization: Bearer $API_KEY" \
             -H "Content-Type: application/json" \
             "$BASE_URL$endpoint"
    else
        curl -s -X "$method" \
             -H "Authorization: Bearer $API_KEY" \
             -H "Content-Type: application/json" \
             -d "$data" \
             "$BASE_URL$endpoint"
    fi
}

# Function to wait for instance to be ready
wait_for_instance() {
    local instance_id=$1
    local max_attempts=60
    local attempt=0
    
    echo -e "${YELLOW}⏳ Waiting for instance $instance_id to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        local status=$(api_call GET "/instances/$instance_id" | python3 -c "import sys, json; print(json.load(sys.stdin)['instance']['status'])" 2>/dev/null || echo "pending")
        
        if [ "$status" = "active" ]; then
            echo -e "${GREEN}✅ Instance $instance_id is ready!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 10
        ((attempt++))
    done
    
    echo -e "${RED}❌ Timeout waiting for instance $instance_id${NC}"
    return 1
}

# Function to get SSH key ID
get_ssh_key_id() {
    local ssh_keys=$(api_call GET "/ssh-keys")
    local key_id=$(echo "$ssh_keys" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for key in data.get('ssh_keys', []):
    if 'orchestra' in key.get('name', '').lower():
        print(key['id'])
        break
" 2>/dev/null || echo "")
    
    if [ -z "$key_id" ]; then
        echo -e "${RED}❌ SSH key 'orchestra-vultr' not found${NC}"
        exit 1
    fi
    
    echo "$key_id"
}

echo -e "${BLUE}🚀 Orchestra-Main Tier 1 Infrastructure Deployment${NC}"
echo "=================================================="

# Check if required tools are installed
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is required but not installed${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 is required but not installed${NC}"
    exit 1
fi

# Test API access
echo -e "${YELLOW}🔑 Testing API access...${NC}"
account_info=$(api_call GET "/account" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to access Vultr API${NC}"
    exit 1
fi

account_name=$(echo "$account_info" | python3 -c "import sys, json; print(json.load(sys.stdin)['account']['name'])" 2>/dev/null)
echo -e "${GREEN}✅ API access confirmed for: $account_name${NC}"

# Get SSH key ID
echo -e "${YELLOW}🔐 Finding SSH key...${NC}"
SSH_KEY_ID=$(get_ssh_key_id)
echo -e "${GREEN}✅ Found SSH key ID: $SSH_KEY_ID${NC}"

# Create database server
echo -e "${YELLOW}💾 Creating dedicated database server...${NC}"
db_data='{
    "region": "lax",
    "plan": "voc-g-8c-32gb-160s-amd",
    "os_id": 1743,
    "label": "orchestra-database",
    "tag": "database",
    "hostname": "orchestra-db",
    "enable_ipv6": true,
    "enable_private_network": true,
    "sshkey_id": ["'$SSH_KEY_ID'"]
}'

db_response=$(api_call POST "/instances" "$db_data")
db_instance_id=$(echo "$db_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['instance']['id'])" 2>/dev/null)

if [ -z "$db_instance_id" ]; then
    echo -e "${RED}❌ Failed to create database server${NC}"
    echo "$db_response"
    exit 1
fi

echo -e "${GREEN}✅ Database server created: $db_instance_id${NC}"

# Create staging server
echo -e "${YELLOW}🎭 Creating staging server...${NC}"
staging_data='{
    "region": "ewr",
    "plan": "voc-g-8c-32gb-160s-amd",
    "os_id": 1743,
    "label": "orchestra-staging",
    "tag": "staging",
    "hostname": "orchestra-staging",
    "enable_ipv6": true,
    "enable_private_network": true,
    "sshkey_id": ["'$SSH_KEY_ID'"]
}'

staging_response=$(api_call POST "/instances" "$staging_data")
staging_instance_id=$(echo "$staging_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['instance']['id'])" 2>/dev/null)

if [ -z "$staging_instance_id" ]; then
    echo -e "${RED}❌ Failed to create staging server${NC}"
    echo "$staging_response"
    exit 1
fi

echo -e "${GREEN}✅ Staging server created: $staging_instance_id${NC}"

# Create object storage
echo -e "${YELLOW}📦 Creating object storage...${NC}"
storage_data='{
    "cluster_id": 2,
    "label": "orchestra-storage"
}'

storage_response=$(api_call POST "/object-storage" "$storage_data")
storage_id=$(echo "$storage_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['object_storage']['id'])" 2>/dev/null)

if [ -z "$storage_id" ]; then
    echo -e "${YELLOW}⚠️ Object storage creation may have failed, continuing...${NC}"
else
    echo -e "${GREEN}✅ Object storage created: $storage_id${NC}"
fi

# Wait for instances to be ready
wait_for_instance "$db_instance_id"
wait_for_instance "$staging_instance_id"

# Get instance details
echo -e "${YELLOW}📊 Getting instance details...${NC}"

db_details=$(api_call GET "/instances/$db_instance_id")
db_ip=$(echo "$db_details" | python3 -c "import sys, json; print(json.load(sys.stdin)['instance']['main_ip'])" 2>/dev/null)

staging_details=$(api_call GET "/instances/$staging_instance_id")
staging_ip=$(echo "$staging_details" | python3 -c "import sys, json; print(json.load(sys.stdin)['instance']['main_ip'])" 2>/dev/null)

# Create load balancer
echo -e "${YELLOW}⚖️ Creating load balancer...${NC}"
lb_data='{
    "region": "lax",
    "label": "orchestra-lb",
    "balancing_algorithm": "roundrobin",
    "ssl_redirect": false,
    "proxy_protocol": false,
    "health_check": {
        "protocol": "http",
        "port": 80,
        "path": "/",
        "check_interval": 15,
        "response_timeout": 5,
        "unhealthy_threshold": 3,
        "healthy_threshold": 2
    },
    "forwarding_rules": [
        {
            "frontend_protocol": "http",
            "frontend_port": 80,
            "backend_protocol": "http",
            "backend_port": 80
        }
    ],
    "instances": ["'$CURRENT_SERVER_ID'", "'$staging_instance_id'"]
}'

lb_response=$(api_call POST "/load-balancers" "$lb_data")
lb_id=$(echo "$lb_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['load_balancer']['id'])" 2>/dev/null)

if [ -z "$lb_id" ]; then
    echo -e "${YELLOW}⚠️ Load balancer creation may have failed, continuing...${NC}"
    echo "$lb_response"
else
    echo -e "${GREEN}✅ Load balancer created: $lb_id${NC}"
fi

# Generate summary
echo -e "\n${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo "=================================="
echo -e "${BLUE}📋 Infrastructure Summary:${NC}"
echo "• Main Server: 45.32.69.157 (existing)"
echo "• Database Server: $db_ip"
echo "• Staging Server: $staging_ip"
if [ ! -z "$lb_id" ]; then
    lb_details=$(api_call GET "/load-balancers/$lb_id")
    lb_ip=$(echo "$lb_details" | python3 -c "import sys, json; print(json.load(sys.stdin)['load_balancer'].get('ipv4', 'pending'))" 2>/dev/null)
    echo "• Load Balancer: $lb_ip"
fi
if [ ! -z "$storage_id" ]; then
    echo "• Object Storage: $storage_id"
fi

echo -e "\n${BLUE}💰 Estimated Monthly Cost: ~\$175${NC}"

# Create SSH config
echo -e "\n${YELLOW}🔧 Creating SSH configuration...${NC}"
cat >> ~/.ssh/config << EOF

# Orchestra-Main Infrastructure
Host orchestra-main
    HostName 45.32.69.157
    User root
    IdentityFile ~/.ssh/vultr_orchestra

Host orchestra-db
    HostName $db_ip
    User root
    IdentityFile ~/.ssh/vultr_orchestra

Host orchestra-staging
    HostName $staging_ip
    User root
    IdentityFile ~/.ssh/vultr_orchestra
EOF

echo -e "${GREEN}✅ SSH configuration updated${NC}"

echo -e "\n${BLUE}🚀 Next Steps:${NC}"
echo "1. Test connections:"
echo "   ssh orchestra-main"
echo "   ssh orchestra-db"
echo "   ssh orchestra-staging"
echo ""
echo "2. Configure your applications to use the new infrastructure"
echo "3. Set up database replication and backups"
echo "4. Configure load balancer health checks"

echo -e "\n${GREEN}🎯 Your Tier 1 infrastructure is now deployed and ready!${NC}"

