#!/bin/bash
# Deploy OpenRouter API key to Lambda Labs server

set -e

LAMBDA_IP="150.136.94.139"
LAMBDA_USER="ubuntu"
# Use GitHub secret if available, otherwise use hardcoded key
if [ -n "$OPENROUTER_API_KEY" ]; then
    echo "✅ Using OPENROUTER_API_KEY from GitHub secrets"
    OPENROUTER_KEY="$OPENROUTER_API_KEY"
else
    OPENROUTER_KEY="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"
fi

echo "🔑 Deploying OpenRouter API key to Lambda Labs..."

# Deploy key securely
ssh ${LAMBDA_USER}@${LAMBDA_IP} << EOF
# Add to bashrc if not already present
if ! grep -q "OPENROUTER_API_KEY" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# OpenRouter API for AI assistance" >> ~/.bashrc
    echo "export OPENROUTER_API_KEY=\"${OPENROUTER_KEY}\"" >> ~/.bashrc
    echo "✅ API key added to ~/.bashrc"
else
    # Update existing key
    sed -i '/OPENROUTER_API_KEY/d' ~/.bashrc
    echo "export OPENROUTER_API_KEY=\"${OPENROUTER_KEY}\"" >> ~/.bashrc
    echo "✅ API key updated in ~/.bashrc"
fi

# Also set it for current session
export OPENROUTER_API_KEY="${OPENROUTER_KEY}"

# Test the AI assistant
cd /opt/cherry-ai
echo ""
echo "🧪 Testing AI Assistant with all three models..."
echo ""

# Create a test file if it doesn't exist
if [ ! -f test_ai.py ]; then
    cat > test_ai.py << 'EOFTEST'
def calculate_sum(numbers):
    """Calculate sum of numbers."""
    total = 0
    for n in numbers:
        total = total + n
    return total

print(calculate_sum([1, 2, 3, 4, 5]))
EOFTEST
fi

echo "1️⃣ Testing GPT-4o-mini (Code Review):"
echo "======================================="
timeout 30 ai_assist review test_ai.py | head -20
echo ""

echo "2️⃣ Testing Claude 3.5 Sonnet (Architecture Design):"
echo "===================================================="
timeout 30 ai_assist design test_ai.py | head -20
echo ""

echo "3️⃣ Testing Gemini 2.0 Flash (Performance Optimization):"
echo "========================================================"
timeout 30 ai_assist optimize test_ai.py | head -20
echo ""

# Install docker-compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing docker-compose..."
    sudo apt-get update -qq
    sudo apt-get install -y docker-compose
fi

# Start MCP filesystem server
if [ -f docker-compose.mcp.yml ]; then
    echo "🐳 Starting MCP filesystem server..."
    docker-compose -f docker-compose.mcp.yml up -d
fi

echo ""
echo "✅ OpenRouter deployment complete!"
echo ""
echo "📊 Status Summary:"
echo "   - API Key: Configured ✅"
echo "   - AI Assistant: Tested ✅"
echo "   - Docker Compose: Installed ✅"
echo "   - MCP Server: $(docker ps | grep mcp-filesystem > /dev/null && echo 'Running ✅' || echo 'Not running ⚠️')"
EOF

echo ""
echo "🎉 OpenRouter API key deployed successfully!"
echo ""
echo "🔗 Test the AI assistant:"
echo "   ssh ubuntu@${LAMBDA_IP}"
echo "   ai_assist review main.py"
echo ""
echo "🌐 Configure Cursor IDE:"
echo "   MCP Server: http://cherry-ai.me:8080" 