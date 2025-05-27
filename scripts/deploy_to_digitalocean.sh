#!/bin/bash
# DigitalOcean Deployment Script
# ==============================
# Deploys the AI Orchestra stack to DigitalOcean using Pulumi

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."
if ! command -v pulumi &> /dev/null; then
    log_error "Pulumi is not installed. Please install it first."
    exit 1
fi

# Set environment
ENVIRONMENT=${1:-dev}
log_info "Deploying to environment: $ENVIRONMENT"

# Navigate to infrastructure directory
cd "$(dirname "$0")/../infra"

# Select Pulumi stack
log_info "Selecting Pulumi stack: $ENVIRONMENT"
pulumi stack select $ENVIRONMENT || {
    log_error "Failed to select stack $ENVIRONMENT"
    exit 1
}

# Check for required environment variables
if [ -z "${DIGITALOCEAN_TOKEN:-}" ]; then
    log_error "DIGITALOCEAN_TOKEN environment variable is not set"
    exit 1
fi

# Deploy with Pulumi
log_info "Starting Pulumi deployment to DigitalOcean..."
pulumi up --yes

# Get outputs
log_info "Getting deployment outputs..."
DROPLET_IP=$(pulumi stack output droplet_ip 2>/dev/null || echo "pending")
SUPERAGI_URL=$(pulumi stack output superagi_url 2>/dev/null || echo "pending")
ADMIN_UI_URL=$(pulumi stack output admin_ui_live_url 2>/dev/null || echo "pending")

# Display summary
log_info "Deployment complete!"
echo ""
echo "==================================="
echo "DigitalOcean Deployment Summary"
echo "==================================="
echo "Environment: ${ENVIRONMENT}"
echo ""
echo "Endpoints:"
echo "- Droplet IP: ${DROPLET_IP}"
echo "- SuperAGI: ${SUPERAGI_URL}"
echo "- Admin UI: ${ADMIN_UI_URL}"
echo ""
echo "Next steps:"
echo "1. Access your Admin UI at: ${ADMIN_UI_URL}"
echo "2. SSH to droplet: ssh root@${DROPLET_IP}"
echo "==================================="
