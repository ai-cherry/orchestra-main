#!/bin/bash
# Pulumi ESC Setup Script for Orchestra AI Infrastructure
# Performance-first, streamlined setup

set -e

echo "🚀 Setting up Orchestra AI Pulumi ESC environments..."

# Check if pulumi is installed
if ! command -v pulumi &> /dev/null; then
    echo "❌ Pulumi CLI not found. Please install: curl -fsSL https://get.pulumi.com | sh"
    exit 1
fi

# Login to Pulumi (if not already logged in)
echo "🔐 Checking Pulumi login..."
if ! pulumi whoami &> /dev/null; then
    echo "Please login to Pulumi:"
    pulumi login
fi

# Create base environment
echo "📦 Creating base environment..."
pulumi env init orchestra-ai/base --yes 2>/dev/null || echo "Base environment already exists"

# Create environment hierarchies
echo "🏗️ Setting up environment hierarchies..."

for env in dev staging prod; do
    echo "  Creating orchestra-ai/$env..."
    pulumi env init orchestra-ai/$env --inherit orchestra-ai/base --yes 2>/dev/null || echo "Environment $env already exists"
done

# Set up base configuration (without secrets for now)
echo "⚙️ Configuring base environment..."
pulumi env set orchestra-ai/base --yes values.project.name "orchestra-ai"
pulumi env set orchestra-ai/base --yes values.project.description "AI Orchestra - Unified AI Agent Management Platform"
pulumi env set orchestra-ai/base --yes values.project.version "1.0.0"

# Performance configurations
pulumi env set orchestra-ai/base --yes values.performance.mode "optimized"
pulumi env set orchestra-ai/base --yes values.performance.resource_limits false
pulumi env set orchestra-ai/base --yes values.performance.auto_scaling true

# Environment-specific configurations
echo "🔧 Setting environment-specific configs..."

# Dev environment
pulumi env set orchestra-ai/dev --yes values.environment "development"
pulumi env set orchestra-ai/dev --yes values.domain "dev.orchestra.ai"
pulumi env set orchestra-ai/dev --yes values.instance_size "small"
pulumi env set orchestra-ai/dev --yes values.replicas 1

# Staging environment  
pulumi env set orchestra-ai/staging --yes values.environment "staging"
pulumi env set orchestra-ai/staging --yes values.domain "staging.orchestra.ai"
pulumi env set orchestra-ai/staging --yes values.instance_size "medium"
pulumi env set orchestra-ai/staging --yes values.replicas 2

# Production environment
pulumi env set orchestra-ai/prod --yes values.environment "production"
pulumi env set orchestra-ai/prod --yes values.domain "orchestra.ai"
pulumi env set orchestra-ai/prod --yes values.instance_size "large"
pulumi env set orchestra-ai/prod --yes values.replicas 3

echo "📋 Current environments:"
pulumi env ls

echo "✅ Pulumi ESC setup complete!"
echo ""
echo "Next steps:"
echo "1. Add secrets: pulumi env set orchestra-ai/base --secret values.secrets.github_token 'your_token'"
echo "2. Configure stacks to use environments"
echo "3. Deploy infrastructure: pulumi up --config pulumi:environment=orchestra-ai/dev" 