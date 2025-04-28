#!/bin/bash
# Script to deploy and update the Phidata Agent UI service using Terraform

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}  Phidata Agent UI Deployment Script (Phase C)       ${NC}"
echo -e "${GREEN}=====================================================${NC}"

# Set default environment values
export ENV="dev"
export FIGMA_PAT="${FIGMA_PAT:-dummy-pat-for-testing}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker and try again.${NC}"
    exit 1
fi

echo -e "${YELLOW}Creating Terraform Docker container...${NC}"

# Create Dockerfile
cat > Dockerfile.terraform << EOF
FROM hashicorp/terraform:1.5.0

RUN apk add --no-cache bash curl jq python3

# Install Google Cloud SDK
RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz && \\
    tar -xf google-cloud-cli-linux-x86_64.tar.gz && \\
    ./google-cloud-sdk/install.sh --quiet && \\
    rm google-cloud-cli-linux-x86_64.tar.gz

ENV PATH=\$PATH:/google-cloud-sdk/bin

WORKDIR /workspace
EOF

# Build Docker image
echo -e "${YELLOW}Building Terraform Docker image...${NC}"
docker build -t terraform-orchestra -f Dockerfile.terraform .

# Set path to the terraform directory
TERRAFORM_DIR="infra/orchestra-terraform"

echo -e "${YELLOW}=== Running Terraform init ===${NC}"
docker run -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
  terraform-orchestra terraform init

echo -e "${YELLOW}=== Creating and selecting dev workspace ===${NC}"
docker run -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
  terraform-orchestra terraform workspace new dev || true
  
docker run -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
  terraform-orchestra terraform workspace select dev

echo -e "${YELLOW}=== Running Terraform plan for dev environment ===${NC}"
docker run -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
  -e FIGMA_PAT=${FIGMA_PAT} \
  terraform-orchestra terraform plan -var="env=dev" -target=google_cloud_run_v2_service.phidata_agent_ui

echo -e "${YELLOW}=== Applying Terraform changes (phidata-agent-ui only) ===${NC}"
docker run -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
  -e FIGMA_PAT=${FIGMA_PAT} \
  terraform-orchestra terraform apply -var="env=dev" -target=google_cloud_run_v2_service.phidata_agent_ui -auto-approve

echo -e "${YELLOW}=== Getting the Phidata Agent UI URL ===${NC}"
PHIDATA_UI_URL=$(docker run -v $(pwd):/workspace -w /workspace/${TERRAFORM_DIR} \
  terraform-orchestra terraform output -json service_urls | jq -r '.ui')

echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}  Phidata Agent UI Deployment Complete               ${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo -e "${YELLOW}Phidata Agent UI URL: ${NC}${PHIDATA_UI_URL}"

echo -e "\n${YELLOW}Instructions for Testing:${NC}"
echo -e "1. Access the Phidata Agent UI using the URL above"
echo -e "2. Send messages that trigger different agents/tools/LLMs"
echo -e "3. Verify that end-to-end interaction works correctly"
echo -e "4. Check that the backend API is properly connected"
echo -e "\n${YELLOW}Common test scenarios:${NC}"
echo -e "- Search for information (to test DuckDuckGo integration)"
echo -e "- Ask for mathematical calculations (to test Calculator tool)"
echo -e "- Request information from Wikipedia (if Wikipedia tool is configured)"
echo -e "- Test different LLM models if multiple are configured"

echo -e "\n${GREEN}=====================================================${NC}"
