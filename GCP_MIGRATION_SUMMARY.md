# GCP Organization Migration Suite

This repository contains a comprehensive set of scripts and configuration files for migrating the `cherry-ai-project` GCP project to organization `873291114285` and configuring it with Vertex AI and hybrid IDE environments.

## Files Overview

### Migration Scripts

1. **`exact_migration_steps.sh`** - The most streamlined script following the exact verified implementation steps with critical waiting periods (5 min IAM propagation) and immediate verification.

2. **`quick_migrate.sh`** - Simplified script for quick migration with visual feedback and error handling.

3. **`gcp_migration_execute.sh`** - Comprehensive migration script with robust error handling, retries, and validation.

4. **`migrate_and_setup_corrected.sh`** - Enhanced version of the original migration script with fixes for organization ID and service account permissions.

### Key Management

1. **`manage_service_account_keys.sh`** - Secure key management utility for creating, rotating, and using service account keys.

2. **`vertex-agent-key-template.json`** - Template for the service account key file.

### Validation Scripts

1. **`validate_migration_minimal.sh`** - Focused validation script for critical components only.

2. **`validate_migration.sh`** - Comprehensive validation script for all migration aspects.

### Infrastructure Configuration

1. **`simplified_workstation_config.tf`** - Terraform configuration for deploying the hybrid IDE environment with n2d-standard-32 and NVIDIA T4 GPUs.

### Documentation

1. **`SERVICE_ACCOUNT_SECURITY.md`** - Best practices for service account key management and security.

2. **`GCP_MIGRATION_GUIDE.md`** - Detailed guide for the migration process.

## Critical Success Factors

1. **Organization ID Format**: Always use the numeric ID `873291114285` without hyphens.

2. **Service Account Roles**:
   - Organization level: `roles/resourcemanager.projectMover`, `roles/resourcemanager.projectCreator`
   - Project level: `roles/aiplatform.serviceAgent`, `roles/storage.admin`

3. **IAM Propagation Delay**: Wait 5 minutes after granting roles before attempting migration.

4. **Service Account Key Security**:
   - Always set permissions to `600` (`chmod 600 vertex-agent-key.json`)
   - Verify key integrity before authentication
   - Consider key rotation as a best practice

5. **Immediate Verification**: Always verify the project's organization membership immediately after migration.

## Quick Start

For the most reliable migration experience:

```bash
# 1. Set up service account key
chmod +x manage_service_account_keys.sh
./manage_service_account_keys.sh template  # Or use your own key file

# 2. Secure the key
chmod 600 vertex-agent-key.json

# 3. Run the exact migration steps
chmod +x exact_migration_steps.sh
./exact_migration_steps.sh

# 4. Validate the migration
chmod +x validate_migration_minimal.sh
./validate_migration_minimal.sh
```

## Troubleshooting

1. **"Permission Denied"**: Wait 5 minutes for IAM propagation.

2. **"Organization Not Found"**: Verify organization ID with `gcloud organizations list`.

3. **"Invalid Key"**: Re-download the key from the GCP Console.

4. **"Billing Not Linked"**: Run `gcloud beta billing projects link cherry-ai-project --billing-account=$(gcloud beta billing accounts list --format="value(name)")`.

## Expected Final Results

```
Organization ID: 873291114285 [✔️]
Workstation IP: x.x.x.x [✔️]
Redis Connection: Successful [✔️]
AlloyDB Status: RUNNING [✔️]
```

## Additional Resources

- For detailed security considerations, see `SERVICE_ACCOUNT_SECURITY.md`
- For a complete migration guide, see `GCP_MIGRATION_GUIDE.md`
