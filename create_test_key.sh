#!/bin/bash
# create_test_key.sh - Script to create a test service account key file
# This is for demonstration purposes only and should not be used in production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${1:-"cherry-ai-project"}
SERVICE_ACCOUNT_NAME=${2:-"github-actions-sa"}
KEY_FILE=${3:-"service-account-key.json"}

echo -e "${YELLOW}WARNING: This script is for demonstration purposes only.${NC}"
echo -e "${YELLOW}In a real environment, you should create a service account with the minimum required permissions.${NC}"
echo -e "${YELLOW}Service account keys should be kept secure and rotated regularly.${NC}"
echo -e "${YELLOW}For production, Workload Identity Federation is the recommended approach.${NC}"
echo

echo -e "${GREEN}Creating a test service account key file...${NC}"

# Create a sample key file for demonstration
cat > ${KEY_FILE} << EOF
{
  "type": "service_account",
  "project_id": "${PROJECT_ID}",
  "private_key_id": "sample-key-id-for-demonstration",
  "private_key": "-----BEGIN PRIVATE KEY-----\nSAMPLE_KEY_FOR_DEMONSTRATION_ONLY\n-----END PRIVATE KEY-----\n",
  "client_email": "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/${SERVICE_ACCOUNT_NAME}%40${PROJECT_ID}.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF

echo -e "${GREEN}Test service account key file created: ${KEY_FILE}${NC}"
echo -e "${YELLOW}Note: This is a dummy key file and will not work for actual authentication.${NC}"
echo -e "${YELLOW}To create a real service account key, use the following command:${NC}"
echo -e "${YELLOW}gcloud iam service-accounts keys create ${KEY_FILE} --iam-account=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com${NC}"
echo
echo -e "${GREEN}For deployment with a real key file, run:${NC}"
echo -e "${YELLOW}./deploy_with_key.sh ${PROJECT_ID} us-central1 dev latest ${KEY_FILE}${NC}"