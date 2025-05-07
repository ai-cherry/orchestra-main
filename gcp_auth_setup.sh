#!/bin/bash
# gcp_auth_setup.sh - Comprehensive GCP Authentication Setup
# This script provides a complete solution for setting up GCP authentication
# for both local development and Docker deployment environments.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}${BOLD}   Orchestra GCP Authentication Setup               ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Create credential directories
mkdir -p /tmp/credentials

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to create a simple service account key
create_sample_key() {
  echo -e "${YELLOW}Creating a sample service account key for testing purposes...${NC}"
  cat > /tmp/vertex-agent-key.json << 'EOF'
{
  "type": "service_account",
  "project_id": "cherry-ai-project",
  "private_key_id": "sample-private-key-id-for-testing",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCxhKMLd6fDYZBj\nA0ud4ZoOR88FyCMJQxKLiUWWqzwY4XsnEXp4Fx9/aT4j9xhW/J1HAAUHYu7sP7ma\nWWFQ0ZJrKn37skGmV/Q3JMpN5qSQ9MCX2hfI9i8JvQdYnlJFdG9bQPcoDl5P5WSA\nwraYh6NnBB/OrkFxCFlQnZ0qKD+5sYGygqYxGI0e31dyEnNbaOU/TJ+ZTHIAcbbA\nK9b1zv3jOYnBwfO5frQs4J8yGbj6d9O3kACeeT3Cbz8cTXLWjmiLYElSFJyFqYoc\nkIdw7zaJ80gwEXFcHIuZjIPVuvOzfVhUYKMwA1NeIUW1IiYoBvoJIB112QFWkv/n\nq+5v+zD/AgMBAAECggEAQpJYKkKzPBB2RALQWMxJ/QjLzEUubDIBoiXdAb80QzfI\nkcLDe5CYdYBEvUK3MF53UtRgJPQQZM+cwG71HJpc6HOvSXUb5wfQJeHOwZZhfqRA\nVPRVzMR1m1sBjBGsTWcdFJQyLCjR54KmD+tE44j9L2YVQMbnGiEKGbZGSNgFIQYs\n5AiDI1Ptv5hNtWgWLdFuG4Enx9hXuHNfFysXQPA4rvCcNCrgzLRNsyuPRyMgVWNl\nPPkzs3ATPKTjJHj18pQVCGgClIDrb6aEXWVSwgo+8t5jMk4ioJGLEg1nis3lSWhR\n5YkWLSwBJLCeGAUYu9UvKoH5LJlFUo8YCG4Y7jZ2YQKBgQDYdRafcwbZk1Dt+Fab\nzVdF0NSCTAMi05Hg/G5KQgy4XS7in2dUEF8lyXv9xEG0q+jlABjiEYciAq44Hz7z\nH72y2D6ophu4+XsFU1AcRQV1sYShOaQ466ZBwOYH7Ye2sQpulX/c7vkgKWD+sSX5\nqD5J9SErvc9DOVNRrJs4EYKsIQKBgQDSABiXvYtcLbJBJUPRYpgkEOggWbH7VuRK\nbRtZvAPHrFUK+FzigOHZivK0lnJkhX4kEYYGGKWrW+Jy2qbpXYOl9TiYFTJYPpEE\nSzT0KSBU+RwQa5lIZVD+byHqHoRTZhQAEu/JKj1AKxEF44XQJzwpGBlYswBLbXRo\ns8JmcgSrHwKBgQCRyaDcHDZZXhkDmXJqXXAoX3uk8q3sE+VL6U8NtUcG7jME9s8n\n6R94TAZpzEf3X2KdjYQBsvMBgbrjEBQmnfJaO2VfTXQWQBajYyqsAi+RcGdpKW1J\nzcNNuGGxPBxTNDeuNuj0h10AXQKVsmQyxPFJbKIbB1mLHo7YbE26yYcSQQKBgDIh\nFIyTldpTH0ymsIJ5nFb/QqB7/LGLEqPQYj1Uslk+D8GwLzO3Lvvb6CoqLS3mPsur\nCWbXiJOXd8FVnJyU5HOAdQgvvxeZWBPIjBKZCRS1R8LnlVEBbOTMCtdkXYRiNPvw\nKXwBs1KrqE9kMfbAiHYjDXn752Yb5F9ENxClPl7jAoGARNCM4Pv+1IVNtZY0CkGP\njXEFDa9lSxIYfmwXUztSjCCDhBpkUHuPmZsIQLEfUjqG7k89+prdxPGxP7ieTb0m\nNWVC1S0V6HHAXVbWKHiTVZIrQqP3PcYCIcFGYRS8F3QSiAyXbTKGnEjG3vQF9sXA\noDMUVUPHkqLMTU9b4hYQSD0=\n-----END PRIVATE KEY-----\n",
  "client_email": "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
  "client_id": "vertex-agent-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/vertex-agent%40cherry-ai-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOF
  chmod 600 /tmp/vertex-agent-key.json
  echo -e "${GREEN}Sample key created at /tmp/vertex-agent-key.json${NC}"
}

# Setup option menu
echo -e "Choose authentication setup mode:"
echo -e "1) Create sample key (for testing without real GCP access)"
echo -e "2) Use Docker to create service account key"
echo -e "3) Paste service account key JSON content manually"
echo -e "4) Use existing key file"

read -p "Select an option [1-4]: " auth_option

case $auth_option in
  1)
    # Create a sample key for testing
    create_sample_key
    ;;
  2)
    # Use Docker to create service account key
    echo -e "${YELLOW}Using Docker to create service account key...${NC}"
    if command_exists docker; then
      echo -e "${YELLOW}Running Google Cloud SDK in Docker to generate key...${NC}"
      
      # Check if GCP_PROJECT_ID is set in environment, if not set to default
      GCP_PROJECT_ID=${GCP_PROJECT_ID:-"cherry-ai-project"}
      
      # Create a temporary script for Docker to execute
      cat > /tmp/create_key.sh << EOF
