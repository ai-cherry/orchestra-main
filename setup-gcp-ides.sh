#!/bin/bash

# Simplified script to provision Google Cloud Workstations and Vertex AI Workbench instances
# Created: 5/7/2025
# Updated: 5/8/2025 - Simplified for easier use

# Load environment variables from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/load_env.sh"

# ============================
# CONFIGURATION - Using environment variables with fallbacks
# ============================

# GCP Project Configuration
PROJECT_ID=$(get_config GCP_PROJECT_ID "cherry-ai-project")
LOCATION=$(get_config GCP_REGION "us-central1")
ZONE=$(get_config GCP_ZONE "us-central1-a")
SERVICE_ACCOUNT=$(get_config GCP_SERVICE_ACCOUNT "default")

# Instance Configuration
WORKSTATION_CONFIG=$(get_config WORKSTATION_CONFIG "cherry-workstation-config")
WORKSTATION_NAME=$(get_config WORKSTATION_NAME "cherry-workstation")
NOTEBOOK_NAME=$(get_config NOTEBOOK_NAME "cherry-notebook")
WORKSTATION_MACHINE_TYPE=$(get_config WORKSTATION_MACHINE_TYPE "e2-standard-4")
NOTEBOOK_MACHINE_TYPE=$(get_config NOTEBOOK_MACHINE_TYPE "n1-standard-4")

# Repository Configuration
REPO_URL=$(get_config REPO_URL "https://github.com/ai-cherry/orchestra-main.git")

# ============================
# SCRIPT EXECUTION
# ============================

echo "Starting GCP IDE provisioning for project: ${PROJECT_ID}"
print_config

# Simplified: Always use public GitHub URL
REPO_CLONE_URL="${REPO_URL}"
echo "Using public GitHub URL"

# Check if required APIs are enabled
echo "Checking if required APIs are enabled..."
for API in workstations.googleapis.com notebooks.googleapis.com; do
  if ! gcloud services list --enabled --project=${PROJECT_ID} --filter="name:${API}" | grep -q ${API}; then
    echo "Enabling ${API}..."
    gcloud services enable ${API} --project=${PROJECT_ID} || echo "Warning: Could not enable ${API}, but continuing anyway"
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
  --startup-script="${WORKSTATION_STARTUP_SCRIPT}" || echo "Warning: Could not create workstation config, but continuing anyway"

# Create Cloud Workstation instance
echo "Creating Cloud Workstation instance: ${WORKSTATION_NAME}"
gcloud beta workstations create ${WORKSTATION_NAME} \
  --config=${WORKSTATION_CONFIG} \
  --project=${PROJECT_ID} \
  --location=${LOCATION} || echo "Warning: Could not create workstation instance, but continuing anyway"

# Create Vertex AI Workbench notebook
echo "Creating Vertex AI Workbench notebook: ${NOTEBOOK_NAME}"
gcloud notebooks instances create ${NOTEBOOK_NAME} \
  --project=${PROJECT_ID} \
  --location=${ZONE} \
  --vm-image-project=deeplearning-platform-release \
  --vm-image-family=common-cpu \
  --machine-type=${NOTEBOOK_MACHINE_TYPE} \
  --service-account=${SERVICE_ACCOUNT} \
  --metadata=startup-script="${NOTEBOOK_STARTUP_SCRIPT}" || echo "Warning: Could not create notebook instance, but continuing anyway"

echo "GCP IDE provisioning completed!"
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
    --quiet || echo "Warning: Could not delete notebook instance"
  
  # Delete Cloud Workstation instance
  echo "Deleting Cloud Workstation instance: ${WORKSTATION_NAME}"
  gcloud beta workstations delete ${WORKSTATION_NAME} \
    --config=${WORKSTATION_CONFIG} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --quiet || echo "Warning: Could not delete workstation instance"
  
  # Delete Cloud Workstation config
  echo "Deleting Cloud Workstation config: ${WORKSTATION_CONFIG}"
  gcloud beta workstations configs delete ${WORKSTATION_CONFIG} \
    --project=${PROJECT_ID} \
    --location=${LOCATION} \
    --quiet || echo "Warning: Could not delete workstation config"
  
  echo "Cleanup completed."
fi
