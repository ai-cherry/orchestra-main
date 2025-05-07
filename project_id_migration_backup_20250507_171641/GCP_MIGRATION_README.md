# AGI Baby Cherry Project - GCP Organization Migration and Hybrid IDE Setup Guide

This guide explains how to use the provided scripts to migrate the "agi-baby-cherry" project to the "cherry-ai" organization and set up the hybrid IDE environment with Redis/AlloyDB memory layer and Gemini Code Assist integration.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Process](#migration-process)
4. [Running the Migration Script](#running-the-migration-script)
5. [Validating the Migration](#validating-the-migration)
6. [Architecture Components](#architecture-components)
7. [Troubleshooting](#troubleshooting)
8. [Additional Resources](#additional-resources)

## Overview

This migration suite includes:

- **`gcp_org_migration_setup.sh`**: Main shell script that performs the migration and setup
- **`hybrid_workstation_config.tf`**: Terraform configuration for Cloud Workstations
- **`validate_migration.sh`**: Validation script to test if the migration was successful

The scripts will perform the following tasks:

1. Authenticate to GCP using the service account key
2. Move the existing project to the new organization
3. Set up a hybrid IDE environment with:
   - Cloud Workstations with JupyterLab and IntelliJ
   - Redis/AlloyDB memory layer configuration
   - Gemini Code Assist integration

## Prerequisites

Before running the scripts, ensure you have:

1. **Required Command-Line Tools**:
   - `gcloud` (Google Cloud SDK) - version 392.0.0 or higher
   - `terraform` - version 1.0.0 or higher
   - `jq` - for JSON processing

2. **Required Permissions**:
   - Organization Admin role in the target organization (`cherry-ai`)
   - Owner or Editor role in the source project (`agi-baby-cherry`)
   - Service Account Admin permissions to create and manage service accounts

3. **Network Requirements**:
   - Outbound internet access to Google Cloud APIs
   - Firewall permissions for Cloud Workstations (ports 22, 443, 3389)

4. **GCP Quotas**:
   - Sufficient GPU quota for 2x NVIDIA Tesla T4 GPUs per workstation
   - vCPU quota for n2d-standard-32 machine type (32 vCPUs)
   - SSD Persistent Disk quota (at least 500GB per workstation)

## Migration Process

The migration process follows these high-level steps:

1. **Preparation**: Review existing resources, set up environment variables
2. **Authentication**: Create service account key and authenticate to GCP
3. **Project Migration**: Move project to the new organization
4. **API Enablement**: Enable required GCP APIs
5. **IAM Setup**: Grant necessary permissions
6. **Infrastructure Setup**: Configure Redis/AlloyDB and Cloud Workstations
7. **Validation**: Test the migration to ensure everything works correctly

## Running the Migration

There are two different approaches to running the migration, depending on your needs:

### Option 1: Phased Migration (Recommended for Production)

For production environments or high-stakes migrations, we recommend using the phased migration approach:

1. Make all scripts executable:
   ```bash
   chmod +x gcp_org_migration_setup.sh
   chmod +x validate_migration.sh
   chmod +x phased_migration.sh
   ```

2. Run the phased migration script with dry-run first to simulate the process:
   ```bash
   ./phased_migration.sh --dry-run
   ```

3. Once you've confirmed the dry run looks good, run the migration in phases:
   ```bash
   ./phased_migration.sh --phase=1
   ```

4. After each phase completes successfully, you can proceed to the next phase:
   ```bash
   ./phased_migration.sh --phase=2
   ```

5. Or run multiple phases at once:
   ```bash
   ./phased_migration.sh --phase=3-5
   ```

6. To run all phases at once:
   ```bash
   ./phased_migration.sh --phase=all
   ```

Key benefits of the phased approach:
- Checkpoints are maintained between phases
- Confirmation prompts before proceeding to the next phase
- Ability to pause and resume the migration
- Detailed logs for each phase
- Safer for production environments
- Progress tracking via checkpoint files

### Option 2: All-at-Once Migration

For development or testing environments, you can use the all-at-once approach:

1. Make the scripts executable:
   ```bash
   chmod +x gcp_org_migration_setup.sh
   chmod +x validate_migration.sh
   ```

2. Review and update the GCP configuration variables in `gcp_org_migration_setup.sh` if needed:
   ```bash
   # GCP Configuration
   GCP_PROJECT_ID="agi-baby-cherry"
   GCP_PROJECT_NUMBER="104944497835"
   GCP_ORG_ID="8732-9111-4285"
   GOOGLE_API_KEY="AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
   VERTEX_AGENT_KEY="0d08481a204c0cdba4095bb94529221e8b8ced5c"
   GCP_RUNTIME_SA_EMAIL="cherrybaby@agi-baby-cherry.iam.gserviceaccount.com"
   ADMIN_EMAIL="scoobyjava@cherry-ai.me"
   SERVICE_ACCOUNT_EMAIL="vertex-agent@agi-baby-cherry.iam.gserviceaccount.com"
   ```

3. Run the migration script:
   ```bash
   ./gcp_org_migration_setup.sh
   ```

4. The script will:
   - Display detailed logs of each step
   - Create log files in the `./migration_logs/` directory
   - Provide error handling for failed operations
   - Display a summary upon completion

5. After the script completes, you will see a summary of the components that were set up.

## Validating the Migration

After running either migration approach, you should validate that the migration was successful:

1. Run the validation script:
   ```bash
   ./validate_migration.sh
   ```

2. The validation script performs comprehensive tests on:
   - GCP authentication
   - Project organization membership
   - Enabled APIs
   - Cloud Workstation configuration
   - Redis/AlloyDB setup
   - Gemini Code Assist integration
   - IAM permissions

3. Review the test results:
   - Green ✅ indicates passed tests
   - Red ❌ indicates failed tests
   - Detailed logs are saved to a validation log file

4. For workstation connectivity testing, the script offers an interactive option to:
   - Connect to a running workstation
   - Test JupyterLab installation
   - Verify Gemini Code Assist configuration
   
5. If any tests fail, consult the troubleshooting section below and fix the issues before proceeding.

## Real-World Migration Considerations

When migrating in a real production environment, consider these additional steps:

1. **Create a backup before migration**:
   ```bash
   # Backup important data
   mkdir -p migration_backup
   gcloud projects get-iam-policy agi-baby-cherry --format=json > migration_backup/iam_policy_before_migration.json
   gcloud services list --project=agi-baby-cherry --format=json > migration_backup/enabled_apis_before_migration.json
   ```

2. **Verify network connectivity**:
   The scripts assume private network connectivity for AlloyDB and Redis. Test this with:
   ```bash
   # Test private service access
   gcloud compute networks describe default --format="value(name)" --project=agi-baby-cherry
   ```

3. **Monitor resource quotas**:
   ```bash
   # Check current quotas
   gcloud compute project-info describe --project=agi-baby-cherry
   ```

4. **Test in a staging environment first**:
   If possible, clone your project to a test environment and run the migration there first.

5. **Have a rollback plan**:
   Document the steps needed to revert the migration if issues are encountered.

## Architecture Components

### Hybrid IDE Environment

The hybrid IDE environment consists of:

1. **Cloud Workstations**:
   - Machine type: n2d-standard-32 with AMD Milan processors
   - 2x NVIDIA Tesla T4 GPUs for AI workloads
   - 500GB SSD boot disk and 1TB persistent storage
   - Preinstalled software: IntelliJ Ultimate and JupyterLab
   - Secure networking with private endpoints

2. **Memory Layer**:
   - Redis Memorystore (10GB) for hot-tier, in-memory cache
   - AlloyDB for persistent vector storage
   - Synchronization between Redis and AlloyDB

3. **Gemini Code Assist Integration**:
   - API integration with Vertex AI endpoints
   - Tool integrations for Redis and AlloyDB
   - Custom commands for code optimization and documentation

### Project Organization 

```mermaid
graph TD
    A[cherry-ai Organization] --> B[agi-baby-cherry Project]
    B --> C[Cloud Workstations]
    B --> D[Memory Layer]
    B --> E[Vertex AI Resources]
    C --> F[Hybrid IDE Cluster]
    F --> G[Workstation 1]
    F --> H[Workstation 2]
    F --> I[Workstation 3]
    D --> J[Redis Memorystore]
    D --> K[AlloyDB Instance]
    K --> L[Vector Storage]
    E --> M[Gemini Code Assist]
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify the service account key is correct
   - Check if the service account has been deleted or disabled
   - Run `gcloud auth list` to confirm the active account

2. **Project Migration Failures**:
   - Ensure you have Organization Admin role in the target organization
   - Check for organization policies that might be blocking the migration
   - Verify the organization ID is correct

3. **API Enablement Issues**:
   - Check if you have sufficient permissions to enable APIs
   - Verify the project hasn't reached API quota limits
   - Try enabling APIs manually through the Google Cloud Console

4. **Cloud Workstation Creation Failures**:
   - Check GPU quota in the target region
   - Verify VPC network settings
   - Check for organization policies restricting resource creation

5. **Redis/AlloyDB Setup Issues**:
   - Ensure private service access is configured correctly
   - Check for IP range conflicts
   - Verify service networking API is enabled

### Logs and Debugging

- Migration logs are stored in `./migration_logs/` directory
- Validation logs are stored as `./validation_results_*.log`
- Terraform logs can be found in `./migration_logs/terraform_*.log`
- For advanced debugging, use `gcloud` commands directly:
  ```bash
  gcloud projects describe "agi-baby-cherry"
  gcloud workstations clusters list --project="agi-baby-cherry"
  gcloud redis instances describe agent-memory --region=us-central1
  ```

## Additional Resources

- [Google Cloud Organization Migration Documentation](https://cloud.google.com/resource-manager/docs/moving-projects-folders)
- [Cloud Workstations Documentation](https://cloud.google.com/workstations/docs)
- [AlloyDB Documentation](https://cloud.google.com/alloydb/docs)
- [Redis Memorystore Documentation](https://cloud.google.com/memorystore/docs/redis)
- [Gemini Code Assist Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/code-assist)
- [Project Hybrid IDE Migration Guide](HYBRID_IDE_MIGRATION_GUIDE.md)
- [Terraform GCP Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
