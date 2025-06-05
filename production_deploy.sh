#!/bin/bash
# Run this directly on the Lambda Labs server

cd /opt/cherry-ai

echo "🚀 Deploying Orchestra AI Complete Ecosystem..."

# Set API keys
OPENROUTER_KEY="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"
V0_KEY="v0_v1:team_63co8i4lkMlbdAbcLCae7xS7:QD0VzamI520lj7xtsojy1AgG"

# Update bashrc with API keys
if ! grep -q "OPENROUTER_API_KEY" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# OpenRouter API for AI assistance" >> ~/.bashrc
    echo "export OPENROUTER_API_KEY=\"${OPENROUTER_KEY}\"" >> ~/.bashrc
else
    sed -i '/OPENROUTER_API_KEY/d' ~/.bashrc
    echo "export OPENROUTER_API_KEY=\"${OPENROUTER_KEY}\"" >> ~/.bashrc
fi

if ! grep -q "V0_API_KEY" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# v0.dev API for UI generation" >> ~/.bashrc
    echo "export V0_API_KEY=\"${V0_KEY}\"" >> ~/.bashrc
else
    sed -i '/V0_API_KEY/d' ~/.bashrc
    echo "export V0_API_KEY=\"${V0_KEY}\"" >> ~/.bashrc
fi

# Export for current session
export OPENROUTER_API_KEY="${OPENROUTER_KEY}"
export V0_API_KEY="${V0_KEY}"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install redis

# Create symlinks
sudo ln -sf /opt/cherry-ai/ai_assist.py /usr/local/bin/ai_assist
sudo ln -sf /opt/cherry-ai/ai_assist_v0.py /usr/local/bin/ai_assist_v0
sudo chmod +x /usr/local/bin/ai_assist /usr/local/bin/ai_assist_v0

# Install Node.js if needed
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install docker-compose if needed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing docker-compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

# Create database schema for UI components
sudo -u postgres psql cherry_ai << 'SQLEOF' 2>/dev/null || true
CREATE TABLE IF NOT EXISTS ui_components (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    component_code TEXT NOT NULL,
    framework VARCHAR(50) DEFAULT 'react',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_ui_components_description 
ON ui_components USING gin(to_tsvector('english', description));
SQLEOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 Test AI Assistant:"
echo "   ai_assist review main.py"
echo "   ai_assist design main.py"
echo "   ai_assist optimize main.py"
echo ""
echo "🎨 Test UI Generation:"
echo "   ai_assist_v0 ui \"modern dashboard\""
echo "   ai_assist_v0 ui \"pricing table\""
echo ""
echo "📋 API Keys configured:"
echo "   - OpenRouter ✅"
echo "   - v0.dev ✅"
echo ""
echo "🔄 Reload your shell to use the new commands:"
echo "   source ~/.bashrc" 