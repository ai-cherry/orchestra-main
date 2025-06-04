#!/bin/bash
# Simple AI cherry_ai Deployment
# ==============================
# One-command deployment for AI cherry_ai with SuperAGI

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "scripts/deploy_cherry_ai.sh" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# Set environment
ENVIRONMENT="${1:-dev}"

log_info "Deploying AI cherry_ai (Environment: $ENVIRONMENT)"
log_info "This will deploy:"
log_info "  - SuperAGI with managed databases"
log_info "  - MongoDB Atlas, DragonflyDB Cloud, Weaviate Cloud"
log_info "  - Monitoring stack (optional)"

# Make sure the main script is executable
chmod +x scripts/deploy_cherry_ai.sh

# Run the main deployment
ENVIRONMENT=$ENVIRONMENT ./scripts/deploy_cherry_ai.sh

log_info "Deployment complete! 🎉"
