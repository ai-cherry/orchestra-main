#!/bin/bash
# Quick SuperAGI Deployment Verification
# ======================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

# Configuration
NAMESPACE="superagi"
PROJECT_ID="${LAMBDA_PROJECT_ID:-}"

echo -e "${BOLD}${BLUE}SuperAGI Quick Verification${NC}"
echo -e "${BLUE}=========================${NC}\n"

# Function to print results
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "  $1"
}

# 1. Check Pulumi Configuration
echo -e "\n${BOLD}1. Pulumi Configuration${NC}"
echo -e "----------------------"

if command -v pulumi &> /dev/null; then
    print_success "Pulumi installed: $(pulumi version)"

    # Check stack
    if pulumi stack ls 2>/dev/null | grep -q "superagi"; then
        print_success "SuperAGI stack found"

        # Try to get outputs
        if pulumi stack select superagi 2>/dev/null; then
            echo -e "\n  Stack outputs:"
            pulumi stack output 2>/dev/null | head -10 || print_warning "Could not retrieve stack outputs"
        fi
    else
        print_warning "SuperAGI stack not found"
    fi
else
    print_error "Pulumi not installed"
fi

# 2. Check Kubernetes Resources
echo -e "\n${BOLD}2. Kubernetes Resources${NC}"
echo -e "----------------------"

