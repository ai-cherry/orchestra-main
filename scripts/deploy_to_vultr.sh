#!/bin/bash
# Deploy AI coordination to Vultr using Pulumi

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              VULTR DEPLOYMENT HELPER                             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

# Add Pulumi to PATH
export PATH=$PATH:/root/.pulumi/bin

# Check if Pulumi is available
if ! command -v pulumi &> /dev/null; then
    echo "❌ Pulumi not found in PATH"
    echo "Installing Pulumi..."
    curl -fsSL https://get.pulumi.com | sh
    export PATH=$PATH:$HOME/.pulumi/bin
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "❌ .env file not found!"
    exit 1
fi

# Check Vultr API key
if [ -z "$VULTR_API_KEY" ]; then
    echo "❌ VULTR_API_KEY not found!"
    echo "Run: ./scripts/configure_api_keys.sh"
    exit 1
fi

echo "✅ Vultr API key found"
echo

# Navigate to infrastructure directory
cd infrastructure || exit 1

# Install Python dependencies for Pulumi
echo "📦 Installing Pulumi dependencies..."
pip install -r requirements.txt

# Initialize Pulumi stack
echo
echo "🚀 Initializing Pulumi stack..."
pulumi stack init production 2>/dev/null || pulumi stack select production

# Set Pulumi configuration
echo "⚙️  Setting Pulumi configuration..."
pulumi config set vultr:api_key "$VULTR_API_KEY" --secret

# Preview deployment
echo
echo "👀 Preview deployment changes:"
echo "════════════════════════════"
pulumi preview

echo
echo "📌 Ready to deploy?"
echo "To deploy, run: pulumi up"
echo
echo "💡 Deployment commands:"
echo "  pulumi up          - Deploy infrastructure"
echo "  pulumi destroy     - Tear down infrastructure"
echo "  pulumi stack       - View stack info"
echo "  pulumi refresh     - Sync state with cloud"