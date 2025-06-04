# Workload Identity Federation for AI cherry_ai

This document serves as the definitive guide for implementing and using Workload Identity Federation (WIF) in the AI cherry_ai project. It provides comprehensive instructions for setup, usage, verification, and troubleshooting.

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

Workload Identity Federation (WIF) allows external identities (like GitHub Actions) to act as
The AI cherry_ai project uses WIF for all deployments to
## Benefits

Using Workload Identity Federation provides several advantages over traditional service account keys:

- **Improved Security**: No long-lived service account keys to manage or rotate
- **Reduced Risk**: No secrets to accidentally expose in logs or code
- **Simplified Management**: No need to create, download, and manage service account keys
- **Audit Trail**: Clear audit logs showing which external identity accessed which resources
- **Principle of Least Privilege**: Fine-grained control over which repositories can access which resources

## Setup Process

The AI cherry_ai project provides a unified script for setting up Workload Identity Federation:

### Prerequisites

Before setting up WIF, ensure you have:

1. A 2. Owner or Editor permissions on the 3. GitHub repository where you want to deploy from
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

1. Enables required 2. Creates a Workload Identity Pool
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
   gh secret set    gh secret set    ```
