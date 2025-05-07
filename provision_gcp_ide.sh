#!/bin/bash

# Enhanced script to provision Google Cloud Workstations and Vertex AI Workbench instances
# Created: 5/7/2025

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration variables
PROJECT_ID="cherry-ai-project"
LOCATION="us-central1"
ZONE="us-central1-a"
SERVICE_ACCOUNT="orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
REPO_URL="https://github.com/ai-cherry/orchestra-main.git"
WORKSTATION_CONFIG="cherry-workstation-config"
WORKSTATION_NAME="cherry-workstation"
NOTEBOOK_NAME="cherry-notebook"

echo "Starting GCP IDE provisioning for project: ${PROJECT_ID}"

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

# Create Cloud Workstation config
echo "Creating Cloud Workstation config: ${WORKSTATION_CONFIG}"
gcloud beta workstations configs create ${WORKSTATION_CONFIG} \
  --project=${PROJECT_ID} \
  --location=${LOCATION} \
  --service-account=${SERVICE_ACCOUNT} \
  --machine-type=e2-standard-4 \
  --startup-script="#!/bin/bash\ngit clone ${REPO_URL} /home/user/my-repo"

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
  --machine-type=n1-standard-4 \
  --service-account=${SERVICE_ACCOUNT} \
  --metadata=startup-script="#!/bin/bash\ngit clone ${REPO_URL} /home/jupyter/my-repo"

echo "GCP IDE provisioning completed successfully!"
echo "Cloud Workstation: ${WORKSTATION_NAME}"
echo "Vertex AI Notebook: ${NOTEBOOK_NAME}"

# Optional: Display URLs to access the created resources
echo ""
echo "Access your resources at:"
echo "Cloud Workstations: https://console.cloud.google.com/workstations/list?project=${PROJECT_ID}"
echo "Vertex AI Workbench: https://console.cloud.google.com/vertex-ai/workbench/list/instances?project=${PROJECT_ID}"

# Resource cleanup (commented out by default)
# To use, remove the comments and run the script
: '
cleanup_resources() {
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
}

# Uncomment the line below to clean up resources
# cleanup_resources
'
