# Workload Identity Federation for AI Orchestra

This document serves as the definitive guide for implementing and using Workload Identity Federation (WIF) in the AI Orchestra project. It provides comprehensive instructions for setup, usage, verification, and troubleshooting.

## Table of Contents

1. [Overview](#overview)
2. [Benefits](#benefits)
3. [Setup Process](#setup-process)
4. [Verification](#verification)
5. [Using WIF in GitHub Actions](#using-wif-in-github-actions)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)
8. [References](#references)

## Overview

Workload Identity Federation (WIF) allows external identities (like GitHub Actions) to act as Google Cloud service accounts without using service account keys. This enables secure authentication between GitHub Actions and Google Cloud Platform for CI/CD pipelines.

The AI Orchestra project uses WIF for all deployments to Google Cloud Platform, eliminating the need for storing service account keys in GitHub secrets.

## Benefits

Using Workload Identity Federation provides several advantages over traditional service account keys:

- **Improved Security**: No long-lived service account keys to manage or rotate
- **Reduced Risk**: No secrets to accidentally expose in logs or code
- **Simplified Management**: No need to create, download, and manage service account keys
- **Audit Trail**: Clear audit logs showing which external identity accessed which resources
- **Principle of Least Privilege**: Fine-grained control over which repositories can access which resources

## Setup Process

The AI Orchestra project provides a unified script for setting up Workload Identity Federation:

### Prerequisites

Before setting up WIF, ensure you have:

1. A Google Cloud Platform project with billing enabled
2. Owner or Editor permissions on the GCP project
3. GitHub repository where you want to deploy from
4. GitHub Personal Access Token with `repo` scope

### Using the Setup Script

The `setup_wif.sh` script handles the complete WIF setup process:

```bash
# Make the script executable
chmod +x setup_wif.sh

# Run with default settings
./setup_wif.sh

# Run with custom settings
./setup_wif.sh \
  --project your-project-id \
  --region us-central1 \
  --repo-owner your-github-org \
  --repo-name your-repo-name \
  --service-account your-sa-name \
  --pool your-pool-name \
  --provider your-provider-name
```

The script performs the following actions:

1. Enables required GCP APIs
2. Creates a Workload Identity Pool
3. Creates a Workload Identity Provider for GitHub
4. Creates a service account with necessary permissions
5. Sets up the binding between GitHub Actions and the service account
6. Sets up GitHub repository secrets

### Manual Setup

If you prefer to set up WIF manually, follow these steps:

1. **Enable required APIs**:
   ```bash
   gcloud services enable iam.googleapis.com \
     iamcredentials.googleapis.com \
     cloudresourcemanager.googleapis.com
   ```

2. **Create Workload Identity Pool**:
   ```bash
   gcloud iam workload-identity-pools create github-pool \
     --location="global" \
     --display-name="GitHub Actions Pool" \
     --description="Identity pool for GitHub Actions"
   ```

3. **Create Workload Identity Provider**:
   ```bash
   gcloud iam workload-identity-pools providers create-oidc github-provider \
     --location="global" \
     --workload-identity-pool=github-pool \
     --display-name="GitHub Provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
     --issuer-uri="https://token.actions.githubusercontent.com"
   ```

4. **Create service account**:
   ```bash
   gcloud iam service-accounts create github-actions-sa \
     --display-name="GitHub Actions Service Account" \
     --description="Service account for GitHub Actions deployments"
   ```

5. **Grant necessary roles to the service account**:
   ```bash
   for role in "roles/run.admin" "roles/storage.admin" "roles/artifactregistry.admin" "roles/iam.serviceAccountUser"; do
     gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:github-actions-sa@your-project-id.iam.gserviceaccount.com" \
       --role="$role"
   done
   ```

6. **Allow GitHub Actions to impersonate the service account**:
   ```bash
   gcloud iam service-accounts add-iam-policy-binding github-actions-sa@your-project-id.iam.gserviceaccount.com \
     --member="principalSet://iam.googleapis.com/projects/your-project-number/locations/global/workloadIdentityPools/github-pool/attribute.repository/your-github-org/your-repo-name" \
     --role="roles/iam.workloadIdentityUser"
   ```

7. **Set up GitHub secrets**:
   ```bash
   gh secret set GCP_PROJECT_ID --body "your-project-id" --repo "your-github-org/your-repo-name"
   gh secret set GCP_REGION --body "your-region" --repo "your-github-org/your-repo-name"
   gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body "projects/your-project-number/locations/global/workloadIdentityPools/github-pool/providers/github-provider" --repo "your-github-org/your-repo-name"
   gh secret set GCP_SERVICE_ACCOUNT --body "github-actions-sa@your-project-id.iam.gserviceaccount.com" --repo "your-github-org/your-repo-name"
   ```

## Verification

After setting up WIF, verify that everything is configured correctly using the `verify_wif_setup.sh` script:

```bash
# Make the script executable
chmod +x verify_wif_setup.sh

# Run the verification script
./verify_wif_setup.sh
```

The verification script checks:

1. Required GitHub secrets are set
2. Workload Identity Pool exists
3. Workload Identity Provider exists
4. Service account exists and has the necessary permissions
5. Workload Identity binding is set up correctly
6. GitHub Actions workflow is present

If any issues are found, the script provides guidance on how to fix them.

## Using WIF in GitHub Actions

The AI Orchestra project provides a template for GitHub Actions workflows that use Workload Identity Federation:

### Workflow Template

Copy the template from `.github/workflows/wif-deploy-template.yml` and customize it for your service:

```bash
# Create a new workflow file
cp .github/workflows/wif-deploy-template.yml .github/workflows/your-service-deploy.yml
```

Then edit the file to customize:
- Service name
- Service path
- Build and test commands
- Deployment parameters

### Key Components

The workflow template includes these key components for WIF:

1. **Permissions**:
   ```yaml
   permissions:
     contents: read
     id-token: write  # Required for requesting the JWT for WIF
   ```

2. **Authentication**:
   ```yaml
   - name: Google Auth via Workload Identity Federation
     id: auth
     uses: google-github-actions/auth@v2
     with:
       workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
       service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
       token_format: 'access_token'
   ```

3. **Cloud SDK Setup**:
   ```yaml
   - name: Set up Cloud SDK
     uses: google-github-actions/setup-gcloud@v2
     with:
       project_id: ${{ env.PROJECT_ID }}
   ```

### Example Usage

A minimal workflow using WIF might look like:

```yaml
name: Deploy with WIF

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Google Auth via WIF
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy my-service \
            --image gcr.io/my-project/my-image \
            --region us-central1
```

## Troubleshooting

### Authentication Issues

If you encounter authentication issues in GitHub Actions:

1. **Check GitHub Secrets**:
   Verify that all required secrets are set correctly:
   ```bash
   ./verify_wif_setup.sh
   ```

2. **Check Service Account Permissions**:
   Ensure the service account has the necessary roles:
   ```bash
   gcloud projects get-iam-policy your-project-id \
     --format="table(bindings.role,bindings.members)" \
     --filter="bindings.members:github-actions-sa@your-project-id.iam.gserviceaccount.com"
   ```

3. **Check Workload Identity Binding**:
   Verify the binding between GitHub and the service account:
   ```bash
   gcloud iam service-accounts get-iam-policy github-actions-sa@your-project-id.iam.gserviceaccount.com \
     --format="table(bindings.role,bindings.members)"
   ```

4. **Check GitHub Actions Logs**:
   Look for specific error messages in the GitHub Actions logs.

### Common Errors

1. **"Permission 'iam.serviceAccounts.getAccessToken' denied"**:
   - The service account doesn't have the workload identity binding
   - The repository attribute mapping is incorrect

2. **"Caller does not have permission"**:
   - The service account doesn't have the necessary roles
   - The service account doesn't exist

3. **"Invalid JWT"**:
   - The Workload Identity Provider is misconfigured
   - The GitHub Actions workflow doesn't have the correct permissions

## Best Practices

1. **Use the Provided Scripts**:
   - `setup_wif.sh` for setting up WIF
   - `verify_wif_setup.sh` for verifying the setup
   - `.github/workflows/wif-deploy-template.yml` as a template for workflows

2. **Limit Service Account Permissions**:
   Only grant the necessary roles to the service account.

3. **Use Repository Conditions**:
   Restrict which repositories can use the service account by specifying the repository in the attribute mapping.

4. **Monitor Usage**:
   Regularly review audit logs for unexpected access patterns.

5. **Keep Dependencies Updated**:
   Regularly update the GitHub Actions workflows and dependencies.

## References

- [Google Cloud Documentation: Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GitHub Actions: Google Auth Action](https://github.com/google-github-actions/auth)
- [GitHub Actions: Deploy Cloud Run Action](https://github.com/google-github-actions/deploy-cloudrun)
- [AI Orchestra GitHub Security Improvements](GITHUB_SECURITY_IMPROVEMENTS.md)