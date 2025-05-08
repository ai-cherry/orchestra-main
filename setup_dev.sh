#!/bin/bash
# setup_dev.sh - Quick development environment setup

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define cleanup function
cleanup() {
  if [ -f "$TEMP_KEY_FILE" ]; then
    rm -f "$TEMP_KEY_FILE"
    echo -e "${GREEN}🧹 Cleaned up temporary files${NC}"
  fi
}

# Register cleanup on exit
trap cleanup EXIT

# Print banner
echo -e "${GREEN}"
echo "=================================================="
echo "   Orchestra Development Environment Setup"
echo "=================================================="
echo -e "${NC}"

# Check for required environment variables
if [ -z "$GCP_MASTER_SERVICE_JSON" ]; then
  echo -e "${RED}Error: GCP_MASTER_SERVICE_JSON environment variable not set${NC}"
  exit 1
fi

# Step 1: Authentication
echo -e "${YELLOW}Step 1/5: Authenticating with GCP${NC}"
# Use more secure temporary file handling
TEMP_KEY_FILE=$(mktemp)
chmod 600 "$TEMP_KEY_FILE"
echo "$GCP_MASTER_SERVICE_JSON" > "$TEMP_KEY_FILE"
export GOOGLE_APPLICATION_CREDENTIALS="$TEMP_KEY_FILE"

if ! gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"; then
  echo -e "${RED}Authentication failed. Check your service account key.${NC}"
  exit 1
fi

gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"
echo -e "${GREEN}✓ Authentication successful${NC}"

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2/5: Installing dependencies${NC}"
if ! command -v poetry &> /dev/null; then
  echo "Installing Poetry..."
  if ! curl -sSL https://install.python-poetry.org | python3 -; then
    echo -e "${RED}Failed to install Poetry. Please install it manually.${NC}"
    echo -e "Visit https://python-poetry.org/docs/#installation for instructions."
    exit 1
  fi
fi

if ! poetry --version; then
  echo -e "${RED}Poetry installation failed or not in PATH.${NC}"
  exit 1
fi

if ! poetry install; then
  echo -e "${RED}Failed to install dependencies.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Set up environment variables
echo -e "${YELLOW}Step 3/5: Setting up environment variables${NC}"
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
  echo -e "${YELLOW}Warning: .env file already exists. Creating backup.${NC}"
  cp "$ENV_FILE" "${ENV_FILE}.bak"
fi

cat > "$ENV_FILE" << EOL
PROJECT_ID=$PROJECT_ID
REGION=$REGION
GOOGLE_APPLICATION_CREDENTIALS=$TEMP_KEY_FILE
EOL
echo -e "${GREEN}✓ Environment variables set up${NC}"

# Step 4: Enable required APIs
echo -e "${YELLOW}Step 4/5: Enabling required APIs${NC}"
if ! gcloud services enable compute.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  vpcaccess.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com; then
  
  echo -e "${RED}Failed to enable some APIs. Check permissions and try again.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ APIs enabled${NC}"

# Step 5: Set up local development server
echo -e "${YELLOW}Step 5/5: Setting up local development server${NC}"
# Make scripts executable
if [ -f "direct_auth.sh" ] && [ -f "deploy_all.sh" ]; then
  chmod +x direct_auth.sh deploy_all.sh
  echo -e "${GREEN}✓ Scripts made executable${NC}"
else
  echo -e "${RED}Warning: Some scripts not found. Check your directory structure.${NC}"
fi

echo -e "${GREEN}✓ Development environment ready!${NC}"
echo -e "Run ${YELLOW}poetry run uvicorn app_performance:app --reload${NC} to start the server"

echo -e "${GREEN}"
echo "=================================================="
echo "   Setup Complete!"
echo "=================================================="
echo -e "${NC}"
echo -e "Next steps:"
echo -e "1. Run ${YELLOW}./direct_auth.sh${NC} to authenticate with GCP"
echo -e "2. Run ${YELLOW}poetry run uvicorn app_performance:app --reload${NC} to start the local server"
echo -e "3. Run ${YELLOW}./deploy_all.sh${NC} to deploy to Cloud Run"