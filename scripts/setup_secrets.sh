#!/bin/bash
# 🔐 Orchestra AI Secrets Setup Script
# Streamlined secrets management for single developer workflow

set -e

echo "🔐 Orchestra AI Secrets Setup"
echo "=============================="

# Check if .env.example exists
if [ ! -f ".env.example" ]; then
    echo "❌ .env.example not found. Please run from repository root."
    exit 1
fi

# Copy template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Creating .env from template..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "📋 .env file already exists"
fi

# Interactive setup
echo ""
echo "🔑 Enter your API keys (press Enter to skip):"
echo "   (Keys will be saved to .env file)"
echo ""

# Function to update env file
update_env() {
    local key=$1
    local value=$2
    if [ ! -z "$value" ]; then
        if grep -q "^${key}=" .env; then
            # Update existing key
            sed -i.bak "s|^${key}=.*|${key}=${value}|" .env
        else
            # Add new key
            echo "${key}=${value}" >> .env
        fi
        echo "✅ Updated ${key}"
    fi
}

# Core API keys
read -p "OpenAI API Key (sk-...): " OPENAI_KEY
update_env "OPENAI_API_KEY" "$OPENAI_KEY"

read -p "Notion API Token (ntn_...): " NOTION_TOKEN
update_env "NOTION_API_TOKEN" "$NOTION_TOKEN"

read -p "Anthropic API Key (sk-ant-...): " ANTHROPIC_KEY
update_env "ANTHROPIC_API_KEY" "$ANTHROPIC_KEY"

# Web automation keys
echo ""
echo "🌐 Web Automation Platforms (optional):"
read -p "Phantombuster API Key: " PHANTOMBUSTER_KEY
update_env "PHANTOMBUSTER_API_KEY" "$PHANTOMBUSTER_KEY"

read -p "Apify API Token: " APIFY_TOKEN
update_env "APIFY_API_TOKEN" "$APIFY_TOKEN"

read -p "ZenRows API Key: " ZENROWS_KEY
update_env "ZENROWS_API_KEY" "$ZENROWS_KEY"

# Database URLs
echo ""
echo "🗄️ Database Configuration (optional):"
read -p "Database URL (postgresql://...): " DATABASE_URL
update_env "DATABASE_URL" "$DATABASE_URL"

read -p "Redis Password: " REDIS_PASSWORD
update_env "REDIS_PASSWORD" "$REDIS_PASSWORD"

# Clean up backup file
rm -f .env.bak

echo ""
echo "✅ Secrets configuration complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Test configuration: python3 utils/fast_secrets.py"
echo "   2. Validate setup: python3 -c 'from utils.fast_secrets import validate_setup; print(validate_setup())'"
echo "   3. Start development: ./ultimate_morning_startup_fixed.sh"
echo ""
echo "🔐 Your secrets are stored in .env (gitignored for security)"

# Test the configuration
echo "🧪 Testing secrets configuration..."
if python3 -c "from utils.fast_secrets import validate_setup; exit(0 if validate_setup() else 1)" 2>/dev/null; then
    echo "✅ Secrets validation passed!"
else
    echo "⚠️  Some required secrets missing, but setup complete"
    echo "   Add missing keys to .env file as needed"
fi

echo ""
echo "🎉 Setup complete! Ready for development." 