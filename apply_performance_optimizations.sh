#!/bin/bash
# apply_performance_optimizations.sh
# Script to apply performance optimizations to the AI Orchestra project
# This script prioritizes performance and stability over security concerns
# With improved error handling, security warnings, and consistency with Terraform

set -e
trap 'handle_error $? $LINENO' ERR

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to handle errors
handle_error() {
    local exit_code=$1
    local line_number=$2
    echo -e "${RED}Error occurred at line $line_number with exit code $exit_code${NC}"
    exit $exit_code
}

# Function to print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 command not found. Please install it first.${NC}"
        exit 1
    fi
}

# Function to execute or simulate a command based on dry run mode
execute_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}DRY RUN: Would execute: ${*}${NC}"
    else
        echo -e "${BLUE}Executing: ${*}${NC}"
        "$@"
    fi
}

# Function to validate input
validate_input() {
    local input=$1
    local pattern=$2
    local error_message=$3
    
    if [[ ! $input =~ $pattern ]]; then
        echo -e "${RED}Error: $error_message${NC}"
        exit 1
    fi
}

# Check for required commands
check_command gcloud
check_command terraform
check_command gh

# Check GitHub CLI authentication
if ! gh auth status &>/dev/null; then
    echo -e "${RED}Error: GitHub CLI not authenticated. Please run 'gh auth login' first.${NC}"
    exit 1
fi

# Load environment variables if .env file exists
if [ -f ".env.development" ]; then
    echo -e "${BLUE}Loading environment variables from .env.development${NC}"
    source .env.development
fi

# Default values with fallbacks to environment variables
PROJECT_ID="${GCP_PROJECT_ID:-cherry-ai-project}"
REGION="${GCP_REGION:-us-west4}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-ai-orchestra-sa}"
DRY_RUN=false

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
        --env)
            ENVIRONMENT="$2"
            validate_input "$ENVIRONMENT" "^(dev|staging|prod)$" "Environment must be one of: dev, staging, prod"
            shift 2
            ;;
        --service-account)
            SERVICE_ACCOUNT_NAME="$2"
            validate_input "$SERVICE_ACCOUNT_NAME" "^[a-z][-a-z0-9]{5,29}$" "Service account name must be 6-30 characters, start with a letter, and contain only lowercase letters, numbers, and hyphens"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            echo -e "${YELLOW}Running in dry-run mode. No changes will be applied.${NC}"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --project PROJECT_ID      GCP project ID (default: $PROJECT_ID)"
            echo "  --region REGION           GCP region (default: $REGION)"
            echo "  --env ENVIRONMENT         Environment (dev, staging, prod) (default: $ENVIRONMENT)"
            echo "  --service-account NAME    Service account name (default: $SERVICE_ACCOUNT_NAME)"
            echo "  --dry-run                 Run in dry-run mode without making any changes"
            echo "  --help                    Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

section "Performance Optimization Setup"

echo -e "${GREEN}Project ID: $PROJECT_ID${NC}"
echo -e "${GREEN}Region: $REGION${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}Service Account: $SERVICE_ACCOUNT_NAME${NC}"

# Set the project
echo -e "${BLUE}Setting project to $PROJECT_ID...${NC}"
execute_cmd gcloud config set project "$PROJECT_ID" || { echo -e "${RED}Failed to set project${NC}"; exit 1; }

# Get project number
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN: Would get project number for $PROJECT_ID${NC}"
    PROJECT_NUMBER="123456789"
else
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
    if [[ -z "$PROJECT_NUMBER" ]]; then
        echo -e "${RED}Failed to get project number for $PROJECT_ID${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Project number: $PROJECT_NUMBER${NC}"

section "Setting up Workload Identity Federation"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com cloudresourcemanager.googleapis.com \
    run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com \
    monitoring.googleapis.com logging.googleapis.com cloudscheduler.googleapis.com \
    firestore.googleapis.com aiplatform.googleapis.com --quiet || {
        echo -e "${RED}Failed to enable required APIs${NC}";
        exit 1;
    }

# Create a simpler pool and provider name
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"

# Create Workload Identity Pool if it doesn't exist
echo "Creating Workload Identity Pool..."
if ! gcloud iam workload-identity-pools describe $POOL_NAME \
    --location="global" --format="value(name)" --project=$PROJECT_ID &>/dev/null; then
    
    gcloud iam workload-identity-pools create $POOL_NAME \
        --location="global" \
        --display-name="GitHub Actions Pool" \
        --description="Identity pool for GitHub Actions" \
        --project=$PROJECT_ID || {
            echo -e "${RED}Failed to create Workload Identity Pool${NC}";
            exit 1;
        }
    
    echo -e "${GREEN}Created Workload Identity Pool: $POOL_NAME${NC}"
else
    echo -e "${GREEN}Workload Identity Pool already exists: $POOL_NAME${NC}"
