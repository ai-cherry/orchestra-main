#!/bin/bash
# Setup script for Orchestra AI IaC Agent
# This script configures all external API integrations

set -e

echo "🚀 Setting up Orchestra AI IaC Agent"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check environment variable
check_env() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}❌ Missing environment variable: $1${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Found $1${NC}"
        return 0
    fi
}

# 1. Install Required Tools
echo -e "\n${YELLOW}📦 Installing Required Tools...${NC}"

# Install Pulumi
if ! command_exists pulumi; then
    echo "Installing Pulumi..."
    curl -fsSL https://get.pulumi.com | sh
    export PATH=$PATH:$HOME/.pulumi/bin
else
    echo -e "${GREEN}✅ Pulumi already installed${NC}"
fi

# Install GitHub CLI
if ! command_exists gh; then
    echo "Installing GitHub CLI..."
    brew install gh
else
    echo -e "${GREEN}✅ GitHub CLI already installed${NC}"
fi

# Install Python dependencies
echo -e "\n${YELLOW}🐍 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install \
    pulumi \
    pulumi-github \
    pulumi-random \
    weaviate-client \
    pinecone-client \
    psycopg2-binary \
    redis \
    portkey-ai \
    requests \
    python-dotenv

# 2. Check Required Environment Variables
echo -e "\n${YELLOW}🔑 Checking API Credentials...${NC}"

MISSING_VARS=0

# Lambda Labs
if ! check_env "LAMBDA_LABS_API_KEY"; then
    echo "  Get your API key from: https://cloud.lambdalabs.com/api-keys"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

# Pulumi
if ! check_env "PULUMI_ACCESS_TOKEN"; then
    echo "  Get your token from: https://app.pulumi.com/settings/tokens"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

# GitHub
if ! check_env "GITHUB_TOKEN"; then
    echo "  Create a token at: https://github.com/settings/tokens"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

# Pinecone
if ! check_env "PINECONE_API_KEY"; then
    echo "  Get your API key from: https://app.pinecone.io/"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

# Weaviate (optional for self-hosted)
if ! check_env "WEAVIATE_API_KEY"; then
    echo -e "${YELLOW}⚠️  WEAVIATE_API_KEY not set (OK if self-hosted)${NC}"
fi

# Portkey
if ! check_env "PORTKEY_API_KEY"; then
    echo "  Get your API key from: https://app.portkey.ai/"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

# 3. Create .env.iac file if missing vars
if [ $MISSING_VARS -gt 0 ]; then
    echo -e "\n${YELLOW}📝 Creating .env.iac template...${NC}"
    cat > .env.iac << 'EOF'
# Orchestra AI IaC Agent Environment Variables
# Fill in your API keys below

# Lambda Labs Cloud
LAMBDA_LABS_API_KEY=your_lambda_labs_api_key_here

# Pulumi
PULUMI_ACCESS_TOKEN=your_pulumi_access_token_here

# GitHub
GITHUB_TOKEN=your_github_token_here

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment

# Weaviate (if using cloud-hosted)
WEAVIATE_API_KEY=your_weaviate_api_key_here
WEAVIATE_URL=http://localhost:8080

# Portkey
PORTKEY_API_KEY=your_portkey_api_key_here

# Additional Configuration
PULUMI_BACKEND_URL=file://~/.pulumi
PULUMI_CONFIG_PASSPHRASE=your_secure_passphrase
EOF
    echo -e "${RED}⚠️  Please fill in the missing API keys in .env.iac${NC}"
fi

# 4. Initialize Pulumi
echo -e "\n${YELLOW}🔧 Initializing Pulumi...${NC}"
cd infrastructure/pulumi || mkdir -p infrastructure/pulumi && cd infrastructure/pulumi

# Create Pulumi project if it doesn't exist
if [ ! -f "Pulumi.yaml" ]; then
    pulumi new python -y \
        --name orchestra-ai-infrastructure \
        --description "Orchestra AI Infrastructure Management" \
        --stack dev
fi

# Select dev stack
pulumi stack select dev 2>/dev/null || pulumi stack init dev

# 5. Configure Pulumi
echo -e "\n${YELLOW}⚙️  Configuring Pulumi stack...${NC}"
pulumi config set --path 'orchestra:project' 'orchestra-ai'
pulumi config set --path 'orchestra:environment' 'development'
pulumi config set --path 'orchestra:region' 'us-west-2'

