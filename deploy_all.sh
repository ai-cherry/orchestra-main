#!/bin/bash
# deploy_all.sh - One-command deployment for Orchestra

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
ENV="dev"

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

# Handle errors
handle_error() {
  echo -e "${RED}Error occurred at line $1${NC}"
  exit 1
}

trap 'handle_error $LINENO' ERR

# Print banner
echo -e "${GREEN}"
echo "=================================================="
echo "   Orchestra One-Command Deployment"
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

# Step 2: Enable APIs
echo -e "${YELLOW}Step 2/5: Enabling required APIs${NC}"
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

# Step 3: Deploy infrastructure with Terraform
echo -e "${YELLOW}Step 3/5: Deploying infrastructure with Terraform${NC}"
if [ ! -d "infra/simplified-terraform" ]; then
  echo -e "${RED}Error: Terraform directory not found at infra/simplified-terraform${NC}"
  exit 1
fi

cd infra/simplified-terraform

# Initialize Terraform
if ! terraform init; then
  echo -e "${RED}Terraform initialization failed${NC}"
  cd ../..
  exit 1
fi

# Apply Terraform configuration
if ! terraform apply -auto-approve -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="env=$ENV"; then
  echo -e "${RED}Terraform apply failed${NC}"
  cd ../..
  exit 1
fi

# Get outputs
echo -e "${YELLOW}Getting Terraform outputs...${NC}"
REDIS_HOST=$(terraform output -raw redis_host 2>/dev/null || echo "redis-host-not-found")
REDIS_PORT=$(terraform output -raw redis_port 2>/dev/null || echo "6379")
SERVICE_ACCOUNT=$(terraform output -raw service_account_email 2>/dev/null || echo "service-account-not-found")
POSTGRES_CONNECTION_NAME=$(terraform output -raw postgres_connection_name 2>/dev/null || echo "postgres-connection-not-found")
POSTGRES_DB=$(terraform output -raw postgres_database 2>/dev/null || echo "phidata_memory")
POSTGRES_USER=$(terraform output -raw postgres_user 2>/dev/null || echo "phidata_user")

# Validate outputs
if [[ "$REDIS_HOST" == "redis-host-not-found" || "$SERVICE_ACCOUNT" == "service-account-not-found" ]]; then
  echo -e "${YELLOW}Warning: Some Terraform outputs were not found. Deployment may fail.${NC}"
fi

cd ../..
echo -e "${GREEN}✓ Infrastructure deployed${NC}"

# Step 4: Build and push Docker image
echo -e "${YELLOW}Step 4/5: Building and pushing Docker image${NC}"
IMAGE_NAME="gcr.io/$PROJECT_ID/orchestra-api:latest"

# Build the image
if ! gcloud builds submit --tag "$IMAGE_NAME" .; then
  echo -e "${RED}Failed to build and push Docker image${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Docker image built and pushed${NC}"

# Step 5: Deploy to Cloud Run
echo -e "${YELLOW}Step 5/5: Deploying to Cloud Run${NC}"
if ! gcloud run deploy orchestra-api \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --service-account "$SERVICE_ACCOUNT" \
  --set-env-vars="REDIS_HOST=$REDIS_HOST,REDIS_PORT=$REDIS_PORT,POSTGRES_CONNECTION_NAME=$POSTGRES_CONNECTION_NAME,POSTGRES_DB=$POSTGRES_DB,POSTGRES_USER=$POSTGRES_USER" \
  --set-secrets="REDIS_PASSWORD=redis-auth-$ENV:latest,POSTGRES_PASSWORD=postgres-password-$ENV:latest" \
  --allow-unauthenticated; then
  
  echo -e "${RED}Failed to deploy to Cloud Run${NC}"
  exit 1
fi

echo -e "${GREEN}"
echo "=================================================="
echo "   Deployment Complete!"
echo "=================================================="
echo -e "${NC}"

# Get the deployed service URL
SERVICE_URL=$(gcloud run services describe orchestra-api --platform managed --region "$REGION" --format="value(status.url)")
if [ -n "$SERVICE_URL" ]; then
  echo -e "Service URL: ${GREEN}$SERVICE_URL${NC}"
  
  # Validate deployment
  echo -e "${YELLOW}Validating deployment...${NC}"
  if curl -s "$SERVICE_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Service health check passed${NC}"
  else
    echo -e "${YELLOW}Warning: Service health check failed or not available${NC}"
  fi
else
  echo -e "${YELLOW}Warning: Could not retrieve service URL${NC}"
fi