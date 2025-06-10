#!/bin/bash

# Orchestra AI Environment Setup Script
# This script helps set up the development environment

set -e

echo "🎼 Orchestra AI Environment Setup"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "Pulumi.frontend.yaml" ]; then
    echo -e "${RED}Error: This script must be run from the orchestra-main directory${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check for required tools
echo -e "\n${YELLOW}Checking required tools...${NC}"

MISSING_TOOLS=()

if ! command_exists python3; then
    MISSING_TOOLS+=("python3")
fi

if ! command_exists node; then
    MISSING_TOOLS+=("node")
fi

if ! command_exists npm; then
    MISSING_TOOLS+=("npm")
fi

if ! command_exists docker; then
    MISSING_TOOLS+=("docker")
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo -e "${RED}Missing required tools: ${MISSING_TOOLS[*]}${NC}"
    echo "Please install these tools and run the script again."
    exit 1
else
    echo -e "${GREEN}✓ All required tools found${NC}"
fi

# 2. Generate .env from Pulumi if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}Generating .env from Pulumi config...${NC}"
    python3 scripts/generate_env_from_pulumi.py
    echo -e "${GREEN}✓ Generated .env file${NC}"
else
    echo -e "\n${GREEN}✓ .env file already exists${NC}"
fi

# 3. Create necessary directories
echo -e "\n${YELLOW}Creating directory structure...${NC}"
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/weaviate
echo -e "${GREEN}✓ Directories created${NC}"

# 4. Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
    python3 -m pip install -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

# 5. Set up integrations
echo -e "\n${YELLOW}Setting up integrations module...${NC}"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "export PYTHONPATH=\"\${PYTHONPATH}:$(pwd)\"" >> ~/.bashrc
echo -e "${GREEN}✓ PYTHONPATH configured${NC}"

# 6. Validate environment
echo -e "\n${YELLOW}Validating environment configuration...${NC}"
python3 scripts/validate_secrets.py || true

# 7. Create SSH directory if needed
if [ ! -d "$HOME/.ssh" ]; then
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
fi

# 8. Display next steps
echo -e "\n${GREEN}🎉 Setup complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Edit .env file and add your API keys"
echo "2. Run 'source ~/.bashrc' to update your shell"
echo "3. Start the development servers:"
echo "   - Backend: cd agent && python main.py"
echo "   - Frontend: cd admin-interface && npm run dev"
echo "4. Access the application at http://localhost:5173"
echo ""
echo "For production deployment:"
echo "   - Add secrets to GitHub repository settings"
echo "   - Run GitHub Actions workflows"
echo ""
echo -e "${GREEN}Happy orchestrating! 🎵${NC}" 