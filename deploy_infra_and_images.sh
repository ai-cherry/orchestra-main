#!/bin/bash
# Comprehensive deployment script for Orchestra AI infra and images.
# Run this from your project root: bash deploy_infra_and_images.sh

set -e

# 1. Authenticate Docker with Artifact Registry
echo "==> Authenticating Docker with Artifact Registry..."
gcloud auth configure-docker us-central1-docker.pkg.dev

# 2. Build and push Docker images
echo "==> Building and pushing Docker images..."

# Build and push admin-interface
docker build -t us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images/admin-interface:latest ./admin-ui
docker push us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images/admin-interface:latest

# Build and push orchestra-main
docker build -t us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images/orchestra-main:latest ./orchestra_api
docker push us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images/orchestra-main:latest

# Build and push web-scraping-agents
docker build -t us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images/web-scraping-agents:latest ./webscraping_app
docker push us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images/web-scraping-agents:latest

# 3. List all VPC networks
echo "==> Listing all VPC networks..."
gcloud compute networks list

echo "==> If you need to delete unused VPC networks, run:"
echo "    gcloud compute networks delete <NETWORK_NAME>"

# 4. Deploy Pulumi stack
echo "==> Deploying Pulumi stack..."
export PATH=$PATH:$HOME/.pulumi/bin
cd infra
source venv/bin/activate
cd pulumi_gcp
pulumi up --yes

echo "==> Deployment complete. Check Pulumi output for service URLs."
