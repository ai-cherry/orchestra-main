#!/bin/bash
# Deploy to Vultr using Pulumi

set -e

echo "🚀 Deploying Cherry AI to Vultr..."

# Check for required tools
command -v pulumi >/dev/null 2>&1 || { echo "❌ Pulumi CLI not found. Please install it first."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install it first."; exit 1; }

# Set environment
export ENVIRONMENT=${ENVIRONMENT:-production}
export VULTR_API_KEY=${VULTR_API_KEY:?Please set VULTR_API_KEY}

# Build Docker images
echo "📦 Building Docker images..."
docker build -t cherry_ai-api:latest -f Dockerfile .
docker build -t cherry_ai-admin-ui:latest -f admin-ui/Dockerfile ./admin-ui

# Push to Vultr Container Registry
echo "📤 Pushing to Vultr Container Registry..."
docker tag cherry_ai-api:latest registry.vultr.com/cherry_ai/api:latest
docker tag cherry_ai-admin-ui:latest registry.vultr.com/cherry_ai/admin-ui:latest
docker push registry.vultr.com/cherry_ai/api:latest
docker push registry.vultr.com/cherry_ai/admin-ui:latest

# Deploy with Pulumi
echo "🏗️ Deploying infrastructure with Pulumi..."
cd infra
pulumi stack select $ENVIRONMENT || pulumi stack init $ENVIRONMENT
pulumi up --yes

echo "✅ Deployment complete!"
