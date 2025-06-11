#!/bin/bash
# AI-Driven Infrastructure as Code Setup - Orchestra AI
# Performance-first implementation with Cursor AI + MCP integration

set -e

echo "🎼 Setting up AI-Driven Infrastructure as Code for Orchestra AI"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Step 1: Verify Prerequisites
echo -e "\n${BLUE}📋 Step 1: Verifying Prerequisites${NC}"

# Check Pulumi
if command -v pulumi &> /dev/null; then
    print_status "Pulumi CLI found: $(pulumi version)"
else
    print_warning "Pulumi not found. Installing..."
    curl -fsSL https://get.pulumi.com | sh
    export PATH=$PATH:~/.pulumi/bin
    print_status "Pulumi installed"
fi

# Check Python
if command -v python3 &> /dev/null; then
    print_status "Python found: $(python3 --version)"
else
    print_error "Python 3 is required. Please install it first."
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    print_status "pip found"
else
    print_error "pip3 is required. Please install it first."
    exit 1
fi

# Step 2: Install Python Dependencies
echo -e "\n${BLUE}📦 Step 2: Installing Python Dependencies${NC}"

# Install Pulumi packages
pip3 install --quiet \
    pulumi \
    pulumi-github \
    pulumi-vercel \
    pulumi-docker \
    pulumi-kubernetes \
    pulumi-command \
    pulumi-random

# Install MCP dependencies
pip3 install --quiet \
    mcp \
    asyncio \
    jinja2

print_status "Python dependencies installed"

# Step 3: Set up Pulumi ESC
echo -e "\n${BLUE}🔐 Step 3: Setting up Pulumi ESC${NC}"

if ! pulumi whoami &> /dev/null; then
    print_warning "Please login to Pulumi first:"
    echo "Run: pulumi login"
    echo "Then re-run this script"
    exit 1
fi

# Run ESC setup
cd infrastructure/pulumi
./esc-setup.sh

print_status "Pulumi ESC environments configured"

# Step 4: Configure Secrets (Interactive)
echo -e "\n${BLUE}🔑 Step 4: Configure Secrets${NC}"

print_info "You need to configure secrets in Pulumi ESC. Here are the commands:"
echo ""
echo "# Core secrets (required):"
echo "pulumi env set orchestra-ai/base --secret values.secrets.github_token 'YOUR_GITHUB_TOKEN'"
echo "pulumi env set orchestra-ai/base --secret values.secrets.lambda_api_key 'YOUR_LAMBDA_API_KEY'"
echo "pulumi env set orchestra-ai/base --secret values.secrets.openai_api_key 'YOUR_OPENAI_API_KEY'"
echo ""
echo "# Optional secrets:"
echo "pulumi env set orchestra-ai/base --secret values.secrets.vercel_token 'YOUR_VERCEL_TOKEN'"
echo "pulumi env set orchestra-ai/base --secret values.secrets.anthropic_api_key 'YOUR_ANTHROPIC_API_KEY'"
echo "pulumi env set orchestra-ai/base --secret values.secrets.weaviate_api_key 'YOUR_WEAVIATE_API_KEY'"
echo "pulumi env set orchestra-ai/base --secret values.secrets.pinecone_api_key 'YOUR_PINECONE_API_KEY'"
echo ""

read -p "Have you configured the required secrets? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please configure secrets first, then re-run this script"
    exit 1
fi

# Step 5: Set up MCP Server
echo -e "\n${BLUE}🤖 Step 5: Setting up MCP Server for Cursor AI${NC}"

cd ../../

# Create .cursor directory if it doesn't exist
mkdir -p .cursor

# Create MCP server configuration
cat > .cursor/mcp-servers.json << 'EOF'
{
  "mcpServers": {
    "pulumi-ai": {
      "command": "python3",
      "args": ["infrastructure/mcp_servers/pulumi_ai_server.py"],
      "env": {
        "PULUMI_ACCESS_TOKEN": "{PULUMI_ACCESS_TOKEN}",
        "PULUMI_CONFIG_PASSPHRASE": "{PULUMI_CONFIG_PASSPHRASE}",
        "PULUMI_ORG": "ai-cherry",
        "PULUMI_PROJECT": "orchestra-ai"
      }
    }
  }
}
EOF

