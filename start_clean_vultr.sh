#!/bin/bash

echo "Starting clean Vultr environment in new shell..."
echo ""
echo "This will open a new bash session without any GCP configuration."
echo "The GCP setup script has been removed from your .bashrc"
echo ""

# Start a new bash session with clean environment
exec bash --norc -c '
# Load only the essentials from bashrc without the GCP setup
export PS1="\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "
export PATH=$PATH:/home/paperspace/.pulumi/bin

# Navigate to project
cd /home/paperspace/cherry_ai-main

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set Vultr environment
export VULTR_SERVER_IP="45.32.69.157"
export ENVIRONMENT="production"
export PROJECT_ROOT="${PWD}"
export PULUMI_CONFIG_PASSPHRASE="cherry_ai-dev-123"
export PULUMI_SKIP_UPDATE_CHECK=true

echo "🎉 Clean Vultr environment ready!"
echo "📍 No GCP configuration loaded"
echo "🐍 Virtual environment: activated"
echo "🌐 Vultr server: $VULTR_SERVER_IP"
echo ""
echo "Remember to set your Vultr API key:"
echo "  export VULTR_API_KEY=your-actual-key"
echo ""

# Start interactive bash
exec bash --norc
'
