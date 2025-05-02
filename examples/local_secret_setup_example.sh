#!/bin/bash
# Example script showing how to use secrets_setup.sh locally
# This is useful for testing your changes before pushing to CI/CD

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${YELLOW}Local Secret Manager Setup Example${NC}"
echo -e "${BLUE}==============================================${NC}"

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Ensure user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
  echo -e "${RED}Error: Not authenticated with gcloud${NC}"
  echo -e "Please run 'gcloud auth login' and try again."
  exit 1
fi

# Set variables (customize these for your environment)
PROJECT_ID="your-project-id"  # Replace with your project ID
SECRET_NAME="TEST_SECRET"     # Name of the secret to create/update
SECRET_FILE="test_secret.key" # Path to the secret file
SERVICE_ACCOUNT="your-service-account@${PROJECT_ID}.iam.gserviceaccount.com"  # Replace with your service account

# Create a temporary secret file for testing (DO NOT use real secrets here)
echo "This is a test secret for local development" > ${SECRET_FILE}
echo -e "${GREEN}Created temporary secret file: ${SECRET_FILE}${NC}"

# Run the secret setup script
echo -e "${YELLOW}Running secrets_setup.sh...${NC}"
echo -e "${BLUE}---------------------------------------------${NC}"
echo -e "Command to execute:"
echo -e "chmod +x ../secrets_setup.sh && ../secrets_setup.sh \\"
echo -e "  --project=${PROJECT_ID} \\"
echo -e "  --file=${SECRET_FILE} \\"
echo -e "  --secret=${SECRET_NAME} \\"
echo -e "  --service-account=${SERVICE_ACCOUNT}"
echo -e "${BLUE}---------------------------------------------${NC}"

# Uncomment the following lines to actually run the script
# chmod +x ../secrets_setup.sh
# ../secrets_setup.sh \
#   --project=${PROJECT_ID} \
#   --file=${SECRET_FILE} \
#   --secret=${SECRET_NAME} \
#   --service-account=${SERVICE_ACCOUNT}

# Clean up the temporary secret file
echo -e "${YELLOW}Cleaning up temporary secret file...${NC}"
rm -f ${SECRET_FILE}
echo -e "${GREEN}Temporary secret file removed${NC}"

echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}Example Completed${NC}"
echo -e "${YELLOW}NOTE: This script didn't actually run secrets_setup.sh.${NC}"
echo -e "${YELLOW}To run it for real, uncomment the relevant lines in this script.${NC}"
echo -e "${BLUE}==============================================${NC}"
