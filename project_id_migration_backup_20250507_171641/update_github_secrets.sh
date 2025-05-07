#!/bin/bash
# update_github_secrets.sh - Script to update GitHub organization secrets
#
# This script helps configure the GitHub repository secrets needed for
# CI/CD workflows to deploy the Orchestra application to GCP.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Update GitHub Organization Secrets                 ${NC}"
echo -e "${BLUE}======================================================${NC}"

if ! command -v gh &> /dev/null; then
  echo -e "${YELLOW}GitHub CLI not found. Installing gh CLI...${NC}"
  
  # Install GitHub CLI based on the OS
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    case $ID in
      ubuntu|debian)
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install gh
        ;;
      *)
        echo -e "${RED}Unsupported OS for automatic installation.${NC}"
        echo -e "${YELLOW}Please install GitHub CLI manually from: https://github.com/cli/cli#installation${NC}"
        exit 1
        ;;
    esac
  else
    echo -e "${RED}Could not determine OS type.${NC}"
    echo -e "${YELLOW}Please install GitHub CLI manually from: https://github.com/cli/cli#installation${NC}"
    exit 1
  fi
fi

# Check if logged in to GitHub
if ! gh auth status &> /dev/null; then
  echo -e "${YELLOW}Please login to GitHub using the GitHub CLI...${NC}"
  gh auth login
fi

# Prompt for repository information
echo -e "${YELLOW}Enter your GitHub repository information:${NC}"
read -p "GitHub username or organization: " github_org
read -p "Repository name: " repo_name

# Confirm repository exists
if ! gh repo view ${github_org}/${repo_name} &> /dev/null; then
  echo -e "${RED}Repository ${github_org}/${repo_name} does not exist or you don't have access to it.${NC}"
  exit 1
fi

echo -e "${GREEN}Repository ${github_org}/${repo_name} confirmed.${NC}"

# Function to add or update a secret
add_secret() {
  local name=$1
  local value=$2
  local description=$3
  
  echo -e "${YELLOW}Setting secret: ${name} - ${description}${NC}"
  echo -n "${value}" | gh secret set ${name} --repo ${github_org}/${repo_name}
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully set secret: ${name}${NC}"
  else
    echo -e "${RED}Failed to set secret: ${name}${NC}"
  fi
}

# Add GCP Project ID, Project Number, and Vertex Key
echo -e "${YELLOW}Setting GCP Project ID...${NC}"
add_secret "ORG_GCP_PROJECT_ID" "agi-baby-cherry" "Google Cloud Project ID"

echo -e "${YELLOW}Setting GCP Project Number...${NC}"
add_secret "ORG_GCP_PROJECT_NUMBER" "104944497835" "Google Cloud Project Number"

echo -e "${YELLOW}Setting Vertex Key...${NC}"
add_secret "ORG_VERTEX_KEY" "0d08481a204c0cdba4095bb94529221e8b8ced5c" "Vertex AI Key"

# Set up GCP Service Account Credentials
echo -e "${BLUE}Setting up GCP service account credentials...${NC}"
echo -e "${YELLOW}The service account key will be used for GitHub Actions workflows.${NC}"

if [ -f "/tmp/vertex-agent-key.json" ]; then
  echo -e "${GREEN}Found service account key at /tmp/vertex-agent-key.json${NC}"
  sa_key=$(cat /tmp/vertex-agent-key.json)
else
  echo -e "${YELLOW}Service account key not found at /tmp/vertex-agent-key.json${NC}"
  echo -e "${BLUE}You have two options:${NC}"
  echo "1. Create a new service account key"
  echo "2. Paste an existing key"
  read -p "Choose an option (1/2): " sa_option

  if [ "$sa_option" == "1" ]; then
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
      echo -e "${RED}Google Cloud SDK not installed. Please install it first.${NC}"
      exit 1
    fi
    
    # Create a new key
    echo -e "${YELLOW}Creating a new service account key...${NC}"
    mkdir -p /tmp/credentials
    gcloud iam service-accounts keys create /tmp/credentials/deploy-key.json \
      --iam-account=cherrybaby@agi-baby-cherry.iam.gserviceaccount.com
    
    sa_key=$(cat /tmp/credentials/deploy-key.json)
  else
    echo -e "${YELLOW}Please paste the contents of your service account key JSON below.${NC}"
    echo -e "${YELLOW}Press Ctrl+D when finished.${NC}"
    sa_key=$(cat)
  fi
