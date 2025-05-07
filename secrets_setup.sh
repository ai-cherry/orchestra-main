#!/bin/bash
# secrets_setup.sh
# Automates the creation of secrets in Google Cloud Secret Manager
# and assigns appropriate IAM permissions

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Default values
PROJECT_ID="cherry-ai-project"
SECRET_NAME="PORTKEY_API_KEY"
SECRET_FILE="portkey.key"
SERVICE_ACCOUNT="vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com"
REPLICATION="automatic"

# Function to display usage information
usage() {
  echo -e "${BOLD}Usage:${NC} $0 [OPTIONS]"
  echo
  echo -e "${BOLD}Options:${NC}"
  echo "  --project=ID        GCP Project ID (default: $PROJECT_ID)"
  echo "  --secret=NAME       Secret name (default: $SECRET_NAME)"
  echo "  --file=PATH         Path to the secret file (default: $SECRET_FILE)"
  echo "  --sa=EMAIL          Service account email (default: $SERVICE_ACCOUNT)"
  echo "  --replication=TYPE  Replication policy (default: $REPLICATION)"
  echo "  --help              Display this help message"
  echo
  echo -e "${BOLD}Example:${NC}"
  echo "  $0 --project=my-project --file=/path/to/secret.key"
}

# Process command-line arguments
for arg in "$@"; do
  case $arg in
    --project=*)
      PROJECT_ID="${arg#*=}"
      shift
      ;;
    --secret=*)
      SECRET_NAME="${arg#*=}"
      shift
      ;;
    --file=*)
      SECRET_FILE="${arg#*=}"
      shift
      ;;
    --sa=*)
      SERVICE_ACCOUNT="${arg#*=}"
      shift
      ;;
    --replication=*)
      REPLICATION="${arg#*=}"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown option: $arg${NC}"
      usage
      exit 1
      ;;
  esac
done

echo -e "${BLUE}======================================================${NC}"
echo -e "${BOLD}Secret Manager Setup Script${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Project:${NC} $PROJECT_ID"
echo -e "${YELLOW}Secret Name:${NC} $SECRET_NAME"
echo -e "${YELLOW}Secret File:${NC} $SECRET_FILE"
echo -e "${YELLOW}Service Account:${NC} $SERVICE_ACCOUNT"
echo -e "${YELLOW}Replication:${NC} $REPLICATION"
echo -e "${BLUE}======================================================${NC}"

# Validate the secret file exists
if [[ ! -f "$SECRET_FILE" ]]; then
  echo -e "${RED}Error: Secret file '$SECRET_FILE' not found${NC}"
  echo -e "Please ensure the file exists and try again."
  exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &>/dev/null; then
  echo -e "${RED}Error: gcloud CLI is not installed or not in PATH${NC}"
  echo -e "Please install the Google Cloud SDK and try again."
  exit 1
fi

# Check if user is authenticated with gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
  echo -e "${RED}Error: Not authenticated with gcloud${NC}"
  echo -e "Please run 'gcloud auth login' and try again."
  exit 1
fi

# Check if the project exists and user has access
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
  echo -e "${RED}Error: Project '$PROJECT_ID' not found or you don't have access${NC}"
  exit 1
fi

# Check if Secret Manager API is enabled
echo -e "${YELLOW}Checking if Secret Manager API is enabled...${NC}"
if ! gcloud services list --enabled --project="$PROJECT_ID" | grep -q "secretmanager.googleapis.com"; then
  echo -e "${YELLOW}Enabling Secret Manager API...${NC}"
  if ! gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"; then
    echo -e "${RED}Error: Failed to enable Secret Manager API${NC}"
    exit 1
  fi
  echo -e "${GREEN}Secret Manager API enabled successfully${NC}"
else
  echo -e "${GREEN}Secret Manager API is already enabled${NC}"
fi

# Check if the secret already exists
echo -e "${YELLOW}Checking if secret '$SECRET_NAME' already exists...${NC}"
if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
  echo -e "${YELLOW}Secret '$SECRET_NAME' already exists${NC}"
  read -p "Do you want to update it? (y/n, default: n): " update_secret
  
  if [[ "$update_secret" != "y" && "$update_secret" != "Y" ]]; then
    echo -e "${YELLOW}Skipping secret creation. Moving to IAM configuration...${NC}"
    secret_exists=true
  else
    echo -e "${YELLOW}Updating secret '$SECRET_NAME'...${NC}"
    secret_exists=true
    # Will be updated below
  fi
else
  echo -e "${YELLOW}Creating new secret '$SECRET_NAME'...${NC}"
  secret_exists=false
fi

# Create or update the secret
if [[ "$secret_exists" == "false" ]]; then
  echo -e "${YELLOW}Creating secret from file '$SECRET_FILE'...${NC}"
  if ! gcloud secrets create "$SECRET_NAME" --data-file="$SECRET_FILE" \
       --project="$PROJECT_ID" --replication-policy="$REPLICATION"; then
    echo -e "${RED}Error: Failed to create secret${NC}"
    exit 1
  fi
  echo -e "${GREEN}Secret '$SECRET_NAME' created successfully${NC}"
elif [[ "$update_secret" == "y" || "$update_secret" == "Y" ]]; then
  echo -e "${YELLOW}Adding new version to secret from file '$SECRET_FILE'...${NC}"
  if ! gcloud secrets versions add "$SECRET_NAME" --data-file="$SECRET_FILE" \
       --project="$PROJECT_ID"; then
    echo -e "${RED}Error: Failed to update secret${NC}"
    exit 1
  fi
  echo -e "${GREEN}Secret '$SECRET_NAME' updated successfully${NC}"
fi

# Set IAM permissions
echo -e "${YELLOW}Setting IAM permissions for service account '$SERVICE_ACCOUNT'...${NC}"
if ! gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor" \
     --project="$PROJECT_ID"; then
  echo -e "${RED}Error: Failed to set IAM permissions${NC}"
  exit 1
fi

echo -e "${GREEN}IAM permissions set successfully${NC}"

# Verify the service account has access
echo -e "${YELLOW}Verifying service account access...${NC}"
if gcloud secrets get-iam-policy "$SECRET_NAME" --project="$PROJECT_ID" | \
   grep -q "serviceAccount:$SERVICE_ACCOUNT"; then
  echo -e "${GREEN}Verified: Service account has access to the secret${NC}"
else
  echo -e "${RED}Warning: Could not verify service account access${NC}"
  echo -e "${YELLOW}Please check IAM permissions manually${NC}"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}${BOLD}Secret Manager setup completed successfully!${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Summary:${NC}"
echo -e "  Secret Name: ${BOLD}$SECRET_NAME${NC}"
echo -e "  Project: ${BOLD}$PROJECT_ID${NC}"
echo -e "  Service Account: ${BOLD}$SERVICE_ACCOUNT${NC}"
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Use the secret in your application via Secret Manager"
echo -e "  2. Review access permissions in GCP Console"
echo -e "${BLUE}======================================================${NC}"
