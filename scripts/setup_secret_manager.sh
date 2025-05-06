#!/bin/bash
# Setup Secret Manager with required secrets for AI Orchestra
# This script creates and populates Secret Manager with required secrets

set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Secret Manager for AI Orchestra...${NC}"

# Enable Secret Manager API if not already enabled
echo -e "${YELLOW}Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com --project ${PROJECT_ID}

# Function to create or update a secret
create_or_update_secret() {
    local secret_id=$1
    local secret_value=$2
    local description=$3

    # Check if secret exists
    if gcloud secrets describe ${secret_id} --project ${PROJECT_ID} &>/dev/null; then
        echo -e "${YELLOW}Secret ${secret_id} already exists. Adding new version...${NC}"
        echo -n "${secret_value}" | gcloud secrets versions add ${secret_id} --data-file=- --project ${PROJECT_ID}
    else
        echo -e "${YELLOW}Creating secret ${secret_id}...${NC}"
        echo -n "${secret_value}" | gcloud secrets create ${secret_id} \
            --replication-policy="user-managed" \
            --locations=${REGION} \
            --data-file=- \
            --description="${description}" \
            --project ${PROJECT_ID}
    fi
    
    echo -e "${GREEN}Secret ${secret_id} created/updated successfully.${NC}"
}

# Function to prompt for secret value
prompt_for_secret() {
    local secret_id=$1
    local description=$2
    local default_value=$3
    
    echo -e "${YELLOW}Enter value for ${secret_id} (${description})${NC}"
    if [ -n "$default_value" ]; then
        echo -e "${YELLOW}Press Enter to use default: [${default_value}]${NC}"
    fi
    
    read -s secret_value
    echo ""
    
    # Use default if no value provided
    if [ -z "$secret_value" ] && [ -n "$default_value" ]; then
        secret_value=$default_value
    fi
    
    # Validate that a value was provided
    if [ -z "$secret_value" ]; then
        echo -e "${RED}No value provided for ${secret_id}. Skipping...${NC}"
        return 1
    fi
    
    create_or_update_secret "${secret_id}" "${secret_value}" "${description}"
    return 0
}

# Function to grant access to a service account
grant_secret_access() {
    local secret_id=$1
    local service_account=$2
    
    echo -e "${YELLOW}Granting access to ${secret_id} for ${service_account}...${NC}"
    gcloud secrets add-iam-policy-binding ${secret_id} \
        --member="serviceAccount:${service_account}" \
        --role="roles/secretmanager.secretAccessor" \
        --project ${PROJECT_ID}
    
    echo -e "${GREEN}Access granted successfully.${NC}"
}

# Create Cloud Run service account if it doesn't exist
CLOUD_RUN_SA="orchestra-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe ${CLOUD_RUN_SA} --project ${PROJECT_ID} &>/dev/null; then
    echo -e "${YELLOW}Creating Cloud Run service account...${NC}"
    gcloud iam service-accounts create orchestra-cloud-run \
        --display-name="Orchestra Cloud Run Service Account" \
        --project ${PROJECT_ID}
    echo -e "${GREEN}Service account created successfully.${NC}"
else
    echo -e "${YELLOW}Cloud Run service account already exists.${NC}"
fi

# Setup LLM API keys
echo -e "\n${GREEN}Setting up LLM API keys...${NC}"

# OpenAI API Key
prompt_for_secret "OPENAI_API_KEY" "OpenAI API Key for GPT models"

# Anthropic API Key
prompt_for_secret "ANTHROPIC_API_KEY" "Anthropic API Key for Claude models"

# Google/Gemini API Key
prompt_for_secret "GEMINI_API_KEY" "Google API Key for Gemini models"

# Azure OpenAI API Key (optional)
prompt_for_secret "AZURE_OPENAI_API_KEY" "Azure OpenAI API Key (optional)" ""

# Azure OpenAI API Base (optional)
if prompt_for_secret "AZURE_OPENAI_API_BASE" "Azure OpenAI API Base URL (optional)" ""; then
    echo -e "${YELLOW}Azure OpenAI API Base URL set.${NC}"
fi

# Setup database credentials
echo -e "\n${GREEN}Setting up database credentials...${NC}"

# Generate a random password for Redis if needed
REDIS_PASSWORD=$(openssl rand -base64 32)
prompt_for_secret "REDIS_PASSWORD" "Redis password for authentication" "${REDIS_PASSWORD}"

# Setup application secrets
echo -e "\n${GREEN}Setting up application secrets...${NC}"

# Generate a random API key for the application
APP_API_KEY=$(openssl rand -base64 32)
prompt_for_secret "APP_API_KEY" "API Key for the application" "${APP_API_KEY}"

# Generate a random JWT secret
JWT_SECRET=$(openssl rand -base64 64)
prompt_for_secret "JWT_SECRET" "Secret for JWT token generation" "${JWT_SECRET}"

# Grant access to the Cloud Run service account
echo -e "\n${GREEN}Granting access to secrets for Cloud Run service account...${NC}"
for secret_id in "OPENAI_API_KEY" "ANTHROPIC_API_KEY" "GEMINI_API_KEY" "AZURE_OPENAI_API_KEY" "AZURE_OPENAI_API_BASE" "REDIS_PASSWORD" "APP_API_KEY" "JWT_SECRET"; do
    if gcloud secrets describe ${secret_id} --project ${PROJECT_ID} &>/dev/null; then
        grant_secret_access "${secret_id}" "${CLOUD_RUN_SA}"
    fi
done

echo -e "\n${GREEN}Secret Manager setup complete!${NC}"
echo -e "${YELLOW}You can now use these secrets in your application by referencing them in your Terraform configuration or directly in your code.${NC}"
echo -e "${YELLOW}Example Terraform usage:${NC}"
echo -e "
resource \"google_cloud_run_v2_service\" \"api\" {
  # ...
  template {
    containers {
      # ...
      env {
        name = \"OPENAI_API_KEY\"
        value_source {
          secret_key_ref {
            secret = \"OPENAI_API_KEY\"
            version = \"latest\"
          }
        }
      }
    }
  }
}
"

echo -e "${YELLOW}Example Python usage with google-cloud-secret-manager:${NC}"
echo -e "
from google.cloud import secretmanager

def get_secret(project_id, secret_id, version_id=\"latest\"):
    client = secretmanager.SecretManagerServiceClient()
    name = f\"projects/{project_id}/secrets/{secret_id}/versions/{version_id}\"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode(\"UTF-8\")

# Usage
openai_api_key = get_secret(\"${PROJECT_ID}\", \"OPENAI_API_KEY\")
"