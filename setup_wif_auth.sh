#!/bin/bash
set -e

# Configuration
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
REPO_NAME="your-github-org/orchestra-main"  # Replace with your actual GitHub org/repo
SERVICE_ACCOUNT_NAME="orchestra-ci-cd"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL_NAME="github-pool"
PROVIDER_NAME="github-provider"

# Create service account if it doesn't exist
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" &>/dev/null; then
  echo "Creating service account: $SERVICE_ACCOUNT_EMAIL"
  gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name="Orchestra CI/CD Service Account" \
    --project="$PROJECT_ID"
fi

# Grant necessary roles to the service account
echo "Granting roles to service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountUser"

# Create Workload Identity Pool if it doesn't exist
if ! gcloud iam workload-identity-pools describe "$POOL_NAME" \
  --location="global" --project="$PROJECT_ID" &>/dev/null; then
  echo "Creating Workload Identity Pool: $POOL_NAME"
  gcloud iam workload-identity-pools create "$POOL_NAME" \
    --location="global" \
    --display-name="GitHub Actions Pool" \
    --project="$PROJECT_ID"
fi

# Get the Workload Identity Pool ID
POOL_ID=$(gcloud iam workload-identity-pools describe "$POOL_NAME" \
  --location="global" \
  --project="$PROJECT_ID" \
  --format="value(name)")

# Create Workload Identity Provider if it doesn't exist
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --project="$PROJECT_ID" &>/dev/null; then
  echo "Creating Workload Identity Provider: $PROVIDER_NAME"
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
    --location="global" \
    --workload-identity-pool="$POOL_NAME" \
    --display-name="GitHub Actions Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --project="$PROJECT_ID"
fi

# Allow authentications from the GitHub repository to impersonate the service account
echo "Setting up IAM policy binding..."
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${REPO_NAME}" \
  --project="$PROJECT_ID"

# Get the Workload Identity Provider resource name
WORKLOAD_IDENTITY_PROVIDER=$(gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --project="$PROJECT_ID" \
  --format="value(name)")

echo ""
echo "✅ Workload Identity Federation setup complete!"
echo ""
echo "Add the following secrets to your GitHub repository:"
echo ""
echo "WORKLOAD_IDENTITY_PROVIDER: $WORKLOAD_IDENTITY_PROVIDER"
echo "SERVICE_ACCOUNT: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "Then update your GitHub Actions workflow to use these secrets."