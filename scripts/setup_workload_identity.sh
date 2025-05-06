#!/bin/bash
# Setup Workload Identity Federation for GitHub Actions
# This script creates and configures Workload Identity Federation for GitHub Actions
# to securely authenticate with GCP without using service account keys.

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
REPO_OWNER="your-github-org"  # Replace with your GitHub organization or username
REPO_NAME="orchestra-main"     # Replace with your repository name
SERVICE_ACCOUNT_NAME="github-actions-wif"
SERVICE_ACCOUNT_DISPLAY_NAME="GitHub Actions Workload Identity"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Workload Identity Federation for GitHub Actions...${NC}"

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable iamcredentials.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com \
    --project ${PROJECT_ID}

# Create service account for GitHub Actions
echo -e "${YELLOW}Creating service account for GitHub Actions...${NC}"
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --project ${PROJECT_ID} &>/dev/null; then
    echo -e "${YELLOW}Service account already exists. Skipping creation.${NC}"
else
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
        --display-name="${SERVICE_ACCOUNT_DISPLAY_NAME}" \
        --project ${PROJECT_ID}
    echo -e "${GREEN}Service account created successfully.${NC}"
fi

# Grant necessary roles to the service account
echo -e "${YELLOW}Granting necessary roles to the service account...${NC}"
for role in "roles/artifactregistry.writer" "roles/run.admin" "roles/secretmanager.secretAccessor" "roles/storage.admin" "roles/iam.serviceAccountUser"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="${role}"
done

# Create Workload Identity Pool
echo -e "${YELLOW}Creating Workload Identity Pool...${NC}"
if gcloud iam workload-identity-pools describe ${POOL_NAME} --project=${PROJECT_ID} --location="global" &>/dev/null; then
    echo -e "${YELLOW}Workload Identity Pool already exists. Skipping creation.${NC}"
else
    gcloud iam workload-identity-pools create ${POOL_NAME} \
        --project=${PROJECT_ID} \
        --location="global" \
        --display-name="GitHub Actions Pool"
    echo -e "${GREEN}Workload Identity Pool created successfully.${NC}"
fi

# Get the Workload Identity Pool ID
POOL_ID=$(gcloud iam workload-identity-pools describe ${POOL_NAME} \
    --project=${PROJECT_ID} \
    --location="global" \
    --format="value(name)")

# Create Workload Identity Provider
echo -e "${YELLOW}Creating Workload Identity Provider...${NC}"
if gcloud iam workload-identity-pools providers describe ${PROVIDER_NAME} --project=${PROJECT_ID} --location="global" --workload-identity-pool=${POOL_NAME} &>/dev/null; then
    echo -e "${YELLOW}Workload Identity Provider already exists. Skipping creation.${NC}"
else
    gcloud iam workload-identity-pools providers create-oidc ${PROVIDER_NAME} \
        --project=${PROJECT_ID} \
        --location="global" \
        --workload-identity-pool=${POOL_NAME} \
        --display-name="GitHub Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com"
    echo -e "${GREEN}Workload Identity Provider created successfully.${NC}"
fi

# Allow authentications from the GitHub repository to impersonate the service account
echo -e "${YELLOW}Setting up authentication binding...${NC}"
gcloud iam service-accounts add-iam-policy-binding ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
    --project=${PROJECT_ID} \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${REPO_OWNER}/${REPO_NAME}"

# Get the Workload Identity Provider resource name
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe ${PROVIDER_NAME} \
    --project=${PROJECT_ID} \
    --location="global" \
    --workload-identity-pool=${POOL_NAME} \
    --format="value(name)")

echo -e "${GREEN}Workload Identity Federation setup complete!${NC}"
echo -e "${YELLOW}Add the following secrets to your GitHub repository:${NC}"
echo -e "${GREEN}WIF_PROVIDER_ID:${NC} ${PROVIDER_ID}"
echo -e "${GREEN}WIF_SERVICE_ACCOUNT:${NC} ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo -e "${YELLOW}Use these values in your GitHub Actions workflow:${NC}"
echo -e "
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: \${{ secrets.WIF_PROVIDER_ID }}
          service_account: \${{ secrets.WIF_SERVICE_ACCOUNT }}
          token_format: access_token
"