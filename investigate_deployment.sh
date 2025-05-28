#!/bin/bash
# Investigate DigitalOcean deployment issues

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_section() {
    echo -e "${YELLOW}=== $1 ===${NC}"
}

# Check for doctl
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}Error: doctl not found. Please install DigitalOcean CLI${NC}"
    exit 1
fi

# Get current app status
print_section "App Platform Status"
doctl apps list

# Get monitoring alerts
print_section "Active Alerts"
doctl monitoring alerts list

# Get logs for most recent deployment
print_section "Recent Deployment Logs"
doctl apps logs --tail 100

# Check database status
print_section "Database Status"
doctl databases list
doctl databases connection --format "Host,Port,User,Database,SSL"

# Check load balancer status
print_section "Load Balancer Status"
doctl compute load-balancer list --format "ID,Name,IP,Status"

# Check droplet status
print_section "Droplet Status"
doctl compute droplet list --format "ID,Name,PublicIPv4,Status"

echo -e "${GREEN}Investigation complete. Check above for any issues.${NC}"