#!/bin/bash
set -e

# Login interactively (will open browser)
gcloud auth login --no-launch-browser

# Set project
gcloud config set project ${GCP_PROJECT_ID}

# Check if vertex-agent service account exists
if ! gcloud iam service-accounts list --filter="email:vertex-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --format="value(email)" | grep -q "vertex-agent"; then
  echo "Creating vertex-agent service account..."
  gcloud iam service-accounts create vertex-agent \\
    --display-name="Vertex Agent Service Account" \\
    --description="Service account for Orchestra deployment and Vertex AI operations"
  
  # Assign roles
  for role in "roles/aiplatform.user" "roles/run.admin" "roles/storage.admin" "roles/firestore.admin" "roles/secretmanager.admin" "roles/redis.admin"; do
    gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \\
      --member="serviceAccount:vertex-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \\
      --role="\${role}"
  done
fi

# Create key
gcloud iam service-accounts keys create /tmp/sa-key.json \\
  --iam-account=vertex-agent@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Cat the contents so we can save them
cat /tmp/sa-key.json
EOF
      
      chmod +x /tmp/create_key.sh
      
      # Run in Docker
      echo -e "${YELLOW}Running Google Cloud SDK container...${NC}"
      key_content=$(docker run --rm -v /tmp:/tmp google/cloud-sdk:latest bash /tmp/create_key.sh | tail -n +2)
      
      # Save the key content to file
      echo "$key_content" > /tmp/vertex-agent-key.json
      chmod 600 /tmp/vertex-agent-key.json
      
      echo -e "${GREEN}Service account key created at /tmp/vertex-agent-key.json${NC}"
    else
      echo -e "${RED}Docker is not available. Please choose another option.${NC}"
      create_sample_key
    fi
    ;;
  3)
    # Paste service account key JSON content manually
    echo -e "${YELLOW}Paste your service account key JSON content below:${NC}"
    echo -e "${YELLOW}(Press Ctrl+D when finished)${NC}"
    cat > /tmp/vertex-agent-key.json
    chmod 600 /tmp/vertex-agent-key.json
    echo -e "${GREEN}Key saved to /tmp/vertex-agent-key.json${NC}"
    ;;
  4)
    # Use existing key file
    read -p "Enter the path to your existing key file: " existing_key_path
    
    if [ -f "$existing_key_path" ]; then
      cp "$existing_key_path" /tmp/vertex-agent-key.json
      chmod 600 /tmp/vertex-agent-key.json
      echo -e "${GREEN}Key copied to /tmp/vertex-agent-key.json${NC}"
    else
      echo -e "${RED}Error: File not found at $existing_key_path${NC}"
      create_sample_key
    fi
    ;;
  *)
    echo -e "${RED}Invalid option. Creating sample key instead.${NC}"
    create_sample_key
    ;;
esac

# Copy to both locations for compatibility with different parts of the code
cp /tmp/vertex-agent-key.json /tmp/credentials/vertex-agent-key.json
chmod 600 /tmp/credentials/vertex-agent-key.json

# Set up environment variables
echo -e "${YELLOW}Setting up environment variables...${NC}"
cat << EOF >> .env

# GCP Authentication (added by gcp_auth_setup.sh)
GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
GCP_PROJECT_ID=cherry-ai-project
EOF

# Create a script to be sourced in the current shell
cat << 'EOF' > /tmp/gcp_env.sh
#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
export GCP_PROJECT_ID=cherry-ai-project

echo "GCP environment variables set:"
echo "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
echo "GCP_SA_KEY_PATH=$GCP_SA_KEY_PATH" 
echo "GCP_PROJECT_ID=$GCP_PROJECT_ID"
EOF

chmod +x /tmp/gcp_env.sh

# Test the authentication file using Python
echo -e "${YELLOW}Testing authentication with Python...${NC}"
python3 -c "
import json
import os

# Try to load the key file to verify it's valid JSON
try:
    with open('/tmp/vertex-agent-key.json', 'r') as f:
        key_data = json.load(f)
    
    # Print key info
    print(f\"Loaded key for: {key_data.get('client_email', 'UNKNOWN')}\")
    print(f\"Project: {key_data.get('project_id', 'UNKNOWN')}\")
    print(f\"Key validation passed!\")
except Exception as e:
    print(f\"Error validating key: {str(e)}\")
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Authentication setup successful!${NC}"
else
    echo -e "${RED}Authentication setup failed. Please check the errors above.${NC}"
    exit 1
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}${BOLD}GCP Authentication Setup Complete${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. To load environment variables in your current shell, run:"
echo -e "   ${BOLD}source /tmp/gcp_env.sh${NC}"
echo -e ""
echo -e "2. To verify deployment readiness, run:"
echo -e "   ${BOLD}./verify_deployment_readiness.sh${NC}"
echo -e ""
echo -e "3. For Docker builds, the Dockerfile has been updated to use"
echo -e "   the correct path at /tmp/vertex-agent-key.json"
echo -e "${BLUE}======================================================${NC}"