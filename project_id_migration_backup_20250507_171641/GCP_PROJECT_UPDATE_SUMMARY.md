# GitHub Workflows GCP Project Update Summary

This document summarizes the changes made to update GitHub Actions workflows with the new GCP project information.

## Updated Project Information

| Item | Old Value | New Value |
|------|-----------|-----------|
| Project ID | agi-baby-cherry | cherry-ai-project |
| Project Number | 104944497835 | 525398941159 |
| Service Account | vertex-agent@agi-baby-cherry.iam.gserviceaccount.com | github-actions-deployer@cherry-ai-project.iam.gserviceaccount.com |
| Workload Identity Pool/Provider | gitlab-pool/gitlab-provider | github-pool/github-provider |

## Files Updated

1. **GitHub Secrets Structure**
   - Moved from variable-based authentication to secret-based authentication for better security
   - Added new secrets:
     - `WIF_PROVIDER_ID`
     - `WIF_SERVICE_ACCOUNT`
     - `GCP_PROJECT_ID`
   - Deleted old service account key: `GCP_SA_KEY`

2. **GitHub Workflows Updated**
   - `.github/workflows/terraform-deploy.yml` - Updated to use secret-based authentication
   - `.github/workflows/migrate-github-secrets.yml` - Updated WIF provider and service account
   - `.github/workflows/ci-cd.yml` - Updated project ID and service account information
   - `.github/workflows/turbo_deploy.yml` - Updated to use new project and service account
   - `.github/workflows/ai_deploy.yml` - Updated GCP project information and authentication
   - `.github/workflows/ai_pipeline.yml` - Updated container registry and authentication

## Scripts Created

1. `get_wif_values.sh` - Generates proper Workload Identity Federation values for the new project
2. `update_wif_secrets.sh` - Script to directly update GitHub repository secrets (note: requires appropriate GitHub token permissions)

## Documentation

- `GITHUB_SECRETS_UPDATE_GUIDE.md` - Detailed guide for manually updating GitHub secrets in both repository secrets and variables

## Next Steps

1. Verify each workflow by testing a small change that triggers the workflow
2. Monitor workflow executions for any authentication or permission errors
3. If workflows fail, double-check the secret values in the GitHub repository settings
4. Update any additional scripts or files that may reference the old project ID

## Security Improvement

This update transitions from using a service account key (GCP_SA_KEY) to using Workload Identity Federation (WIF), which is more secure as it doesn't require storing long-lived credentials in GitHub.
