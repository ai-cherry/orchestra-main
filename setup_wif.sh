#!/bin/bash
# setup_wif.sh - Unified script for setting up Workload Identity Federation
# This script handles the complete WIF setup process for the AI Orchestra project

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

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    source .env
    success "Loaded environment variables from .env file"
fi

# Default values with fallbacks to environment variables
PROJECT_ID="${GCP_PROJECT_ID:-cherry-ai-project}"
REGION="${GCP_REGION:-us-west4}"
GITHUB_PAT="${GH_CLASSIC_PAT_TOKEN:-${GITHUB_TOKEN:-$(gh auth token 2>/dev/null || echo "")}}"
REPO_OWNER="${REPO_OWNER:-""}"
REPO_NAME="${REPO_NAME:-"orchestra-main"}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-github-actions-wif}"
POOL_NAME="${POOL_NAME:-github-actions-pool}"
PROVIDER_NAME="${PROVIDER_NAME:-github-provider}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --repo-owner)
            REPO_OWNER="$2"
            shift 2
            ;;
        --repo-name)
            REPO_NAME="$2"
            shift 2
            ;;
        --service-account)
            SERVICE_ACCOUNT_NAME="$2"
            shift 2
            ;;
        --pool)
            POOL_NAME="$2"
            shift 2
            ;;
        --provider)
            PROVIDER_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --project PROJECT_ID      GCP project ID (default: $PROJECT_ID)"
            echo "  --region REGION           GCP region (default: $REGION)"
            echo "  --repo-owner OWNER        GitHub repository owner (default: auto-detect)"
            echo "  --repo-name REPO          GitHub repository name (default: $REPO_NAME)"
            echo "  --service-account NAME    Service account name (default: $SERVICE_ACCOUNT_NAME)"
            echo "  --pool NAME               Workload Identity Pool name (default: $POOL_NAME)"
            echo "  --provider NAME           Workload Identity Provider name (default: $PROVIDER_NAME)"
            echo "  --help                    Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

section "Workload Identity Federation Setup"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    warning "GitHub CLI not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux installation
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install gh -y
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS installation
        brew install gh
    else
        error "Unsupported OS. Please install GitHub CLI manually: https://github.com/cli/cli#installation"
        exit 1
    fi
fi

# Validate GitHub token
if [ -z "$GITHUB_PAT" ]; then
    error "GitHub token not available. Please set GH_CLASSIC_PAT_TOKEN or GITHUB_TOKEN environment variable."
    echo "You can also run 'gh auth login' to authenticate with GitHub CLI."
    exit 1
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

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if logged in to gcloud
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

section "Setting up Workload Identity Federation"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
if [[ -z "$PROJECT_NUMBER" ]]; then
    error "Failed to get project number for $PROJECT_ID"
    exit 1
fi
success "Project number: $PROJECT_NUMBER"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable iam.googleapis.com \
    iamcredentials.googleapis.com \
    cloudresourcemanager.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    --quiet

success "Enabled required APIs"

# Create Workload Identity Pool if it doesn't exist
echo "Creating Workload Identity Pool..."
if ! gcloud iam workload-identity-pools describe $POOL_NAME \
    --location="global" \
    --format="value(name)" \
    --project=$PROJECT_ID &>/dev/null; then
    
    gcloud iam workload-identity-pools create $POOL_NAME \
        --location="global" \
        --display-name="GitHub Actions Pool" \
        --description="Identity pool for GitHub Actions" \
        --project=$PROJECT_ID
    
    success "Created Workload Identity Pool: $POOL_NAME"
else
    success "Workload Identity Pool already exists: $POOL_NAME"
fi

# Get the Workload Identity Pool ID
POOL_ID=$(gcloud iam workload-identity-pools describe $POOL_NAME \
    --location="global" \
    --format="value(name)" \
    --project=$PROJECT_ID)