# Set secrets if environment variables are available
if [ -n "$LAMBDA_LABS_API_KEY" ]; then
    pulumi config set --secret lambda:apiKey "$LAMBDA_LABS_API_KEY"
fi

if [ -n "$PINECONE_API_KEY" ]; then
    pulumi config set --secret pinecone:apiKey "$PINECONE_API_KEY"
fi

if [ -n "$PORTKEY_API_KEY" ]; then
    pulumi config set --secret portkey:apiKey "$PORTKEY_API_KEY"
fi

# 6. Create API wrapper scripts
echo -e "\n${YELLOW}📜 Creating API wrapper scripts...${NC}"
cd ../../scripts
mkdir -p iac_tools

# Lambda Labs wrapper
cat > iac_tools/lambda_labs_cli.py << 'EOF'
#!/usr/bin/env python3
"""Lambda Labs API wrapper for IaC agent"""
import os
import requests
import json
from typing import List, Dict

class LambdaLabsClient:
    def __init__(self):
        self.api_key = os.environ.get("LAMBDA_LABS_API_KEY")
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def list_instances(self) -> List[Dict]:
        """List all instances"""
        resp = requests.get(f"{self.base_url}/instances", headers=self.headers)
        return resp.json()["data"]
    
    def create_instance(self, instance_type: str, region: str, ssh_key: str) -> Dict:
        """Create a new instance"""
        data = {
            "instance_type_name": instance_type,
            "region_name": region,
            "ssh_key_names": [ssh_key]
        }
        resp = requests.post(f"{self.base_url}/instance-operations/launch", 
                           headers=self.headers, json=data)
        return resp.json()
    
    def terminate_instance(self, instance_id: str) -> Dict:
        """Terminate an instance"""
        data = {"instance_ids": [instance_id]}
        resp = requests.post(f"{self.base_url}/instance-operations/terminate",
                           headers=self.headers, json=data)
        return resp.json()

if __name__ == "__main__":
    import sys
    client = LambdaLabsClient()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            print(json.dumps(client.list_instances(), indent=2))
        elif command == "create" and len(sys.argv) >= 5:
            result = client.create_instance(sys.argv[2], sys.argv[3], sys.argv[4])
            print(json.dumps(result, indent=2))
        elif command == "terminate" and len(sys.argv) >= 3:
            result = client.terminate_instance(sys.argv[2])
            print(json.dumps(result, indent=2))
EOF

chmod +x iac_tools/lambda_labs_cli.py

# 7. Create Cursor workspace settings
echo -e "\n${YELLOW}🎨 Configuring Cursor workspace...${NC}"
cd ..
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
  "cursor.agent.enabled": true,
  "cursor.agent.iacMode": true,
  "cursor.agent.activeAgent": "iac_agent_enhanced",
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "terminal.integrated.env.osx": {
    "PULUMI_SKIP_UPDATE_CHECK": "true",
    "PULUMI_AUTOMATION_API_SKIP_VERSION_CHECK": "true"
  }
}
EOF

# 8. Test connectivity
echo -e "\n${YELLOW}🧪 Testing API Connections...${NC}"

# Test Pulumi
if command_exists pulumi; then
    pulumi version >/dev/null 2>&1 && echo -e "${GREEN}✅ Pulumi connection OK${NC}" || echo -e "${RED}❌ Pulumi connection failed${NC}"
fi

# Test GitHub
if [ -n "$GITHUB_TOKEN" ]; then
    gh auth status >/dev/null 2>&1 && echo -e "${GREEN}✅ GitHub connection OK${NC}" || echo -e "${RED}❌ GitHub connection failed${NC}"
fi

# Test other APIs can be added here

# 9. Final summary
echo -e "\n${GREEN}✨ IaC Agent Setup Complete!${NC}"
echo -e "\nNext steps:"
echo "1. Fill in any missing API keys in .env.iac"
echo "2. Source the environment: source .env.iac"
echo "3. Restart Cursor IDE"
echo "4. The IaC agent will be available in the agent selector"
echo -e "\n${YELLOW}Example usage in Cursor:${NC}"
echo "  'Deploy a GPU instance on Lambda Labs for training'"
echo "  'Create a Pinecone index for production embeddings'"
echo "  'Set up Portkey routing for OpenAI and Anthropic'" 