#!/bin/bash
# Setup API keys for Cherry AI
# This script should be run locally and NOT committed with actual keys

echo "🔐 Setting up API keys for Cherry AI"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from env.example..."
    cp env.example .env
fi

# Function to update or add a key in .env
update_env_key() {
    local key=$1
    local value=$2
    
    if grep -q "^${key}=" .env; then
        # Key exists, update it
        sed -i "s|^${key}=.*|${key}=${value}|" .env
    else
        # Key doesn't exist, add it
        echo "${key}=${value}" >> .env
    fi
}

# ElevenLabs API Key
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "⚠️  ELEVENLABS_API_KEY not set in environment"
    echo "Please set it with: export ELEVENLABS_API_KEY=your_key_here"
    echo "Then run this script again"
else
    update_env_key "ELEVENLABS_API_KEY" "$ELEVENLABS_API_KEY"
    echo "✅ ElevenLabs API key configured"
fi

# Other API keys can be added here
# Example:
# if [ -n "$OPENAI_API_KEY" ]; then
#     update_env_key "OPENAI_API_KEY" "$OPENAI_API_KEY"
# fi

echo ""
echo "✨ API keys setup complete!"
echo "Remember to source .env before running the application:"
echo "  source .env"
echo ""
echo "⚠️  IMPORTANT: Never commit .env with actual API keys!" 