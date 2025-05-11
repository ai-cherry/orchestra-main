#!/bin/bash
# setup_badass_credentials.sh - Script to set up powerful service accounts for Vertex AI and Gemini
# Uses GitHub organization-level secrets to create and configure service accounts

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up badass credentials for AI Orchestra...${NC}"

# Variables
PROJECT_ID="cherry-ai-project"
REGION="us-central1"
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"

# Create temporary directory for credentials
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Function to set up GCP credentials
setup_gcp_credentials() {
    echo -e "${YELLOW}Setting up GCP credentials...${NC}"
    
    # Check if GCP_PROJECT_ADMIN_KEY is set
    if [ -z "${GCP_PROJECT_ADMIN_KEY}" ]; then
        echo -e "${RED}Error: GCP_PROJECT_ADMIN_KEY environment variable is not set.${NC}"
        echo "Please set the GCP_PROJECT_ADMIN_KEY environment variable with your GCP project admin key."
        exit 1
    fi
    
    # Check if GCP_SECRET_MANAGEMENT_KEY is set
    if [ -z "${GCP_SECRET_MANAGEMENT_KEY}" ]; then
        echo -e "${RED}Error: GCP_SECRET_MANAGEMENT_KEY environment variable is not set.${NC}"
        echo "Please set the GCP_SECRET_MANAGEMENT_KEY environment variable with your GCP secret management key."
        exit 1
    fi
    
    # Save credentials to temporary files
    echo "${GCP_PROJECT_ADMIN_KEY}" > "${TEMP_DIR}/project-admin-key.json"
    echo "${GCP_SECRET_MANAGEMENT_KEY}" > "${TEMP_DIR}/secret-management-key.json"
    chmod 600 "${TEMP_DIR}/project-admin-key.json" "${TEMP_DIR}/secret-management-key.json"
    
    # Authenticate with gcloud using project admin key
    echo -e "${YELLOW}Authenticating with Google Cloud using project admin key...${NC}"
    gcloud auth activate-service-account --key-file="${TEMP_DIR}/project-admin-key.json"
    gcloud config set project ${PROJECT_ID}
}

# Function to create badass Vertex AI service account
create_vertex_ai_service_account() {
    echo -e "${YELLOW}Creating badass Vertex AI service account...${NC}"
    
    # Create service account
    gcloud iam service-accounts create vertex-ai-badass \
        --display-name="Vertex AI Badass Service Account" \
        --description="Service account with extensive permissions for all Vertex AI operations"
    
    # Grant permissions
    for role in \
        "roles/aiplatform.admin" \
        "roles/aiplatform.user" \
        "roles/storage.admin" \
        "roles/logging.admin" \
        "roles/iam.serviceAccountUser" \
        "roles/iam.serviceAccountTokenCreator"
    do
        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
            --member="serviceAccount:vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com" \
            --role="${role}"
    done
    
    # Create service account key
    gcloud iam service-accounts keys create "${TEMP_DIR}/vertex-ai-badass-key.json" \
        --iam-account="vertex-ai-badass@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Store key in Secret Manager
    gcloud secrets create vertex-ai-badass-key \
        --data-file="${TEMP_DIR}/vertex-ai-badass-key.json" \
        --replication-policy="automatic"
    
    # Update GitHub organization secret
    echo -e "${YELLOW}Updating GitHub organization secret GCP_VERTEX_AI_KEY...${NC}"
    gh secret set GCP_VERTEX_AI_KEY --org ${GITHUB_ORG} --body "$(cat ${TEMP_DIR}/vertex-ai-badass-key.json)"
}

# Function to create badass Gemini service account
create_gemini_service_account() {
    echo -e "${YELLOW}Creating badass Gemini service account...${NC}"
    
    # Create service account
    gcloud iam service-accounts create gemini-badass \
        --display-name="Gemini Badass Service Account" \
        --description="Service account with extensive permissions for all Gemini API operations"
    
    # Grant permissions
    for role in \
        "roles/aiplatform.user" \
        "roles/serviceusage.serviceUsageConsumer" \
        "roles/iam.serviceAccountUser" \
        "roles/iam.serviceAccountTokenCreator"
    do
        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
            --member="serviceAccount:gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com" \
            --role="${role}"
    done
    
    # Create service account key
    gcloud iam service-accounts keys create "${TEMP_DIR}/gemini-badass-key.json" \
        --iam-account="gemini-badass@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Store key in Secret Manager
    gcloud secrets create gemini-badass-key \
        --data-file="${TEMP_DIR}/gemini-badass-key.json" \
        --replication-policy="automatic"
    
    # Update GitHub organization secret
    echo -e "${YELLOW}Updating GitHub organization secret GCP_GEMINI_KEY...${NC}"
    gh secret set GCP_GEMINI_KEY --org ${GITHUB_ORG} --body "$(cat ${TEMP_DIR}/gemini-badass-key.json)"
}

# Function to update GitHub organization secrets
update_github_org_secrets() {
    echo -e "${YELLOW}Updating GitHub organization secrets...${NC}"
    
    # Authenticate with GitHub CLI
    echo -e "${YELLOW}Authenticating with GitHub CLI...${NC}"
    echo "${GITHUB_PAT}" | gh auth login --with-token
    
    # Update project-related secrets
    gh secret set GCP_PROJECT_ID --org ${GITHUB_ORG} --body "${PROJECT_ID}"
    gh secret set GCP_PROJECT_NUMBER --org ${GITHUB_ORG} --body "525398941159"
    gh secret set GCP_REGION --org ${GITHUB_ORG} --body "${REGION}"
    
    # Update service account keys
    gh secret set GCP_PROJECT_ADMIN_KEY --org ${GITHUB_ORG} --body "$(cat ${TEMP_DIR}/project-admin-key.json)"
    gh secret set GCP_SECRET_MANAGEMENT_KEY --org ${GITHUB_ORG} --body "$(cat ${TEMP_DIR}/secret-management-key.json)"
}

# Main execution
main() {
    # Set up GCP credentials
    setup_gcp_credentials
    
    # Create badass service accounts
    create_vertex_ai_service_account
    create_gemini_service_account
    
    # Update GitHub organization secrets
    update_github_org_secrets
    
    echo -e "${GREEN}Badass credentials setup complete!${NC}"
    echo -e "${GREEN}The following secrets have been updated in the GitHub organization:${NC}"
    echo -e "  - GCP_PROJECT_ID"
    echo -e "  - GCP_PROJECT_NUMBER"
    echo -e "  - GCP_REGION"
    echo -e "  - GCP_PROJECT_ADMIN_KEY"
    echo -e "  - GCP_SECRET_MANAGEMENT_KEY"
    echo -e "  - GCP_VERTEX_AI_KEY"
    echo -e "  - GCP_GEMINI_KEY"
}

# Run the main function
main