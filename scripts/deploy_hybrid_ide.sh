#!/bin/bash
# Hybrid IDE Deployment Script for AGI Baby Cherry Project
# This script automates the deployment of the optimized Hybrid IDE configuration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}========================================================"
echo "AGI Baby Cherry - Hybrid IDE Deployment Script"
echo -e "========================================================${NC}"
echo "Date: $(date)"
echo

# Validate environment
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    echo "Please install Terraform before running this script"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: Google Cloud SDK is not installed${NC}"
    echo "Please install gcloud before running this script"
    exit 1
fi

# Check gcloud auth
echo -e "${YELLOW}Checking gcloud authentication...${NC}"
gcloud auth list --filter=status:ACTIVE --format="value(account)" || {
    echo -e "${RED}Error: No active gcloud account found${NC}"
    echo "Please run 'gcloud auth login' first"
    exit 1
}

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
echo -e "${GREEN}Using Google Cloud project: ${PROJECT_ID}${NC}"

# Validate we're in the right directory
if [[ ! -f "infra/cloud_workstation_config.tf" || ! -f "infra/monitoring_config.tf" ]]; then
    echo -e "${RED}Error: Required Terraform files not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Create deployment log directory
LOG_DIR="deployment_logs/$(date +%Y%m%d_%H%M%S)"
mkdir -p "${LOG_DIR}"
echo -e "${GREEN}Deployment logs will be saved to: ${LOG_DIR}${NC}"

# Ask for confirmation
echo
echo -e "${YELLOW}This script will deploy the Hybrid IDE setup with the following components:${NC}"
echo "- Cloud Workstation configuration with n2d-standard-32 machine"
echo "- 2x NVIDIA Tesla T4 GPUs"
echo "- 1TB persistent storage"
echo "- Monitoring configuration with alerting"
echo "- Gemini Code Assist setup"
echo
read -p "Do you want to proceed with the deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled by user${NC}"
    exit 0
fi

# Deploy Terraform infrastructure
echo
echo -e "${BLUE}========================================================${NC}"
echo -e "${GREEN}Step 1: Deploying Terraform infrastructure${NC}"
echo -e "${BLUE}========================================================${NC}"

echo "Initializing Terraform..."
terraform init > "${LOG_DIR}/terraform_init.log" 2>&1 || {
    echo -e "${RED}Error: Terraform initialization failed${NC}"
    echo "Check the logs at ${LOG_DIR}/terraform_init.log"
    exit 1
}

echo "Running Terraform plan..."
terraform plan -out=tfplan > "${LOG_DIR}/terraform_plan.log" 2>&1 || {
    echo -e "${RED}Error: Terraform plan failed${NC}"
    echo "Check the logs at ${LOG_DIR}/terraform_plan.log"
    exit 1
}

echo "Applying Terraform configuration..."
terraform apply -auto-approve tfplan > "${LOG_DIR}/terraform_apply.log" 2>&1 || {
    echo -e "${RED}Error: Terraform apply failed${NC}"
    echo "Check the logs at ${LOG_DIR}/terraform_apply.log"
    exit 1
}

echo -e "${GREEN}Terraform deployment successful!${NC}"

# Get workstation details
echo
echo -e "${BLUE}========================================================${NC}"
echo -e "${GREEN}Step 2: Collecting workstation information${NC}"
echo -e "${BLUE}========================================================${NC}"

WORKSTATION_INFO=$(terraform output -json workstation_details)
if [[ -z "${WORKSTATION_INFO}" ]]; then
    echo -e "${RED}Error: Failed to get workstation details from Terraform${NC}"
    echo "Check if the workstation was created successfully"
    exit 1
fi

echo "${WORKSTATION_INFO}" > "${LOG_DIR}/workstation_details.json"
echo -e "${GREEN}Workstation details saved to ${LOG_DIR}/workstation_details.json${NC}"

# Extract workstation name and cluster from the JSON output
WORKSTATION_CLUSTER=$(echo "${WORKSTATION_INFO}" | jq -r '.cluster.name')
# Get the first workstation from the list
WORKSTATION_NAME=$(echo "${WORKSTATION_INFO}" | jq -r '.workstations[0].name')
REGION=$(echo "${WORKSTATION_INFO}" | jq -r '.cluster.location')

echo "Workstation cluster: ${WORKSTATION_CLUSTER}"
echo "Workstation name: ${WORKSTATION_NAME}"
echo "Region: ${REGION}"

# Wait for workstation to be ready
echo
echo -e "${YELLOW}Waiting for workstation to be ready...${NC}"
echo "This might take a few minutes..."

# Poll for workstation state every 10 seconds
MAX_RETRIES=30
RETRY_COUNT=0
while true; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [[ ${RETRY_COUNT} -gt ${MAX_RETRIES} ]]; then
        echo -e "${RED}Error: Timed out waiting for workstation to be ready${NC}"
        exit 1
    fi
    
    STATUS=$(gcloud workstations get \
        --cluster=${WORKSTATION_CLUSTER} \
        --config=hybrid-ide-config \
        --project=${PROJECT_ID} \
        --region=${REGION} \
        --format="value(state)" \
        ${WORKSTATION_NAME} 2>/dev/null || echo "PENDING")
    
    echo "Current status: ${STATUS}"
    
    if [[ "${STATUS}" == "RUNNING" ]]; then
        echo -e "${GREEN}Workstation is ready!${NC}"
        break
    fi
    
    if [[ "${STATUS}" == "ERROR" ]]; then
        echo -e "${RED}Error: Workstation failed to start${NC}"
        exit 1
    fi
    
    echo "Waiting for workstation to be ready... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 10
