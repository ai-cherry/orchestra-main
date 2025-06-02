#!/bin/bash
# Deploy to Vultr using Pulumi

set -e

echo "🚀 Deploying Orchestra AI to Vultr..."

# Check for required tools
command -v pulumi >/dev/null 2>&1 || { echo "❌ Pulumi CLI not found. Please install it first."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install it first."; exit 1; }

# Set environment
export ENVIRONMENT=${ENVIRONMENT:-production}
export VULTR_API_KEY=${VULTR_API_KEY:?Please set VULTR_API_KEY}

# Build Docker images
echo "📦 Building Docker images..."
docker build -t orchestra-api:latest -f Dockerfile .
docker build -t orchestra-admin-ui:latest -f admin-ui/Dockerfile ./admin-ui

# Push to Vultr Container Registry
echo "📤 Pushing to Vultr Container Registry..."
docker tag orchestra-api:latest registry.vultr.com/orchestra/api:latest
docker tag orchestra-admin-ui:latest registry.vultr.com/orchestra/admin-ui:latest
docker push registry.vultr.com/orchestra/api:latest
docker push registry.vultr.com/orchestra/admin-ui:latest

# Deploy with Pulumi
echo "🏗️ Deploying infrastructure with Pulumi..."
cd infra
pulumi stack select $ENVIRONMENT || pulumi stack init $ENVIRONMENT
pulumi up --yes

echo "✅ Deployment complete!"
