#!/bin/bash
# Script to set up GCP Cloud Workstation and Vertex AI IDE for AI Orchestra project
# This script uses gcloud commands to create the necessary resources

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration variables
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
ZONE="${REGION}-a"
CLUSTER_NAME="ai-orchestra-cluster"
CONFIG_NAME="ai-orchestra-config"
WORKSTATION_NAME="ai-orchestra-workstation"
SERVICE_ACCOUNT_NAME="vertex-ai-admin"
MACHINE_TYPE="n2d-standard-16"
BOOT_DISK_SIZE="200"
NETWORK="default"
SUBNETWORK="default"

# Print header
echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   GCP CLOUD WORKSTATION AND VERTEX AI IDE SETUP   ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# Function to check if gcloud is installed and authenticated
check_gcloud() {
  echo -e "\n${YELLOW}Checking gcloud installation and authentication...${NC}"
  
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
  fi
  
  # Check if user is authenticated
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with gcloud. Please run 'gcloud auth login' first.${NC}"
    exit 1
  fi
  
  # Check if project exists and is accessible
  if ! gcloud projects describe "${PROJECT_ID}" &> /dev/null; then
    echo -e "${RED}Error: Project ${PROJECT_ID} does not exist or is not accessible.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}gcloud is properly configured.${NC}"
}

# Function to enable required APIs
enable_apis() {
  echo -e "\n${YELLOW}Enabling required APIs...${NC}"
  
  APIS=(
    "workstations.googleapis.com"
    "compute.googleapis.com"
    "aiplatform.googleapis.com"
    "storage.googleapis.com"
    "iam.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "secretmanager.googleapis.com"
  )
  
  for api in "${APIS[@]}"; do
    echo "Enabling $api..."
    gcloud services enable $api --project="${PROJECT_ID}"
  done
  
  echo -e "${GREEN}All required APIs have been enabled.${NC}"
}

# Function to create service account
create_service_account() {
  echo -e "\n${YELLOW}Creating service account for Cloud Workstation...${NC}"
  
  if gcloud iam service-accounts describe "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" --project="${PROJECT_ID}" &> /dev/null; then
    echo -e "${YELLOW}Service account already exists. Skipping creation.${NC}"
  else
    gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
      --display-name="Vertex AI Workstation Service Account" \
      --description="Service account for Cloud Workstations with Vertex AI access" \
      --project="${PROJECT_ID}"
    echo -e "${GREEN}Service account created successfully.${NC}"
  fi
  
  # Assign roles to the service account
  echo -e "\n${YELLOW}Assigning roles to service account...${NC}"
  
  ROLES=(
    "roles/aiplatform.user"
    "roles/storage.objectViewer"
    "roles/compute.viewer"
    "roles/workstations.user"
    "roles/secretmanager.secretAccessor"
  )
  
  for role in "${ROLES[@]}"; do
    echo "Assigning role $role..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
      --role="${role}" \
      --quiet
  done
  
  echo -e "${GREEN}Roles assigned successfully.${NC}"
}

# Function to create Cloud Workstation cluster
create_workstation_cluster() {
  echo -e "\n${YELLOW}Creating Cloud Workstation cluster...${NC}"
  
  if gcloud workstations clusters describe "${CLUSTER_NAME}" --project="${PROJECT_ID}" --location="${REGION}" &> /dev/null; then
    echo -e "${YELLOW}Workstation cluster already exists. Skipping creation.${NC}"
  else
    gcloud workstations clusters create "${CLUSTER_NAME}" \
      --project="${PROJECT_ID}" \
      --location="${REGION}" \
      --network="${NETWORK}" \
      --subnetwork="${SUBNETWORK}" \
      --labels="environment=prod,managed_by=script,project=ai-orchestra" \
      --private-cluster-config="enable-private-endpoint=true"
    echo -e "${GREEN}Workstation cluster created successfully.${NC}"
  fi
}

