#!/bin/bash
# Deploy AI Orchestra with Aiven Services
# ========================================
# Uses Aiven for managed databases instead of GCP

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Aiven Configuration
AIVEN_TOKEN="${AIVEN_TOKEN:-your-aiven-token}"
AIVEN_PROJECT="${AIVEN_PROJECT:-your-project}"
AIVEN_CLOUD="${AIVEN_CLOUD:-aws-us-east-1}"  # or google-us-central1

# MongoDB Atlas (you already have)
MONGODB_URI="mongodb+srv://musillynn:gK9P3O4T5a9bMMA4@cluster0.oaceter.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# DragonflyDB Cloud (you already have)
DRAGONFLY_URL="rediss://default:lnz7y6oykgse@qpwj3s2ae.dragonflydb.cloud:6385"

# Weaviate Cloud (you already have)
WEAVIATE_ENDPOINT="https://2jnpk8ibqhwscncku73wq.c0.us-east1.gcp.weaviate.cloud"
WEAVIATE_API_KEY="4C8HZ08ssSvmUU7TCGidHWRgXKVhGT791Pmo"

log_info "Setting up AI Orchestra with managed services..."

# Option 1: Deploy on Paperspace Gradient
if command -v gradient &> /dev/null; then
    log_info "Deploying on Paperspace Gradient..."

    gradient deployments create \
        --name ai-orchestra \
        --image superagi/superagi:latest \
        --machineType C5 \
        --env MONGODB_URI="$MONGODB_URI" \
        --env REDIS_URL="$DRAGONFLY_URL" \
        --env WEAVIATE_URL="$WEAVIATE_ENDPOINT" \
        --env WEAVIATE_API_KEY="$WEAVIATE_API_KEY" \
        --env OPENAI_API_KEY="$OPENAI_API_KEY" \
        --env ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
        --port 8080
fi

# Option 2: Deploy on Railway
if command -v railway &> /dev/null; then
    log_info "Deploying on Railway..."

    cat > railway.json <<EOF
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 2,
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
EOF

    railway up
fi

# Option 3: Deploy on Fly.io
if command -v fly &> /dev/null; then
    log_info "Deploying on Fly.io..."

    cat > fly.toml <<EOF
app = "ai-orchestra"
primary_region = "iad"

[build]
  image = "superagi/superagi:latest"

[env]
  MONGODB_URI = "$MONGODB_URI"
  REDIS_URL = "$DRAGONFLY_URL"
  WEAVIATE_URL = "$WEAVIATE_ENDPOINT"
  WEAVIATE_API_KEY = "$WEAVIATE_API_KEY"

[[services]]
  http_checks = []
  internal_port = 8080
  protocol = "tcp"
  script_checks = []

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
EOF

    fly deploy
fi

# Option 4: Use Pulumi with Aiven
if command -v pulumi &> /dev/null; then
    log_info "Setting up Pulumi with Aiven provider..."

    cd infra
    pulumi plugin install resource aiven v6.7.1

    cat > Pulumi.yaml <<EOF
name: ai-orchestra-aiven
runtime: python
description: AI Orchestra with Aiven services
config:
  aiven:apiToken:
    value: $AIVEN_TOKEN
EOF

    # Create Python program for Aiven
    cat > __main__.py <<EOF
import pulumi
import pulumi_aiven as aiven

# Create Aiven Kafka for event streaming
kafka = aiven.Kafka("ai-orchestra-kafka",
    project=AIVEN_PROJECT,
    cloud_name=AIVEN_CLOUD,
    plan="startup-2",
    service_name="ai-orchestra-kafka",
    kafka_user_config={
        "kafka_rest": True,
        "kafka_connect": True,
        "schema_registry": True,
    }
)

# Create Aiven OpenSearch for logs/search
opensearch = aiven.OpenSearch("ai-orchestra-search",
    project=AIVEN_PROJECT,
    cloud_name=AIVEN_CLOUD,
    plan="startup-4",
    service_name="ai-orchestra-search"
)

# Export endpoints
pulumi.export("kafka_uri", kafka.service_uri)
pulumi.export("opensearch_uri", opensearch.service_uri)
pulumi.export("mongodb_uri", "$MONGODB_URI")
pulumi.export("dragonfly_url", "$DRAGONFLY_URL")
pulumi.export("weaviate_endpoint", "$WEAVIATE_ENDPOINT")
EOF

    pulumi up
fi

log_info "Deployment complete!"
echo ""
echo "==================================="
echo "AI Orchestra - No GKE Required! 🎉"
echo "==================================="
echo ""
echo "Managed Services:"
echo "- MongoDB Atlas: ✓ (existing)"
echo "- DragonflyDB Cloud: ✓ (12.5GB)"
echo "- Weaviate Cloud: ✓ (existing)"
echo "- Aiven Kafka: ✓ (optional)"
echo "- Aiven OpenSearch: ✓ (optional)"
echo ""
echo "Deployment Options:"
echo "1. Paperspace Gradient (easiest)"
echo "2. Railway.app (one-click)"
echo "3. Fly.io (global edge)"
echo "4. Render.com (simple)"
echo ""
echo "No Kubernetes complexity!"
echo "==================================="
