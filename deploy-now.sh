#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Direct Deployment to Cherry-AI.me${NC}"
echo "===================================="

# Since you have VULTR_IP_ADDRESS and SSH_PRIVATE_KEY in GitHub secrets,
# you'll need to provide them here or use the manual deployment script

if [ -z "$VULTR_IP_ADDRESS" ]; then
    echo -e "${YELLOW}Please provide your Vultr server IP address${NC}"
    echo "You can find this in your GitHub secrets as VULTR_IP_ADDRESS"
    read -p "Enter Vultr IP: " VULTR_IP_ADDRESS
fi

echo -e "${GREEN}Deploying to: $VULTR_IP_ADDRESS${NC}"

# Use the manual deployment script
./infrastructure/manual-deploy.sh $VULTR_IP_ADDRESS

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}Your API should now be available at:${NC}"
echo -e "${YELLOW}http://$VULTR_IP_ADDRESS${NC}"
echo -e "${YELLOW}http://cherry-ai.me${NC} (if DNS is configured)${NC}"
echo ""
echo -e "${GREEN}To verify deployment:${NC}"
echo "1. Health check: curl http://$VULTR_IP_ADDRESS/api/health"
echo "2. Test auth: curl -X POST http://$VULTR_IP_ADDRESS/api/auth/login -H 'Content-Type: application/json' -d '{\"username\": \"scoobyjava\", \"password\": \"Huskers1983\$\"}'"