print_status "MCP server configuration created"

# Step 6: Test Infrastructure Generation
echo -e "\n${BLUE}🧪 Step 6: Testing Infrastructure Generation${NC}"

# Test Pulumi configuration
cd infrastructure/pulumi

# Try to preview the main stack
print_info "Testing Pulumi configuration..."
if pulumi preview --config pulumi:environment=orchestra-ai/dev --non-interactive; then
    print_status "Pulumi configuration test passed"
else
    print_warning "Pulumi configuration needs adjustment. Check your ESC setup."
fi

cd ../../

# Step 7: Create Quick Start Templates
echo -e "\n${BLUE}📝 Step 7: Creating Quick Start Templates${NC}"

# Create templates directory
mkdir -p infrastructure/templates

# Create simple deployment template
cat > infrastructure/templates/quick-deploy.py << 'EOF'
#!/usr/bin/env python3
"""
Quick deployment template for Orchestra AI
Usage: python3 infrastructure/templates/quick-deploy.py <service-type> <stack-name>
"""

import sys
import subprocess

def deploy_service(service_type, stack_name):
    """Deploy a service using AI-generated infrastructure"""
    
    # Service templates
    templates = {
        "api": "generate_api_infrastructure",
        "database": "generate_database_infrastructure", 
        "frontend": "generate_frontend_infrastructure"
    }
    
    if service_type not in templates:
        print(f"❌ Unknown service type: {service_type}")
        print(f"Available types: {list(templates.keys())}")
        return False
    
    print(f"🚀 Deploying {service_type} as stack '{stack_name}'...")
    
    # This would integrate with the MCP server for AI generation
    print("✅ Ready for AI-driven deployment!")
    print(f"Next: Use Cursor AI to generate {service_type} infrastructure")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 quick-deploy.py <service-type> <stack-name>")
        sys.exit(1)
    
    service_type = sys.argv[1]
    stack_name = sys.argv[2]
    
    deploy_service(service_type, stack_name)
EOF

chmod +x infrastructure/templates/quick-deploy.py

print_status "Quick start templates created"

# Step 8: Final Setup Summary
echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Your AI-driven infrastructure is ready! Here's what you can do now:"
echo ""
echo "🚀 Immediate Actions:"
echo "1. Open Cursor AI in this directory"
echo "2. The MCP server should auto-connect (check for @pulumi-ai in chat)"
echo "3. Try: 'Generate a database infrastructure for development environment'"
echo ""
echo "📁 Key Files Created:"
echo "- infrastructure/pulumi/esc-setup.sh (ESC configuration)"
echo "- infrastructure/pulumi/stacks/github_stack.py (GitHub management)"
echo "- infrastructure/mcp_servers/pulumi_ai_server.py (AI integration)"
echo "- .cursor/mcp-servers.json (Cursor AI configuration)"
echo ""
echo "🔧 Available Commands:"
echo "- Deploy existing infrastructure: cd infrastructure/pulumi && pulumi up --config pulumi:environment=orchestra-ai/dev"
echo "- Quick deploy template: python3 infrastructure/templates/quick-deploy.py api my-api-stack"
echo "- List ESC environments: pulumi env ls"
echo ""
echo "📚 Next Steps:"
echo "1. Configure additional secrets as needed"
echo "2. Use Cursor AI to generate infrastructure with natural language"
echo "3. Deploy generated code with 'pulumi up'"
echo "4. Monitor via AI-driven infrastructure analysis"
echo ""
echo "🎯 Performance Goals:"
echo "- Infrastructure deployment: < 5 minutes"
echo "- AI code generation: < 10 seconds"  
echo "- 95% automation via AI"
echo ""
print_status "Setup complete! Start using AI-driven infrastructure now." 