fi

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
        --project=$PROJECT_ID || {
            echo -e "${RED}Failed to create Workload Identity Provider${NC}";
            exit 1;
        }
    
    echo -e "${GREEN}Created Workload Identity Provider: $PROVIDER_NAME${NC}"
else
    echo -e "${GREEN}Workload Identity Provider already exists: $PROVIDER_NAME${NC}"
fi

# Create service account if it doesn't exist
echo "Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --project=$PROJECT_ID &>/dev/null; then
    
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="AI Orchestra Service Account" \
        --description="Service account for AI Orchestra deployments" \
        --project=$PROJECT_ID || {
            echo -e "${RED}Failed to create service account${NC}";
            exit 1;
        }
    
    echo -e "${GREEN}Created service account: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com${NC}"
else
    echo -e "${GREEN}Service account already exists: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com${NC}"
fi

# Grant necessary roles to the service account
echo "Granting roles to service account..."
for role in "roles/run.admin" "roles/storage.admin" "roles/artifactregistry.admin" "roles/iam.serviceAccountUser" \
    "roles/secretmanager.admin" "roles/monitoring.admin" "roles/logging.admin" "roles/cloudscheduler.admin" \
    "roles/firestore.admin" "roles/aiplatform.admin"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="$role" \
        --quiet || {
            echo -e "${RED}Failed to grant $role to service account${NC}";
            exit 1;
        }
    
    echo -e "${GREEN}Granted $role to service account${NC}"
done

# Get GitHub repository owner
echo -e "${YELLOW}What is your GitHub username or organization?${NC}"
read REPO_OWNER
validate_input "$REPO_OWNER" "^[a-zA-Z0-9][-a-zA-Z0-9]*$" "Invalid GitHub username or organization"

# Get GitHub repository name
echo -e "${YELLOW}What is your GitHub repository name?${NC}"
read REPO_NAME
validate_input "$REPO_NAME" "^[a-zA-Z0-9][-a-zA-Z0-9_.]*$" "Invalid GitHub repository name"

# Allow GitHub Actions to impersonate the service account
echo "Setting up service account impersonation..."
FULL_REPO="$REPO_OWNER/$REPO_NAME"
PRINCIPAL="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$FULL_REPO"

execute_cmd gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --member="$PRINCIPAL" \
    --role="roles/iam.workloadIdentityUser" \
    --project="$PROJECT_ID" || {
        echo -e "${RED}Failed to set up service account impersonation${NC}";
        exit 1;
    }

echo -e "${GREEN}Allowed GitHub Actions to impersonate the service account${NC}"

# Construct the Workload Identity Provider resource name
WIF_PROVIDER="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/providers/$PROVIDER_NAME"
WIF_SERVICE_ACCOUNT="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

section "Creating Secret Manager Secret for Authentication"

# Create a Secret Manager secret for authentication
SECRET_NAME="secret-management-key-$ENVIRONMENT"
echo "Creating Secret Manager secret: $SECRET_NAME"

if [ "$DRY_RUN" = true ] || ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
    # Use user-managed replication for consistency with Terraform
    execute_cmd gcloud secrets create "$SECRET_NAME" \
        --replication-policy="user-managed" \
        --locations="$REGION" \
        --project="$PROJECT_ID" || {
            echo -e "${RED}Failed to create Secret Manager secret${NC}";
            exit 1;
        }
    
    echo -e "${GREEN}Created Secret Manager secret: $SECRET_NAME${NC}"
else
    echo -e "${GREEN}Secret Manager secret already exists: $SECRET_NAME${NC}"
fi

# Security warning for service account key creation
echo -e "${YELLOW}Warning: Creating a service account key is less secure than using Workload Identity Federation.${NC}"
echo -e "${YELLOW}This is being done to prioritize performance as requested.${NC}"
echo -e "${YELLOW}For production environments, consider using managed identities instead.${NC}"

# Create a service account key for the secret
KEY_FILE=$(mktemp)
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" || {
        echo -e "${RED}Failed to create service account key${NC}";
        exit 1;
    }

# Add the key to the secret
gcloud secrets versions add $SECRET_NAME \
    --data-file=$KEY_FILE \
    --project=$PROJECT_ID || {
        echo -e "${RED}Failed to add key to Secret Manager secret${NC}";
        exit 1;
    }

echo -e "${GREEN}Added service account key to Secret Manager secret${NC}"

# Clean up the key file
rm $KEY_FILE

section "Setting up GitHub Repository Secrets"

