#!/bin/bash
# setup_and_deploy_with_wif.sh - Main script to set up WIF and deploy the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${1:-"cherry-ai-project"}
REGION=${2:-"us-central1"}
ENVIRONMENT=${3:-"dev"}
GITHUB_REPO=${4:-"ai-cherry/orchestra-main"}
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
SERVICE_ACCOUNT_ID="github-actions-sa"

# Print banner
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  AI Orchestra - WIF Setup and Deployment              ${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"
echo -e "${YELLOW}GitHub Repository: ${GITHUB_REPO}${NC}"
echo -e "${BLUE}=======================================================${NC}"

# Check if required tools are installed
echo -e "${GREEN}Checking required tools...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Google Cloud SDK (gcloud) is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}Visit https://cloud.google.com/sdk/docs/install for installation instructions.${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${YELLOW}Terraform is not installed. Skipping Terraform setup.${NC}"
    USE_TERRAFORM=false
else
    echo -e "${GREEN}Terraform is installed. Using Terraform for setup.${NC}"
    USE_TERRAFORM=true
fi

if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI (gh) is not installed. Skipping GitHub secrets setup.${NC}"
    SETUP_GITHUB_SECRETS=false
else
    echo -e "${GREEN}GitHub CLI is installed. Will set up GitHub secrets.${NC}"
    SETUP_GITHUB_SECRETS=true
fi

# Check if user is authenticated with gcloud CLI
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}You are not authenticated with gcloud CLI. Please run 'gcloud auth login' first.${NC}"
    exit 1
fi

# Get the project number
echo -e "${GREEN}Getting project number...${NC}"
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
echo -e "${GREEN}Project number: ${PROJECT_NUMBER}${NC}"

# Step 1: Set up Workload Identity Federation
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Step 1: Setting up Workload Identity Federation      ${NC}"
echo -e "${BLUE}=======================================================${NC}"

if [ "$USE_TERRAFORM" = true ]; then
    echo -e "${GREEN}Using Terraform to set up Workload Identity Federation...${NC}"
    
    # Create Terraform configuration
    mkdir -p terraform/wif
    cat > terraform/wif/main.tf << EOF
module "wif" {
  source = "../modules/wif"
  
  project_id     = "${PROJECT_ID}"
  project_number = "${PROJECT_NUMBER}"
  repository     = "${GITHUB_REPO}"
  pool_id        = "${POOL_ID}"
  provider_id    = "${PROVIDER_ID}"
  service_account_id = "${SERVICE_ACCOUNT_ID}"
}

output "workload_identity_provider" {
  value = module.wif.workload_identity_provider
}

output "service_account_email" {
  value = module.wif.service_account_email
}
EOF
    
    # Initialize and apply Terraform
    cd terraform/wif
    terraform init
    terraform apply -auto-approve
    
    # Get outputs
    WIF_PROVIDER=$(terraform output -raw workload_identity_provider)
    SERVICE_ACCOUNT_EMAIL=$(terraform output -raw service_account_email)
    
    cd ../..
else
    echo -e "${GREEN}Using deploy_wif.sh script to set up Workload Identity Federation...${NC}"
    ./deploy_wif.sh
    
    # Construct the Workload Identity Provider resource name
    WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
    SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
fi

# Step 2: Set up GitHub secrets
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Step 2: Setting up GitHub secrets                    ${NC}"
echo -e "${BLUE}=======================================================${NC}"

if [ "$SETUP_GITHUB_SECRETS" = true ]; then
    echo -e "${GREEN}Setting up GitHub secrets...${NC}"
    ./setup_github_wif_secrets.sh "${PROJECT_ID}" "${REGION}" "${GITHUB_REPO}" "${POOL_ID}" "${PROVIDER_ID}" "${SERVICE_ACCOUNT_ID}"
else
    echo -e "${YELLOW}Skipping GitHub secrets setup. Please set up the following secrets manually:${NC}"
    echo -e "${YELLOW}GCP_PROJECT_ID: ${PROJECT_ID}${NC}"
    echo -e "${YELLOW}GCP_REGION: ${REGION}${NC}"
    echo -e "${YELLOW}GCP_WORKLOAD_IDENTITY_PROVIDER: ${WIF_PROVIDER}${NC}"
    echo -e "${YELLOW}GCP_SERVICE_ACCOUNT: ${SERVICE_ACCOUNT_EMAIL}${NC}"
fi

# Step 3: Test the setup
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Step 3: Testing the setup                            ${NC}"
echo -e "${BLUE}=======================================================${NC}"

echo -e "${GREEN}Testing Workload Identity Federation setup...${NC}"
./test_wif_setup.sh "${PROJECT_ID}" "${REGION}" "${POOL_ID}" "${PROVIDER_ID}" "${SERVICE_ACCOUNT_ID}"

# Step 4: Deploy the application
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Step 4: Deploying the application                    ${NC}"
echo -e "${BLUE}=======================================================${NC}"

echo -e "${GREEN}Deploying the application...${NC}"
echo -e "${YELLOW}Note: This step would normally be done by GitHub Actions.${NC}"
echo -e "${YELLOW}For local deployment, we'll use the deploy_wif.sh script.${NC}"

read -p "Do you want to deploy the application now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./deploy_wif.sh "${ENVIRONMENT}"
else
    echo -e "${YELLOW}Skipping deployment. You can deploy later using:${NC}"
    echo -e "${YELLOW}./deploy_wif.sh ${ENVIRONMENT}${NC}"
fi

# Step 5: Summary
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Step 5: Summary                                      ${NC}"
echo -e "${BLUE}=======================================================${NC}"

echo -e "${GREEN}Workload Identity Federation setup complete!${NC}"
echo -e "${GREEN}GitHub secrets have been set up (or instructions provided).${NC}"
echo -e "${GREEN}The setup has been tested and is working correctly.${NC}"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}The application has been deployed.${NC}"
else
    echo -e "${YELLOW}The application has not been deployed yet.${NC}"
fi

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Next Steps                                           ${NC}"
echo -e "${BLUE}=======================================================${NC}"

echo -e "${GREEN}1. Push your code to GitHub to trigger the GitHub Actions workflow.${NC}"
echo -e "${GREEN}2. Monitor the workflow in the GitHub Actions tab.${NC}"
echo -e "${GREEN}3. Check the deployed application at the URL provided by Cloud Run.${NC}"

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Documentation                                        ${NC}"
echo -e "${BLUE}=======================================================${NC}"

echo -e "${GREEN}For more information, see the documentation at:${NC}"
echo -e "${YELLOW}docs/workload_identity_federation.md${NC}"