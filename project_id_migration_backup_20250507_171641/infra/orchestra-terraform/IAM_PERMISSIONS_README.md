# Managing GCP IAM Permissions with Terraform

This document explains how to manage Google Cloud Platform IAM permissions, specifically for Secret Manager, using Terraform.

## Overview

Instead of manually running `gcloud` commands to grant IAM permissions like:

```bash
gcloud projects add-iam-policy-binding agi-baby-cherry \
  --member=user:YOUR_EMAIL@gmail.com \
  --role=roles/secretmanager.admin
```

We manage these permissions through Terraform, providing several benefits:
- **Version control**: Permission changes are tracked in Git
- **Consistency**: Permissions are applied consistently across environments
- **Documentation**: Permissions are self-documenting through code
- **Automation**: Permissions can be part of CI/CD pipelines

## Getting Started

### Prerequisites

- Terraform CLI installed (included in this dev container)
- Google Cloud SDK authentication configured
- Access to the `agi-baby-cherry` project

### Configuration Files

- `iam_permissions.tf`: Contains the IAM permission configurations
- `dev.tfvars`: Environment-specific values for development
- `prod.tfvars`: Environment-specific values for production

## Adding New Administrators

To add a new user with Secret Manager Admin permissions:

1. Edit the appropriate environment's `.tfvars` file:

   ```terraform
   # For development environment
   secret_manager_admins = [
     "existing-admin@example.com",
     "new-admin@example.com"  # Add the new admin here
   ]
   ```

2. Apply the changes using Terraform:

   ```bash
   # For development environment
   cd /workspaces/orchestra-main/infra/orchestra-terraform
   terraform apply -var-file=dev.tfvars
   
   # For production environment
   terraform apply -var-file=prod.tfvars
   ```

## Using Service Accounts for Automation

The configuration automatically creates a service account with Secret Manager Admin permissions for CI/CD purposes. You can reference this account in your automation scripts.

The service account email is available as an output:

```bash
terraform output cicd_secret_manager_email
```

## Security Considerations

- Keep the list of administrators minimal, especially in production
- Regularly review and audit permissions
- Consider using Google Cloud's IAM Recommender to identify and remove excess permissions
- For production, consider enabling audit logging for all Secret Manager operations

## Additional Resources

- [Terraform Google Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Google Cloud IAM Documentation](https://cloud.google.com/iam/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)