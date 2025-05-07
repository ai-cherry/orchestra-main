#!/bin/bash

# Enhanced script to provision Google Cloud Workstations and Vertex AI Workbench instances
# Created: 5/7/2025

# Exit immediately if a command exits with a non-zero status
set -e

# ============================
# CUSTOMIZATION SECTION - Modify these parameters as needed
# ============================

# GCP Project Configuration
PROJECT_ID="cherry-ai-project"                                               # Your GCP project ID
LOCATION="us-central1"                                                       # Region for Cloud Workstation deployment
ZONE="us-central1-a"                                                         # Zone for Vertex AI Workbench deployment
SERVICE_ACCOUNT="orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"  # Service account to use

# Instance Configuration
WORKSTATION_CONFIG="cherry-workstation-config"                               # Name for your Cloud Workstation configuration
WORKSTATION_NAME="cherry-workstation"                                        # Name for your Cloud Workstation instance
NOTEBOOK_NAME="cherry-notebook"                                              # Name for your Vertex AI Workbench notebook
WORKSTATION_MACHINE_TYPE="e2-standard-4"                                     # Machine type for Cloud Workstation
NOTEBOOK_MACHINE_TYPE="n1-standard-4"                                        # Machine type for Vertex AI Workbench

# Repository Configuration
REPO_URL="https://github.com/ai-cherry/orchestra-main.git"                   # Your GitHub repository URL
GITHUB_TOKEN=""                                                              # Optional: Personal access token for private repos

# ============================
# SCRIPT EXECUTION - No need to modify below this line unless you're customizing the script
# ============================

echo "Starting GCP IDE provisioning for project: ${PROJECT_ID}"

# Configure git clone command based on whether a token is provided
REPO_CLONE_URL="${REPO_URL}"
if [ -n "${GITHUB_TOKEN}" ]; then
    # Extract repo parts to build authenticated URL
    REPO_HOST=$(echo "${REPO_URL}" | sed -E 's|https://([^/]+)/.*|\1|')
    REPO_PATH=$(echo "${REPO_URL}" | sed -E 's|https://[^/]+/(.*)|\\1|')
    REPO_CLONE_URL="https://${GITHUB_TOKEN}@${REPO_HOST}/${REPO_PATH}"
    echo "Using authenticated GitHub URL"
else
    echo "Using public GitHub URL - if your repository is private, please provide a GITHUB_TOKEN"
fi

# Verify that the service account exists and has proper permissions
echo "Verifying service account permissions..."
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project=${PROJECT_ID} &>/dev/null; then
  echo "ERROR: Service account ${SERVICE_ACCOUNT} does not exist in project ${PROJECT_ID}"
  exit 1
fi

echo "Checking service account permissions..."
gcloud projects get-iam-policy ${PROJECT_ID} --format="table(bindings.role,bindings.members)" | grep ${SERVICE_ACCOUNT} || {
  echo "WARNING: Service account ${SERVICE_ACCOUNT} may not have sufficient permissions in the project."
  echo "Continuing anyway, but provisioning might fail."
}

# Check if required APIs are enabled
echo "Checking if required APIs are enabled..."
for API in workstations.googleapis.com notebooks.googleapis.com; do
  if ! gcloud services list --enabled --project=${PROJECT_ID} --filter="name:${API}" | grep -q ${API}; then
    echo "Enabling ${API}..."
    gcloud services enable ${API} --project=${PROJECT_ID}
  fi
done

# Prepare startup scripts with proper escaping for command-line arguments
WORKSTATION_STARTUP_SCRIPT="#!/bin/bash\\ngit clone ${REPO_CLONE_URL} /home/user/my-repo"
NOTEBOOK_STARTUP_SCRIPT="#!/bin/bash\\ngit clone ${REPO_CLONE_URL} /home/jupyter/my-repo"

# Create Cloud Workstation config
echo "Creating Cloud Workstation config: ${WORKSTATION_CONFIG}"
gcloud beta workstations configs create ${WORKSTATION_CONFIG} \
  --project=${PROJECT_ID} \
  --location=${LOCATION} \
  --service-account=${SERVICE_ACCOUNT} \
  --machine-type=${WORKSTATION_MACHINE_TYPE} \
  --startup-script="${WORKSTATION_STARTUP_SCRIPT}"

# Create Cloud Workstation instance
echo "Creating Cloud Workstation instance: ${WORKSTATION_NAME}"
gcloud beta workstations create ${WORKSTATION_NAME} \
  --config=${WORKSTATION_CONFIG} \
  --project=${PROJECT_ID} \
  --location=${LOCATION}

# Create Vertex AI Workbench notebook
echo "Creating Vertex AI Workbench notebook: ${NOTEBOOK_NAME}"
gcloud notebooks instances create ${NOTEBOOK_NAME} \
  --project=${PROJECT_ID} \
  --location=${ZONE} \
  --vm-image-project=deeplearning-platform-release \
  --vm-image-family=common-cpu \
  --machine-type=${NOTEBOOK_MACHINE_TYPE} \
  --service-account=${SERVICE_ACCOUNT} \
  --metadata=startup-script="${NOTEBOOK_STARTUP_SCRIPT}"

echo "GCP IDE provisioning completed successfully!"
echo "Cloud Workstation: ${WORKSTATION_NAME}"
echo "Vertex AI Notebook: ${NOTEBOOK_NAME}"

# Optional: Display URLs to access the created resources
echo ""
echo "Access your resources at:"
echo "Cloud Workstations: https://console.cloud.google.com/workstations/list?project=${PROJECT_ID}"
echo "Vertex AI Workbench: https://console.cloud.google.com/vertex-ai/workbench/list/instances?project=${PROJECT_ID}"

# Resource cleanup (commented out by default)
# To use, uncomment and run with: ./setup-gcp-ides.sh cleanup
if [ "$1" = "cleanup" ]; then
  echo "Cleaning up resources..."
  
  # Delete Vertex AI Workbench notebook
  echo "Deleting Vertex AI Workbench notebook: ${NOTEBOOK_NAME}"
  gcloud notebooks instances delete ${NOTEBOOK_NAME} \
    --project=${PROJECT_ID} \
    --location=${ZONE} \
    --quiet
  
  # Delete Cloud Workstation instance
  echo "Deleting Cloud Workstation instance: ${WORKSTATION_NAME}"
  gcloud beta workstations delete ${WORKSTATION_NAME} \
    --config=${WORKSTATION_CONFIG} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --quiet
  
  # Delete Cloud Workstation config
  echo "Deleting Cloud Workstation config: ${WORKSTATION_CONFIG}"
  gcloud beta workstations configs delete ${WORKSTATION_CONFIG} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --quiet
  
  echo "Cleanup completed."
fi
