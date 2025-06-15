# Docker Build and Security Optimization Script
# Based on optimal IaC workflow architecture recommendations

#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY_URL="${REGISTRY_URL:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
SCAN_ENABLED="${SCAN_ENABLED:-true}"
CACHE_ENABLED="${CACHE_ENABLED:-true}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install security scanning tools
install_security_tools() {
    print_status "Installing security scanning tools..."
    
    # Install Trivy for vulnerability scanning
    if ! command_exists trivy; then
        print_status "Installing Trivy..."
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    fi
    
    # Install Hadolint for Dockerfile linting
    if ! command_exists hadolint; then
        print_status "Installing Hadolint..."
        wget -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
        chmod +x /usr/local/bin/hadolint
    fi
    
    print_success "Security tools installed successfully"
}

# Function to lint Dockerfiles
lint_dockerfiles() {
    print_status "Linting Dockerfiles..."
    
    local dockerfile_errors=0
    
    for dockerfile in $(find . -name "Dockerfile*" -type f); do
        print_status "Linting $dockerfile..."
        if hadolint "$dockerfile"; then
            print_success "✓ $dockerfile passed linting"
        else
            print_error "✗ $dockerfile failed linting"
            dockerfile_errors=$((dockerfile_errors + 1))
        fi
    done
    
    if [ $dockerfile_errors -eq 0 ]; then
        print_success "All Dockerfiles passed linting"
    else
        print_error "$dockerfile_errors Dockerfile(s) failed linting"
        return 1
    fi
}

# Function to build optimized images
build_optimized_images() {
    print_status "Building optimized Docker images..."
    
    # Enable BuildKit for advanced features
    export DOCKER_BUILDKIT=1
    export BUILDKIT_PROGRESS=plain
    
    # Build backend image
    print_status "Building optimized backend image..."
    docker build \
        --file Dockerfile.backend.optimized \
        --tag orchestra-backend:${IMAGE_TAG} \
        --tag orchestra-backend:latest \
        ${CACHE_ENABLED:+--cache-from orchestra-backend:latest} \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        .
    
    # Build frontend image
    print_status "Building optimized frontend image..."
    docker build \
        --file modern-admin/Dockerfile.frontend.optimized \
        --tag orchestra-frontend:${IMAGE_TAG} \
        --tag orchestra-frontend:latest \
        ${CACHE_ENABLED:+--cache-from orchestra-frontend:latest} \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        modern-admin/
    
    print_success "Docker images built successfully"
}

# Function to scan images for vulnerabilities
scan_images() {
    if [ "$SCAN_ENABLED" != "true" ]; then
        print_warning "Security scanning disabled"
        return 0
    fi
    
    print_status "Scanning images for vulnerabilities..."
    
    local scan_errors=0
    
    # Scan backend image
    print_status "Scanning backend image..."
    if trivy image --exit-code 1 --severity HIGH,CRITICAL orchestra-backend:${IMAGE_TAG}; then
        print_success "✓ Backend image passed security scan"
    else
        print_error "✗ Backend image failed security scan"
        scan_errors=$((scan_errors + 1))
    fi
    
    # Scan frontend image
    print_status "Scanning frontend image..."
    if trivy image --exit-code 1 --severity HIGH,CRITICAL orchestra-frontend:${IMAGE_TAG}; then
        print_success "✓ Frontend image passed security scan"
    else
        print_error "✗ Frontend image failed security scan"
        scan_errors=$((scan_errors + 1))
    fi
    
    if [ $scan_errors -eq 0 ]; then
        print_success "All images passed security scanning"
    else
        print_error "$scan_errors image(s) failed security scanning"
        return 1
    fi
}

# Function to optimize images
optimize_images() {
    print_status "Optimizing Docker images..."
    
    # Get image sizes
    backend_size=$(docker images orchestra-backend:${IMAGE_TAG} --format "table {{.Size}}" | tail -n 1)
    frontend_size=$(docker images orchestra-frontend:${IMAGE_TAG} --format "table {{.Size}}" | tail -n 1)
    
    print_success "Image sizes:"
    print_success "  Backend: $backend_size"
    print_success "  Frontend: $frontend_size"
    
    # Remove dangling images
    print_status "Cleaning up dangling images..."
    docker image prune -f
    
    print_success "Image optimization completed"
}

# Function to push images to registry
push_images() {
    if [ -z "$REGISTRY_URL" ]; then
        print_warning "No registry URL provided, skipping push"
        return 0
    fi
    
    print_status "Pushing images to registry..."
    
    # Tag and push backend image
    docker tag orchestra-backend:${IMAGE_TAG} ${REGISTRY_URL}/orchestra-backend:${IMAGE_TAG}
    docker push ${REGISTRY_URL}/orchestra-backend:${IMAGE_TAG}
    
    # Tag and push frontend image
    docker tag orchestra-frontend:${IMAGE_TAG} ${REGISTRY_URL}/orchestra-frontend:${IMAGE_TAG}
    docker push ${REGISTRY_URL}/orchestra-frontend:${IMAGE_TAG}
    
    print_success "Images pushed to registry successfully"
}

# Function to run tests
run_tests() {
    print_status "Running container tests..."
    
    # Test backend container
    print_status "Testing backend container..."
    docker run --rm --detach --name test-backend orchestra-backend:${IMAGE_TAG}
    sleep 10
    
    if docker exec test-backend curl -f http://localhost:8000/health; then
        print_success "✓ Backend container health check passed"
    else
        print_error "✗ Backend container health check failed"
        docker logs test-backend
        docker stop test-backend
        return 1
    fi
    
    docker stop test-backend
    
    # Test frontend container
    print_status "Testing frontend container..."
    docker run --rm --detach --name test-frontend orchestra-frontend:${IMAGE_TAG}
    sleep 5
    
    if docker exec test-frontend curl -f http://localhost:8080/health; then
        print_success "✓ Frontend container health check passed"
    else
        print_error "✗ Frontend container health check failed"
        docker logs test-frontend
        docker stop test-frontend
        return 1
    fi
    
    docker stop test-frontend
    
    print_success "All container tests passed"
}

# Main execution
main() {
    print_status "Starting Docker optimization and security pipeline..."
    
    # Check prerequisites
    if ! command_exists docker; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Install security tools
    install_security_tools
    
    # Lint Dockerfiles
    lint_dockerfiles
    
    # Build optimized images
    build_optimized_images
    
    # Scan for vulnerabilities
    scan_images
    
    # Optimize images
    optimize_images
    
    # Run tests
    run_tests
    
    # Push to registry if configured
    push_images
    
    print_success "Docker optimization and security pipeline completed successfully!"
}

# Execute main function
main "$@"

