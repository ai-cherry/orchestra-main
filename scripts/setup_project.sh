#!/bin/bash
# Project setup script for AI Orchestra

set -e

# Set variables
PROJECT_ID="cherry-ai-project"
REGION="us-west4"
GITHUB_REPO="ai-cherry/orchestra-main"

echo "Setting up AI Orchestra project in GCP..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo "Error: gcloud CLI is not installed. Please install it first."
  exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
  echo "Error: You are not authenticated with gcloud. Please run 'gcloud auth login' first."
  exit 1
fi

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  workstations.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create service accounts
echo "Creating service accounts..."
gcloud iam service-accounts create vertex-ai-sa \
  --display-name="Vertex AI Service Account" \
  --description="Service account for Vertex AI operations"

gcloud iam service-accounts create gemini-sa \
  --display-name="Gemini Service Account" \
  --description="Service account for Gemini API operations"

gcloud iam service-accounts create cloud-run-sa \
  --display-name="Cloud Run Service Account" \
  --description="Service account for Cloud Run services"

gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account" \
  --description="Service account for GitHub Actions"

# Grant permissions
echo "Granting permissions to service accounts..."
# Vertex AI service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:vertex-ai-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:vertex-ai-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Gemini service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:gemini-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Cloud Run service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# GitHub Actions service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create storage buckets
echo "Creating storage buckets..."
gsutil mb -l $REGION gs://$PROJECT_ID-model-artifacts-dev
gsutil mb -l $REGION gs://$PROJECT_ID-data-sync-dev

# Create Artifact Registry repository
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create orchestra \
  --repository-format=docker \
  --location=$REGION \
  --description="AI Orchestra Docker repository"

# Create secrets
echo "Creating secrets..."
echo "Creating GCP_MASTER_SERVICE_JSON secret..."
gcloud secrets create gcp-master-service-json \
  --replication-policy="automatic"

echo "Creating GH_CLASSIC_PAT_TOKEN secret..."
gcloud secrets create gh-classic-pat-token \
  --replication-policy="automatic"

echo "Creating GH_FINE_GRAINED_PAT_TOKEN secret..."
gcloud secrets create gh-fine-grained-pat-token \
  --replication-policy="automatic"

# Set up Workload Identity Federation for GitHub Actions
echo "Setting up Workload Identity Federation for GitHub Actions..."
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Allow GitHub Actions to impersonate the service accounts
gcloud iam service-accounts add-iam-policy-binding vertex-ai-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_ID/locations/global/workloadIdentityPools/github-pool/attribute.repository/$GITHUB_REPO"

gcloud iam service-accounts add-iam-policy-binding gemini-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_ID/locations/global/workloadIdentityPools/github-pool/attribute.repository/$GITHUB_REPO"

gcloud iam service-accounts add-iam-policy-binding github-actions@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_ID/locations/global/workloadIdentityPools/github-pool/attribute.repository/$GITHUB_REPO"

echo "Project setup complete!"
echo "Next steps:"
echo "1. Upload values for the secrets in Secret Manager"
echo "2. Configure GitHub repository with the Workload Identity Federation provider"
echo "3. Run Terraform to deploy the infrastructure"