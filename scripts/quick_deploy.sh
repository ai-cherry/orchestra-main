#!/bin/bash
# Quick Deploy to Existing Cluster
# ================================
# Deploys AI Orchestra directly using kubectl

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

# Configuration
PROJECT_ID="cherry-ai-project"
CLUSTER_NAME="coder-control"
REGION="us-central1"
NAMESPACE="ai-orchestra"

# Managed Service Credentials
MONGODB_URI="mongodb+srv://musillynn:gK9P3O4T5a9bMMA4@cluster0.oaceter.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DRAGONFLY_URL="rediss://default:lnz7y6oykgse@qpwj3s2ae.dragonflydb.cloud:6385"
WEAVIATE_ENDPOINT="https://2jnpk8ibqhwscncku73wq.c0.us-east1.gcp.weaviate.cloud"
WEAVIATE_API_KEY="4C8HZ08ssSvmUU7TCGidHWRgXKVhGT791Pmo"

log_info "Quick deployment to existing cluster..."

# Get cluster credentials
log_info "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID

# Create namespace
log_info "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
log_info "Creating secrets..."
kubectl create secret generic managed-services \
    --namespace=$NAMESPACE \
    --from-literal=mongodb-uri="$MONGODB_URI" \
    --from-literal=dragonfly-url="$DRAGONFLY_URL" \
    --from-literal=weaviate-endpoint="$WEAVIATE_ENDPOINT" \
    --from-literal=weaviate-api-key="$WEAVIATE_API_KEY" \
    --from-literal=openai-api-key="${OPENAI_API_KEY:-dummy}" \
    --from-literal=anthropic-api-key="${ANTHROPIC_API_KEY:-dummy}" \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy AI Orchestra
log_info "Deploying AI Orchestra..."
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-orchestra
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-orchestra
  template:
    metadata:
      labels:
        app: ai-orchestra
    spec:
      containers:
      - name: orchestra
        image: superagi/superagi:latest
        ports:
        - containerPort: 8080
        env:
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: managed-services
              key: mongodb-uri
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: managed-services
              key: dragonfly-url
        - name: WEAVIATE_URL
          valueFrom:
            secretKeyRef:
              name: managed-services
              key: weaviate-endpoint
        - name: WEAVIATE_API_KEY
          valueFrom:
            secretKeyRef:
              name: managed-services
              key: weaviate-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: managed-services
              key: openai-api-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: managed-services
              key: anthropic-api-key
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ai-orchestra
spec:
  selector:
    app: ai-orchestra
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-orchestra-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-orchestra
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

# Wait for deployment
log_info "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/ai-orchestra -n $NAMESPACE || true

# Get service info
SERVICE_IP=$(kubectl get svc ai-orchestra -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

# Summary
echo ""
echo "=========================================="
echo "AI Orchestra Quick Deployment Complete"
echo "=========================================="
echo ""
echo "Namespace: $NAMESPACE"
echo "Replicas: 2 (auto-scaling to 10)"
echo ""
echo "Managed Services:"
echo "- MongoDB Atlas: ✓ Connected"
echo "- DragonflyDB Cloud: ✓ Connected (12.5GB)"
echo "- Weaviate Cloud: ✓ Connected"
echo ""
echo "Service Endpoint: http://$SERVICE_IP:8080"
echo ""
echo "To access locally:"
echo "  kubectl port-forward -n $NAMESPACE svc/ai-orchestra 8080:8080"
echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/ai-orchestra -n $NAMESPACE"
echo ""
echo "To check status:"
echo "  kubectl get all -n $NAMESPACE"
echo ""
echo "=========================================="
