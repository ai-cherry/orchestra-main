#!/bin/bash
# verify_wif_setup.sh - Script to verify Workload Identity Federation setup
# This script checks if the WIF setup is correctly configured for the AI Orchestra project

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

section "Workload Identity Federation Verification"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    error "GitHub CLI not found. Please install it first."
    echo "Visit https://github.com/cli/cli#installation for installation instructions."
    exit 1
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
success "Repository access verified"

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

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
if [[ -z "$PROJECT_NUMBER" ]]; then
    error "Failed to get project number for $PROJECT_ID"
    exit 1
fi
success "Project number: $PROJECT_NUMBER"

section "Verifying GitHub Secrets"

# Function to check if a secret exists
check_secret() {
    local secret_name=$1
    local required=$2
    
    echo -e "Checking for secret: ${secret_name}..."
    
    # Use GitHub API to check if the secret exists
    response=$(gh api "/repos/${REPO_OWNER}/${REPO_NAME}/actions/secrets/${secret_name}" 2>/dev/null || echo '{"message": "Not Found"}')
    
    if echo "$response" | grep -q "Not Found"; then
        if [ "$required" = "true" ]; then
            error "Required secret ${secret_name} not found"
            return 1
        else
            warning "Optional secret ${secret_name} not found"
            return 0
        fi
    else
        success "Secret ${secret_name} found"
        return 0
    fi
}

# Check for required secrets
echo "Checking required GitHub secrets..."
required_secrets=(
    "GCP_PROJECT_ID"
    "GCP_REGION"
    "GCP_WORKLOAD_IDENTITY_PROVIDER"
    "GCP_SERVICE_ACCOUNT"
)

missing_required=0
for secret in "${required_secrets[@]}"; do
    if ! check_secret "$secret" "true"; then
        missing_required=$((missing_required + 1))
    fi
done

if [ $missing_required -gt 0 ]; then
    error "$missing_required required secrets are missing"
    echo "Please run setup_wif.sh to set up the required secrets"
else
    success "All required secrets are available"
fi

section "Verifying Workload Identity Pool"

# Check if Workload Identity Pool exists
echo "Checking Workload Identity Pool..."
POOL_ID=$(gcloud iam workload-identity-pools describe $POOL_NAME \
    --location="global" \
    --format="value(name)" \
    --project=$PROJECT_ID 2>/dev/null || echo "")

if [[ -z "$POOL_ID" ]]; then
    error "Workload Identity Pool $POOL_NAME not found"
    echo "Please run setup_wif.sh to create the Workload Identity Pool"
    exit 1
fi
success "Workload Identity Pool exists: $POOL_NAME"

section "Verifying Workload Identity Provider"

# Check if Workload Identity Provider exists
echo "Checking Workload Identity Provider..."
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool=$POOL_NAME \
    --format="value(name)" \
    --project=$PROJECT_ID 2>/dev/null || echo "")

if [[ -z "$PROVIDER_ID" ]]; then
    error "Workload Identity Provider $PROVIDER_NAME not found"
    echo "Please run setup_wif.sh to create the Workload Identity Provider"
    exit 1
fi
success "Workload Identity Provider exists: $PROVIDER_NAME"

section "Verifying Service Account"

# Check if service account exists
echo "Checking service account..."
SA_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
SA_EXISTS=$(gcloud iam service-accounts describe $SA_EMAIL \
    --project=$PROJECT_ID \
    --format="value(email)" 2>/dev/null || echo "")

if [[ -z "$SA_EXISTS" ]]; then
    error "Service account $SA_EMAIL not found"
    echo "Please run setup_wif.sh to create the service account"
    exit 1
fi
success "Service account exists: $SA_EMAIL"

# Check service account roles
echo "Checking service account roles..."
required_roles=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/artifactregistry.admin"
    "roles/iam.serviceAccountUser"
)

missing_roles=0
for role in "${required_roles[@]}"; do
    echo "Checking role: $role..."
    has_role=$(gcloud projects get-iam-policy $PROJECT_ID \
        --format="json" | jq -r --arg EMAIL "$SA_EMAIL" --arg ROLE "$role" \
        '.bindings[] | select(.role == $ROLE) | .members[] | select(. == "serviceAccount:" + $EMAIL)' 2>/dev/null || echo "")
    
    if [[ -z "$has_role" ]]; then
        error "Service account does not have role: $role"
        missing_roles=$((missing_roles + 1))
    else
        success "Service account has role: $role"
    fi
done

if [ $missing_roles -gt 0 ]; then
    error "$missing_roles required roles are missing"
    echo "Please run setup_wif.sh to grant the required roles"
else
    success "Service account has all required roles"
fi

section "Verifying Workload Identity Binding"

# Check if service account has workload identity binding
echo "Checking workload identity binding..."
FULL_REPO="$REPO_OWNER/$REPO_NAME"
PRINCIPAL="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$FULL_REPO"

has_binding=$(gcloud iam service-accounts get-iam-policy $SA_EMAIL \
    --project=$PROJECT_ID \
    --format="json" | jq -r --arg PRINCIPAL "$PRINCIPAL" --arg ROLE "roles/iam.workloadIdentityUser" \
    '.bindings[] | select(.role == $ROLE) | .members[] | select(. == $PRINCIPAL)' 2>/dev/null || echo "")

if [[ -z "$has_binding" ]]; then
    error "Service account does not have workload identity binding for repository: $FULL_REPO"
    echo "Please run setup_wif.sh to set up the workload identity binding"
    exit 1
fi
success "Service account has workload identity binding for repository: $FULL_REPO"

section "Verifying GitHub Actions Workflow"

# Check if GitHub Actions workflow exists
echo "Checking GitHub Actions workflow..."
if [ -f ".github/workflows/wif-deploy.yml" ]; then
    success "GitHub Actions workflow exists: .github/workflows/wif-deploy.yml"
else
    warning "GitHub Actions workflow not found: .github/workflows/wif-deploy.yml"
    echo "You can use the template at .github/workflows/wif-deploy-template.yml to create your workflow"
fi

section "Verification Summary"

# Print summary
echo "Workload Identity Federation setup verification summary:"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "Repository: $REPO_OWNER/$REPO_NAME"
echo "Workload Identity Pool: $POOL_NAME"
echo "Workload Identity Provider: $PROVIDER_NAME"
echo "Service Account: $SA_EMAIL"
echo ""

if [ $missing_required -gt 0 ] || [ $missing_roles -gt 0 ]; then
    error "Verification failed. Please fix the issues above."
    exit 1
else
    success "Workload Identity Federation setup is correctly configured!"
    echo ""
    echo "You can now use Workload Identity Federation in your GitHub Actions workflows."
    echo "See the template at .github/workflows/wif-deploy-template.yml for an example."
fi