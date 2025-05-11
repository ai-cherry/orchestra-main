#!/bin/bash
# test_wif_setup.sh - Script to test Workload Identity Federation setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${1:-"cherry-ai-project"}
REGION=${2:-"us-central1"}
POOL_ID=${3:-"github-pool"}
PROVIDER_ID=${4:-"github-provider"}
SERVICE_ACCOUNT_ID=${5:-"github-actions-sa"}

echo -e "${GREEN}Testing Workload Identity Federation setup...${NC}"
echo -e "${YELLOW}Project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Pool ID: ${POOL_ID}${NC}"
echo -e "${YELLOW}Provider ID: ${PROVIDER_ID}${NC}"
echo -e "${YELLOW}Service Account ID: ${SERVICE_ACCOUNT_ID}${NC}"

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Google Cloud SDK (gcloud) is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}Visit https://cloud.google.com/sdk/docs/install for installation instructions.${NC}"
    exit 1
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

# Test 1: Check if Workload Identity Pool exists
echo -e "${YELLOW}Test 1: Checking if Workload Identity Pool exists...${NC}"
if gcloud iam workload-identity-pools describe ${POOL_ID} --project=${PROJECT_ID} --location=global &> /dev/null; then
    echo -e "${GREEN}✓ Workload Identity Pool '${POOL_ID}' exists.${NC}"
else
    echo -e "${RED}✗ Workload Identity Pool '${POOL_ID}' does not exist.${NC}"
    exit 1
fi

# Test 2: Check if Workload Identity Provider exists
echo -e "${YELLOW}Test 2: Checking if Workload Identity Provider exists...${NC}"
if gcloud iam workload-identity-pools providers describe ${PROVIDER_ID} \
    --project=${PROJECT_ID} \
    --location=global \
    --workload-identity-pool=${POOL_ID} &> /dev/null; then
    echo -e "${GREEN}✓ Workload Identity Provider '${PROVIDER_ID}' exists.${NC}"
else
    echo -e "${RED}✗ Workload Identity Provider '${PROVIDER_ID}' does not exist.${NC}"
    exit 1
fi

# Test 3: Check if service account exists
echo -e "${YELLOW}Test 3: Checking if service account exists...${NC}"
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com \
    --project=${PROJECT_ID} &> /dev/null; then
    echo -e "${GREEN}✓ Service account '${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com' exists.${NC}"
else
    echo -e "${RED}✗ Service account '${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com' does not exist.${NC}"
    exit 1
fi

# Test 4: Check if service account has necessary roles
echo -e "${YELLOW}Test 4: Checking if service account has necessary roles...${NC}"
REQUIRED_ROLES=("roles/run.admin" "roles/storage.admin")
for role in "${REQUIRED_ROLES[@]}"; do
    if gcloud projects get-iam-policy ${PROJECT_ID} \
        --format="value(bindings.members)" \
        --filter="bindings.role=${role}" | grep -q "serviceAccount:${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"; then
        echo -e "${GREEN}✓ Service account has role '${role}'.${NC}"
    else
        echo -e "${RED}✗ Service account does not have role '${role}'.${NC}"
        exit 1
    fi
done

# Test 5: Check if service account has workload identity binding
echo -e "${YELLOW}Test 5: Checking if service account has workload identity binding...${NC}"
if gcloud iam service-accounts get-iam-policy ${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com \
    --project=${PROJECT_ID} \
    --format="value(bindings.members)" \
    --filter="bindings.role=roles/iam.workloadIdentityUser" | grep -q "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}"; then
    echo -e "${GREEN}✓ Service account has workload identity binding.${NC}"
else
    echo -e "${RED}✗ Service account does not have workload identity binding.${NC}"
    exit 1
fi

# Test 6: Construct and display the Workload Identity Provider resource name
echo -e "${YELLOW}Test 6: Constructing Workload Identity Provider resource name...${NC}"
WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
echo -e "${GREEN}✓ Workload Identity Provider resource name: ${WIF_PROVIDER}${NC}"

# Test 7: Display the service account email
echo -e "${YELLOW}Test 7: Displaying service account email...${NC}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
echo -e "${GREEN}✓ Service account email: ${SERVICE_ACCOUNT_EMAIL}${NC}"

echo -e "${GREEN}All tests passed! Workload Identity Federation is set up correctly.${NC}"
echo -e "${GREEN}You can now use the following values in your GitHub Actions workflow:${NC}"
echo -e "${YELLOW}GCP_PROJECT_ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}GCP_REGION: ${REGION}${NC}"
echo -e "${YELLOW}GCP_WORKLOAD_IDENTITY_PROVIDER: ${WIF_PROVIDER}${NC}"
echo -e "${YELLOW}GCP_SERVICE_ACCOUNT: ${SERVICE_ACCOUNT_EMAIL}${NC}"