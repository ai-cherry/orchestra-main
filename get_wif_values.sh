#!/bin/bash
# Script to retrieve Workload Identity Federation values from GCP 
# and provide instructions for adding them to GitHub

set -e

echo "Retrieving Workload Identity Federation values from GCP..."

# Set the project ID
GCP_PROJECT_ID="cherry-ai-project"
PROJECT_NUMBER="525398941159"

# Construct the Workload Identity Provider ID
# Format: projects/{PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/providers/github-provider
WIF_PROVIDER_ID="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"

# Construct the GitHub Actions Deployer service account email
WIF_SERVICE_ACCOUNT="github-actions-deployer@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

echo "--------------------------------------------------"
echo "Add these values to GitHub repository Settings -> Secrets and variables -> Actions:"
echo ""
echo "SECRETS (click on 'New repository secret'):"
echo ""
echo "Name: WIF_PROVIDER_ID"
echo "Value: ${WIF_PROVIDER_ID}"
echo ""
echo "Name: WIF_SERVICE_ACCOUNT"
echo "Value: ${WIF_SERVICE_ACCOUNT}"
echo ""
echo "Name: GCP_PROJECT_ID"
echo "Value: ${GCP_PROJECT_ID}"
echo ""
echo "Then delete the old GCP_SA_KEY secret if it exists."
echo "--------------------------------------------------"
echo ""
echo "These values will be used in your GitHub Actions workflow to authenticate with GCP"
echo "using Workload Identity Federation, which is more secure than using service account keys."
echo ""
echo "To use these in your workflow, update to:"
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
