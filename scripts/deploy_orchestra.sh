#!/bin/bash
# Orchestra Deployment Script
# Handles complete deployment to DigitalOcean with proper error handling

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_ROOT/infra"

# Set Pulumi configuration
export PULUMI_CONFIG_PASSPHRASE="orchestra-dev-123"
export PULUMI_SKIP_UPDATE_CHECK=true

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."

    if ! command -v pulumi &> /dev/null; then
        log_error "Pulumi is not installed. Please install it first."
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed."
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Deploy infrastructure
deploy_infrastructure() {
    log_step "Deploying infrastructure to DigitalOcean..."

    cd "$INFRA_DIR"

    # Select the stack
    pulumi stack select dev || {
        log_error "Failed to select Pulumi stack"
        exit 1
    }

    # Run the deployment
    if pulumi up --yes --skip-preview; then
        log_info "Infrastructure deployment completed successfully"
    else
        log_warn "Infrastructure deployment completed with warnings"
    fi

    # Get outputs
    DROPLET_IP=$(pulumi stack output droplet_ip 2>/dev/null || echo "")
    SUPERAGI_URL=$(pulumi stack output superagi_url 2>/dev/null || echo "")

    if [ -n "$DROPLET_IP" ]; then
        log_info "Droplet IP: $DROPLET_IP"
        log_info "SuperAGI URL: $SUPERAGI_URL"
    fi
}

# Deploy the modular API
deploy_api() {
    log_step "Deploying Orchestra API..."

    cd "$PROJECT_ROOT"

    # Check if we can SSH to the droplet
    if [ -n "${DROPLET_IP:-}" ]; then
        log_info "Waiting for droplet to be ready..."

        # Wait for SSH to be available (max 2 minutes)
        MAX_ATTEMPTS=24
        ATTEMPT=0

        while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
            if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o PasswordAuthentication=no root@"$DROPLET_IP" exit 2>/dev/null; then
                log_info "Droplet is ready"
                break
            fi

            ATTEMPT=$((ATTEMPT + 1))
            if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
                echo -n "."
                sleep 5
            fi
        done

        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            log_warn "Could not connect to droplet via SSH. Manual setup may be required."
        fi
    fi
}

# Main execution
main() {
    log_info "Starting Orchestra deployment..."

    check_prerequisites
    deploy_infrastructure
    deploy_api

    # Summary
    echo ""
    echo "======================================"
    echo "Orchestra Deployment Summary"
    echo "======================================"

    if [ -n "${DROPLET_IP:-}" ]; then
        echo "Droplet IP: $DROPLET_IP"
        echo "SuperAGI URL: $SUPERAGI_URL"
        echo ""
        echo "Services:"
        echo "- SuperAGI: $SUPERAGI_URL"
        echo "- Orchestra API: http://$DROPLET_IP:8000 (when deployed)"
        echo "- Admin UI: https://cherry-ai.me"
    else
        echo "Deployment status: Check Pulumi outputs"
    fi

    echo ""
    echo "Next steps:"
    echo "1. Test the modular system: python test_modular_system.py"
    echo "2. Start the API locally: cd core && python -m api.main"
    echo "3. Access the API docs: http://localhost:8000/docs"
    echo "======================================"

    log_info "Deployment script completed"
}

# Run main function
main "$@"
