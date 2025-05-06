#!/bin/bash
# Setup GitHub Secrets using GitHub PAT
# This script automatically sets up GitHub secrets for the AI Orchestra project

set -e  # Exit on any error

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"  # No Color

# Print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Variables
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
GITHUB_PAT=${GITHUB_PAT:-"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"}
REPO_OWNER=${REPO_OWNER:-""}
REPO_NAME=${REPO_NAME:-"orchestra-main"}
SERVICE_ACCOUNT_NAME="github-actions-wif"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"

section "GitHub Secrets Setup"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    warning "GitHub CLI not found. Installing..."
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh
fi

# Authenticate with GitHub
echo "Authenticating with GitHub..."
echo "$GITHUB_PAT" | gh auth login --with-token

# Get repository owner if not provided
if [[ -z "$REPO_OWNER" ]]; then
    # Try to get from git remote
    REMOTE_URL=$(git config --get remote.origin.url || echo "")
    if [[ -n "$REMOTE_URL" ]]; then
        if [[ "$REMOTE_URL" == *"github.com"* ]]; then
            # Extract owner and repo from GitHub URL
            REPO_INFO=$(echo "$REMOTE_URL" | sed -n 's/.*github.com[:/]\([^/]*\)\/\([^.]*\).*/\1 \2/p')
            REPO_OWNER=$(echo "$REPO_INFO" | cut -d' ' -f1)
            REPO_NAME=$(echo "$REPO_INFO" | cut -d' ' -f2)
        fi
    fi
    
    # If still empty, prompt user
    if [[ -z "$REPO_OWNER" ]]; then
        read -p "Enter your GitHub organization or username: " REPO_OWNER
    fi
fi

echo "Repository: $REPO_OWNER/$REPO_NAME"

# Check if we can access the repository
echo "Checking repository access..."
if ! gh repo view "$REPO_OWNER/$REPO_NAME" &> /dev/null; then
    error "Cannot access repository $REPO_OWNER/$REPO_NAME. Please check your permissions."
    exit 1
fi

# Get Workload Identity Federation details
section "Getting Workload Identity Federation details"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if logged in
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
if [[ -z "$ACCOUNT" ]]; then
    error "You are not logged in to gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

echo "Currently authenticated as: $ACCOUNT"
echo "Project ID: $PROJECT_ID"

# Set the project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Get the Workload Identity Pool ID
echo "Getting Workload Identity Pool ID..."
POOL_ID=$(gcloud iam workload-identity-pools describe $POOL_NAME \
    --location="global" \
    --format="value(name)" \
    --project=$PROJECT_ID 2>/dev/null || echo "")

if [[ -z "$POOL_ID" ]]; then
    error "Workload Identity Pool $POOL_NAME not found. Please run setup_workload_identity.sh first."
    exit 1
fi

# Get the Workload Identity Provider ID
echo "Getting Workload Identity Provider ID..."
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --format="value(name)" \
    --project=$PROJECT_ID 2>/dev/null || echo "")

if [[ -z "$PROVIDER_ID" ]]; then
    error "Workload Identity Provider $PROVIDER_NAME not found. Please run setup_workload_identity.sh first."
    exit 1
fi

# Set up GitHub secrets
section "Setting up GitHub secrets"

# WIF_PROVIDER_ID
echo "Setting WIF_PROVIDER_ID secret..."
WIF_PROVIDER_ID="projects/${PROJECT_ID}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"
gh secret set WIF_PROVIDER_ID --body "$WIF_PROVIDER_ID" --repo "$REPO_OWNER/$REPO_NAME"
success "Set WIF_PROVIDER_ID secret"

# WIF_SERVICE_ACCOUNT
echo "Setting WIF_SERVICE_ACCOUNT secret..."
WIF_SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
gh secret set WIF_SERVICE_ACCOUNT --body "$WIF_SERVICE_ACCOUNT" --repo "$REPO_OWNER/$REPO_NAME"
success "Set WIF_SERVICE_ACCOUNT secret"

# GCP_PROJECT_ID
echo "Setting GCP_PROJECT_ID secret..."
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID" --repo "$REPO_OWNER/$REPO_NAME"
success "Set GCP_PROJECT_ID secret"

# GCP_REGION
echo "Setting GCP_REGION secret..."
gh secret set GCP_REGION --body "$REGION" --repo "$REPO_OWNER/$REPO_NAME"
success "Set GCP_REGION secret"

section "GitHub Secrets Setup Complete"
echo "The following secrets have been set up in your GitHub repository:"
echo "- WIF_PROVIDER_ID"
echo "- WIF_SERVICE_ACCOUNT"
echo "- GCP_PROJECT_ID"
echo "- GCP_REGION"
echo ""
echo "These secrets will be used by GitHub Actions workflows for authentication and deployment."
echo ""
echo "IMPORTANT: For security, the GitHub PAT used in this script should be revoked after setup."
echo "Visit https://github.com/settings/tokens to manage your tokens."