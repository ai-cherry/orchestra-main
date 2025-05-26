#!/bin/bash
# Setup GitHub Secrets for AI Orchestra CI/CD
# ===========================================

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GITHUB_REPO="${GITHUB_REPOSITORY:-}"
GCP_PROJECT_ID="${GCP_PROJECT_ID:-}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check for GitHub CLI
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed. Install it from: https://cli.github.com/"
        exit 1
    fi

    # Check GitHub authentication
    if ! gh auth status &> /dev/null; then
        log_error "Not authenticated with GitHub. Run: gh auth login"
        exit 1
    fi

    # Check environment variables
    if [[ -z "$GITHUB_REPO" ]]; then
        log_error "GITHUB_REPOSITORY environment variable not set (format: owner/repo)"
        exit 1
    fi

    if [[ -z "$GCP_PROJECT_ID" ]]; then
        log_error "GCP_PROJECT_ID environment variable not set"
        exit 1
    fi

    log_success "Prerequisites checked"
}

setup_workload_identity() {
    log_info "Setting up Workload Identity Federation..."

    # Create service account for GitHub Actions
    SA_NAME="github-actions-sa"
    SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

    # Create service account
    gcloud iam service-accounts create $SA_NAME \
        --display-name="GitHub Actions Service Account" \
        --project=$GCP_PROJECT_ID || true

    # Grant necessary permissions
    log_info "Granting permissions to service account..."

    roles=(
        "roles/container.developer"
        "roles/storage.admin"
        "roles/artifactregistry.writer"
        "roles/iam.serviceAccountUser"
    )

    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
            --member="serviceAccount:${SA_EMAIL}" \
            --role="$role" \
            --condition=None
    done

    # Create Workload Identity Pool
    POOL_NAME="github-actions-pool"
    PROVIDER_NAME="github-provider"

    log_info "Creating Workload Identity Pool..."
    gcloud iam workload-identity-pools create $POOL_NAME \
        --location="global" \
        --display-name="GitHub Actions Pool" \
        --project=$GCP_PROJECT_ID || true

    # Create Workload Identity Provider
    log_info "Creating Workload Identity Provider..."
    gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
        --location="global" \
        --workload-identity-pool=$POOL_NAME \
        --display-name="GitHub Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --project=$GCP_PROJECT_ID || true

    # Get provider resource name
    PROVIDER_RESOURCE=$(gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
        --location="global" \
        --workload-identity-pool=$POOL_NAME \
        --project=$GCP_PROJECT_ID \
        --format="value(name)")

    # Grant service account access
    log_info "Configuring service account impersonation..."
    gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
        --role="roles/iam.workloadIdentityUser" \
        --member="principalSet://iam.googleapis.com/${PROVIDER_RESOURCE}/attribute.repository/${GITHUB_REPO}" \
        --project=$GCP_PROJECT_ID

    echo
    log_success "Workload Identity Federation configured!"
    echo "WIF_PROVIDER: ${PROVIDER_RESOURCE}"
    echo "WIF_SERVICE_ACCOUNT: ${SA_EMAIL}"
}

set_github_secrets() {
    log_info "Setting GitHub repository secrets..."

    # Get Pulumi access token
    read -sp "Enter your Pulumi Access Token: " PULUMI_TOKEN
    echo

    # Set secrets
    log_info "Setting PULUMI_ACCESS_TOKEN..."
    echo "$PULUMI_TOKEN" | gh secret set PULUMI_ACCESS_TOKEN --repo=$GITHUB_REPO

    log_info "Setting GCP_PROJECT_ID..."
    echo "$GCP_PROJECT_ID" | gh secret set GCP_PROJECT_ID --repo=$GITHUB_REPO

    log_info "Setting WIF_PROVIDER..."
    echo "$PROVIDER_RESOURCE" | gh secret set WIF_PROVIDER --repo=$GITHUB_REPO

    log_info "Setting WIF_SERVICE_ACCOUNT..."
    echo "$SA_EMAIL" | gh secret set WIF_SERVICE_ACCOUNT --repo=$GITHUB_REPO

    # Optional secrets
    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        log_info "Setting SLACK_WEBHOOK..."
        echo "$SLACK_WEBHOOK" | gh secret set SLACK_WEBHOOK --repo=$GITHUB_REPO
    fi

    log_success "GitHub secrets configured!"
}

print_summary() {
    echo
    echo -e "${GREEN}=== Setup Complete ===${NC}"
    echo
    echo "GitHub Actions is now configured with:"
    echo "- Workload Identity Federation for keyless authentication"
    echo "- Pulumi access token for infrastructure deployments"
    echo "- GCP project configuration"
    echo
    echo "Next steps:"
    echo "1. Commit and push your changes to trigger the workflow"
    echo "2. Monitor the Actions tab in your GitHub repository"
    echo "3. The workflow will automatically deploy on push to main/develop"
    echo
    echo "Manual deployment:"
    echo "gh workflow run pulumi-deploy.yml -f stack=dev"
}

main() {
    log_info "Starting GitHub Actions setup for AI Orchestra..."

    check_prerequisites
    setup_workload_identity
    set_github_secrets
    print_summary
}

# Run main
main "$@"
