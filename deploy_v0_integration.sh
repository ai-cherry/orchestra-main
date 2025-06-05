#!/bin/bash
# Deploy v0.dev integration to Lambda Labs

set -e

LAMBDA_IP="150.136.94.139"
LAMBDA_USER="ubuntu"

echo "🎨 Deploying v0.dev Integration to Orchestra AI..."

# Copy enhanced AI assistant
scp ai_assist_v0.py ${LAMBDA_USER}@${LAMBDA_IP}:/opt/cherry-ai/
scp docs/v0_integration_guide.md ${LAMBDA_USER}@${LAMBDA_IP}:/opt/cherry-ai/docs/

# Deploy on server
ssh ${LAMBDA_USER}@${LAMBDA_IP} << 'EOF'
cd /opt/cherry-ai

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Create v0 bridge script
cat > v0_bridge.mjs << 'EOFBRIDGE'
import { generateText } from 'ai';
import { vercel } from '@ai-sdk/vercel';

const args = process.argv.slice(2);
const prompt = args.join(' ');

async function generateUI() {
  try {
    const { text } = await generateText({
      model: vercel('v0-1.0-md'),
      prompt: prompt,
    });
    console.log(text);
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

generateUI();
EOFBRIDGE

# Initialize npm project if needed
if [ ! -f package.json ]; then
    npm init -y
fi

# Install Vercel AI SDK
echo "📦 Installing Vercel AI SDK..."
npm install ai @ai-sdk/vercel

# Install redis Python module for caching
pip3 install redis

# Create a combined AI assistant that includes v0.dev
sudo cp ai_assist_v0.py /usr/local/bin/ai_assist_v0
sudo chmod +x /usr/local/bin/ai_assist_v0

# Create database schema for UI components
sudo -u postgres psql cherry_ai << 'SQLEOF'
-- Create table for UI components if not exists
CREATE TABLE IF NOT EXISTS ui_components (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    component_code TEXT NOT NULL,
    framework VARCHAR(50) DEFAULT 'react',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Index for text search
CREATE INDEX IF NOT EXISTS idx_ui_components_description 
ON ui_components USING gin(to_tsvector('english', description));
SQLEOF

# Add v0.dev API key to bashrc
# Use GitHub secret if available, otherwise use hardcoded key
if [ -n "$V0_API_KEY" ]; then
    echo "✅ Using V0_API_KEY from GitHub secrets"
    V0_KEY="$V0_API_KEY"
else
    V0_KEY="v0_v1:team_63co8i4lkMlbdAbcLCae7xS7:QD0VzamI520lj7xtsojy1AgG"
fi

if ! grep -q "V0_API_KEY" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# v0.dev API for UI generation" >> ~/.bashrc
    echo "export V0_API_KEY='${V0_KEY}'" >> ~/.bashrc
else
    # Update existing key
    sed -i '/V0_API_KEY/d' ~/.bashrc
    echo "export V0_API_KEY='${V0_KEY}'" >> ~/.bashrc
fi
export V0_API_KEY="${V0_KEY}"

echo ""
echo "✅ v0.dev integration deployed!"
echo ""
echo "📋 To complete setup:"
echo "1. Get your v0.dev API key from https://v0.dev"
echo "2. Set it on the server:"
echo "   export V0_API_KEY='v0_v1:team_63co8i4lkMlbdAbcLCae7xS7:QD0VzamI520lj7xtsojy1AgG'"
echo "   echo \"export V0_API_KEY='v0_v1:team_63co8i4lkMlbdAbcLCae7xS7:QD0VzamI520lj7xtsojy1AgG'\" >> ~/.bashrc"
echo ""
echo "🧪 Test commands:"
echo "   ai_assist_v0 ui \"modern pricing table with 3 tiers\""
echo "   ai_assist_v0 ui \"dashboard with sidebar navigation\""
echo "   ai_assist_v0 review main.py"
echo ""
echo "📊 Features added:"
echo "   - UI component generation with v0.dev"
echo "   - Redis caching for generated components"
echo "   - PostgreSQL storage for component library"
echo "   - Node.js bridge for Vercel AI SDK"
EOF

echo ""
echo "🎉 v0.dev integration deployed!"
echo ""
echo "🔗 Next steps:"
echo "1. SSH to server: ssh ubuntu@${LAMBDA_IP}"
echo "2. Set V0_API_KEY environment variable"
echo "3. Test UI generation: ai_assist_v0 ui \"your UI description\""
echo ""
echo "📚 Documentation deployed to:"
echo "   /opt/cherry-ai/docs/v0_integration_guide.md" 