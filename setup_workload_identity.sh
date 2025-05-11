#!/bin/bash
# setup_workload_identity.sh - Script to set up Workload Identity Federation for GitHub Actions

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="cherry-ai-project"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"
SERVICE_ACCOUNT_NAME="github-actions-sa"
REPO_OWNER="ai-cherry"
REPO_NAME="orchestra-main"
REGION="us-central1"

echo -e "${BLUE}=== Setting up Workload Identity Federation for GitHub Actions ===${NC}"
echo -e "Project ID: ${PROJECT_ID}"
echo -e "GitHub Repository: ${REPO_OWNER}/${REPO_NAME}"
echo -e "Region: ${REGION}"
echo

# Step 1: Create a Workload Identity Pool
echo -e "${YELLOW}Step 1: Creating Workload Identity Pool${NC}"
if gcloud iam workload-identity-pools describe $POOL_NAME \
  --project=$PROJECT_ID \
  --location="global" &>/dev/null; then
  echo -e "${GREEN}✓ Workload Identity Pool already exists${NC}"
else
  gcloud iam workload-identity-pools create $POOL_NAME \
    --project=$PROJECT_ID \
    --location="global" \
    --display-name="GitHub Actions Pool"
  echo -e "${GREEN}✓ Workload Identity Pool created${NC}"
fi

# Get the Workload Identity Pool ID
POOL_ID=$(gcloud iam workload-identity-pools describe $POOL_NAME \
  --project=$PROJECT_ID \
  --location="global" \
  --format="value(name)")

echo -e "Workload Identity Pool ID: ${POOL_ID}"

# Step 2: Create a Workload Identity Provider
echo -e "\n${YELLOW}Step 2: Creating Workload Identity Provider${NC}"
if gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool=$POOL_NAME &>/dev/null; then
  echo -e "${GREEN}✓ Workload Identity Provider already exists${NC}"
else
  gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
    --project=$PROJECT_ID \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"
  echo -e "${GREEN}✓ Workload Identity Provider created${NC}"
fi

# Get the Workload Identity Provider resource name
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool=$POOL_NAME \
  --format="value(name)")

echo -e "Workload Identity Provider ID: ${PROVIDER_ID}"

# Step 3: Create a Service Account
echo -e "\n${YELLOW}Step 3: Creating Service Account${NC}"
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
  --project=$PROJECT_ID &>/dev/null; then
  echo -e "${GREEN}✓ Service Account already exists${NC}"
else
  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --project=$PROJECT_ID \
    --description="Service account for GitHub Actions" \
    --display-name="GitHub Actions Service Account"
  echo -e "${GREEN}✓ Service Account created${NC}"
fi

# Step 4: Grant the Service Account necessary permissions
echo -e "\n${YELLOW}Step 4: Granting Service Account permissions${NC}"
echo -e "  Adding roles/run.admin..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

echo -e "  Adding roles/storage.admin..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

echo -e "  Adding roles/iam.serviceAccountUser..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

echo -e "${GREEN}✓ Service Account permissions granted${NC}"

# Step 5: Allow the GitHub Repository to impersonate the Service Account
echo -e "\n${YELLOW}Step 5: Allowing GitHub Repository to impersonate the Service Account${NC}"
gcloud iam service-accounts add-iam-policy-binding \
  $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${REPO_OWNER}/${REPO_NAME}"

echo -e "${GREEN}✓ GitHub Repository allowed to impersonate the Service Account${NC}"

# Step 6: Get the values for GitHub Secrets
echo -e "\n${BLUE}=== Values for GitHub Secrets ===${NC}"
echo -e "${YELLOW}GCP_PROJECT_ID:${NC} $PROJECT_ID"
echo -e "${YELLOW}GCP_REGION:${NC} $REGION"
echo -e "${YELLOW}GCP_WORKLOAD_IDENTITY_PROVIDER:${NC} $PROVIDER_ID"
echo -e "${YELLOW}GCP_SERVICE_ACCOUNT:${NC} $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo -e "\n${BLUE}=== Next Steps ===${NC}"
echo -e "1. Add the above values as secrets in your GitHub repository"
echo -e "2. Update your GitHub Actions workflow file with the updated_workflow.yml content"
echo -e "3. Push the changes to your repository"
echo -e "4. Trigger the workflow manually from the GitHub Actions tab"