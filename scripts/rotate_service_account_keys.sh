#!/bin/bash
# rotate_service_account_keys.sh - Securely rotate GCP service account keys
# This script rotates GCP service account keys and updates them in both GitHub Actions secrets and GCP Secret Manager

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
REPO_OWNER="${REPO_OWNER:-""}"
REPO_NAME="${REPO_NAME:-"orchestra-main"}"
SECRET_MANAGER_KEY="${GCP_SECRET_MANAGEMENT_KEY:-""}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-"github-actions-sa"}"

section "GCP Service Account Key Rotation"

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

# Check if service account exists
echo "Checking if service account exists..."
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" &>/dev/null; then
    error "Service account $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com does not exist."
    exit 1
fi
success "Service account exists"

# Create a new service account key
section "Creating New Service Account Key"
echo "Creating new service account key..."
KEY_FILE="/tmp/$SERVICE_ACCOUNT_NAME-$(date +%Y%m%d%H%M%S).json"
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --project="$PROJECT_ID"
success "Created new service account key: $KEY_FILE"

# Store the new key in GitHub Actions secrets
section "Updating GitHub Secrets"
echo "Updating GCP_SA_KEY in GitHub Actions secrets..."
gh secret set GCP_SA_KEY --body "$(cat "$KEY_FILE")" --repo "$REPO_OWNER/$REPO_NAME"
success "Updated GCP_SA_KEY in GitHub Actions secrets"

# Store the new key in GCP Secret Manager
section "Updating GCP Secret Manager"
echo "Updating gcp-service-account-key in GCP Secret Manager..."
gcloud secrets create gcp-service-account-key --data-file="$KEY_FILE" --project="$PROJECT_ID" 2>/dev/null || \
gcloud secrets versions add gcp-service-account-key --data-file="$KEY_FILE" --project="$PROJECT_ID"
success "Updated gcp-service-account-key in GCP Secret Manager"

# List existing keys for the service account
section "Managing Existing Keys"
echo "Listing existing keys for service account..."
KEYS=$(gcloud iam service-accounts keys list \
    --iam-account="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --project="$PROJECT_ID" \
    --format="value(name)")

# Count the number of keys
KEY_COUNT=$(echo "$KEYS" | wc -l)
echo "Found $KEY_COUNT keys for service account"

# If there are more than 2 keys, delete the oldest ones
if [ "$KEY_COUNT" -gt 2 ]; then
    echo "More than 2 keys found. Deleting oldest keys..."
    
    # Sort keys by creation time and keep only the oldest ones to delete
    KEYS_TO_DELETE=$(echo "$KEYS" | sort | head -n $(($KEY_COUNT - 2)))
    
    # Delete each old key
    for KEY in $KEYS_TO_DELETE; do
        KEY_ID=$(echo "$KEY" | awk -F'/' '{print $NF}')
        echo "Deleting key: $KEY_ID"
        gcloud iam service-accounts keys delete "$KEY_ID" \
            --iam-account="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
            --project="$PROJECT_ID" \
            --quiet
        success "Deleted key: $KEY_ID"
    done
fi

# Clean up the temporary key file
rm "$KEY_FILE"
success "Cleaned up temporary key file"

section "Service Account Key Rotation Complete"
echo "GCP service account key has been successfully rotated and synchronized between GitHub Actions and GCP Secret Manager."
echo ""
echo "The new key is now active and ready for use in your workflows."
echo ""
echo "IMPORTANT: Old keys have been automatically cleaned up to maintain security."