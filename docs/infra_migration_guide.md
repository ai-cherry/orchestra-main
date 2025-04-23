# Infrastructure Migration Guide

This document provides guidance on migrating from the deprecated Vertex AI Agent Manager to the new direct Terraform approach.

## Overview

The Orchestra platform is transitioning from a custom automation layer (Vertex AI Agent Manager) to a standard Terraform workflow. This change provides:

- Greater transparency in infrastructure operations
- Better error handling and resilience
- Standard, documented approaches to infrastructure management
- Improved CI/CD integration

## Migration Steps

Follow these steps to migrate your workflow to the new direct Terraform approach:

### 1. Understand the New Structure

The new infrastructure is organized by environment:
- `infra/dev/` - Development environment configuration
- `infra/prod/` - Production environment configuration
- `infra/modules/` - Shared Terraform modules (unchanged)

### 2. Mapping Old Commands to New Workflow

| Old Command | New Workflow |
|-------------|--------------|
| `./infra/run_with_vertex.sh init` | `cd infra/dev && terraform init && terraform apply -var="env=dev"` |
| `./infra/run_with_vertex.sh deploy dev` | `cd infra/dev && terraform apply -var="env=dev"` |
| `./infra/run_with_vertex.sh deploy prod` | `cd infra/prod && terraform apply -var="env=prod"` |
| `./infra/run_with_vertex.sh create-team <name>` | Use standard Terraform to create resources for teams |
| `./infra/run_with_vertex.sh monitor` | Use Google Cloud Console monitoring or configure monitoring using Terraform |

### 3. Set Up Remote State (Recommended)

For team environments and better state management:

```bash
# Run the remote state setup script
cd /workspaces/orchestra-main
./infra/setup_remote_state.sh

# Initialize with the remote backend in each environment
cd infra/dev
terraform init -migrate-state

cd ../prod
terraform init -migrate-state
```

### 4. CI/CD Integration

The new approach includes GitHub Actions workflows:

- `.github/workflows/terraform.yml` - Handles Terraform planning and application
- On PRs: Validates and plans changes
- On merges to main: Applies changes to dev, then prod (with approval)

### 5. Working with Non-Profit Projects

To deploy infrastructure for RC-Arena Non-Profit projects:

```bash
cd infra/dev
terraform workspace new nonprofit
terraform apply -var="env=nonprofit"
```

## Old vs. New Approaches

### Old Approach (Deprecated)

- Custom Python wrapper around Terraform
- Shell commands executed via `os.system()`
- Limited error handling
- Mock implementations for many features
- Abstraction adding complexity

### New Approach

- Standard Terraform workflows
- Environment-specific configurations
- Proper workspace separation
- Automated CI/CD integration
- Improved documentation
- Better error handling and visibility

## Accessing Legacy Code

The deprecated code is still available in the sandbox:

- `sandbox/legacy_tools/vertex_client/` - Python package
- `sandbox/legacy_tools/run_with_vertex.sh` - Helper script

## Common Issues During Migration

- **State conflicts**: If you've used the old approach previously, you might have Terraform state files. Use `terraform state list` to check existing state before migration.
- **Permission issues**: Ensure your Google Cloud credentials have the necessary permissions.
- **GCP API enablement**: Some services might require enabling APIs. The Terraform logs will indicate if you need to enable any APIs.

## Getting Help

Refer to the comprehensive [Infrastructure Documentation](./infra.md) for detailed guidance on using the new approach.

If you encounter issues during migration, check:
1. The main [Infrastructure Documentation](./infra.md)
2. Terraform error messages (usually descriptive and helpful)
3. Google Cloud Console logs
