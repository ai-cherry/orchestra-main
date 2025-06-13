#!/bin/bash

# 🎼 Orchestra AI Production Deployment Script
# Comprehensive deployment with safety checks and rollback capabilities

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PRODUCTION_BRANCH="main"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
HEALTH_CHECK_TIMEOUT=60
ROLLBACK_ENABLED=true

# Log functions
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] INFO: $1${NC}"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "🔍 Running pre-deployment checks..."
    
    # Check if we're on the correct branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$PRODUCTION_BRANCH" ]; then
        error "Not on production branch. Current: $current_branch, Expected: $PRODUCTION_BRANCH"
        exit 1
    fi
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        error "Uncommitted changes detected. Please commit or stash before deployment."
        git status --short
        exit 1
    fi
    
    # Run environment validation
    if [ -f "validate_environment.py" ]; then
        log "Running environment validation..."
        if ! python3 validate_environment.py; then
            error "Environment validation failed. Please fix issues before deployment."
            exit 1
        fi
    fi
    
    # Run tests if available
    if [ -f "api/test_setup.py" ]; then
        log "Running API tests..."
        cd api && python3 test_setup.py && cd ..
    fi
    
    # Check frontend build
    if [ -d "web" ]; then
        log "Building frontend..."
        cd web && npm run build && cd ..
    fi
    
    log "✅ Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log "📦 Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current codebase
    git archive HEAD | tar -x -C "$BACKUP_DIR"
    
    # Backup database if exists
    if [ -f "api/orchestra.db" ]; then
        cp "api/orchestra.db" "$BACKUP_DIR/"
    fi
    
    # Backup configuration files
    if [ -f ".env" ]; then
        cp ".env" "$BACKUP_DIR/"
    fi
    
    log "✅ Backup created at $BACKUP_DIR"
}

# Deploy services
deploy_services() {
    log "🚀 Deploying services..."
    
    # Stop existing services
    if [ -f "stop_all_services.sh" ]; then
        ./stop_all_services.sh
    fi
    
    # Update dependencies
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        pip install -r api/requirements.txt
    fi
    
    # Install frontend dependencies
    if [ -d "web" ]; then
        cd web && npm install && cd ..
    fi
    
    # Start services
    if [ -f "start_orchestra.sh" ]; then
        ./start_orchestra.sh
    fi
    
    log "✅ Services deployed"
}

# Health checks
run_health_checks() {
    log "🏥 Running health checks..."
    
    local start_time=$(date +%s)
    local timeout=$((start_time + HEALTH_CHECK_TIMEOUT))
    
    # Check API health
    while [ $(date +%s) -lt $timeout ]; do
        if curl -f -s http://localhost:8000/api/health > /dev/null; then
            log "✅ API health check passed"
            break
        fi
        info "Waiting for API to respond..."
        sleep 5
    done
    
    if [ $(date +%s) -ge $timeout ]; then
        error "API health check failed after ${HEALTH_CHECK_TIMEOUT}s"
        return 1
    fi
    
    # Check frontend
    if curl -f -s http://localhost:3000 > /dev/null; then
        log "✅ Frontend health check passed"
    else
        warn "Frontend health check failed"
    fi
    
    log "✅ Health checks completed"
}

# Rollback function
rollback() {
    error "🔄 Initiating rollback..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        error "Backup directory not found. Cannot rollback."
        exit 1
    fi
    
    # Stop current services
    if [ -f "stop_all_services.sh" ]; then
        ./stop_all_services.sh
    fi
    
    # Restore from backup
    rsync -av --delete "$BACKUP_DIR/" ./
    
    # Restore database
    if [ -f "$BACKUP_DIR/orchestra.db" ]; then
        cp "$BACKUP_DIR/orchestra.db" "api/"
    fi
    
    # Restart services
    if [ -f "start_orchestra.sh" ]; then
        ./start_orchestra.sh
    fi
    
    error "🔄 Rollback completed"
}

# Post-deployment tasks
post_deployment() {
    log "🎯 Running post-deployment tasks..."
    
    # Update documentation timestamp
    echo "Last deployment: $(date)" > LAST_DEPLOYMENT.txt
    
    # Clean old backups (keep last 5)
    if [ -d "backups" ]; then
        cd backups && ls -t | tail -n +6 | xargs rm -rf && cd ..
    fi
    
    # Send deployment notification (if configured)
    if [ -n "$DEPLOYMENT_WEBHOOK" ]; then
        curl -X POST "$DEPLOYMENT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🎼 Orchestra AI deployed successfully at $(date)\"}"
    fi
    
    log "✅ Post-deployment tasks completed"
}

# Main deployment process
main() {
    log "🎼 Orchestra AI Production Deployment"
    log "======================================="
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                BACKUP_ENABLED=false
                shift
                ;;
            --no-rollback)
                ROLLBACK_ENABLED=false
                shift
                ;;
            --verify)
                # Just run checks without deploying
                pre_deployment_checks
                log "✅ Verification completed successfully"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--no-backup] [--no-rollback] [--verify]"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    trap 'if [ "$ROLLBACK_ENABLED" = true ]; then rollback; fi' ERR
    
    pre_deployment_checks
    create_backup
    deploy_services
    
    if ! run_health_checks; then
        if [ "$ROLLBACK_ENABLED" = true ]; then
            rollback
            exit 1
        fi
    fi
    
    post_deployment
    
    log "🎉 Deployment completed successfully!"
    log "🔗 Services available at:"
    log "   Frontend: http://localhost:3000"
    log "   API: http://localhost:8000"
    log "   Health: http://localhost:8000/api/health"
}

# Execute main function
main "$@" 