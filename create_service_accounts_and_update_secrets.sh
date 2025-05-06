#!/bin/bash

# Script to create service accounts and update secrets

set -e

# Configuration
export PROJECT_ID="cherry-ai.me"
export PROJECT_NUMBER="525398941159"
export REGION="us-central1"
export SERVICE_ACCOUNT="vertex-agent"

echo "Creating service accounts and configuring permissions..."

# Create Vertex AI service account
gcloud iam service-accounts create ${SERVICE_ACCOUNT} \
    --project=${PROJECT_ID} \
    --display-name="Vertex AI Agent Service Account"

# Grant necessary roles
roles=(
    "roles/aiplatform.user"
    "roles/storage.objectViewer"
    "roles/artifactregistry.reader"
    "roles/run.invoker"
)

for role in "${roles[@]}"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="${role}"
done

# Create Workload Identity Federation pool
gcloud iam workload-identity-pools create "github-pool" \
    --project=${PROJECT_ID} \
    --location="global" \
    --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --project=${PROJECT_ID} \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --display-name="GitHub Actions Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"

# Allow GitHub Actions to impersonate service account
gcloud iam service-accounts add-iam-policy-binding \
    "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project=${PROJECT_ID} \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/*"

echo "Service accounts and permissions configured successfully!"

# Create and populate secrets
echo "Creating secrets in Secret Manager..."

secrets=(
    "OPENAI_API_KEY"
    "PORTKEY_API_KEY"
    "OPENROUTER_API_KEY"
)

for secret in "${secrets[@]}"; do
    # Create secret
    gcloud secrets create ${secret} \
        --project=${PROJECT_ID} \
        --replication-policy="automatic"
    
    echo "Created secret: ${secret}"
done

echo "Setup complete!"
