#!/bin/bash
# setup_workload_identity_federation.sh
#
# This script sets up Workload Identity Federation for securely authenticating 
# GitHub Actions workflows with GCP, eliminating the need for service account keys.
#
# Usage:
#   ./setup_workload_identity_federation.sh --project-id=YOUR_PROJECT_ID --github-repo=YOUR_ORG/YOUR_REPO
#
# Security benefits:
#   - No service account keys needed (more secure than key-based auth)
#   - Short-lived tokens instead of long-lived credentials
#   - Limited scope based on GitHub repository/branch
#   - Detailed audit logging of all authentications

set -e

# Parse arguments
for arg in "$@"; do
  case $arg in
    --project-id=*)
    PROJECT_ID="${arg#*=}"
    shift
    ;;
    --github-repo=*)
    GITHUB_REPO="${arg#*=}"
    shift
    ;;
    --service-account=*)
    SERVICE_ACCOUNT="${arg#*=}"
    shift
    ;;
    --pool-id=*)
    POOL_ID="${arg#*=}"
    shift
    ;;
    --provider-id=*)
    PROVIDER_ID="${arg#*=}"
    shift
    ;;
    --branch=*)
    BRANCH="${arg#*=}"
    shift
    ;;
    *)
    # Unknown option
    ;;
  esac
done

# Set defaults if not provided
POOL_ID=${POOL_ID:-"github-actions-pool"}
PROVIDER_ID=${PROVIDER_ID:-"github-provider"}
BRANCH=${BRANCH:-"main"}
SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-"vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com"}

# Validate required arguments
if [ -z "$PROJECT_ID" ]; then
  echo "Error: --project-id is required"
  exit 1
fi

if [ -z "$GITHUB_REPO" ]; then
  echo "Error: --github-repo is required (format: org/repo)"
  exit 1
fi

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project=$PROJECT_ID

echo "APIs enabled successfully."

# Create workload identity pool
echo "Creating workload identity pool: $POOL_ID"
gcloud iam workload-identity-pools create $POOL_ID \
  --location="global" \
  --description="GitHub Actions federation" \
  --project=$PROJECT_ID

# Get the workload identity pool ID
WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe $POOL_ID \
  --location="global" \
  --project=$PROJECT_ID \
  --format="value(name)")

echo "Workload identity pool created: $WORKLOAD_IDENTITY_POOL_ID"

# Configure OIDC provider
echo "Creating OIDC provider: $PROVIDER_ID"
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_ID \
  --workload-identity-pool=$POOL_ID \
  --location="global" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub" \
  --project=$PROJECT_ID

# Extract project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Grant Workload Identity User role to the GitHub repository
echo "Granting Workload Identity User role to GitHub repository: $GITHUB_REPO"
gcloud iam service-accounts add-iam-policy-binding \
  $SERVICE_ACCOUNT \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_ID/attribute.repository/$GITHUB_REPO" \
  --project=$PROJECT_ID

# Add branch-specific binding
echo "Adding branch-specific binding for branch: $BRANCH"
gcloud iam service-accounts add-iam-policy-binding \
  $SERVICE_ACCOUNT \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_ID/attribute.ref/refs/heads/$BRANCH" \
  --project=$PROJECT_ID

# Output workload identity provider
WORKLOAD_IDENTITY_PROVIDER="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_ID/providers/$PROVIDER_ID"
echo ""
echo "======================================================="
echo "Setup Complete! Use the following configuration in your GitHub Actions workflow:"
echo ""
echo "Workload Identity Provider:"
echo "$WORKLOAD_IDENTITY_PROVIDER"
echo ""
echo "Service Account:"
echo "$SERVICE_ACCOUNT"
echo ""
echo "GitHub Action Example:"
echo "- name: Authenticate to Google Cloud"
echo "  uses: google-github-actions/auth@v1"
echo "  with:"
echo "    workload_identity_provider: $WORKLOAD_IDENTITY_PROVIDER"
echo "    service_account: $SERVICE_ACCOUNT"
echo "======================================================="
