#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Cherry Admin UI Quick Deploy${NC}"
echo -e "${BLUE}=============================${NC}"

# Check if DIGITALOCEAN_TOKEN is set
if [ -z "$DIGITALOCEAN_TOKEN" ]; then
    echo -e "${YELLOW}DIGITALOCEAN_TOKEN not found in environment.${NC}"
    echo -e "${YELLOW}Please set it with: export DIGITALOCEAN_TOKEN=your-token${NC}"
    echo -e "${YELLOW}Or run: source .env (if you have a .env file)${NC}"
    exit 1
fi

# Check if admin-ui/dist exists
if [ ! -d "admin-ui/dist" ]; then
    echo -e "${RED}Error: admin-ui/dist not found. Please build first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found admin-ui/dist${NC}"
echo -e "${GREEN}✓ DIGITALOCEAN_TOKEN is set${NC}"

# Run the Python deployment script
echo -e "${BLUE}Starting deployment...${NC}"
python3 deploy_admin_ui_api.py --token "$DIGITALOCEAN_TOKEN" --skip-build

echo -e "${GREEN}Deployment script completed!${NC}" 