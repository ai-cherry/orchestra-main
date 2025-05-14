# AI Orchestra GCP Migration Toolkit

This toolkit provides a comprehensive solution for migrating the AI Orchestra project to Google Cloud Platform (GCP). It addresses migration challenges including organization policy constraints, Terraform configuration issues, and deployment automation.

## Overview

The GCP Migration Toolkit includes several components:

1. **Organization Policy Management**
   - Handles restrictive organization policies that block public access to Cloud Run services
   - Fixes Vertex AI model access limitations
   - Resolves IAM policy member domain restrictions

2. **Service Account Interface**
   - Creates and manages the required service accounts
   - Sets up environment variables for authentication
   - Handles credentials for different components

3. **Terraform Configuration**
   - Resolves backend configuration conflicts
   - Creates minimal working Terraform setup
   - Supports local development and production environments

4. **Non-Interactive Execution**
   - Provides automated deployment without requiring manual intervention
   - Uses service account-based authentication
   - Handles errors gracefully

## Getting Started

### Prerequisites

- GCP project (`cherry-ai-project`)
- `gcloud` CLI installed and configured
- Python 3.8+
- Access to a service account with organization policy admin permissions

### Quick Start

For the fastest way to complete the migration, run:

```bash
# Run complete migration script
./gcp_migration/complete_migration.sh
```

This script performs all necessary steps:
1. Creates/obtains service account key
2. Fixes Terraform backend configuration
3. Applies organization policies
4. Runs non-interactive migration
5. Verifies deployment
6. Generates a final report

### Step by Step Migration

If you prefer more control over the migration process, you can run the individual scripts:

1. **Set up Service Account**:
   ```bash
   # Create service account key
   ./gcp_migration/create_service_account_key.sh
   
   # Source environment variables
   source setup_policy_manager_env.sh
   ```

2. **Fix Terraform Backend**:
   ```bash
   # Fix Terraform backend configuration
   ./gcp_migration/fix_terraform_duplicate_backend.sh
   ```

3. **Apply Organization Policies**:
   ```bash
   # Run organization policy manager
   python3 gcp_migration/use_org_policy_manager.py
   ```

4. **Run Migration**:
   ```bash
   # Run non-interactive migration
   ./gcp_migration/execute_non_interactive.sh
   ```

## Components in Detail

### Organization Policy Manager

The organization policy manager (`use_org_policy_manager.py`) addresses these policy constraints:

1. **run.requireInvokerIam**: Controls whether Cloud Run services require authentication
2. **iam.allowedPolicyMemberDomains**: Restricts which domains can be granted permissions
3. **vertexai.allowedModels**: Controls which Vertex AI models can be accessed

This component uses the `org-policy-manager-sa` service account, which has the necessary permissions to modify these policies.

### Service Account Management

The service account setup scripts help create and manage credentials:

- `create_service_account_key.sh`: Creates a key for the organization policy manager service account
- `setup_service_account.sh`: Interactive script for setting up service account credentials

### Terraform Configuration

The Terraform configuration components:

- `fix_terraform_duplicate_backend.sh`: Resolves conflicts between Terraform backends
- Creates minimal Terraform configuration in `terraform/migration/`

### Non-Interactive Migration

The non-interactive migration script (`execute_non_interactive.sh`):

- Uses service account authentication instead of interactive login
- Deploys a minimal Cloud Run service for testing
- Tests Vertex AI connectivity
- Generates detailed logs and reports

## Troubleshooting

### Service Account Permissions

If you encounter permission errors:

1. Ensure the service account has the necessary roles:
   - Organization Policy Administrator (`roles/orgpolicy.policyAdmin`)
   - Cloud Run Admin (`roles/run.admin`)
   - Vertex AI Administrator (`roles/aiplatform.admin`)
   - Project IAM Admin (`roles/resourcemanager.projectIamAdmin`)

2. Verify the key:
   ```bash
   gcloud auth activate-service-account --key-file=gcp_migration/keys/org-policy-manager-key.json
   ```

### Terraform Errors

If you encounter Terraform errors:

1. Clear the Terraform state and re-initialize:
   ```bash
   rm -rf terraform/migration/.terraform*
   terraform -chdir=terraform/migration init
   ```

2. Check for backend configuration conflicts:
   ```bash
   ./gcp_migration/fix_terraform_duplicate_backend.sh
   ```

### Organization Policy Issues

If organization policies continue to block your deployment:

1. Manually check organization policies:
   ```bash
   gcloud org-policies list --project=cherry-ai-project
   ```

2. Use the GitHub Action workflow for CI/CD-based policy management:
   ```bash
   # Copy workflow file to GitHub workflows directory
   cp gcp_migration/apply_org_policies_github_action.yml .github/workflows/
   ```

## Logs and Reports

The migration process generates several logs and reports:

- Migration logs: `gcp_migration/migration_logs/*.log`
- Migration reports: `gcp_migration/migration_logs/*.md`
- Service account keys: `gcp_migration/keys/`

## Security Considerations

The GCP migration toolkit includes service account keys that should be kept secure. Consider these best practices:

1. Don't commit service account keys to version control systems
2. Use Workload Identity Federation when possible instead of service account keys
3. Restrict service account permissions to only what's necessary
4. Rotate service account keys regularly

## Next Steps

After completing the migration:

1. Set up CI/CD pipelines for ongoing deployments
2. Configure monitoring and alerting
3. Implement comprehensive backup and disaster recovery procedures
4. Set up Vertex AI integration for model deployment and serving
5. Configure Google Cloud Monitoring for observability