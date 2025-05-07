# Migration Execution Plan

## Preparation Complete

The following steps have been completed to prepare for the migration:

1. **Environment Validation**
   - Service account key verified and secured (permissions set to 600)
   - Terraform configuration validated
   - Redis to AlloyDB sync worker confirmed with correct debounce interval (0.5s)

2. **Safety Measures**
   - Backups created of existing Terraform configurations in `backup_configs/` directory
   - Validation script created to verify prerequisites

## Migration Process Overview

The migration process using `execute_migration.sh` will:

1. Set environment variables including:
   - `GCP_PROJECT_ID="cherry-ai-project"`
   - `GCP_ORG_ID="873291114285"`
   - `GCP_SA_JSON` (from vertex-agent-service-account.json file)

2. Execute `migrate_and_setup_corrected.sh` which will:
   - Install Google Cloud SDK if needed (using --force-install flag)
   - Authenticate to GCP using the service account
   - Grant needed permissions to the service account
   - Check organization policies
   - Migrate project to organization
   - Verify and update billing
   - Enable required APIs
   - Set up infrastructure (Redis, AlloyDB)
   - Create/update `hybrid_workstation_config.tf` and deploy using Terraform
   - Perform final validation

## Important Notes

1. **Duration**: The migration process might take 20-30 minutes to complete, especially the Terraform deployment of Cloud Workstations.

2. **Potential Conflicts**: The script creates `hybrid_workstation_config.tf` in the root directory, which may conflict with the existing file. A backup of the current file has been created.

3. **IAM Propagation**: There may be delays (5+ minutes) for IAM role propagation during the process.

4. **Required User Input**: The script may prompt for confirmation at various stages, particularly during organization policy checks.

5. **Post-Migration Verification**: After the migration completes, verify the results match the expected outputs in GCP_MIGRATION_SUMMARY.md.

## Executing the Migration

To execute the migration:

```bash
./execute_migration.sh
```

## Rollback Options

If issues occur during migration:

1. Use the backups in `backup_configs/` to restore configurations.
2. Use `exact_migration_steps.sh` for manual step-by-step migration with precise control.
