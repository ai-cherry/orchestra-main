#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVER_IP="45.32.69.157"

echo -e "${GREEN}AI cherry_ai Deployment to cherry-ai.me${NC}"
echo "========================================"
echo -e "${YELLOW}Server IP: $SERVER_IP${NC}"
echo ""

echo -e "${YELLOW}SSH Setup Instructions:${NC}"
echo ""
echo "Since we need SSH access, you have two options:"
echo ""
echo -e "${GREEN}Option 1: Use your GitHub SSH key${NC}"
echo "1. Get your SSH private key from GitHub secrets (SSH_PRIVATE_KEY)"
echo "2. Save it to a file: ~/.ssh/vultr_key"
echo "3. Set permissions: chmod 600 ~/.ssh/vultr_key"
echo "4. Run deployment with key:"
echo "   scp -i ~/.ssh/vultr_key cherry_ai-api-minimal.tar.gz root@$SERVER_IP:/tmp/"
echo ""
echo -e "${GREEN}Option 2: Use password authentication${NC}"
echo "Run the deployment and enter your root password when prompted:"
echo "   ./infrastructure/manual-deploy.sh $SERVER_IP"
echo ""
echo -e "${GREEN}Option 3: Add your current SSH key to the server${NC}"
echo "1. Generate SSH key if you don't have one:"
echo "   ssh-keygen -t rsa -b 4096"
echo "2. Copy it to the server (you'll need the root password once):"
echo "   ssh-copy-id root@$SERVER_IP"
echo "3. Then run deployment:"
echo "   ./infrastructure/manual-deploy.sh $SERVER_IP"
echo ""
echo -e "${YELLOW}Quick Test Commands After Deployment:${NC}"
echo "curl http://$SERVER_IP/api/health"
echo "curl http://cherry-ai.me/api/health"
echo ""
echo -e "${YELLOW}For GitHub Actions deployment:${NC}"
echo "Push your code to GitHub and it will use the SSH_PRIVATE_KEY secret automatically."