# Function to create Cloud Workstation configuration
create_workstation_config() {
  echo -e "\n${YELLOW}Creating Cloud Workstation configuration...${NC}"
  
  if gcloud workstations configs describe "${CONFIG_NAME}" --cluster="${CLUSTER_NAME}" --project="${PROJECT_ID}" --location="${REGION}" &> /dev/null; then
    echo -e "${YELLOW}Workstation configuration already exists. Skipping creation.${NC}"
  else
    # Create a temporary file for the startup script
    STARTUP_SCRIPT=$(mktemp)
    cat > "${STARTUP_SCRIPT}" << 'EOT'
#!/bin/bash
set -e

echo "Setting up AI Orchestra development environment..."

# Install JupyterLab
echo "Installing JupyterLab..."
pip3 install jupyterlab ipywidgets pandas matplotlib scikit-learn tensorflow
jupyter serverextension enable --py jupyterlab --sys-prefix

# Install Vertex AI SDK
echo "Installing Vertex AI SDK..."
pip3 install google-cloud-aiplatform

# Install Gemini SDK
echo "Installing Gemini SDK..."
pip3 install google-generativeai

# Install Poetry
echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

echo "AI Orchestra development environment setup complete!"
EOT
    
    gcloud workstations configs create "${CONFIG_NAME}" \
      --cluster="${CLUSTER_NAME}" \
      --project="${PROJECT_ID}" \
      --location="${REGION}" \
      --machine-type="${MACHINE_TYPE}" \
      --service-account="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
      --boot-disk-size="${BOOT_DISK_SIZE}GB" \
      --container-predefined-image="intellij-ultimate" \
      --container-command-file="${STARTUP_SCRIPT}" \
      --container-env="VERTEX_ENDPOINT=projects/${PROJECT_ID}/locations/${REGION}/endpoints/agent-core,GCP_PROJECT_ID=${PROJECT_ID},JUPYTER_PORT=8888" \
      --labels="environment=prod,managed_by=script,project=ai-orchestra" \
      --shielded-secure-boot \
      --shielded-vtpm \
      --shielded-integrity-monitoring
    
    # Clean up the temporary file
    rm "${STARTUP_SCRIPT}"
    
    echo -e "${GREEN}Workstation configuration created successfully.${NC}"
  fi
}

# Function to create Cloud Workstation
create_workstation() {
  echo -e "\n${YELLOW}Creating Cloud Workstation...${NC}"
  
  if gcloud workstations describe "${WORKSTATION_NAME}" --config="${CONFIG_NAME}" --cluster="${CLUSTER_NAME}" --project="${PROJECT_ID}" --location="${REGION}" &> /dev/null; then
    echo -e "${YELLOW}Workstation already exists. Skipping creation.${NC}"
  else
    gcloud workstations create "${WORKSTATION_NAME}" \
      --config="${CONFIG_NAME}" \
      --cluster="${CLUSTER_NAME}" \
      --project="${PROJECT_ID}" \
      --location="${REGION}" \
      --labels="environment=prod,managed_by=script,project=ai-orchestra"
    echo -e "${GREEN}Workstation created successfully.${NC}"
  fi
}

# Function to display workstation details
display_workstation_details() {
  echo -e "\n${YELLOW}Workstation Details:${NC}"
  
  WORKSTATION_URL=$(gcloud workstations describe "${WORKSTATION_NAME}" \
    --config="${CONFIG_NAME}" \
    --cluster="${CLUSTER_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --format="value(name)")
  
  echo -e "${BLUE}Workstation Name:${NC} ${WORKSTATION_NAME}"
  echo -e "${BLUE}Configuration:${NC} ${CONFIG_NAME}"
  echo -e "${BLUE}Cluster:${NC} ${CLUSTER_NAME}"
  echo -e "${BLUE}Region:${NC} ${REGION}"
  echo -e "${BLUE}URL:${NC} https://${REGION}.workstations.cloud.google.com/${PROJECT_ID}/${REGION}/${CLUSTER_NAME}/${CONFIG_NAME}/${WORKSTATION_NAME}"
}

# Main execution
check_gcloud
enable_apis
create_service_account
create_workstation_cluster
create_workstation_config
create_workstation
display_workstation_details

echo -e "\n${GREEN}${BOLD}GCP Cloud Workstation and Vertex AI IDE setup completed successfully!${NC}"