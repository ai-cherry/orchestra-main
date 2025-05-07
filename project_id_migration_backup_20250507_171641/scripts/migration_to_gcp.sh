#!/bin/bash

# Migration Script: Codespaces to Google Cloud Workstations and Vertex AI Workbench
# Project: orchestra-main
# Target Project ID: agi-baby-cherry

echo "Starting migration process for orchestra-main to Google Cloud Workstations and Vertex AI Workbench..."

# Step 0: Ensure necessary tools are installed
echo "Step 0: Installing necessary tools if not already present..."
bash scripts/setup_gcloud_sdk.sh

# Step 1: Preparation and Authentication
echo "Step 1: Authenticating with Google Cloud SDK..."
gcloud auth login
gcloud config set project agi-baby-cherry
# Replace /path/to/service-account-key.json with the actual path to your key file
gcloud auth activate-service-account vertex-agent@agi-baby-cherry.iam.gserviceaccount.com --key-file=/path/to/service-account-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Step 2: Copy Source Code and Config Files to GCS Bucket
echo "Step 2: Creating GCS Bucket and syncing project files..."
gsutil mb -p agi-baby-cherry gs://agi-baby-cherry-codespaces-migration || echo "Bucket already exists"
gsutil -m cp -r /workspaces/orchestra-main/* gs://agi-baby-cherry-codespaces-migration/
gsutil ls -r gs://agi-baby-cherry-codespaces-migration/ | head -n 20 && echo "... (output truncated, check full list if needed)"

# Step 3: Set Up Google Cloud Workstations
echo "Step 3: Setting up Google Cloud Workstations..."
gcloud workstations clusters create orchestra-cluster --region=us-central1 --project=agi-baby-cherry || echo "Cluster already exists or setup failed, proceeding..."
gcloud workstations configs create orchestra-config --cluster=orchestra-cluster --region=us-central1 --machine-type=e2-standard-4 --project=agi-baby-cherry || echo "Config already exists or setup failed, proceeding..."
gcloud workstations start orchestra-workstation --config=orchestra-config --cluster=orchestra-cluster --region=us-central1 --project=agi-baby-cherry || echo "Workstation start failed, check status manually"

# Step 4: Set Up Vertex AI Workbench
echo "Step 4: Setting up Vertex AI Workbench..."
gcloud notebooks instances create orchestra-notebook --vm-image-project=deeplearning-platform-release --vm-image-family=tf-2-11-cu113-notebooks --machine-type=n1-standard-4 --location=us-central1-a --project=agi-baby-cherry || echo "Notebook creation failed, check status manually"

# Step 5: Instructions for Manual Setup of Tools and Extensions
echo "Step 5: Manual setup required for tools and extensions in Workstations and Workbench."
echo "  - Access your Google Cloud Workstation and Vertex AI Workbench."
echo "  - Install tools on Workstation if not pre-installed:"
echo "    sudo apt update && sudo apt install -y python3 python3-pip && pip3 install poetry"
echo "    sudo apt install -y docker.io && sudo systemctl start docker && sudo systemctl enable docker"
echo "    sudo apt-get update && sudo apt-get install -y gnupg software-properties-common curl && curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add - && sudo apt-add-repository 'deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main' && sudo apt-get update && sudo apt-get install terraform"
echo "  - Install tools on Workbench if not pre-installed (Docker as example):"
echo "    sudo apt-get update && sudo apt-get install -y docker.io && sudo systemctl start docker"
echo "  - Install extensions in VS Code on Workstation:"
echo "    Open VS Code, go to Extensions view, install 'Cloud Code', 'Gemini Code Assist', and other recommended extensions like Python, Docker, Terraform."

# Step 6: Clone Project Files from GCS to New Environments
echo "Step 6: Instructions for downloading project files from GCS to new environments."
echo "  - In both Workstation and Workbench, run:"
echo "    gsutil -m cp -r gs://agi-baby-cherry-codespaces-migration/* /workspaces/orchestra-main/"
echo "  - Verify project structure:"
echo "    ls -laR /workspaces/orchestra-main/ | head -n 20 && echo '... (output truncated)'"

# Step 7: Final Configuration and Validation
echo "Step 7: Final configuration instructions."
echo "  - Set up environment variables in .bashrc or equivalent:"
echo "    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json"
echo "  - Install project dependencies:"
echo "    cd /workspaces/orchestra-main && poetry install"
echo "  - Validate setup with a test (if applicable):"
echo "    python3 -m unittest discover tests"

echo "Migration script execution completed. Please follow the manual steps for tool installation, extension setup, and final configuration in Google Cloud Workstations and Vertex AI Workbench."