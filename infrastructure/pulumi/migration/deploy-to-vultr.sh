#!/bin/bash

# Pulumi Migration Framework - Vultr Deployment Script
# Deploys the containerized application to Vultr infrastructure

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
DOCKER_IMAGE="${DOCKER_IMAGE:-pulumi-migration}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
VULTR_INSTANCE_ID="${VULTR_INSTANCE_ID}"
VULTR_API_KEY="${VULTR_API_KEY}"
SSH_KEY_PATH="${SSH_KEY_PATH:-~/.ssh/id_rsa}"
DEPLOY_USER="${DEPLOY_USER:-root}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
    fi
    
    # Check if required environment variables are set
    if [[ -z "${VULTR_API_KEY}" ]]; then
        log_error "VULTR_API_KEY environment variable is not set."
    fi
    
    if [[ -z "${VULTR_INSTANCE_ID}" ]]; then
        log_error "VULTR_INSTANCE_ID environment variable is not set."
    fi
    
    # Check if SSH key exists
    if [[ ! -f "${SSH_KEY_PATH}" ]]; then
        log_error "SSH key not found at ${SSH_KEY_PATH}"
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image..."
    
    # Build the image
    docker build -t "${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}" .
    
    log_success "Docker image built successfully"
}

# Push Docker image to registry
push_docker_image() {
    log_info "Pushing Docker image to registry..."
    
    # Login to Docker registry if credentials are provided
    if [[ -n "${DOCKER_USERNAME:-}" ]] && [[ -n "${DOCKER_PASSWORD:-}" ]]; then
        echo "${DOCKER_PASSWORD}" | docker login "${DOCKER_REGISTRY}" -u "${DOCKER_USERNAME}" --password-stdin
    fi
    
    # Push the image
    docker push "${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}"
    
    log_success "Docker image pushed successfully"
}

# Get Vultr instance IP
get_instance_ip() {
    log_info "Getting Vultr instance IP..."
    
    # Use Vultr API to get instance details
    INSTANCE_IP=$(curl -s -H "Authorization: Bearer ${VULTR_API_KEY}" \
        "https://api.vultr.com/v2/instances/${VULTR_INSTANCE_ID}" | \
        jq -r '.instance.main_ip')
    
    if [[ -z "${INSTANCE_IP}" ]] || [[ "${INSTANCE_IP}" == "null" ]]; then
        log_error "Failed to get instance IP"
    fi
    
    log_success "Instance IP: ${INSTANCE_IP}"
}

# Deploy to Vultr instance
deploy_to_instance() {
    log_info "Deploying to Vultr instance..."
    
    # Create deployment script
    cat > /tmp/deploy-remote.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Pull the latest image
docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}

# Stop existing container if running
docker stop pulumi-migration || true
docker rm pulumi-migration || true

# Create necessary directories
mkdir -p /opt/pulumi-migration/{config,state,reports}

# Run the new container
docker run -d \
    --name pulumi-migration \
    --restart unless-stopped \
    -v /opt/pulumi-migration/config:/app/config:ro \
    -v /opt/pulumi-migration/state:/app/.pulumi-migration \
    -v /opt/pulumi-migration/reports:/app/reports \
    -e PULUMI_ACCESS_TOKEN="${PULUMI_ACCESS_TOKEN}" \
    -e Vultr_PROJECT_ID="${Vultr_PROJECT_ID}" \
    -e Vultr_REGION="${Vultr_REGION:-us-central1}" \
    -e NODE_ENV=production \
    --memory="4g" \
    --cpus="2" \
    ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}

# Check if container is running
sleep 5
if docker ps | grep -q pulumi-migration; then
    echo "Container is running successfully"
else
    echo "Container failed to start"
    docker logs pulumi-migration
    exit 1
fi
EOF

    # Copy and execute deployment script
    scp -i "${SSH_KEY_PATH}" -o StrictHostKeyChecking=no /tmp/deploy-remote.sh "${DEPLOY_USER}@${INSTANCE_IP}:/tmp/"
    
    # Make script executable and run it
    ssh -i "${SSH_KEY_PATH}" -o StrictHostKeyChecking=no "${DEPLOY_USER}@${INSTANCE_IP}" \
        "chmod +x /tmp/deploy-remote.sh && \
         DOCKER_REGISTRY='${DOCKER_REGISTRY}' \
         DOCKER_IMAGE='${DOCKER_IMAGE}' \
         DOCKER_TAG='${DOCKER_TAG}' \
         PULUMI_ACCESS_TOKEN='${PULUMI_ACCESS_TOKEN:-}' \
         Vultr_PROJECT_ID='${Vultr_PROJECT_ID:-}' \
         Vultr_REGION='${Vultr_REGION:-}' \
         /tmp/deploy-remote.sh"
    
    # Clean up
    rm -f /tmp/deploy-remote.sh
    
    log_success "Deployment completed successfully"
}

# Setup monitoring (optional)
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    ssh -i "${SSH_KEY_PATH}" -o StrictHostKeyChecking=no "${DEPLOY_USER}@${INSTANCE_IP}" << 'EOF'
# Install monitoring stack if not already installed
if ! docker ps | grep -q prometheus; then
    # Create monitoring network
    docker network create monitoring || true
    
    # Run Prometheus
    docker run -d \
        --name prometheus \
        --network monitoring \
        --restart unless-stopped \
        -p 9090:9090 \
        -v /opt/prometheus:/etc/prometheus \
        prom/prometheus
    
    # Run Grafana
    docker run -d \
        --name grafana \
        --network monitoring \
        --restart unless-stopped \
        -p 3000:3000 \
        grafana/grafana
fi

# Connect pulumi-migration to monitoring network
docker network connect monitoring pulumi-migration || true
EOF
    
    log_success "Monitoring setup completed"
}

# Main deployment flow
main() {
    log_info "Starting Pulumi Migration Framework deployment to Vultr..."
    
    # Check prerequisites
    check_prerequisites
    
    # Build and push Docker image
    build_docker_image
    push_docker_image
    
    # Get instance IP
    get_instance_ip
    
    # Deploy to instance
    deploy_to_instance
    
    # Setup monitoring (optional)
    if [[ "${SETUP_MONITORING:-false}" == "true" ]]; then
        setup_monitoring
    fi
    
    log_success "Deployment completed successfully!"
    log_info "Application is running at: http://${INSTANCE_IP}"
    
    if [[ "${SETUP_MONITORING:-false}" == "true" ]]; then
        log_info "Prometheus is available at: http://${INSTANCE_IP}:9090"
        log_info "Grafana is available at: http://${INSTANCE_IP}:3000"
    fi
}

# Run main function
main "$@"