if command -v kubectl &> /dev/null; then
    print_success "kubectl installed"

    # Check cluster connection
    if kubectl cluster-info &> /dev/null; then
        print_success "Connected to Kubernetes cluster"

        # Check namespace
        if kubectl get namespace $NAMESPACE &> /dev/null; then
            print_success "Namespace '$NAMESPACE' exists"

            # Check deployments
            echo -e "\n  Deployments:"
            kubectl get deployments -n $NAMESPACE 2>/dev/null || print_error "Failed to list deployments"

            # Check pods
            echo -e "\n  Pods:"
            kubectl get pods -n $NAMESPACE 2>/dev/null || print_error "Failed to list pods"

            # Check services
            echo -e "\n  Services:"
            kubectl get services -n $NAMESPACE 2>/dev/null || print_error "Failed to list services"

            # Get SuperAGI service IP
            SERVICE_IP=$(kubectl get service superagi -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
            if [ -n "$SERVICE_IP" ]; then
                print_success "SuperAGI service IP: $SERVICE_IP"
            else
                print_warning "SuperAGI service IP not yet assigned"
            fi
        else
            print_error "Namespace '$NAMESPACE' not found"
        fi
    else
        print_error "Not connected to Kubernetes cluster"
    fi
else
    print_error "kubectl not installed"
fi

# 3. Check Storage (DragonflyDB + Firestore)
echo -e "\n${BOLD}3. Storage Verification${NC}"
echo -e "----------------------"

# Check DragonflyDB
if kubectl get deployment dragonfly -n $NAMESPACE &> /dev/null; then
    DRAGONFLY_READY=$(kubectl get deployment dragonfly -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    DRAGONFLY_DESIRED=$(kubectl get deployment dragonfly -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")

    if [ "$DRAGONFLY_READY" = "$DRAGONFLY_DESIRED" ]; then
        print_success "DragonflyDB: $DRAGONFLY_READY/$DRAGONFLY_DESIRED replicas ready"
    else
        print_warning "DragonflyDB: $DRAGONFLY_READY/$DRAGONFLY_DESIRED replicas ready"
    fi
else
    print_error "DragonflyDB deployment not found"
fi

# Check Firestore (via project)
if [ -n "$PROJECT_ID" ]; then
    print_info "Firestore project: $PROJECT_ID"

    # Check if Firestore API is enabled
    if gcloud services list --enabled --project="$PROJECT_ID" 2>/dev/null | grep -q "firestore.googleapis.com"; then
        print_success "Firestore API enabled"
    else
        print_warning "Firestore API status unknown"
    fi
else
    print_warning "LAMBDA_PROJECT_ID not set - cannot verify Firestore"
fi

# 4. Check SuperAGI Deployment
echo -e "\n${BOLD}4. SuperAGI Deployment${NC}"
echo -e "---------------------"

if kubectl get deployment superagi -n $NAMESPACE &> /dev/null; then
    SUPERAGI_READY=$(kubectl get deployment superagi -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    SUPERAGI_DESIRED=$(kubectl get deployment superagi -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "2")

    if [ "$SUPERAGI_READY" = "$SUPERAGI_DESIRED" ]; then
        print_success "SuperAGI: $SUPERAGI_READY/$SUPERAGI_DESIRED replicas ready"

        # Try to test the API
        if [ -n "$SERVICE_IP" ]; then
            echo -e "\n  Testing SuperAGI API..."
            if curl -s -f "http://${SERVICE_IP}:8080/health" > /dev/null 2>&1; then
                print_success "Health endpoint responding"

                # Get health details
                HEALTH=$(curl -s "http://${SERVICE_IP}:8080/health" 2>/dev/null | jq -r '.status' 2>/dev/null || echo "unknown")
                print_info "Health status: $HEALTH"
            else
                print_warning "Health endpoint not responding"
            fi
        else
            print_info "Using port-forward to test API..."

            # Setup port-forward
            kubectl port-forward -n $NAMESPACE service/superagi 8080:8080 > /dev/null 2>&1 &
            PF_PID=$!
            sleep 3

            if curl -s -f "http://localhost:8080/health" > /dev/null 2>&1; then
                print_success "Health endpoint responding (via port-forward)"

                # List agents
                AGENTS=$(curl -s "http://localhost:8080/agents" 2>/dev/null | jq -r '.agents | length' 2>/dev/null || echo "0")
                print_info "Available agents: $AGENTS"
            else
                print_error "Health endpoint not responding"
            fi

            # Clean up port-forward
            kill $PF_PID 2>/dev/null || true
        fi
    else
        print_warning "SuperAGI: $SUPERAGI_READY/$SUPERAGI_DESIRED replicas ready"
    fi
else
    print_error "SuperAGI deployment not found"
fi

# 5. Check Secrets
echo -e "\n${BOLD}5. Secrets Management${NC}"
echo -e "--------------------"

# Check environment variables
if [ -n "$PROJECT_ID" ]; then
    print_success "LAMBDA_PROJECT_ID is set"
else
    print_warning "LAMBDA_PROJECT_ID not set"
fi

if [ -n "${OPENROUTER_API_KEY:-}" ]; then
    print_success "OPENROUTER_API_KEY is set"
else
    print_warning "OPENROUTER_API_KEY not set"
fi

# Check Kubernetes secret
if kubectl get secret superagi-secrets -n $NAMESPACE &> /dev/null; then
    print_success "Kubernetes secret 'superagi-secrets' exists"
else
    print_warning "Kubernetes secret 'superagi-secrets' not found"
fi

# Check for legacy Google Secrets Manager
echo -e "\n  Checking for legacy secrets references..."
if grep -r "google.cloud.secretmanager" . --exclude-dir=.git --exclude-dir=venv --exclude-dir=.mypy_cache 2>/dev/null | grep -v "verify_superagi"; then
    print_warning "Found Google Secrets Manager references - consider removing"
else
    print_success "No Google Secrets Manager references found"
fi

# 6. Summary
echo -e "\n${BOLD}Summary${NC}"
echo -e "-------"

# Count successes and failures
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Simple counting based on colored output
if [ -f /tmp/verify_output.txt ]; then
    PASSED_CHECKS=$(grep -c "✓" /tmp/verify_output.txt || echo 0)
    TOTAL_CHECKS=$(($(grep -c "✓" /tmp/verify_output.txt || echo 0) + $(grep -c "✗" /tmp/verify_output.txt || echo 0) + $(grep -c "⚠" /tmp/verify_output.txt || echo 0)))
fi

echo -e "\n${BOLD}Quick Actions:${NC}"
echo "1. View pod logs: kubectl logs -f deployment/superagi -n $NAMESPACE"
echo "2. Scale deployment: kubectl scale deployment/superagi --replicas=3 -n $NAMESPACE"
echo "3. Port-forward for testing: kubectl port-forward -n $NAMESPACE service/superagi 8080:8080"
echo "4. Run full verification: python scripts/verify_superagi_deployment.py"

echo -e "\n${BLUE}For detailed verification, run: python scripts/verify_superagi_deployment.py${NC}"
