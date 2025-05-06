# Badass GCP-GitHub Toolkit

This toolkit provides comprehensive scripts and documentation for managing GCP authentication, GitHub integration, and secure deployment processes.

## Overview

The toolkit includes scripts for:
1. Configuring GCP authentication with service account keys and Workload Identity Federation
2. Applying Terraform configurations in the correct sequence
3. Setting up secure GitHub-GCP integrations
4. Verifying deployments and authentication
5. Synchronizing secrets between GitHub and GCP

## Authentication Components

### Local Authentication

- **`authenticate_codespaces.sh`**: Re-authenticates your local Codespaces environment with GCP
  ```bash
  ./authenticate_codespaces.sh
  ```

### GitHub Actions Authentication

- **`github_actions_migration_workflow.yml`**: GitHub Actions workflow using temporary SA key authentication
- **`switch_to_wif_authentication.sh`**: Switches from service account keys to Workload Identity Federation
- **`secure_setup_workload_identity.sh`**: Sets up Workload Identity Federation pools and providers

## Deployment Components

- **`apply_terraform_sequence.sh`**: Applies Terraform in sequence (common → dev → prod)
- **`deploy_gcp_infra_complete.sh`**: Master script orchestrating the complete deployment process
- **`verify_deployment.sh`**: Verifies Cloud Run deployments with comprehensive checks

## Security and Secret Management

- **`create_badass_service_keys.sh`**: Creates service accounts with extensive permissions
- **`secure_integration.sh`**: Integrates deployment with GitHub-GCP secret synchronization
- **`gcp_github_secret_manager.sh`**: Manages secrets between GitHub and GCP Secret Manager

## Documentation

- **`GCP_TERRAFORM_DEPLOYMENT_GUIDE.md`**: Complete guide to the deployment process
- **`POST_DEPLOYMENT_VERIFICATION_CHECKLIST.md`**: Checklist for verifying successful deployment
- **`GITHUB_GCP_SERVICE_KEYS_README.md`**: Guide to managing service account keys

## Usage Instructions

### Initial Setup

1. **Create Service Account Keys**: 
   ```bash
   ./create_badass_service_keys.sh
   ```

2. **Apply Terraform Configurations**:
   ```bash
   ./apply_terraform_sequence.sh
   ```

3. **Set Up Workload Identity Federation** (after initial deployment):
   ```bash
   ./secure_setup_workload_identity.sh
   ```

### Deployment Verification

1. **Re-authenticate Codespaces**:
   ```bash
   ./authenticate_codespaces.sh
   ```

2. **Verify Deployment**:
   ```bash
   ./verify_deployment.sh
   ```

3. **Check Verification Checklist**:
   Review `POST_DEPLOYMENT_VERIFICATION_CHECKLIST.md`

### Secret Management

For synchronizing secrets between GitHub and GCP:
```bash
./secure_integration.sh
```

## Security Best Practices

1. **Transition to Workload Identity Federation** as soon as possible after initial setup
2. **Delete service account keys** after they're no longer needed
3. **Regularly audit IAM permissions** on all service accounts
4. **Rotate credentials** according to your security policies
5. **Use Secret Manager** for storing sensitive credentials
6. **Enable audit logging** for all critical resources

## Common Commands

Re-authenticate with GCP:
```bash
gcloud auth application-default login --project=cherry-ai-project
```

List active service accounts:
```bash
gcloud iam service-accounts list --project=cherry-ai-project
```

View GitHub secrets (requires GitHub CLI):
```bash
gh secret list --org ai-cherry
```

Trigger workflows (requires GitHub CLI):
```bash
gh workflow run github_actions_migration_workflow.yml --ref main
