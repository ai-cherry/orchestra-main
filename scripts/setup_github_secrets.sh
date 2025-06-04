#!/bin/bash
# Setup GitHub Secrets for AI coordination System
# This script uses GitHub CLI to set repository secrets

set -e

echo "=== GitHub Secrets Setup for AI coordination ==="
echo

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo "Error: Not in a GitHub repository or cannot determine repository."
    echo "Make sure you're in the repository directory."
    exit 1
fi

echo "Setting secrets for repository: $REPO"
echo

# Function to set a secret
set_secret() {
    local name=$1
    local value=$2
    
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $name (no value provided)"
        return
    fi
    
    echo -n "Setting $name... "
    if gh secret set "$name" --body "$value" &>/dev/null; then
        echo "✓"
    else
        echo "✗ (failed)"
    fi
}

# Database Configuration
echo "=== Database Configuration ==="
set_secret "POSTGRES_HOST" "localhost"
set_secret "POSTGRES_PORT" "5432"
set_secret "POSTGRES_DB" "cherry_ai"
set_secret "POSTGRES_USER" "cherry_ai"
set_secret "POSTGRES_PASSWORD" "cherry_ai"

# Weaviate Configuration
echo -e "\n=== Weaviate Configuration ==="
set_secret "WEAVIATE_URL" "http://localhost:8080"
set_secret "WEAVIATE_API_KEY" "local-dev-key"

# AI Service API Keys (from environment or prompt)
echo -e "\n=== AI Service API Keys ==="

# Function to get API key from environment or prompt
get_api_key() {
    local key_name=$1
    local env_value="${!key_name}"
    
    if [ -n "$env_value" ]; then
        echo "$env_value"
    else
        echo ""
    fi
}

# Set AI service keys
set_secret "ANTHROPIC_API_KEY" "$(get_api_key ANTHROPIC_API_KEY)"
set_secret "OPENAI_API_KEY" "$(get_api_key OPENAI_API_KEY)"
set_secret "OPENROUTER_API_KEY" "$(get_api_key OPENROUTER_API_KEY)"
set_secret "GROK_AI_API_KEY" "$(get_api_key GROK_AI_API_KEY)"
set_secret "MISTRAL_API_KEY" "$(get_api_key MISTRAL_API_KEY)"
set_secret "PERPLEXITY_API_KEY" "$(get_api_key PERPLEXITY_API_KEY)"

# Other Service Keys
echo -e "\n=== Other Service API Keys ==="
set_secret "ELEVEN_LABS_API_KEY" "$(get_api_key ELEVEN_LABS_API_KEY)"
set_secret "FIGMA_PERSONAL_ACCESS_TOKEN" "$(get_api_key FIGMA_PERSONAL_ACCESS_TOKEN)"
set_secret "NOTION_API_KEY" "$(get_api_key NOTION_API_KEY)"
set_secret "PORTKEY_API_KEY" "$(get_api_key PORTKEY_API_KEY)"
set_secret "PORTKEY_CONFIG" "$(get_api_key PORTKEY_CONFIG)"
set_secret "PHANTOM_BUSTER_API_KEY" "$(get_api_key PHANTOM_BUSTER_API_KEY)"

# GitHub Tokens
echo -e "\n=== GitHub Tokens ==="
set_secret "GITHUB_TOKEN" "$(get_api_key GITHUB_TOKEN)"
set_secret "GH_CLASSIC_PAT_TOKEN" "$(get_api_key GH_CLASSIC_PAT_TOKEN)"
set_secret "GH_FINE_GRAINED_TOKEN" "$(get_api_key GH_FINE_GRAINED_TOKEN)"

# Infrastructure Keys (for deployment)
echo -e "\n=== Infrastructure Keys ==="
set_secret "VULTR_API_KEY" "$(get_api_key VULTR_API_KEY)"
set_secret "AIRBYTE_API_KEY" "$(get_api_key AIRBYTE_API_KEY)"
set_secret "AIRBYTE_API_URL" "$(get_api_key AIRBYTE_API_URL)"
set_secret "AIRBYTE_WORKSPACE_ID" "$(get_api_key AIRBYTE_WORKSPACE_ID)"

# Pulumi Configuration
set_secret "PULUMI_CONFIG_PASSPHRASE" "$(get_api_key PULUMI_CONFIG_PASSPHRASE)"
set_secret "AWS_ACCESS_KEY_ID" "$(get_api_key AWS_ACCESS_KEY_ID)"
set_secret "AWS_SECRET_ACCESS_KEY" "$(get_api_key AWS_SECRET_ACCESS_KEY)"

echo -e "\n=== Setup Complete ==="
echo "GitHub Secrets have been configured for $REPO"
echo
echo "To view all secrets:"
echo "  gh secret list"
echo
echo "To update a specific secret:"
echo "  gh secret set SECRET_NAME"
echo
echo "Note: Secrets are encrypted and only available to GitHub Actions workflows."
