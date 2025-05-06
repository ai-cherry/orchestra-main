# GitHub Secrets Update Guide

This guide outlines the steps to update GitHub repository secrets and variables with new Google Cloud Platform (GCP) project information.

## Values to Add/Update

Based on the new GCP project information, the following values need to be set in GitHub:

| Name | Value |
|------|-------|
| WIF_PROVIDER_ID | projects/525398941159/locations/global/workloadIdentityPools/github-pool/providers/github-provider |
| WIF_SERVICE_ACCOUNT | github-actions-deployer@cherry-ai-project.iam.gserviceaccount.com |
| GCP_PROJECT_ID | cherry-ai-project |

## Update Instructions

Since these values need to be accessible in both GitHub Secrets and GitHub Variables contexts (depending on the workflow), follow these steps to ensure they're correctly configured in both places.

### Step 1: Update GitHub Repository Secrets

1. Go to your GitHub repository: `https://github.com/ai-cherry/orchestra-main`
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. In the **Secrets** tab, add or update the following secrets:

   - Add/Update **WIF_PROVIDER_ID**:
     - Value: `projects/525398941159/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

   - Add/Update **WIF_SERVICE_ACCOUNT**:
     - Value: `github-actions-deployer@cherry-ai-project.iam.gserviceaccount.com`

   - Add/Update **GCP_PROJECT_ID**:
     - Value: `cherry-ai-project`

4. Delete the old **GCP_SA_KEY** secret if it exists (as it's being replaced by Workload Identity Federation)

### Step 2: Update GitHub Repository Variables

1. While still in **Settings** → **Secrets and variables** → **Actions**
2. Switch to the **Variables** tab
3. Add or update the following variables:

   - Add/Update **WORKLOAD_IDENTITY_PROVIDER**:
     - Value: `projects/525398941159/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

   - Add/Update **TERRAFORM_SERVICE_ACCOUNT**:
     - Value: `github-actions-deployer@cherry-ai-project.iam.gserviceaccount.com`

   - Add/Update **GCP_PROJECT_ID**:
     - Value: `cherry-ai-project`

### Step A: Update Variables for Codespaces (if using GitHub Codespaces)

If your team is using GitHub Codespaces:

1. Go to **Settings** → **Secrets and variables** → **Codespaces**
2. Add or update the same values in both the **Secrets** and **Variables** tabs

## Affected Workflows

The following GitHub Actions workflows use these values and will need to be verified:

1. `.github/workflows/terraform-deploy.yml` - Uses GitHub Variables:
   ```yaml
   with:
     workload_identity_provider: ${{ vars.WORKLOAD_IDENTITY_PROVIDER }}
     service_account: ${{ vars.TERRAFORM_SERVICE_ACCOUNT }}
     project_id: ${{ vars.GCP_PROJECT_ID }}
   ```

2. `.github/workflows/migrate-github-secrets.yml` - Uses GitHub Secrets:
   ```yaml
   with:
     workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
     service_account: ${{ secrets.GCP_SA_EMAIL }}
   ```

   This workflow may need to be updated to use the new secret names.

## Security Note

This update transitions from using a service account key (GCP_SA_KEY) to using Workload Identity Federation, which is more secure as it doesn't require storing long-lived credentials in GitHub.

## Verification

After updating the secrets and variables:

1. Manually trigger the `terraform-deploy` workflow to verify the new credentials work
2. Monitor the workflow execution to ensure it completes successfully
3. If there are any authentication errors, double-check the values against the GCP console
