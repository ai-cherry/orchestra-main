#!/bin/bash
# Verify SuperAGI Deployment with Domain Configuration

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "SuperAGI Domain Deployment Verification"
echo "========================================"
echo

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: kubectl not configured${NC}"
    echo "Run: gcloud container clusters get-credentials <cluster-name> --zone=us-central1-a"
    exit 1
fi

# Check namespace
echo "1. Checking namespace..."
if kubectl get namespace superagi &> /dev/null; then
    echo -e "${GREEN}✓ Namespace 'superagi' exists${NC}"
else
    echo -e "${RED}✗ Namespace 'superagi' not found${NC}"
    exit 1
fi

# Check deployments
echo -e "\n2. Checking deployments..."
kubectl get deployments -n superagi

# Check pods
echo -e "\n3. Checking pod status..."
kubectl get pods -n superagi

# Check services
echo -e "\n4. Checking services..."
kubectl get services -n superagi

# Check ingress
echo -e "\n5. Checking ingress..."
if kubectl get ingress -n superagi &> /dev/null; then
    kubectl get ingress -n superagi
    
    # Get ingress IP
    INGRESS_IP=$(kubectl get ingress superagi-ingress -n superagi -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$INGRESS_IP" ]; then
        echo -e "\n${GREEN}Ingress IP: $INGRESS_IP${NC}"
        echo -e "${YELLOW}Configure DNS A record: cherry-ai.me -> $INGRESS_IP${NC}"
    else
        echo -e "\n${YELLOW}Ingress IP not yet assigned. Waiting for LoadBalancer...${NC}"
    fi
else
    echo -e "${YELLOW}No ingress found. Domain configuration not deployed.${NC}"
fi

# Check certificate
echo -e "\n6. Checking SSL certificate..."
if kubectl get certificate -n superagi &> /dev/null; then
    kubectl get certificate -n superagi
    kubectl describe certificate superagi-tls -n superagi | grep -A 5 "Status:"
else
    echo -e "${YELLOW}No certificate found. SSL not configured.${NC}"
fi

# Check HPA
echo -e "\n7. Checking auto-scaling..."
kubectl get hpa -n superagi

# Check secrets
echo -e "\n8. Checking secrets..."
kubectl get secrets -n superagi | grep -E "(superagi|database|tls)"

# DNS check
echo -e "\n9. DNS Resolution Check..."
if command -v dig &> /dev/null; then
    CURRENT_IP=$(dig +short cherry-ai.me @8.8.8.8 | head -1)
    if [ -n "$CURRENT_IP" ]; then
        echo -e "Current DNS: cherry-ai.me -> $CURRENT_IP"
        if [ "$CURRENT_IP" = "$INGRESS_IP" ]; then
            echo -e "${GREEN}✓ DNS is correctly configured${NC}"
        else
            echo -e "${YELLOW}⚠ DNS points to different IP. Update needed.${NC}"
        fi
    else
        echo -e "${YELLOW}No DNS record found for cherry-ai.me${NC}"
    fi
fi

# Test endpoints
echo -e "\n10. Testing endpoints..."
if [ -n "$INGRESS_IP" ]; then
    echo "Testing HTTP redirect..."
    curl -I -s "http://$INGRESS_IP" -H "Host: cherry-ai.me" | head -1
    
    echo "Testing HTTPS..."
    curl -I -s -k "https://$INGRESS_IP" -H "Host: cherry-ai.me" | head -1
fi

# Summary
echo -e "\n========================================"
echo "Summary"
echo "========================================"

if [ -n "$INGRESS_IP" ]; then
    echo -e "${GREEN}Deployment Status: Ready${NC}"
    echo
    echo "Next steps:"
    echo "1. Update DNS A record: cherry-ai.me -> $INGRESS_IP"
    echo "2. Wait for SSL certificate to be issued (2-5 minutes)"
    echo "3. Access SuperAGI at: https://cherry-ai.me"
    echo
    echo "Monitor certificate status:"
    echo "  kubectl describe certificate superagi-tls -n superagi"
else
    echo -e "${YELLOW}Deployment Status: In Progress${NC}"
    echo
    echo "Waiting for:"
    echo "- Ingress controller to assign IP"
    echo "- SSL certificate provisioning"
    echo
    echo "Check again in a few minutes."
fi

echo
echo "Useful commands:"
echo "- View logs: kubectl logs -f deployment/superagi -n superagi"
echo "- Port forward: kubectl port-forward svc/superagi 8080:8080 -n superagi"
echo "- Watch ingress: kubectl get ingress -n superagi -w" 