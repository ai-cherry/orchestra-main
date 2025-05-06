#!/bin/bash
# Setup Workload Identity Federation for GitHub Actions
# This script sets up Workload Identity Federation for GitHub Actions to authenticate with GCP

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
POOL_ID="github-actions-pool"
PROVIDER_ID="github-actions-provider"
SERVICE_ACCOUNT_NAME="github-actions-sa"
REPO_NAME=${REPO_NAME:-"your-github-org/orchestra-main"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${RED}Error: You are not logged in to gcloud. Please run 'gcloud auth login' first.${NC}"
    exit 1
fi

# Print configuration
echo -e "${BLUE}=== Configuration ===${NC}"
echo -e "Project ID: ${GREEN}${PROJECT_ID}${NC}"
echo -e "Pool ID: ${GREEN}${POOL_ID}${NC}"
echo -e "Provider ID: ${GREEN}${PROVIDER_ID}${NC}"
echo -e "Service Account: ${GREEN}${SERVICE_ACCOUNT_NAME}${NC}"
echo -e "GitHub Repository: ${GREEN}${REPO_NAME}${NC}"
echo ""

# Confirm with user
read -p "Do you want to proceed with this configuration? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Setup cancelled.${NC}"
    exit 0
fi

# Set the project
echo -e "${BLUE}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${BLUE}Enabling required APIs...${NC}"
gcloud services enable \
    iamcredentials.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com \
    --project=${PROJECT_ID}

# Create Workload Identity Pool
echo -e "${BLUE}Creating Workload Identity Pool...${NC}"
if ! gcloud iam workload-identity-pools describe ${POOL_ID} \
    --location=global \
    --project=${PROJECT_ID} &> /dev/null; then
    gcloud iam workload-identity-pools create ${POOL_ID} \
        --location=global \
        --display-name="GitHub Actions Pool" \
        --project=${PROJECT_ID}
    echo -e "${GREEN}Created Workload Identity Pool: ${POOL_ID}${NC}"
else
    echo -e "${YELLOW}Workload Identity Pool already exists: ${POOL_ID}${NC}"
fi

# Get the Workload Identity Pool ID
POOL_ID_FULL=$(gcloud iam workload-identity-pools describe ${POOL_ID} \
    --location=global \
    --project=${PROJECT_ID} \
    --format="value(name)")

# Create Workload Identity Provider
echo -e "${BLUE}Creating Workload Identity Provider...${NC}"
if ! gcloud iam workload-identity-pools providers describe ${PROVIDER_ID} \
    --location=global \
    --workload-identity-pool=${POOL_ID} \
    --project=${PROJECT_ID} &> /dev/null; then
    gcloud iam workload-identity-pools providers create-oidc ${PROVIDER_ID} \
        --location=global \
        --workload-identity-pool=${POOL_ID} \
        --display-name="GitHub Actions Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --project=${PROJECT_ID}
    echo -e "${GREEN}Created Workload Identity Provider: ${PROVIDER_ID}${NC}"
else
    echo -e "${YELLOW}Workload Identity Provider already exists: ${PROVIDER_ID}${NC}"
fi

# Get the Workload Identity Provider ID
PROVIDER_ID_FULL=$(gcloud iam workload-identity-pools providers describe ${PROVIDER_ID} \
    --location=global \
    --workload-identity-pool=${POOL_ID} \
    --project=${PROJECT_ID} \
    --format="value(name)")

# Create Service Account for GitHub Actions
echo -e "${BLUE}Creating Service Account for GitHub Actions...${NC}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} \
    --project=${PROJECT_ID} &> /dev/null; then
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
        --display-name="GitHub Actions Service Account" \
        --project=${PROJECT_ID}
    echo -e "${GREEN}Created Service Account: ${SERVICE_ACCOUNT_EMAIL}${NC}"
else
    echo -e "${YELLOW}Service Account already exists: ${SERVICE_ACCOUNT_EMAIL}${NC}"
fi

# Grant necessary roles to the service account
echo -e "${BLUE}Granting necessary roles to the service account...${NC}"
for role in "roles/run.admin" "roles/storage.admin" "roles/iam.serviceAccountUser" "roles/secretmanager.admin" "roles/redis.admin" "roles/firestore.admin"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="${role}" \
        --condition=None
done

# Allow GitHub Actions to impersonate the service account
echo -e "${BLUE}Allowing GitHub Actions to impersonate the service account...${NC}"
gcloud iam service-accounts add-iam-policy-binding ${SERVICE_ACCOUNT_EMAIL} \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_ID_FULL}/attribute.repository/${REPO_NAME}" \
    --project=${PROJECT_ID}

# Print the values to use in GitHub Actions
echo -e "${BLUE}=== GitHub Actions Configuration ===${NC}"
echo -e "${GREEN}WIF_PROVIDER_ID:${NC} ${PROVIDER_ID_FULL}"
echo -e "${GREEN}WIF_SERVICE_ACCOUNT:${NC} ${SERVICE_ACCOUNT_EMAIL}"
echo ""
echo -e "${BLUE}Add these secrets to your GitHub repository:${NC}"
echo -e "1. WIF_PROVIDER_ID: ${PROVIDER_ID_FULL}"
echo -e "2. WIF_SERVICE_ACCOUNT: ${SERVICE_ACCOUNT_EMAIL}"
echo -e "3. PROJECT_ID: ${PROJECT_ID}"

echo -e "${GREEN}Setup completed successfully!${NC}"