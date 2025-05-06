#!/bin/bash
# Main deployment script for Orchestra

set -e

# Configuration
export PROJECT_ID="cherry-ai.me"
export PROJECT_NUMBER="525398941159"
export REGION="us-central1"
export SERVICE_ACCOUNT="vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com"
export REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/orchestra"

# Parse arguments
ENVIRONMENT=${1:-prod}
DEPLOYMENT_TYPE=${2:-terraform}

echo "Deploying to environment: ${ENVIRONMENT}"
echo "Deployment type: ${DEPLOYMENT_TYPE}"

# Build Docker image
echo "Building Docker image..."
docker build -t ${REGISTRY}/api:${ENVIRONMENT} .
docker push ${REGISTRY}/api:${ENVIRONMENT}

# Deploy based on type
if [ "${DEPLOYMENT_TYPE}" = "cloud-run" ]; then
    echo "Deploying to Cloud Run..."
    gcloud run deploy orchestra-${ENVIRONMENT} \
        --image ${REGISTRY}/api:${ENVIRONMENT} \
        --platform managed \
        --region ${REGION} \
        --service-account ${SERVICE_ACCOUNT} \
        --project ${PROJECT_ID}
else
    echo "Deploying with Terraform..."
    cd infra/terraform/gcp
    
    # Initialize Terraform
    terraform init \
        -backend-config="bucket=tfstate-cherry-ai-me-orchestra" \
        -backend-config="prefix=terraform/state/${ENVIRONMENT}"
    
    # Apply Terraform changes
    terraform apply \
        -var="project_id=${PROJECT_ID}" \
        -var="environment=${ENVIRONMENT}" \
        -auto-approve
fi

echo "Deployment complete!"
