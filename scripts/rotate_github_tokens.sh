#!/bin/bash
# rotate_github_tokens.sh - Securely rotate GitHub tokens and sync with GCP Secret Manager
# This script rotates GitHub tokens and updates them in both GitHub Actions secrets and GCP Secret Manager

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

section "GitHub Token Rotation"

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

# Generate new GitHub fine-grained token (this requires manual intervention)
section "Generate New GitHub Fine-Grained Token"
echo "Please generate a new GitHub fine-grained token with the following scopes:"
echo "- Repository: contents:read, deployments:write, actions:write"
echo "- Workflow: read and write"
echo "- Packages: read and write"
echo ""
echo "Visit: https://github.com/settings/tokens?type=beta"
echo ""
read -p "Enter your new GitHub fine-grained token: " NEW_FINE_GRAINED_TOKEN

if [ -z "$NEW_FINE_GRAINED_TOKEN" ]; then
    error "No token provided. Exiting."
    exit 1
fi

# Store the new token in GitHub Actions secrets
section "Updating GitHub Secrets"
echo "Updating GH_FINE_GRAINED_TOKEN in GitHub Actions secrets..."
gh secret set GH_FINE_GRAINED_TOKEN --body "$NEW_FINE_GRAINED_TOKEN" --repo "$REPO_OWNER/$REPO_NAME"
success "Updated GH_FINE_GRAINED_TOKEN in GitHub Actions secrets"

# Store the new token in GCP Secret Manager
section "Updating GCP Secret Manager"
echo "Updating github-fine-grained-token in GCP Secret Manager..."
echo -n "$NEW_FINE_GRAINED_TOKEN" | gcloud secrets create github-fine-grained-token --data-file=- --project="$PROJECT_ID" 2>/dev/null || \
echo -n "$NEW_FINE_GRAINED_TOKEN" | gcloud secrets versions add github-fine-grained-token --data-file=- --project="$PROJECT_ID"
success "Updated github-fine-grained-token in GCP Secret Manager"

section "Token Rotation Complete"
echo "GitHub token has been successfully rotated and synchronized between GitHub Actions and GCP Secret Manager."
echo ""
echo "The new token is now active and ready for use in your workflows."
echo ""
echo "IMPORTANT: For security, consider revoking the old token if it's no longer needed."
echo "Visit https://github.com/settings/tokens to manage your tokens."