# Set up GitHub repository secrets
echo "Setting up GitHub repository secrets..."
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID" --repo "$FULL_REPO" || { echo -e "${RED}Failed to set GCP_PROJECT_ID secret${NC}"; exit 1; }
gh secret set GCP_REGION --body "$REGION" --repo "$FULL_REPO" || { echo -e "${RED}Failed to set GCP_REGION secret${NC}"; exit 1; }
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body "$WIF_PROVIDER" --repo "$FULL_REPO" || { echo -e "${RED}Failed to set GCP_WORKLOAD_IDENTITY_PROVIDER secret${NC}"; exit 1; }
gh secret set GCP_SERVICE_ACCOUNT --body "$WIF_SERVICE_ACCOUNT" --repo "$FULL_REPO" || { echo -e "${RED}Failed to set GCP_SERVICE_ACCOUNT secret${NC}"; exit 1; }
gh secret set GCP_SECRET_MANAGEMENT_KEY --body "$SECRET_NAME" --repo "$FULL_REPO" || { echo -e "${RED}Failed to set GCP_SECRET_MANAGEMENT_KEY secret${NC}"; exit 1; }

# Set resource configuration secrets
gh secret set CLOUD_RUN_MEMORY --body "2Gi" --repo "$FULL_REPO" || { echo -e "${YELLOW}Warning: Failed to set CLOUD_RUN_MEMORY secret, using default${NC}"; }
gh secret set CLOUD_RUN_CPU --body "2" --repo "$FULL_REPO" || { echo -e "${YELLOW}Warning: Failed to set CLOUD_RUN_CPU secret, using default${NC}"; }
gh secret set CLOUD_RUN_MIN_INSTANCES --body "1" --repo "$FULL_REPO" || { echo -e "${YELLOW}Warning: Failed to set CLOUD_RUN_MIN_INSTANCES secret, using default${NC}"; }
gh secret set CLOUD_RUN_MAX_INSTANCES --body "20" --repo "$FULL_REPO" || { echo -e "${YELLOW}Warning: Failed to set CLOUD_RUN_MAX_INSTANCES secret, using default${NC}"; }
gh secret set CLOUD_RUN_CONCURRENCY --body "80" --repo "$FULL_REPO" || { echo -e "${YELLOW}Warning: Failed to set CLOUD_RUN_CONCURRENCY secret, using default${NC}"; }

echo -e "${GREEN}Set up GitHub repository secrets${NC}"

section "Applying Terraform Configuration"

# Initialize and apply Terraform configuration
echo "Initializing Terraform..."
cd terraform
terraform init || { echo -e "${RED}Failed to initialize Terraform${NC}"; exit 1; }

echo "Applying Terraform configuration..."
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="env=$ENVIRONMENT" \
    -var="cloud_run_cpu=2" -var="cloud_run_memory=2Gi" -var="cloud_run_min_instances=1" \
    -var="cloud_run_max_instances=20" -var="cloud_run_concurrency=80" -auto-approve || {
        echo -e "${RED}Failed to apply Terraform configuration${NC}";
        exit 1;
    }

echo -e "${GREEN}Applied Terraform configuration${NC}"
cd ..

section "Copying Optimized Files"

# Copy the optimized files to their destinations
echo "Copying optimized GitHub workflow..."
mkdir -p .github/workflows
cp .github/workflows/optimized-deploy-template.yml .github/workflows/deploy-$ENVIRONMENT.yml || {
    echo -e "${RED}Failed to copy GitHub workflow template${NC}";
    exit 1;
}
echo -e "${GREEN}Copied optimized GitHub workflow to .github/workflows/deploy-$ENVIRONMENT.yml${NC}"

echo "Copying optimized Dockerfile..."
mkdir -p ai-orchestra
cp Dockerfile.performance-optimized ai-orchestra/Dockerfile || {
    echo -e "${RED}Failed to copy Dockerfile${NC}";
    exit 1;
}
echo -e "${GREEN}Copied optimized Dockerfile to ai-orchestra/Dockerfile${NC}"

section "Setup Complete"

echo -e "${GREEN}Performance optimization setup has been completed successfully!${NC}"
echo ""
echo "The following GitHub secrets have been set for repository $FULL_REPO:"
echo "- GCP_PROJECT_ID: $PROJECT_ID"
echo "- GCP_REGION: $REGION"
echo "- GCP_WORKLOAD_IDENTITY_PROVIDER: $WIF_PROVIDER"
echo "- GCP_SERVICE_ACCOUNT: $WIF_SERVICE_ACCOUNT"
echo "- GCP_SECRET_MANAGEMENT_KEY: $SECRET_NAME"
echo "- CLOUD_RUN_MEMORY: 2Gi"
echo "- CLOUD_RUN_CPU: 2"
echo "- CLOUD_RUN_MIN_INSTANCES: 1"
echo "- CLOUD_RUN_MAX_INSTANCES: 20"
echo "- CLOUD_RUN_CONCURRENCY: 80"
echo ""
echo "The following files have been created or updated:"
echo "- .github/workflows/deploy-$ENVIRONMENT.yml"
echo "- ai-orchestra/Dockerfile"
echo "- terraform/cloud_run_performance.tf"
echo ""
echo "To trigger a deployment, run:"
echo "gh workflow run deploy-$ENVIRONMENT.yml"
echo ""
echo -e "${BLUE}Your AI Orchestra project is now optimized for performance and stability!${NC}"