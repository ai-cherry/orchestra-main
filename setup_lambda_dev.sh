#!/bin/bash

echo "🚀 Setting up Lambda development environment"
echo "=========================================="

# Check if we're on Lambda server
if [[ $(hostname -I) != *"45.32.69.157"* ]]; then
    echo "⚠️  This should be run on the Lambda server!"
    echo "   SSH to server first: ssh root@45.32.69.157"
    exit 1
fi

cd /root/cherry_ai-main

# Install development tools
echo "Installing development tools..."
apt-get update -qq
apt-get install -y vim nano htop git curl wget jq

# Set up Python environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure git
git config --global user.email "admin@cherry-ai.me"
git config --global user.name "cherry_ai Admin"

# Create development aliases
cat >> ~/.bashrc << 'EOF'

# cherry_ai aliases
alias orch='cd /root/cherry_ai-main'
alias logs='docker-compose logs -f'
alias deploy='cd /root/cherry_ai-main && ./deploy.sh'
alias status='docker-compose ps'
alias restart='docker-compose restart'
EOF

echo ""
echo "✅ Lambda development environment ready!"
echo ""
echo "Useful commands:"
echo "- orch: Go to project directory"
echo "- logs: View Docker logs"
echo "- deploy: Deploy changes"
echo "- status: Check service status"
echo "- restart: Restart services"
echo ""
echo "To start coding:"
echo "1. cd /root/cherry_ai-main"
echo "2. Edit files with vim or nano"
echo "3. Run ./deploy.sh to deploy changes"
