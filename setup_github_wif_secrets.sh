#!/bin/bash
# Script to retrieve Workload Identity Federation values from Terraform outputs
# and provide instructions for adding them as GitHub repository secrets

set -e

echo "Retrieving Workload Identity Federation values from Terraform outputs..."

# Check if we're in the right directory
if [[ ! -d "infra/terraform/gcp/environments/common" ]]; then
  echo "Error: This script must be run from the repository root directory"
  exit 1
fi

# Change to the common environment directory where the outputs exist
cd infra/terraform/gcp/environments/common

# Get the Provider ID
# Note: The output name in Terraform is 'workload_identity_provider'
WIF_PROVIDER_ID=$(terraform output -raw workload_identity_provider 2>/dev/null || echo "Error: Unable to retrieve workload_identity_provider")

# Get the SA email 
# Note: The output name in Terraform is 'github_actions_deployer_email'
WIF_SERVICE_ACCOUNT=$(terraform output -raw github_actions_deployer_email 2>/dev/null || echo "Error: Unable to retrieve github_actions_deployer_email")

# Go back to the root directory
cd ../../../../..

echo "--------------------------------------------------"
echo "Add these secrets to GitHub repo 'ai-cherry/orchestra-main':"
echo "WIF_PROVIDER_ID : ${WIF_PROVIDER_ID}"
echo "WIF_SERVICE_ACCOUNT : ${WIF_SERVICE_ACCOUNT}"
echo "GCP_PROJECT_ID : cherry-ai-project"
echo "--------------------------------------------------"
echo ""
echo "These values will be used in your GitHub Actions workflow to authenticate with GCP"
echo "using Workload Identity Federation, which is more secure than using service account keys."
echo ""
echo "After adding these secrets, update your GitHub workflow files to use them like this:"
echo ""
echo "  - name: Authenticate to Google Cloud"
echo "    uses: google-github-actions/auth@v1"
echo "    with:"
echo "      workload_identity_provider: \${{ secrets.WIF_PROVIDER_ID }}"
echo "      service_account: \${{ secrets.WIF_SERVICE_ACCOUNT }}"
echo ""
echo "  - name: Setup gcloud CLI"
echo "    uses: google-github-actions/setup-gcloud@v1"
echo "    with:"
echo "      project_id: \${{ secrets.GCP_PROJECT_ID }}"
