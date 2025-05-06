#!/bin/bash
# Setup Agent Infrastructure for AI Orchestra
# This script sets up the necessary GCP resources for the AI Orchestra agent system

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
REGION=${REGION:-"us-west4"}
ENVIRONMENT=${ENVIRONMENT:-"staging"}
TERRAFORM_STATE_BUCKET="${PROJECT_ID}-terraform-state"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${RED}Error: You are not logged in to gcloud. Please run 'gcloud auth login' first.${NC}"
    exit 1
fi

# Print configuration
echo -e "${BLUE}=== Configuration ===${NC}"
echo -e "Project ID: ${GREEN}${PROJECT_ID}${NC}"
echo -e "Region: ${GREEN}${REGION}${NC}"
echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "Terraform State Bucket: ${GREEN}${TERRAFORM_STATE_BUCKET}${NC}"
echo ""

# Confirm with user
read -p "Do you want to proceed with this configuration? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Setup cancelled.${NC}"
    exit 0
fi

# Set the project
echo -e "${BLUE}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${BLUE}Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    redis.googleapis.com \
    cloudtasks.googleapis.com \
    pubsub.googleapis.com \
    --project=${PROJECT_ID}

# Create Terraform state bucket if it doesn't exist
echo -e "${BLUE}Creating Terraform state bucket...${NC}"
if ! gsutil ls -b gs://${TERRAFORM_STATE_BUCKET} &> /dev/null; then
    gsutil mb -l ${REGION} gs://${TERRAFORM_STATE_BUCKET}
    gsutil versioning set on gs://${TERRAFORM_STATE_BUCKET}
    echo -e "${GREEN}Created Terraform state bucket: ${TERRAFORM_STATE_BUCKET}${NC}"
else
    echo -e "${YELLOW}Terraform state bucket already exists: ${TERRAFORM_STATE_BUCKET}${NC}"
fi

# Create service account for Terraform if it doesn't exist
SA_NAME="terraform-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo -e "${BLUE}Creating service account for Terraform...${NC}"
if ! gcloud iam service-accounts describe ${SA_EMAIL} &> /dev/null; then
    gcloud iam service-accounts create ${SA_NAME} \
        --display-name="Terraform Service Account" \
        --project=${PROJECT_ID}
    echo -e "${GREEN}Created service account: ${SA_EMAIL}${NC}"
else
    echo -e "${YELLOW}Service account already exists: ${SA_EMAIL}${NC}"
fi

# Grant necessary roles to the service account
echo -e "${BLUE}Granting necessary roles to the service account...${NC}"
for role in "roles/editor" "roles/secretmanager.admin" "roles/iam.serviceAccountAdmin"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${role}" \
        --condition=None
done

# Initialize Terraform
echo -e "${BLUE}Initializing Terraform...${NC}"
cd "$(dirname "$0")/../terraform"
terraform init -backend-config="bucket=${TERRAFORM_STATE_BUCKET}"

# Create Terraform variables file
echo -e "${BLUE}Creating Terraform variables file...${NC}"
cat > terraform.tfvars << EOL
project_id = "${PROJECT_ID}"
region = "${REGION}"
environment = "${ENVIRONMENT}"
EOL

# Plan Terraform changes
echo -e "${BLUE}Planning Terraform changes...${NC}"
terraform plan -var-file=terraform.tfvars -out=tfplan

# Ask user if they want to apply the changes
read -p "Do you want to apply these changes? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Terraform apply cancelled.${NC}"
    exit 0
fi

# Apply Terraform changes
echo -e "${BLUE}Applying Terraform changes...${NC}"
terraform apply -auto-approve tfplan

# Create secrets for LLM providers
echo -e "${BLUE}Creating secrets for LLM providers...${NC}"
for secret_id in "openai-api-key" "anthropic-api-key" "gemini-api-key"; do
    if ! gcloud secrets describe ${secret_id} --project=${PROJECT_ID} &> /dev/null; then
        echo -e "${GREEN}Creating secret: ${secret_id}${NC}"
        gcloud secrets create ${secret_id} --project=${PROJECT_ID}
    else
        echo -e "${YELLOW}Secret already exists: ${secret_id}${NC}"
    fi
done

# Prompt user to add secret values
echo -e "${BLUE}Please add your API keys to the secrets:${NC}"
echo -e "${YELLOW}For OpenAI:${NC} gcloud secrets versions add openai-api-key --data-file=-"
echo -e "${YELLOW}For Anthropic:${NC} gcloud secrets versions add anthropic-api-key --data-file=-"
echo -e "${YELLOW}For Gemini:${NC} gcloud secrets versions add gemini-api-key --data-file=-"

# Print outputs
echo -e "${BLUE}=== Setup Complete ===${NC}"
echo -e "${GREEN}Project ID:${NC} ${PROJECT_ID}"
echo -e "${GREEN}Region:${NC} ${REGION}"
echo -e "${GREEN}Environment:${NC} ${ENVIRONMENT}"
echo -e "${GREEN}Terraform State Bucket:${NC} ${TERRAFORM_STATE_BUCKET}"
echo -e "${GREEN}Service Account:${NC} ${SA_EMAIL}"

# Print next steps
echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "1. Add your API keys to the secrets"
echo -e "2. Deploy your application to Cloud Run"
echo -e "3. Configure your CI/CD pipeline"
echo -e "4. Set up monitoring and alerting"

echo -e "${GREEN}Setup completed successfully!${NC}"