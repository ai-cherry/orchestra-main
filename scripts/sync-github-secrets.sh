#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}GitHub Secrets Sync Script${NC}"
echo "=========================="
echo ""
echo "This script helps you sync your local environment with GitHub secrets"
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo -e "${YELLOW}Warning: .env file already exists. Backing up to .env.backup${NC}"
    cp .env .env.backup
fi

# Create .env file from template
cp .env.example .env

echo -e "${GREEN}Created .env file from template${NC}"
echo ""
echo "Please update the .env file with your actual values."
echo ""
echo "The following secrets are configured in GitHub and should be added to your .env:"
echo ""
echo -e "${YELLOW}Critical for deployment:${NC}"
echo "  - VULTR_API_KEY"
echo "  - VULTR_IP_ADDRESS"
echo "  - SSH_PRIVATE_KEY"
echo "  - DOCKERHUB_USERNAME"
echo "  - DOCKER_PERSONAL_ACCESS_TOKEN"
echo ""
echo -e "${YELLOW}AI Services:${NC}"
echo "  - ANTHROPIC_API_KEY"
echo "  - OPENAI_API_KEY"
echo "  - PORTKEY_API_KEY"
echo "  - LANGCHAIN_API_KEY"
echo ""
echo -e "${YELLOW}Optional services:${NC}"
echo "  - REDIS_DATABASE_NAME"
echo "  - REDIT_DATABASE_ENDPOINT"
echo "  - ELEVENLABS_API_KEY"
echo "  - HUGGINGFACE_API_TOKEN"
echo ""

# Function to test deployment readiness
test_deployment_readiness() {
    echo -e "${YELLOW}Testing deployment readiness...${NC}"
    
    # Source the .env file
    set -a
    source .env
    set +a
    
    # Check critical variables
    READY=true
    
    if [ -z "$VULTR_API_KEY" ] || [ "$VULTR_API_KEY" = "your-vultr-api-key" ]; then
        echo -e "${RED}✗ VULTR_API_KEY not set${NC}"
        READY=false
    else
        echo -e "${GREEN}✓ VULTR_API_KEY set${NC}"
    fi
    
    if [ -z "$VULTR_IP_ADDRESS" ] || [ "$VULTR_IP_ADDRESS" = "your-vultr-server-ip" ]; then
        echo -e "${RED}✗ VULTR_IP_ADDRESS not set${NC}"
        READY=false
    else
        echo -e "${GREEN}✓ VULTR_IP_ADDRESS set${NC}"
    fi
    
    if [ -z "$SSH_PRIVATE_KEY" ] || [ "$SSH_PRIVATE_KEY" = "your-ssh-private-key" ]; then
        echo -e "${RED}✗ SSH_PRIVATE_KEY not set${NC}"
        READY=false
    else
        echo -e "${GREEN}✓ SSH_PRIVATE_KEY set${NC}"
    fi
    
    if [ -z "$DOCKERHUB_USERNAME" ] || [ "$DOCKERHUB_USERNAME" = "your-dockerhub-username" ]; then
        echo -e "${RED}✗ DOCKERHUB_USERNAME not set${NC}"
        READY=false
    else
        echo -e "${GREEN}✓ DOCKERHUB_USERNAME set${NC}"
    fi
    
    if [ "$READY" = true ]; then
        echo -e "${GREEN}✓ All critical variables are set!${NC}"
        echo ""
        echo "You can now:"
        echo "1. Deploy manually: ./infrastructure/manual-deploy.sh $VULTR_IP_ADDRESS"
        echo "2. Push to GitHub to trigger automatic deployment"
    else
        echo -e "${RED}✗ Some critical variables are missing${NC}"
        echo "Please update your .env file with the actual values"
    fi
}

# Ask if user wants to test
echo ""
read -p "Do you want to test deployment readiness? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    test_deployment_readiness
fi

echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your actual values"
echo "2. Run 'source .env' to load environment variables"
echo "3. Deploy using GitHub Actions or manual scripts"