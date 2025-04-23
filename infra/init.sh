#!/bin/bash
# Infrastructure Initialization Script for Orchestra
# This script bootstraps the GCP infrastructure for the Orchestra system
# It sets up:
# - GCS bucket for Terraform state
# - Cloud Build triggers
# - Artifact Registry repository
# - Vertex AI Agent
# - Terraform workspaces for environments

set -e

echo "=== Orchestra Infrastructure Initialization ==="

# Set variables
PROJECT_ID="agi-baby-cherry"
REGION="us-west2"
GCS_BUCKET="${PROJECT_ID}-terraform-state"
REPO_NAME="orchestra"
SERVICE_ACCOUNT="vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if GSA key file exists
if [ ! -f "/tmp/gsa-key.json" ]; then
  echo "Error: GCP service account key file not found at /tmp/gsa-key.json"
  echo "Please run the bootstrap commands first:"
  echo "echo \"\$GCP_API_KEY\" | base64 -d > /tmp/gsa-key.json"
  echo "gcloud auth activate-service-account --key-file=/tmp/gsa-key.json"
  exit 1
fi

# 1. Authenticate and set project
echo "=== 1. Configuring gcloud ==="
gcloud config set project ${PROJECT_ID}
gcloud config set run/region ${REGION}

# 2. Enable required APIs
echo "=== 2. Enabling required APIs ==="
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com

# 3. Create GCS bucket for Terraform state if it doesn't exist
echo "=== 3. Setting up Terraform state bucket ==="
if ! gsutil ls -b gs://${GCS_BUCKET} &>/dev/null; then
  echo "Creating GCS bucket for Terraform state..."
  gsutil mb -l ${REGION} gs://${GCS_BUCKET}
  gsutil versioning set on gs://${GCS_BUCKET}
else
  echo "Terraform state bucket already exists."
fi

# 4. Create Artifact Registry repository if it doesn't exist
echo "=== 4. Setting up Artifact Registry ==="
if ! gcloud artifacts repositories describe ${REPO_NAME} --location=${REGION} &>/dev/null; then
  echo "Creating Artifact Registry repository..."
  gcloud artifacts repositories create ${REPO_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Docker repository for Orchestra services"
else
  echo "Artifact Registry repository already exists."
fi

# 5. Set up Cloud Build triggers
echo "=== 5. Setting up Cloud Build triggers ==="

# Check if GitHub repository is connected
if ! gcloud beta builds repositories list 2>/dev/null | grep -q "ai-cherry/orchestra-main"; then
  echo "Connecting GitHub repository..."
  echo "Please follow manual instructions to connect your GitHub repo through the Google Cloud Console."
  echo "Visit: https://console.cloud.google.com/cloud-build/triggers/connect"
  read -p "Press enter to continue after connecting the repository..."
fi

# Create/update Cloud Build triggers for different environments
# Development trigger (on push to dev branch)
gcloud beta builds triggers create github \
  --name="orchestra-ci-dev" \
  --region=${REGION} \
  --repo-owner="ai-cherry" \
  --repo-name="orchestra-main" \
  --branch-pattern="^dev$" \
  --build-config="infra/cloudbuild.yaml" \
  --substitutions="_ENV=dev" \
  --description="Build and deploy to dev environment"

# Staging trigger (on push to staging branch)
gcloud beta builds triggers create github \
  --name="orchestra-ci-stage" \
  --region=${REGION} \
  --repo-owner="ai-cherry" \
  --repo-name="orchestra-main" \
  --branch-pattern="^staging$" \
  --build-config="infra/cloudbuild.yaml" \
  --substitutions="_ENV=stage" \
  --description="Build and deploy to staging environment"

# Production trigger (on push to main branch)
gcloud beta builds triggers create github \
  --name="orchestra-ci-prod" \
  --region=${REGION} \
  --repo-owner="ai-cherry" \
  --repo-name="orchestra-main" \
  --branch-pattern="^main$" \
  --build-config="infra/cloudbuild.yaml" \
  --substitutions="_ENV=prod" \
  --description="Build and deploy to production environment"

# 6. Create Secret Manager secrets if they don't exist
echo "=== 6. Setting up Secret Manager ==="
if ! gcloud secrets describe openrouter &>/dev/null; then
  echo "Creating OpenRouter API key secret..."
  gcloud secrets create openrouter \
    --replication-policy="automatic"
  
  # Prompt for the API key to store
  read -sp "Enter OpenRouter API key: " OPENROUTER_KEY
  echo
  echo $OPENROUTER_KEY | gcloud secrets versions add openrouter --data-file=-
  echo "Secret 'openrouter' created."
else
  echo "Secret 'openrouter' already exists."
fi

if ! gcloud secrets describe gcp-service-account &>/dev/null; then
  echo "Creating GCP service account key secret for CI/CD..."
  gcloud secrets create gcp-service-account \
    --replication-policy="automatic"
  
  # Use the existing GSA key
  cat /tmp/gsa-key.json | gcloud secrets versions add gcp-service-account --data-file=-
  echo "Secret 'gcp-service-account' created."
else
  echo "Secret 'gcp-service-account' already exists."
fi

# 7. Configure IAM roles for the service account
echo "=== 7. Configuring IAM permissions ==="
# Grant necessary roles to the service account
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.admin"

# 8. Initialize Terraform
echo "=== 8. Initializing Terraform ==="
cd "$(dirname "$0")"  # Navigate to script directory

# Initialize Terraform
terraform init -backend-config="bucket=${GCS_BUCKET}"

# Create workspaces for each environment
echo "Creating Terraform workspaces..."
if ! terraform workspace list | grep -q "dev"; then
  terraform workspace new dev
else
  echo "Workspace 'dev' already exists."
fi

if ! terraform workspace list | grep -q "stage"; then
  terraform workspace new stage
else
  echo "Workspace 'stage' already exists."
fi

if ! terraform workspace list | grep -q "prod"; then
  terraform workspace new prod
else
  echo "Workspace 'prod' already exists."
fi

# Switch back to dev workspace
terraform workspace select dev

# 9. Initialize Vertex AI Agent (if specified)
echo "=== 9. Setting up Vertex AI Agent ==="
read -p "Do you want to initialize a Vertex AI DevOps Agent? (y/n): " SETUP_VERTEX
if [[ "$SETUP_VERTEX" == "y" ]]; then
  # Create a Python script to initialize the agent and execute it
  cat > setup_vertex_agent.py << 'EOF'
import vertexai
import google.cloud.aiplatform as aiplatform
from google.cloud import secretmanager

# Initialize Vertex AI
vertexai.init(project="agi-baby-cherry", location="us-west2")

# Create or update the agent
agent = vertexai.preview.agent_builder.Agent.create(
    display_name="DevOps Bot",
    description="Executes gcloud & Terraform commands to manage Orchestra infrastructure."
)

print(f"Agent created with name: {agent.display_name}")
print(f"Agent ID: {agent.id}")
EOF

  # Execute the Python script
  python setup_vertex_agent.py
else
  echo "Skipping Vertex AI Agent setup."
fi

echo "=== Infrastructure initialization complete ==="
echo
echo "Next steps:"
echo "1. Run Terraform to create resources for each environment:"
echo "   terraform workspace select dev && terraform apply -var='env=dev'"
echo "   terraform workspace select stage && terraform apply -var='env=stage'"
echo "   terraform workspace select prod && terraform apply -var='env=prod'"
echo
echo "2. Set up branch protection rules in your GitHub repository"
echo
echo "3. Start developing by pushing to the dev branch"
