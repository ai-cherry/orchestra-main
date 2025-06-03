#!/bin/bash
# GitHub Authentication and Secrets Setup

echo "=== GitHub CLI Authentication Setup ==="
echo

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI not found. Installing..."
    sudo apt update && sudo apt install -y gh
fi

# Check current auth status
if gh auth status &> /dev/null; then
    echo "✅ Already authenticated with GitHub"
    gh auth status
else
    echo "📝 Setting up GitHub authentication..."
    echo
    echo "You'll need a GitHub Personal Access Token (PAT) with these scopes:"
    echo "  - repo (full control of private repositories)"
    echo "  - workflow (update GitHub Action workflows)"
    echo "  - admin:org (if using organization secrets)"
    echo
    echo "Create a token at: https://github.com/settings/tokens/new"
    echo
    echo "Press Enter when ready to authenticate..."
    read -r
    
    # Authenticate with GitHub
    gh auth login
fi

echo
echo "=== Setting Up Repository Secrets ==="
echo

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo "⚠️  Not in a GitHub repository. Please specify the repository:"
    echo "Format: owner/repo (e.g., myusername/orchestra-main)"
    read -r REPO
fi

echo "Setting secrets for repository: $REPO"
echo

# Function to set secret from .env file
set_secret_from_env() {
    local key=$1
    local value=$(grep "^$key=" .env 2>/dev/null | cut -d'=' -f2-)
    
    if [ -n "$value" ]; then
        echo -n "Setting $key... "
        if echo "$value" | gh secret set "$key" -R "$REPO" 2>/dev/null; then
            echo "✅"
        else
            echo "❌ Failed"
        fi
    else
        echo "⚠️  $key not found in .env file"
    fi
}

# Load secrets from .env file
if [ -f .env ]; then
    echo "Loading secrets from .env file..."
    echo
    
    # Database secrets
    echo "📊 Database Configuration:"
    set_secret_from_env "POSTGRES_HOST"
    set_secret_from_env "POSTGRES_PORT"
    set_secret_from_env "POSTGRES_DB"
    set_secret_from_env "POSTGRES_USER"
    set_secret_from_env "POSTGRES_PASSWORD"
    
    # Weaviate secrets
    echo -e "\n🔍 Weaviate Configuration:"
    set_secret_from_env "WEAVIATE_URL"
    set_secret_from_env "WEAVIATE_API_KEY"
    
    # AI Service secrets
    echo -e "\n🤖 AI Service API Keys:"
    set_secret_from_env "ANTHROPIC_API_KEY"
    set_secret_from_env "OPENAI_API_KEY"
    set_secret_from_env "OPENROUTER_API_KEY"
    set_secret_from_env "GROK_AI_API_KEY"
    set_secret_from_env "MISTRAL_API_KEY"
    set_secret_from_env "PERPLEXITY_API_KEY"
    
    # Other service secrets
    echo -e "\n🔧 Other Service Keys:"
    set_secret_from_env "ELEVEN_LABS_API_KEY"
    set_secret_from_env "FIGMA_PERSONAL_ACCESS_TOKEN"
    set_secret_from_env "NOTION_API_KEY"
    set_secret_from_env "PORTKEY_API_KEY"
    set_secret_from_env "PORTKEY_CONFIG"
    set_secret_from_env "PHANTOM_BUSTER_API_KEY"
    
    # Infrastructure secrets - check if we can set them from environment
    echo -e "\n🏗️ Infrastructure Keys:"
    
    # Try to set infrastructure keys if available
    set_secret_from_env "VULTR_API_KEY"
    
    # For local development, these are optional
    echo -e "\n📌 Infrastructure Keys Status:"
    echo "These keys are only needed for production deployment:"
    echo
    echo "🔸 VULTR_API_KEY - Required for deploying to Vultr cloud"
    echo "   Priority: HIGH if deploying to production"
    echo "   Not needed for local development"
    echo
    echo "🔸 AIRBYTE_API_KEY/URL/WORKSPACE_ID - For data pipeline integration"
    echo "   Priority: LOW - Only if using Airbyte for ETL"
    echo "   Not needed for core AI orchestration"
    echo
    echo "🔸 PULUMI_CONFIG_PASSPHRASE - For infrastructure state encryption"
    echo "   Priority: MEDIUM if using Pulumi for deployment"
    echo "   Can use local state for development"
    echo
    echo "🔸 AWS_ACCESS_KEY_ID/SECRET - For S3 state backend"
    echo "   Priority: LOW - Only if using S3 for Pulumi state"
    echo "   Local file state works fine for development"
    echo
    echo "✅ For local development: These are NOT required!"
    echo "✅ Your AI orchestration is fully functional without them!"
    
else
    echo "❌ .env file not found!"
    echo "Run: ./scripts/configure_api_keys.sh first"
    exit 1
fi

echo
echo "=== Verification ==="
echo "To view all secrets:"
echo "  gh secret list -R $REPO"
echo
echo "To manually set a secret:"
echo "  gh secret set SECRET_NAME -R $REPO"
echo
echo "✅ GitHub Secrets setup complete!"