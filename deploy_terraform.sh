#!/bin/bash
# Script to deploy Terraform infrastructure

set -e

# Configuration
export PROJECT_ID="cherry-ai.me"
export PROJECT_NUMBER="525398941159"
export REGION="us-central1"
export BUCKET="tfstate-cherry-ai-me-orchestra"

# Parse environment argument
ENVIRONMENT=${1:-prod}

echo "Deploying Terraform infrastructure for environment: ${ENVIRONMENT}"

# Navigate to Terraform directory
cd infra/terraform/gcp

# Initialize Terraform
echo "Initializing Terraform..."
terraform init \
    -backend-config="bucket=${BUCKET}" \
    -backend-config="prefix=terraform/state/${ENVIRONMENT}"

# Validate Terraform configuration
echo "Validating Terraform configuration..."
terraform validate

# Plan Terraform changes
echo "Planning Terraform changes..."
terraform plan \
    -var="project_id=${PROJECT_ID}" \
    -var="environment=${ENVIRONMENT}" \
    -out=tfplan

# Apply Terraform changes
echo "Applying Terraform changes..."
terraform apply tfplan

echo "Terraform deployment complete!"