done

# Deploy test scripts and configuration files
echo
echo -e "${BLUE}========================================================${NC}"
echo -e "${GREEN}Step 3: Deploying test scripts and configuration files${NC}"
echo -e "${BLUE}========================================================${NC}"

echo "Creating directories on workstation..."
gcloud workstations ssh ${WORKSTATION_NAME} \
    --cluster=${WORKSTATION_CLUSTER} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --command="mkdir -p ~/agent/tests ~/scripts" || {
    echo -e "${RED}Error: Failed to create directories on workstation${NC}"
    exit 1
}

echo "Copying IDE stress test script..."
gcloud workstations ssh ${WORKSTATION_NAME} \
    --cluster=${WORKSTATION_CLUSTER} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --command="cat > ~/agent/tests/ide_stress_test.py" < agent/tests/ide_stress_test.py || {
    echo -e "${RED}Error: Failed to copy IDE stress test script${NC}"
    exit 1
}

echo "Copying stress test runner script..."
gcloud workstations ssh ${WORKSTATION_NAME} \
    --cluster=${WORKSTATION_CLUSTER} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --command="cat > ~/scripts/run_ide_stress_test.sh" < scripts/run_ide_stress_test.sh || {
    echo -e "${RED}Error: Failed to copy stress test runner script${NC}"
    exit 1
}

echo "Making scripts executable..."
gcloud workstations ssh ${WORKSTATION_NAME} \
    --cluster=${WORKSTATION_CLUSTER} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --command="chmod +x ~/scripts/run_ide_stress_test.sh" || {
    echo -e "${RED}Error: Failed to make scripts executable${NC}"
    exit 1
}

echo "Copying Gemini Code Assist configuration..."
gcloud workstations ssh ${WORKSTATION_NAME} \
    --cluster=${WORKSTATION_CLUSTER} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --command="cat > ~/.gemini-code-assist.yaml" < .gemini-code-assist.yaml || {
    echo -e "${RED}Error: Failed to copy Gemini Code Assist configuration${NC}"
    exit 1
}

echo "Copying metrics upload script..."
gcloud workstations ssh ${WORKSTATION_NAME} \
    --cluster=${WORKSTATION_CLUSTER} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --command="cat > ~/scripts/upload_stress_test_metrics.py" < scripts/upload_stress_test_metrics.py || {
    echo -e "${RED}Error: Failed to copy metrics upload script${NC}"
    exit 1
}

gcloud workstations ssh ${WORKSTATION_NAME} \
    --cluster=${WORKSTATION_CLUSTER} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --command="chmod +x ~/scripts/upload_stress_test_metrics.py" || {
    echo -e "${RED}Error: Failed to make scripts executable${NC}"
    exit 1
}

echo -e "${GREEN}Files successfully deployed to workstation!${NC}"

# Run initial validation (optional)
echo
echo -e "${BLUE}========================================================${NC}"
echo -e "${GREEN}Step 4: Running initial validation (optional)${NC}"
echo -e "${BLUE}========================================================${NC}"

echo "Would you like to run a quick IDE stress test to validate the setup?"
echo "This will run a short 5-minute test with 8 threads."
read -p "Run validation test? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Running quick validation test...${NC}"
    echo "This will take about 5 minutes..."
    
    gcloud workstations ssh ${WORKSTATION_NAME} \
        --cluster=${WORKSTATION_CLUSTER} \
        --project=${PROJECT_ID} \
        --region=${REGION} \
        --command="cd ~ && python3 agent/tests/ide_stress_test.py --threads=8 --duration=300 --test-dir=/tmp/ide_stress_test" > "${LOG_DIR}/validation_test.log" 2>&1 || {
        echo -e "${RED}Warning: Validation test failed or was interrupted${NC}"
        echo "Check the logs at ${LOG_DIR}/validation_test.log"
    }
    
    echo -e "${GREEN}Validation test completed!${NC}"
else
    echo -e "${YELLOW}Skipping validation test${NC}"
fi

# Deployment complete
echo
echo -e "${BLUE}========================================================${NC}"
echo -e "${GREEN}Hybrid IDE Deployment Complete!${NC}"
echo -e "${BLUE}========================================================${NC}"
echo
echo -e "${GREEN}The following components have been deployed:${NC}"
echo "- Cloud Workstation with n2d-standard-32 machine and 2x T4 GPUs"
echo "- 1TB persistent storage for agent memory"
echo "- Monitoring configuration with dashboards and alerts"
echo "- IDE stress testing tools"
echo "- Gemini Code Assist configuration"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Access your workstation in the Google Cloud Console:"
echo "   https://console.cloud.google.com/workstations/list?project=${PROJECT_ID}"
echo
echo "2. Run a full IDE stress test on the workstation:"
echo "   gcloud workstations ssh ${WORKSTATION_NAME} --cluster=${WORKSTATION_CLUSTER} --project=${PROJECT_ID} --region=${REGION} --command=\"bash ~/scripts/run_ide_stress_test.sh\""
echo
echo "3. View the monitoring dashboards:"
echo "   https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
echo
echo "4. Review the full migration guide for more details:"
echo "   HYBRID_IDE_MIGRATION_GUIDE.md"
echo
echo -e "${GREEN}Deployment logs saved to: ${LOG_DIR}${NC}"
