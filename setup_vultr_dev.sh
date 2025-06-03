#!/bin/bash

echo "🚀 Setting up Vultr development environment"
echo "=========================================="

# Check if we're on Vultr server
if [[ $(hostname -I) != *"45.32.69.157"* ]]; then
    echo "⚠️  This should be run on the Vultr server!"
    echo "   SSH to server first: ssh root@45.32.69.157"
    exit 1
fi

cd /root/orchestra-main

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
git config --global user.name "Orchestra Admin"

# Create development aliases
cat >> ~/.bashrc << 'EOF'

# Orchestra aliases
alias orch='cd /root/orchestra-main'
alias logs='docker-compose logs -f'
alias deploy='cd /root/orchestra-main && ./deploy.sh'
alias status='docker-compose ps'
alias restart='docker-compose restart'
EOF

echo ""
echo "✅ Vultr development environment ready!"
echo ""
echo "Useful commands:"
echo "- orch: Go to project directory"
echo "- logs: View Docker logs"
echo "- deploy: Deploy changes"
echo "- status: Check service status"
echo "- restart: Restart services"
echo ""
echo "To start coding:"
echo "1. cd /root/orchestra-main"
echo "2. Edit files with vim or nano"
echo "3. Run ./deploy.sh to deploy changes"
