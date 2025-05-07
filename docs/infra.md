# Orchestra Infrastructure Documentation

This document describes the infrastructure setup for the Orchestra platform using Terraform on Google Cloud Platform.

## Overview

Orchestra's infrastructure is managed using Terraform and deployed on Google Cloud Platform. The infrastructure is organized into environments (dev, prod) with shared modules for common components. Each environment has its own separate state but uses the same module code.

### Key Components

- **Cloud Run**: Hosts the Orchestra API services
- **Firestore**: Provides structured data storage
- **Pub/Sub**: Event bus for communication between services
- **Vertex AI Vector Search**: Powers semantic search capabilities
- **Secret Manager**: Securely stores API keys and credentials
- **Artifact Registry**: Stores Docker images

## Directory Structure

```
infra/
├── dev/                 # Development environment configuration
│   └── main.tf
├── prod/                # Production environment configuration
│   └── main.tf
├── modules/             # Shared Terraform modules
│   ├── cloud-run/       # Cloud Run service module
│   ├── firestore/       # Firestore database module
│   ├── pubsub/          # Pub/Sub topics module
│   └── vertex/          # Vertex AI Vector Search module
└── README.md            # Infrastructure overview
```

## Prerequisites

Before you begin, ensure you have:

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
2. [Terraform](https://www.terraform.io/downloads.html) (version 1.5+ recommended) installed
3. Access to the `cherry-ai-project` GCP project
4. A service account key with appropriate permissions

## Authentication

To authenticate with Google Cloud:

```bash
# Using a service account key
echo "$GCP_API_KEY" | base64 -d > /tmp/gsa-key.json
gcloud auth activate-service-account --key-file=/tmp/gsa-key.json

# Set default project and region
gcloud config set project cherry-ai-project
gcloud config set run/region us-west2
```

## Standard Terraform Workflow

### 1. Initialize Terraform

First, navigate to the appropriate environment directory and initialize Terraform:

```bash
cd infra/dev  # or infra/prod
terraform init
```

This will download the required providers and set up the Terraform working directory.

### 2. Create a New Workspace (First Time Only)

```bash
terraform workspace new dev  # or prod
```

### 3. Select an Existing Workspace

```bash
terraform workspace select dev  # or prod
```

### 4. Plan the Changes

Before applying changes, review what Terraform will do:

```bash
terraform plan -var="env=dev"  # or -var="env=prod"
```

This will show you what resources will be created, modified, or deleted.

### 5. Apply the Changes

Once you're satisfied with the plan, apply the changes:

```bash
terraform apply -var="env=dev"  # or -var="env=prod"
```

Terraform will ask for confirmation before proceeding.

### 6. Destroy Resources (When Needed)

To tear down the infrastructure:

```bash
terraform destroy -var="env=dev"  # or -var="env=prod"
```

**CAUTION**: This will remove all resources. Use with care, especially in production.

## Environment-Specific Configurations

### Development Environment

- Minimum instances: 0 (scales to zero when idle)
- Maximum instances: 20
- Features full development setup with lower resource allocation

### Production Environment

- Minimum instances: 1 (always running)
- Maximum instances: 50
- Higher replication for better availability

## CI/CD Integration

To integrate with CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Terraform

on:
  push:
    branches: [main]
    paths: ['infra/**']
  pull_request:
    branches: [main]
    paths: ['infra/**']

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Initialize Terraform
        working-directory: infra/dev  # or infra/prod
        run: terraform init
      
      - name: Terraform Plan
        working-directory: infra/dev  # or infra/prod
        run: terraform plan -var="env=dev"  # or -var="env=prod"
        
      # Only apply on push to main
      - name: Terraform Apply
        if: github.event_name == 'push'
        working-directory: infra/dev  # or infra/prod
        run: terraform apply -auto-approve -var="env=dev"  # or -var="env=prod"
```

## Remote State Management

For team environments, consider using a remote state backend. To enable this:

1. Uncomment the backend configuration in `main.tf`
2. Create a GCS bucket for Terraform state:

```bash
gsutil mb -l us-west2 gs://cherry-ai-project-terraform-state
gsutil versioning set on gs://cherry-ai-project-terraform-state
```

3. Re-initialize Terraform to migrate state:

```bash
terraform init -migrate-state
```

## Best Practices

1. **Version Control**: Always commit Terraform changes to version control
2. **Plan Before Apply**: Always run `terraform plan` before `terraform apply`
3. **Use Workspaces**: Keep environments separate with workspaces
4. **Protect Secrets**: Never commit sensitive values to version control
5. **Lock State**: Use remote state with locking for team workflows

## Testing Infrastructure Changes

For significant changes, consider testing using a temporary environment:

```bash
terraform workspace new test-feature
terraform apply -var="env=test"
# Verify changes work as expected
terraform destroy -var="env=test"
terraform workspace select dev
terraform workspace delete test-feature
```

## Troubleshooting

### Common Issues

- **Authentication errors**: Ensure your service account has the necessary permissions
- **Terraform state lock**: If a lock persists after an interrupted operation, use `terraform force-unlock`
- **Resource conflicts**: If resources already exist, consider importing them with `terraform import`

### Getting Help

For assistance with infrastructure issues:
- Check the [Terraform GCP provider documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- Review the module code in `infra/modules/`
- Consult the Orchestra team Slack channel

## RC-Arena Non-Profit Project Integration

To deploy infrastructure for the RC-Arena Non-Profit project:

1. Create a new workspace for the non-profit project:
   ```bash
   cd infra/dev
   terraform workspace new nonprofit
   ```

2. Apply with appropriate variables:
   ```bash
   terraform apply -var="env=nonprofit"
   ```

This allows sharing the same message bus and other infrastructure components.
