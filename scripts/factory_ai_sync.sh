#!/bin/bash
# Factory AI Sync Script
# Ensures Factory AI is working with the latest code

set -e

echo "🔄 Factory AI Sync Script"
echo "========================="

# Navigate to the correct directory
cd /root/orchestra-main

# Activate virtual environment
source venv/bin/activate

# Pull latest from GitHub
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Install any new dependencies
echo "📦 Installing dependencies..."
pip install -r requirements/base.txt

# Show current status
echo ""
echo "✅ Sync complete!"
echo "Current branch: $(git branch --show-current)"
echo "Latest commit: $(git log -1 --oneline)"
echo "Python: $(which python)"
echo "Virtual env: $VIRTUAL_ENV"

# Optional: restart services if needed
if systemctl is-active --quiet orchestra-api; then
    echo "🔄 Restarting Orchestra API..."
    sudo systemctl restart orchestra-api
fi

echo ""
echo "🎉 Factory AI is ready to code!" 