# Create Workload Identity Provider if it doesn't exist
echo "Creating Workload Identity Provider..."
if ! gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --format="value(name)" \
    --project=$PROJECT_ID &>/dev/null; then
    
    gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
        --location="global" \
        --workload-identity-pool=$POOL_NAME \
        --display-name="GitHub Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --project=$PROJECT_ID
    
    success "Created Workload Identity Provider: $PROVIDER_NAME"
else
    success "Workload Identity Provider already exists: $PROVIDER_NAME"
fi

# Get the Workload Identity Provider ID
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --format="value(name)" \
    --project=$PROJECT_ID)

# Create service account if it doesn't exist
echo "Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --project=$PROJECT_ID &>/dev/null; then
    
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="GitHub Actions Service Account" \
        --description="Service account for GitHub Actions deployments" \
        --project=$PROJECT_ID
    
    success "Created service account: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
else
    success "Service account already exists: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
fi

# Grant necessary roles to the service account
echo "Granting roles to service account..."
for role in "roles/run.admin" "roles/storage.admin" "roles/artifactregistry.admin" "roles/iam.serviceAccountUser"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="$role" \
        --quiet
    
    success "Granted $role to service account"
done

# Allow GitHub Actions to impersonate the service account
echo "Setting up service account impersonation..."
FULL_REPO="$REPO_OWNER/$REPO_NAME"
PRINCIPAL="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$FULL_REPO"

gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --member="$PRINCIPAL" \
    --role="roles/iam.workloadIdentityUser" \
    --project=$PROJECT_ID

success "Allowed GitHub Actions to impersonate the service account"

# Construct the Workload Identity Provider resource name
WIF_PROVIDER="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/providers/$PROVIDER_NAME"
WIF_SERVICE_ACCOUNT="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

section "Setting up GitHub secrets"

# Set up GitHub secrets
echo "Setting up GitHub secrets..."
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID" --repo "$REPO_OWNER/$REPO_NAME"
gh secret set GCP_REGION --body "$REGION" --repo "$REPO_OWNER/$REPO_NAME"
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body "$WIF_PROVIDER" --repo "$REPO_OWNER/$REPO_NAME"
gh secret set GCP_SERVICE_ACCOUNT --body "$WIF_SERVICE_ACCOUNT" --repo "$REPO_OWNER/$REPO_NAME"

success "Set up GitHub secrets"

section "Verifying setup"

# Verify the setup
echo "Verifying Workload Identity Federation setup..."
echo "Project ID: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "Repository: $REPO_OWNER/$REPO_NAME"
echo "Workload Identity Pool: $POOL_NAME"
echo "Workload Identity Provider: $PROVIDER_NAME"
echo "Service Account: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
echo "WIF Provider Resource: $WIF_PROVIDER"

# Create .github/workflows directory if it doesn't exist
if [ ! -d ".github/workflows" ]; then
    echo "Creating .github/workflows directory..."
    mkdir -p .github/workflows
    success "Created .github/workflows directory"
fi

section "Setup Complete"

echo "Workload Identity Federation has been successfully set up!"
echo ""
echo "The following GitHub secrets have been set:"
echo "- GCP_PROJECT_ID: $PROJECT_ID"
echo "- GCP_REGION: $REGION"
echo "- GCP_WORKLOAD_IDENTITY_PROVIDER: $WIF_PROVIDER"
echo "- GCP_SERVICE_ACCOUNT: $WIF_SERVICE_ACCOUNT"
echo ""
echo "To use Workload Identity Federation in your GitHub Actions workflows:"
echo "1. Add the following permissions to your workflow:"
echo "   permissions:"
echo "     contents: read"
echo "     id-token: write"
echo ""
echo "2. Add the following authentication step:"
echo "   - name: Google Auth via Workload Identity Federation"
echo "     uses: google-github-actions/auth@v2"
echo "     with:"
echo "       workload_identity_provider: \${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}"
echo "       service_account: \${{ secrets.GCP_SERVICE_ACCOUNT }}"
echo ""
echo "For a complete example, see the wif-deploy.yml workflow in the .github/workflows directory."