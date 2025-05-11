# Workload Identity Federation for GitHub Actions

This document explains how to set up and use Workload Identity Federation (WIF) for secure authentication between GitHub Actions and Google Cloud Platform in the AI Orchestra project.

## What is Workload Identity Federation?

Workload Identity Federation allows external identities (like GitHub Actions) to act as Google Cloud service accounts without using service account keys. This provides several benefits:

- **Improved Security**: No long-lived service account keys to manage or rotate
- **Reduced Risk**: No secrets to accidentally expose in logs or code
- **Simplified Management**: No need to create, download, and manage service account keys
- **Audit Trail**: Clear audit logs showing which external identity accessed which resources

## Setup Process

The AI Orchestra project provides several tools to set up Workload Identity Federation:

1. **Terraform Module**: `terraform/modules/wif/main.tf`
2. **Setup Script**: `deploy_wif.sh`
3. **GitHub Secrets Setup Script**: `setup_github_wif_secrets.sh`
4. **GitHub Actions Workflow**: `.github/workflows/wif-deploy.yml`

### Option 1: Using Terraform (Recommended)

1. Navigate to the terraform directory:
   ```bash
   cd terraform
   ```

2. Create a new file `wif.tf` with the following content:
   ```hcl
   module "wif" {
     source = "./modules/wif"
     
     project_id     = var.project_id
     project_number = "525398941159"  # Replace with your project number
     repository     = "ai-cherry/orchestra-main"  # Replace with your GitHub repository
   }
   
   output "workload_identity_provider" {
     value = module.wif.workload_identity_provider
   }
   
   output "service_account_email" {
     value = module.wif.service_account_email
   }
   ```

3. Initialize and apply the Terraform configuration:
   ```bash
   terraform init
   terraform apply
   ```

4. Note the outputs for `workload_identity_provider` and `service_account_email`, which you'll need for GitHub secrets.

### Option 2: Using the Setup Script

1. Make the script executable:
   ```bash
   chmod +x deploy_wif.sh
   ```

2. Run the script:
   ```bash
   ./deploy_wif.sh
   ```

3. The script will set up Workload Identity Federation and output the values needed for GitHub secrets.

## Setting Up GitHub Secrets

After setting up Workload Identity Federation, you need to add the following secrets to your GitHub repository:

- `GCP_PROJECT_ID`: Your Google Cloud project ID (e.g., "cherry-ai-project")
- `GCP_REGION`: Your Google Cloud region (e.g., "us-central1")
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: The full resource name of your Workload Identity Provider
- `GCP_SERVICE_ACCOUNT`: The email of your service account

You can set these secrets manually in the GitHub repository settings, or use the provided script:

```bash
chmod +x setup_github_wif_secrets.sh
./setup_github_wif_secrets.sh
```

## Using Workload Identity Federation in GitHub Actions

The AI Orchestra project includes a GitHub Actions workflow that uses Workload Identity Federation for authentication:

```yaml
# .github/workflows/wif-deploy.yml
```

This workflow:

1. Checks out the code
2. Sets up Python and Poetry
3. Authenticates to Google Cloud using Workload Identity Federation
4. Builds and pushes a Docker image
5. Deploys the service to Cloud Run

To use this workflow, simply push to the main branch or manually trigger the workflow from the GitHub Actions tab.

## Troubleshooting

### Authentication Issues

If you encounter authentication issues, check the following:

1. Verify that the GitHub secrets are set correctly
2. Ensure that the service account has the necessary permissions
3. Check that the Workload Identity Pool and Provider are set up correctly
4. Verify that the repository attribute mapping is correct

### Permission Issues

If you encounter permission issues, check the following:

1. Ensure that the service account has the necessary roles (e.g., `roles/run.admin`, `roles/storage.admin`)
2. Verify that the service account binding is set up correctly
3. Check the audit logs for more details on the permission issue

## Best Practices

1. **Use Terraform**: Manage your Workload Identity Federation setup with Terraform for reproducibility
2. **Limit Permissions**: Grant only the necessary permissions to the service account
3. **Use Repository Conditions**: Restrict which repositories can use the service account
4. **Monitor Usage**: Regularly review audit logs for unexpected access patterns
5. **Keep Dependencies Updated**: Regularly update the GitHub Actions workflows and dependencies

## References

- [Google Cloud Documentation: Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GitHub Actions: Google Auth Action](https://github.com/google-github-actions/auth)
- [GitHub Actions: Deploy Cloud Run Action](https://github.com/google-github-actions/deploy-cloudrun)