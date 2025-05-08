#!/bin/bash
# direct_gcp_auth.sh - Direct GCP authentication for AI Orchestra

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"

# Define cleanup function
cleanup() {
  if [ -f "$TEMP_KEY_FILE" ]; then
    rm -f "$TEMP_KEY_FILE"
    echo -e "${GREEN}🧹 Cleaned up temporary files${NC}"
  fi
}

# Register cleanup on exit
trap cleanup EXIT

# Handle errors
handle_error() {
  echo -e "${RED}Error occurred at line $1${NC}"
  exit 1
}

trap 'handle_error $LINENO' ERR

# Print banner
echo -e "${GREEN}"
echo "=================================================="
echo "   AI Orchestra Direct GCP Authentication"
echo "=================================================="
echo -e "${NC}"

# Check for required environment variables
if [ -z "$GCP_MASTER_SERVICE_JSON" ]; then
  # Check if we have stored credentials
  if [ -f ~/.orchestra/credentials/gcp-master.json ]; then
    echo -e "${YELLOW}Using stored GCP credentials...${NC}"
    TEMP_KEY_FILE=~/.orchestra/credentials/gcp-master.json
  else
    echo -e "${RED}Error: GCP_MASTER_SERVICE_JSON environment variable not set and no stored credentials found${NC}"
    echo -e "${YELLOW}Run credential_manager.sh first to set up credentials${NC}"
    exit 1
  fi
else
  # Use environment variable
  echo -e "${YELLOW}Using GCP_MASTER_SERVICE_JSON environment variable...${NC}"
  TEMP_KEY_FILE=$(mktemp)
  chmod 600 "$TEMP_KEY_FILE"
  echo "$GCP_MASTER_SERVICE_JSON" > "$TEMP_KEY_FILE"
fi

# Set environment variable for authentication
export GOOGLE_APPLICATION_CREDENTIALS="$TEMP_KEY_FILE"

# Authenticate with gcloud
echo -e "${YELLOW}Authenticating with GCP...${NC}"
if ! gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"; then
  echo -e "${RED}Authentication failed. Check your service account key.${NC}"
  exit 1
fi

# Configure gcloud
echo -e "${YELLOW}Configuring gcloud...${NC}"
gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"

echo -e "${GREEN}✅ Authentication successful${NC}"

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs (this may take a few minutes)...${NC}"

# Function to enable API with timeout and retry
enable_api() {
  local api=$1
  local max_attempts=3
  local attempt=1
  local timeout=60
  
  while [ $attempt -le $max_attempts ]; do
    echo -e "  Enabling $api (attempt $attempt/$max_attempts)..."
    if timeout $timeout gcloud services enable $api; then
      echo -e "  ${GREEN}✓ $api enabled${NC}"
      return 0
    else
      echo -e "  ${YELLOW}Failed to enable $api, retrying...${NC}"
      attempt=$((attempt+1))
      sleep 2
    fi
  done
  
  echo -e "  ${RED}Failed to enable $api after $max_attempts attempts${NC}"
  return 1
}

# List of APIs to enable
apis=(
  "compute.googleapis.com"
  "aiplatform.googleapis.com"
  "firestore.googleapis.com"
  "redis.googleapis.com"
  "secretmanager.googleapis.com"
  "artifactregistry.googleapis.com"
  "run.googleapis.com"
  "cloudbuild.googleapis.com"
  "sqladmin.googleapis.com"
  "vpcaccess.googleapis.com"
  "iam.googleapis.com"
  "iamcredentials.googleapis.com"
  "cloudresourcemanager.googleapis.com"
  "container.googleapis.com"
)

# Enable APIs with progress tracking
total_apis=${#apis[@]}
enabled_apis=0

for api in "${apis[@]}"; do
  if enable_api $api; then
    enabled_apis=$((enabled_apis+1))
  fi
done

if [ $enabled_apis -eq $total_apis ]; then
  echo -e "${GREEN}✅ All APIs enabled successfully${NC}"
else
  echo -e "${YELLOW}⚠️ Enabled $enabled_apis/$total_apis APIs${NC}"
fi

# Verify authentication and project access
echo -e "${YELLOW}Verifying project access...${NC}"
if gcloud projects describe "$PROJECT_ID" > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Project access verified${NC}"
else
  echo -e "${RED}❌ Could not access project. Check permissions.${NC}"
  exit 1
fi

echo -e "${GREEN}"
echo "=================================================="
echo "   GCP Authentication Complete!"
echo "=================================================="
echo -e "${NC}"
echo -e "Project: ${YELLOW}$PROJECT_ID${NC}"
echo -e "Region:  ${YELLOW}$REGION${NC}"
echo -e "APIs:    ${YELLOW}$enabled_apis/$total_apis${NC} enabled"
echo -e ""
echo -e "You can now use gcloud, terraform, and other GCP tools."