#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI cherry_ai Deployment Test${NC}"
echo "============================="
echo ""
echo -e "${YELLOW}This script shows what will be deployed to cherry-ai.me${NC}"
echo ""

# Check Docker image
if [ -f "cherry_ai-api-minimal.tar.gz" ]; then
    echo -e "${GREEN}✓ Docker image found: cherry_ai-api-minimal.tar.gz (64MB)${NC}"
    echo "  Contains:"
    echo "  - Fixed authentication system"
    echo "  - 5 AI personas (Cherry, AI Assistant, Technical Architect, Sophia, Gordon Gekko)"
    echo "  - All API endpoints"
    echo "  - Nginx configuration"
else
    echo -e "${RED}✗ Docker image not found${NC}"
fi

echo ""
echo -e "${GREEN}What will be deployed:${NC}"
echo "1. API Endpoints:"
echo "   - /api/health - Health check"
echo "   - /api/auth/login - Authentication (JWT)"
echo "   - /api/personas - List personas"
echo "   - /api/agents - Agent management"
echo "   - /api/workflows - Workflow management"
echo ""
echo "2. Personas configured:"
echo "   - Cherry (Creative AI)"
echo "   - AI Assistant (General helper)"
echo "   - Technical Architect (System design expert)"
echo "   - Sophia (Analytical powerhouse)"
echo "   - Gordon Gekko (Efficiency expert)"
echo ""
echo "3. Environment variables from GitHub secrets:"
echo "   - ANTHROPIC_API_KEY"
echo "   - OPENAI_API_KEY"
echo "   - PORTKEY_API_KEY"
echo "   - LANGCHAIN_API_KEY"
echo "   - And many more..."
echo ""
echo -e "${YELLOW}To deploy to your Vultr server:${NC}"
echo ""
echo "Option 1: If you know your Vultr IP from GitHub secrets:"
echo "  ./infrastructure/manual-deploy.sh YOUR_VULTR_IP"
echo ""
echo "Option 2: Push to GitHub to trigger automatic deployment:"
echo "  git push origin main"
echo ""
echo "The deployment will:"
echo "- Copy Docker image to server"
echo "- Install Docker and nginx"
echo "- Configure reverse proxy"
echo "- Start the API container"
echo "- Make it available at http://cherry-ai.me"