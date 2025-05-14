#!/bin/bash
# Cloud Setup Script for AI Orchestra GCP Workstation
# This script performs initial setup tasks for Google Cloud Platform

set -e

echo "======================================================================"
echo "                      AI ORCHESTRA CLOUD SETUP                        "
echo "======================================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Environment: ${ENV}"
echo "======================================================================"

# Ensure we have project ID
if [ -z "${PROJECT_ID}" ]; then
    echo "ERROR: PROJECT_ID environment variable is not set."
    echo "Please set PROJECT_ID and try again."
    exit 1
fi

# Check if user is authenticated with gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "ERROR: Not authenticated with Google Cloud."
    echo "Please run 'gcloud auth login' and try again."
    exit 1
fi

# Enable required APIs
enable_apis() {
    echo "Enabling required Google Cloud APIs..."
    
    gcloud services enable \
        aiplatform.googleapis.com \
        artifactregistry.googleapis.com \
        bigquery.googleapis.com \
        cloudresourcemanager.googleapis.com \
        compute.googleapis.com \
        containerregistry.googleapis.com \
        iam.googleapis.com \
        run.googleapis.com \
        secretmanager.googleapis.com \
        serviceusage.googleapis.com \
        storage.googleapis.com \
        workstations.googleapis.com
}

# Create service account if it doesn't exist
create_service_account() {
    local SA_NAME="orchestra-sa"
    local SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    echo "Checking for service account: ${SA_EMAIL}..."
    
    if gcloud iam service-accounts describe "${SA_EMAIL}" > /dev/null 2>&1; then
        echo "Service account already exists."
    else
        echo "Creating service account: ${SA_NAME}..."
        gcloud iam service-accounts create "${SA_NAME}" \
            --display-name="AI Orchestra Service Account"
    fi
    
    echo "Granting roles to service account..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/aiplatform.user"
        
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/artifactregistry.admin"
        
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/run.admin"
        
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/secretmanager.secretAccessor"
        
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.admin"
        
    # Create and download a key if requested
    if [ "$1" = "--create-key" ]; then
        echo "Creating and downloading service account key..."
        gcloud iam service-accounts keys create "${SA_NAME}-key.json" \
            --iam-account="${SA_EMAIL}"
        
        mkdir -p /home/user/orchestra/.gcp
        mv "${SA_NAME}-key.json" /home/user/orchestra/.gcp/service-account-key.json
        echo "Service account key saved to /home/user/orchestra/.gcp/service-account-key.json"
    fi
}

# Create Cloud Storage bucket if it doesn't exist
create_storage_bucket() {
    local BUCKET_NAME="${PROJECT_ID}-orchestra-${ENV}"
    
    echo "Checking for storage bucket: ${BUCKET_NAME}..."
    
    if gsutil ls -b "gs://${BUCKET_NAME}" > /dev/null 2>&1; then
        echo "Storage bucket already exists."
    else
        echo "Creating storage bucket: ${BUCKET_NAME}..."
        gsutil mb -l "${REGION}" "gs://${BUCKET_NAME}"
        gsutil versioning set on "gs://${BUCKET_NAME}"
    fi
    
    # Export bucket name as environment variable
    echo "ORCHESTRA_BUCKET=${BUCKET_NAME}" >> /home/user/orchestra/.env
    echo "Storage bucket setup complete: ${BUCKET_NAME}"
}

# Create Artifact Registry repository if it doesn't exist
create_artifact_repository() {
    local REPO_NAME="orchestra-registry"
    
    echo "Checking for Artifact Registry repository: ${REPO_NAME}..."
    
    if gcloud artifacts repositories describe "${REPO_NAME}" \
        --location="${REGION}" > /dev/null 2>&1; then
        echo "Artifact Registry repository already exists."
    else
        echo "Creating Artifact Registry repository: ${REPO_NAME}..."
        gcloud artifacts repositories create "${REPO_NAME}" \
            --repository-format=docker \
            --location="${REGION}" \
            --description="AI Orchestra container registry"
    fi
    
    # Configure Docker to use Artifact Registry
    gcloud auth configure-docker "${REGION}-docker.pkg.dev"
    
    # Export repository URL as environment variable
    local REPO_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"
    echo "DOCKER_REPOSITORY=${REPO_URL}" >> /home/user/orchestra/.env
    echo "Artifact Registry setup complete: ${REPO_URL}"
}

# Set up Secret Manager secrets
setup_secrets() {
    echo "Setting up Secret Manager secrets..."
    
    # Check if .env.secrets file exists
    if [ ! -f "/home/user/orchestra/.env.secrets" ]; then
        echo "No .env.secrets file found. Creating a template..."
        cat > /home/user/orchestra/.env.secrets << EOF
# Secret values for AI Orchestra
# This file should not be committed to version control

# API Keys
API_KEY=your-api-key-here

# Database Credentials
DB_USERNAME=orchestra
DB_PASSWORD=change-me

# Other Sensitive Information
SIGNING_KEY=generate-a-secure-random-key
EOF
        echo ".env.secrets template created. Please edit with real values."
        return
    fi
    
    # Create secrets from .env.secrets
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        if [[ "$line" =~ ^#.*$ ]] || [[ -z "$line" ]]; then
            continue
        fi
        
        # Parse key and value
        key=$(echo "$line" | cut -d= -f1)
        value=$(echo "$line" | cut -d= -f2-)
        
        echo "Creating/updating secret: $key"
        
        # Check if secret exists
        if gcloud secrets describe "$key" --project="${PROJECT_ID}" > /dev/null 2>&1; then
            # Secret exists, add a new version
            echo -n "$value" | gcloud secrets versions add "$key" --data-file=-
        else
            # Create new secret
            echo -n "$value" | gcloud secrets create "$key" --replication-policy="automatic" --data-file=-
        fi
    done < "/home/user/orchestra/.env.secrets"
    
    echo "Secrets setup complete."
}

# Main execution flow
main() {
    echo "Starting Cloud Setup for AI Orchestra..."
    
    # Run setup steps
    enable_apis
    create_service_account "$@"
    create_storage_bucket
    create_artifact_repository
    
    # Ask about setting up secrets
    read -p "Do you want to set up Secret Manager secrets? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_secrets
    fi
    
    echo "Cloud Setup completed successfully!"
    echo "Your GCP environment is now ready for AI Orchestra development."
}

# Run main function with any arguments
main "$@"