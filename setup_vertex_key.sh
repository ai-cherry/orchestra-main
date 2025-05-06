#!/bin/bash
# setup_vertex_key.sh - Set up the Vertex agent key for deployment
#
# This script handles the creation and configuration of the vertex-agent
# service account key required for deployment to GCP.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Setting up Vertex Agent Service Account Key        ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Create directories
mkdir -p /tmp/credentials

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Install Google Cloud SDK if not installed
if ! command_exists gcloud; then
  echo -e "${YELLOW}Google Cloud SDK not found. Installing using apt-get...${NC}"
  
  # Install Google Cloud SDK using apt
  echo -e "${YELLOW}Adding Google Cloud SDK repository...${NC}"
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
  
  echo -e "${YELLOW}Installing required packages...${NC}"
  sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates gnupg
  
  echo -e "${YELLOW}Adding Google Cloud public key...${NC}"
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
  
  echo -e "${YELLOW}Installing Google Cloud SDK...${NC}"
  sudo apt-get update && sudo apt-get install -y google-cloud-sdk
  
  echo -e "${GREEN}Google Cloud SDK installed successfully.${NC}"
else
  echo -e "${GREEN}Google Cloud SDK is already installed.${NC}"
fi

# Auth setup
echo -e "${YELLOW}Setting up GCP authentication...${NC}"

# Check if gcloud is already authenticated
auth_status=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
if [ -z "$auth_status" ]; then
  echo -e "${YELLOW}Not authenticated with gcloud. Initiating login...${NC}"
  gcloud auth login
else
  echo -e "${GREEN}Already authenticated as: $auth_status${NC}"
fi

# Set project
echo -e "${YELLOW}Setting GCP project to agi-baby-cherry...${NC}"
gcloud config set project agi-baby-cherry

# Create service account key
echo -e "${YELLOW}Setting up Vertex Agent service account key...${NC}"
echo -e "${BLUE}The vertex-agent service account has full permissions to GCP resources.${NC}"
echo -e "${BLUE}You have two options:${NC}"
echo "1. Create a new vertex-agent service account key"
echo "2. Use an existing key file"
read -p "Choose an option (1/2): " key_option

if [ "$key_option" == "1" ]; then
  echo -e "${YELLOW}Creating new service account key for vertex-agent...${NC}"
  
  # Check if service account exists
  sa_exists=$(gcloud iam service-accounts list --filter="email:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" --format="value(email)" 2>/dev/null || echo "")
  
  if [ -z "$sa_exists" ]; then
    echo -e "${YELLOW}Service account does not exist. Creating it now...${NC}"
    gcloud iam service-accounts create vertex-agent \
      --display-name="Vertex Agent Service Account" \
      --description="Service account for Orchestra deployment and Vertex AI operations"
    
    # Assign required roles
    echo -e "${YELLOW}Assigning necessary roles to the service account...${NC}"
    roles=(
      "roles/aiplatform.user"
      "roles/run.admin"
      "roles/storage.admin"
      "roles/firestore.admin"
      "roles/secretmanager.admin"
      "roles/redis.admin"
      "roles/artifactregistry.admin"
    )
    
    for role in "${roles[@]}"; do
      gcloud projects add-iam-policy-binding agi-baby-cherry \
        --member="serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com" \
        --role="$role"
    done
  else
    echo -e "${GREEN}Service account vertex-agent already exists.${NC}"
  fi
  
  # Create key
  gcloud iam service-accounts keys create /tmp/credentials/vertex-agent-key.json \
    --iam-account=vertex-agent@agi-baby-cherry.iam.gserviceaccount.com
  echo -e "${GREEN}New key created at /tmp/credentials/vertex-agent-key.json${NC}"
else
  echo -e "${YELLOW}Please provide the path to your existing vertex-agent key file:${NC}"
  read -p "Key file path: " existing_key_path
  
  if [ -f "$existing_key_path" ]; then
    cp "$existing_key_path" /tmp/credentials/vertex-agent-key.json
    echo -e "${GREEN}Key copied to /tmp/credentials/vertex-agent-key.json${NC}"
  else
    echo -e "${RED}Error: File not found at $existing_key_path${NC}"
    echo -e "${YELLOW}Please paste the contents of your key file below.${NC}"
    echo -e "${YELLOW}Press Ctrl+D when finished.${NC}"
    cat > /tmp/credentials/vertex-agent-key.json
    echo -e "${GREEN}Key saved to /tmp/credentials/vertex-agent-key.json${NC}"
  fi
fi

# Copy to the expected location
cp /tmp/credentials/vertex-agent-key.json /tmp/vertex-agent-key.json
chmod 600 /tmp/vertex-agent-key.json

# Set environment variables
echo -e "${YELLOW}Setting up environment variables...${NC}"
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json

# Add to shell profile for persistence
cat << EOF >> ~/.bashrc

# GCP Authentication for Orchestra
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
export GCP_PROJECT_ID=agi-baby-cherry
EOF

# Test authentication
echo -e "${YELLOW}Testing GCP authentication with the service account key...${NC}"

# Test using the key
if command_exists python; then
  python -c "
import json
from google.oauth2 import service_account
from google.cloud import storage

print('Loading service account key...')
key_path = '/tmp/vertex-agent-key.json'

with open(key_path, 'r') as f:
    key_data = json.load(f)
    print(f\"Loaded key for: {key_data.get('client_email')}\")
    print(f\"Project: {key_data.get('project_id')}\")

print('Creating credentials object...')
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

print('Testing GCS access...')
storage_client = storage.Client(credentials=credentials)
buckets = list(storage_client.list_buckets(max_results=5))
print(f'Successfully listed {len(buckets)} buckets')
for bucket in buckets:
    print(f' - {bucket.name}')

print('Authentication test successful!')
"
  auth_success=$?
  
  if [ $auth_success -eq 0 ]; then
    echo -e "${GREEN}Authentication successful! The vertex-agent key is working properly.${NC}"
  else
    echo -e "${RED}Authentication test failed. Please check the service account permissions.${NC}"
  fi
else
  echo -e "${YELLOW}Python not available to test authentication.${NC}"
  echo -e "${YELLOW}You can test authentication manually using:${NC}"
  echo -e "GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json gcloud auth application-default print-access-token"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Vertex Agent service account key is now set up at: /tmp/vertex-agent-key.json${NC}"
echo -e "${YELLOW}This key has full permissions to GCP resources and can be used for deployment.${NC}"
echo -e "${BLUE}======================================================${NC}"

echo -e "You can now run:"
echo -e "  ./verify_deployment_readiness.sh  (to check deployment readiness)"
echo -e "  ./deploy_to_cloud_run.sh prod     (to deploy to Cloud Run)"
