#!/bin/bash

# Script to deploy Terraform configuration for Cloud Workstations

set -e

# Source the authentication script
source ./authenticate_codespaces.sh

# Check if required environment variables are set
if [ -z "$GCP_PROJECT_ADMIN_KEY" ] || [ -z "$GCP_SECRET_MANAGEMENT_KEY" ] || [ -z "$GITHUB_PAT" ]; then
  echo "Error: Required environment variables are not set."
  echo "Please set GCP_PROJECT_ADMIN_KEY, GCP_SECRET_MANAGEMENT_KEY, and GITHUB_PAT."
  exit 1
fi

# Set Terraform backend configuration
export TF_VAR_gcs_bucket="your-terraform-state-bucket" # Replace with your GCS bucket
export TF_VAR_project_id="your-gcp-project-id" # Replace with your GCP project ID

# Initialize Terraform
terraform init -backend-config="bucket=$TF_VAR_gcs_bucket"

# Apply Terraform configuration
terraform apply -auto-approve

echo "Terraform deployment completed."