de a#!/bin/bash
# sync_github_gcp_secrets.sh - Synchronize secrets between GitHub and GCP Secret Manager
# This script ensures credentials are consistent across both platforms

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

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

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    source .env
    echo "Loaded environment variables from .env file"
fi

# Variables with fallbacks to environment variables
PROJECT_ID="${GCP_PROJECT_ID:-cherry-ai-project}"
REGION="${GCP_REGION:-us-west4}"
GITHUB_PAT="${GH_CLASSIC_PAT_TOKEN:-${GITHUB_TOKEN:-$(gh auth token)}}"
GITHUB_FINE_GRAINED="${GH_FINE_GRAINED_TOKEN:-""}"
REPO_OWNER="${REPO_OWNER:-""}"
REPO_NAME="${REPO_NAME:-"orchestra-main"}"
SECRET_MANAGER_KEY="${GCP_SECRET_MANAGEMENT_KEY:-""}"
SYNC_DIRECTION="${1:-bidirectional}"  # github-to-gcp, gcp-to-github, or bidirectional

section "Secret Synchronization"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    error "GitHub CLI not found. Please install it first."
    exit 1
fi

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found. Please install it first."
    exit 1
fi

# Authenticate with GitHub if token is provided
if [ -n "$GITHUB_PAT" ]; then
    echo "Authenticating with GitHub..."
    echo "$GITHUB_PAT" | gh auth login --with-token
    success "Authenticated with GitHub"
fi

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

# Authenticate with GCP using Secret Manager key if provided
if [ -n "$SECRET_MANAGER_KEY" ]; then
    echo "Authenticating with GCP using Secret Manager key..."
    echo "$SECRET_MANAGER_KEY" > /tmp/secret-manager-key.json
    gcloud auth activate-service-account --key-file=/tmp/secret-manager-key.json
    success "Authenticated with GCP"
    rm /tmp/secret-manager-key.json
fi

# Define the secrets to synchronize
# Format: "github_secret_name:gcp_secret_name"
SECRETS_TO_SYNC=(
    "GCP_PROJECT_ID:gcp-project-id"
    "GCP_REGION:gcp-region"
    "GCP_WORKLOAD_IDENTITY_PROVIDER:gcp-workload-identity-provider"
    "GCP_SERVICE_ACCOUNT:gcp-service-account"
    "GH_FINE_GRAINED_TOKEN:github-fine-grained-token"
)

# Function to sync from GitHub to GCP
sync_github_to_gcp() {
    section "Syncing from GitHub to GCP"
    
    for secret_pair in "${SECRETS_TO_SYNC[@]}"; do
        # Split the pair
        GITHUB_SECRET=$(echo "$secret_pair" | cut -d':' -f1)
        GCP_SECRET=$(echo "$secret_pair" | cut -d':' -f2)
        
        echo "Syncing $GITHUB_SECRET to $GCP_SECRET..."
        
        # Get the secret from GitHub
        SECRET_VALUE=$(gh secret list --repo "$REPO_OWNER/$REPO_NAME" | grep "$GITHUB_SECRET" > /dev/null && echo "exists" || echo "")
        
        if [ -z "$SECRET_VALUE" ]; then
            warning "Secret $GITHUB_SECRET does not exist in GitHub. Skipping."
            continue
        fi
        
        # For security reasons, we can't directly get the value of a GitHub secret
        # We need to prompt the user for the value
        read -p "Enter the value for $GITHUB_SECRET (leave empty to skip): " -s SECRET_VALUE
        echo ""
        
        if [ -z "$SECRET_VALUE" ]; then
            warning "No value provided for $GITHUB_SECRET. Skipping."
            continue
        fi
        
        # Create or update the secret in GCP Secret Manager
        echo "Updating $GCP_SECRET in GCP Secret Manager..."
        echo -n "$SECRET_VALUE" | gcloud secrets create "$GCP_SECRET" --data-file=- --project="$PROJECT_ID" 2>/dev/null || \
        echo -n "$SECRET_VALUE" | gcloud secrets versions add "$GCP_SECRET" --data-file=- --project="$PROJECT_ID"
        
        success "Synced $GITHUB_SECRET to $GCP_SECRET"
    done
}

# Function to sync from GCP to GitHub
sync_gcp_to_github() {
    section "Syncing from GCP to GitHub"
    
    for secret_pair in "${SECRETS_TO_SYNC[@]}"; do
        # Split the pair
        GITHUB_SECRET=$(echo "$secret_pair" | cut -d':' -f1)
        GCP_SECRET=$(echo "$secret_pair" | cut -d':' -f2)
        
        echo "Syncing $GCP_SECRET to $GITHUB_SECRET..."
        
        # Check if the secret exists in GCP
        if ! gcloud secrets describe "$GCP_SECRET" --project="$PROJECT_ID" &>/dev/null; then
            warning "Secret $GCP_SECRET does not exist in GCP Secret Manager. Skipping."
            continue
        fi
        
        # Get the latest version of the secret
        SECRET_VALUE=$(gcloud secrets versions access latest --secret="$GCP_SECRET" --project="$PROJECT_ID")
        
        if [ -z "$SECRET_VALUE" ]; then
            warning "No value found for $GCP_SECRET. Skipping."
            continue
        fi
        
        # Update the secret in GitHub
        echo "Updating $GITHUB_SECRET in GitHub..."
        echo "$SECRET_VALUE" | gh secret set "$GITHUB_SECRET" --repo "$REPO_OWNER/$REPO_NAME"
        
        success "Synced $GCP_SECRET to $GITHUB_SECRET"
    done
}

# Perform synchronization based on direction
case "$SYNC_DIRECTION" in
    "github-to-gcp")
        sync_github_to_gcp
        ;;
    "gcp-to-github")
        sync_gcp_to_github
        ;;
    "bidirectional"|*)
        # Default to bidirectional sync
        sync_github_to_gcp
        sync_gcp_to_github
        ;;
esac

section "Secret Synchronization Complete"
echo "Secrets have been synchronized between GitHub and GCP Secret Manager."
echo ""
echo "IMPORTANT: For security, consider revoking any temporary tokens used for this process."