fi

# Add service account key
add_secret "ORG_GCP_CREDENTIALS" "${sa_key}" "GCP Service Account Credentials"

# Add API key configurations
echo -e "${BLUE}Setting up API keys...${NC}"
echo -e "${YELLOW}Setting Portkey API Key...${NC}"
add_secret "ORG_PORTKEY_API_KEY" "l1wHW8yhd/SU32fK4wJIUvAcxAC+" "Portkey API Key"

# Add Redis configuration
echo -e "${BLUE}Setting up Redis configuration...${NC}"
read -p "Redis host (leave blank to skip): " redis_host
if [ ! -z "$redis_host" ]; then
  add_secret "ORG_REDIS_HOST" "${redis_host}" "Redis Host"
  
  read -p "Redis port (default: 6379): " redis_port
  redis_port=${redis_port:-6379}
  add_secret "ORG_REDIS_PORT" "${redis_port}" "Redis Port"
  
  read -p "Redis password (leave blank if none): " -s redis_pass
  echo ""
  if [ ! -z "$redis_pass" ]; then
    add_secret "ORG_REDIS_PASSWORD" "${redis_pass}" "Redis Password"
  fi
fi

# Add Kubernetes configuration if needed
echo -e "${BLUE}Do you want to set up Kubernetes cluster information? (y/n)${NC}"
read -p "Set up Kubernetes? " setup_k8s

if [ "$setup_k8s" == "y" ]; then
  read -p "Production cluster name (e.g., autopilot-cluster-1): " prod_cluster
  add_secret "ORG_GKE_CLUSTER_PROD" "${prod_cluster}" "Production GKE Cluster Name"
  
  read -p "Staging cluster name (leave blank if same as production): " stage_cluster
  stage_cluster=${stage_cluster:-$prod_cluster}
  add_secret "ORG_GKE_CLUSTER_STAGING" "${stage_cluster}" "Staging GKE Cluster Name"
  
  read -p "GCP Region (default: us-central1): " gcp_region
  gcp_region=${gcp_region:-"us-central1"}
  add_secret "ORG_GCP_REGION" "${gcp_region}" "GCP Region"
fi

# Set up Docker Hub credentials
echo -e "${BLUE}Do you want to set up Docker Hub credentials? (y/n)${NC}"
read -p "Set up Docker Hub? " setup_docker

if [ "$setup_docker" == "y" ]; then
  read -p "Docker Hub username: " docker_user
  read -p "Docker Hub token: " -s docker_token
  echo ""
  
  add_secret "DOCKERHUB_USERNAME" "${docker_user}" "Docker Hub Username"
  add_secret "DOCKERHUB_TOKEN" "${docker_token}" "Docker Hub Access Token"
fi

# Set up Slack webhook for notifications (optional)
echo -e "${BLUE}Do you want to set up Slack notifications? (y/n)${NC}"
read -p "Set up Slack? " setup_slack

if [ "$setup_slack" == "y" ]; then
  read -p "Slack webhook URL: " slack_webhook
  add_secret "SLACK_WEBHOOK_URL" "${slack_webhook}" "Slack Webhook URL"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}GitHub secrets have been configured successfully!${NC}"
echo -e "${YELLOW}These secrets will be used by the GitHub Actions workflows for deployment.${NC}"
echo -e "${BLUE}======================================================${NC}"

echo -e "${YELLOW}To trigger a deployment, push to the main branch or create a pull request.${NC}"
