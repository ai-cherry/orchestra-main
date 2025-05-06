# AI Orchestra Terraform Infrastructure Guide

This guide provides an overview of the Terraform infrastructure setup for the AI Orchestra project and instructions on how to use the provided scripts for validation and deployment.

## Infrastructure Overview

The AI Orchestra infrastructure is managed using Terraform and is organized into environments:

- **Dev Environment**: `/infra/terraform/gcp/environments/dev/`
- **Prod Environment**: `/infra/terraform/gcp/environments/prod/`
- **Common Resources**: `/infra/terraform/gcp/environments/common/`

### Key Components

1. **Cloud Run Services**:
   - `orchestrator-api-dev`: Main API service for the orchestrator
   - `phidata-agent-ui-dev`: UI service for the Phidata agent

2. **Service Accounts**:
   - `orchestra-runner-sa`: Used by Cloud Run services
   - `orchestrator-test-sa`: Used for testing

3. **Secret Management**:
   - Secrets are injected into Cloud Run services via `secret_key_ref`
   - Includes API keys, database credentials, etc.

## Management Scripts

### Validation Script

The `scripts/validate_terraform.sh` script helps maintain consistency across all Terraform configurations:

```bash
# Run from project root
./scripts/validate_terraform.sh
```

This script:
- Formats all Terraform files with `terraform fmt -recursive ./infra`
- Initializes with `terraform init -upgrade` in each environment directory
- Validates with `terraform validate` in each environment directory

### Deployment Script

The `scripts/deploy_terraform.sh` script automates the deployment process:

```bash
# Deploy all environments with default settings
./scripts/deploy_terraform.sh

# Deploy only dev environment
./scripts/deploy_terraform.sh --env=dev

# Deploy with a specific project ID
./scripts/deploy_terraform.sh --project-id=my-project-id

# Deploy with auto-approve (no confirmation prompts)
./scripts/deploy_terraform.sh --auto-approve
```

This script:
- Runs `terraform plan` to show changes
- Prompts for confirmation before applying (unless `--auto-approve` is used)
- Applies changes with `terraform apply`

### Restricted Mode Detection

If you're working in GitHub Codespaces and encounter restricted mode issues, use:

```bash
./scripts/exit_restricted_mode.sh
```

This script:
- Detects if the environment is in restricted mode
- Attempts to exit restricted mode using available methods
- Provides guidance if automatic exit fails

## Best Practices

1. **Always validate before deploying**:
   ```bash
   ./scripts/validate_terraform.sh && ./scripts/deploy_terraform.sh
   ```

2. **Use environment-specific variables**:
   - Store environment-specific values in the respective `variables.tf` files
   - Use `var.project_id`, `var.region`, etc. instead of hardcoding values

3. **Secret Management**:
   - Never store secrets in Terraform files
   - Use Secret Manager and reference secrets via `secret_key_ref`

4. **CI/CD Integration**:
   - Add validation to pre-commit hooks
   - Include validation in CI pipelines
   - Use deployment script with `--auto-approve` in CD pipelines

## Infrastructure Diagram

```
┌─────────────────────────────────────┐
│                                     │
│  Google Cloud Platform (GCP)        │
│                                     │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │  Cloud Run                  │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │ orchestrator-api-dev│    │    │
│  │  └─────────────────────┘    │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │ phidata-agent-ui-dev│    │    │
│  │  └─────────────────────┘    │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │  IAM                        │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │ orchestra-runner-sa │    │    │
│  │  └─────────────────────┘    │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │ orchestrator-test-sa│    │    │
│  │  └─────────────────────┘    │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │  Secret Manager             │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │ API Keys            │    │    │
│  │  └─────────────────────┘    │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │ Database Credentials│    │    │
│  │  └─────────────────────┘    │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

1. **Terraform not initialized**:
   ```
   Error: Terraform not initialized
   ```
   Solution: Run `terraform init` in the environment directory

2. **Permission denied**:
   ```
   Error: googleapi: Error 403: Permission denied
   ```
   Solution: Ensure you have the necessary IAM permissions

3. **Restricted mode in Codespaces**:
   ```
   Error: Unable to access gcloud auth
   ```
   Solution: Run `./scripts/exit_restricted_mode.sh`

### Getting Help

For more information on the AI Orchestra infrastructure, refer to:
- [GCP_TERRAFORM_DEPLOYMENT_GUIDE.md](./GCP_TERRAFORM_DEPLOYMENT_GUIDE.md)
- [INFRASTRUCTURE_OPTIMIZATION_GUIDE.md](./INFRASTRUCTURE_OPTIMIZATION_GUIDE.md)
- [SECURE_CREDENTIAL_MANAGEMENT.md](./SECURE_CREDENTIAL_MANAGEMENT.md)