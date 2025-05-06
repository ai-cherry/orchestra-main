#!/bin/bash
# Script to deploy the Figma webhook handler to Google Cloud Run
# This provides a secure HTTPS endpoint for Figma webhooks in production

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo -e "${RED}Error: Google Cloud SDK (gcloud) is not installed${NC}"
  echo "Please install it: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Check if user is authenticated with GCP
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
  echo -e "${RED}Error: Not authenticated with Google Cloud SDK${NC}"
  echo "Please run: gcloud auth login"
  exit 1
fi

# Defaults
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="figma-webhook-handler"
MEMORY="256Mi"
CPU="1"
CONCURRENCY="80"
MIN_INSTANCES="0"
MAX_INSTANCES="3"
CONTAINER_PORT="3000"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --service-name)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --min-instances)
      MIN_INSTANCES="$2"
      shift 2
      ;;
    --max-instances)
      MAX_INSTANCES="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Validate inputs
if [ -z "$PROJECT_ID" ]; then
  echo -e "${RED}Error: Project ID is required${NC}"
  echo "Please specify with --project or set default project with: gcloud config set project PROJECT_ID"
  exit 1
fi

echo -e "${BLUE}=== Deploying Figma Webhook Handler to Cloud Run ===${NC}"
echo -e "Project: ${GREEN}$PROJECT_ID${NC}"
echo -e "Region: ${GREEN}$REGION${NC}"
echo -e "Service: ${GREEN}$SERVICE_NAME${NC}"

# Create a Dockerfile if it doesn't exist
if [ ! -f "scripts/Dockerfile" ]; then
  echo -e "${YELLOW}Creating Dockerfile...${NC}"
  cat > scripts/Dockerfile << EOL
FROM node:18-slim

WORKDIR /app

# Copy package.json and package-lock.json
COPY scripts/package.json scripts/package-lock.json* ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY scripts/figma_webhook_handler.js ./
COPY .env* ./

# Create logs directory
RUN mkdir -p logs

# Expose port 3000
EXPOSE 3000

# Set environment variables
ENV PORT=3000
ENV NODE_ENV=production

# Start the application
CMD ["node", "figma_webhook_handler.js"]
EOL
  echo -e "${GREEN}Dockerfile created.${NC}"
fi

# Check if Secret Manager API is enabled
if ! gcloud services list --enabled --filter="name:secretmanager.googleapis.com" --project="$PROJECT_ID" | grep -q "secretmanager.googleapis.com"; then
  echo -e "${YELLOW}Enabling Secret Manager API...${NC}"
  gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"
fi

# Check if Cloud Run API is enabled
if ! gcloud services list --enabled --filter="name:run.googleapis.com" --project="$PROJECT_ID" | grep -q "run.googleapis.com"; then
  echo -e "${YELLOW}Enabling Cloud Run API...${NC}"
  gcloud services enable run.googleapis.com --project="$PROJECT_ID"
fi

# Create secrets in Secret Manager if they don't exist
echo -e "${BLUE}Setting up secrets in Secret Manager...${NC}"

# Function to create or update a secret
create_or_update_secret() {
  local secret_name="$1"
  local env_var_name="$2"
  local prompt_text="$3"
  
  # Check if the secret exists
  if ! gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &> /dev/null; then
    echo -e "${YELLOW}Creating $secret_name secret...${NC}"
    
    # If environment variable doesn't exist, prompt for value
    if [ -z "${!env_var_name}" ]; then
      read -sp "$prompt_text: " secret_value
      echo
    else
      secret_value="${!env_var_name}"
    fi
    
    # Create the secret
    echo -n "$secret_value" | gcloud secrets create "$secret_name" \
      --data-file=- \
      --replication-policy="automatic" \
      --project="$PROJECT_ID"
  else
    echo -e "${GREEN}Secret $secret_name already exists.${NC}"
  fi
}

# Create secrets for webhook handler
create_or_update_secret "figma-webhook-secret" "FIGMA_WEBHOOK_SECRET" "Enter Figma webhook secret"
create_or_update_secret "github-pat" "GITHUB_PAT" "Enter GitHub Personal Access Token"
create_or_update_secret "github-owner" "GITHUB_OWNER" "Enter GitHub owner (username or organization)"
create_or_update_secret "github-repo" "GITHUB_REPO" "Enter GitHub repository name"

# Build and deploy to Cloud Run
echo -e "${BLUE}Building and deploying to Cloud Run...${NC}"

# Get the current directory
CURRENT_DIR=$(pwd)

# Navigate to the project root directory
cd "$CURRENT_DIR"

# Build and deploy using gcloud
echo -e "${BLUE}Deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --dockerfile=scripts/Dockerfile \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory="$MEMORY" \
  --cpu="$CPU" \
  --concurrency="$CONCURRENCY" \
  --min-instances="$MIN_INSTANCES" \
  --max-instances="$MAX_INSTANCES" \
  --port="$CONTAINER_PORT" \
  --set-secrets="FIGMA_WEBHOOK_SECRET=figma-webhook-secret:latest,GITHUB_PAT=github-pat:latest,GITHUB_OWNER=github-owner:latest,GITHUB_REPO=github-repo:latest" \
  --project="$PROJECT_ID"

# Get the deployed service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)")

echo -e "\n${GREEN}=== Deployment Complete! ===${NC}"
echo -e "Figma webhook handler is now running at: ${GREEN}$SERVICE_URL${NC}"
echo -e "Webhook endpoint: ${GREEN}$SERVICE_URL/figma-webhook${NC}"
echo -e "Health check endpoint: ${GREEN}$SERVICE_URL/health${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Update your Figma webhook configuration with the new endpoint URL"
echo -e "   ${GREEN}$SERVICE_URL/figma-webhook${NC}"
echo -e "2. Test the webhook using the test script:"
echo -e "   ${GREEN}node scripts/test_figma_webhook.js --url=$SERVICE_URL/figma-webhook${NC}"
echo -e "3. Monitor your webhook logs in the Google Cloud Console"

echo -e "\n${BLUE}=== Deployment Successful ===${NC}"
