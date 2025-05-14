# AI Orchestra GCP Migration Toolkit

This toolkit provides a collection of scripts and tools for migrating the AI Orchestra project to Google Cloud Platform.

## Overview

The AI Orchestra GCP Migration Toolkit includes:

1. Fixed migration scripts that address the issues found in the original implementation
2. Permission-fixing utilities for Cloud Run and Vertex AI
3. Simplified Cloud Run deployment tools
4. Vertex AI connectivity testing utilities
5. Local development configurations

## Components

### Migration Scripts

- `execute_migration_fixed.sh` - Fixed version of the migration script that addresses authentication, building, and deployment issues
- `execute_non_interactive.sh` - Non-interactive version that uses service account authentication instead of interactive login
- `deploy_minimal_service.py` - Python script to deploy a minimal FastAPI service for testing Cloud Run
- `test_vertex_ai.py` - Python script to test connectivity to Vertex AI

### Permission Fixing Utilities

- `fix_cloud_run_access.sh` - Script to diagnose and fix Cloud Run access issues, generating Cloud Shell commands if needed
- `fix_vertex_ai_auth.py` - Python script to set up Vertex AI authentication and permissions

### Terraform Configurations

- `/terraform/migration/` - Directory containing clean Terraform configurations for migration

## Usage

### Complete Migration

To execute the complete migration process:

```bash
./gcp_migration/execute_non_interactive.sh
```

This script will:
1. Install required dependencies
2. Set up proper authentication using the service account
3. Configure local infrastructure
4. Plan Terraform deployment
5. Deploy a minimal test service
6. Test Vertex AI connectivity
7. Generate a final migration report

### Fix Cloud Run Access Issues

If you encounter permission issues with Cloud Run services:

```bash
./gcp_migration/fix_cloud_run_access.sh
```

This script will:
1. Check current Cloud Run service configuration
2. Try different approaches to fix the permissions
3. Redeploy the service with correct settings if needed
4. Generate Cloud Shell commands for manual execution if automatic fixes fail

### Fix Vertex AI Authentication

To set up proper Vertex AI permissions:

```bash
./gcp_migration/fix_vertex_ai_auth.py [--project-id PROJECT_ID] [--service-account SERVICE_ACCOUNT] [--key-path KEY_PATH]
```

This script will:
1. Set up necessary IAM roles for Vertex AI access
2. Create a service account key if needed
3. Test Vertex AI connectivity to verify the configuration

### Deploy Test Service

To deploy only the minimal test service:

```bash
python3 ./gcp_migration/deploy_minimal_service.py
```

### Test Vertex AI Connectivity

To test connectivity to Vertex AI:

```bash
python3 ./gcp_migration/test_vertex_ai.py
```

## Fixed Issues

This toolkit addresses the following issues found in the original migration implementation:

1. **Authentication Issues**
   - Now using service account authentication instead of interactive login
   - Added Docker authentication configuration
   - Provides tools to diagnose and fix permissions problems

2. **Docker Build Issues**
   - Fixed Dockerfile to handle missing poetry.lock file
   - Added fallback for Docker builds
   - Implemented robust error handling

3. **Terraform Configuration Issues**
   - Using local backend for initial testing
   - Created clean Terraform files without conflicts
   - Simplified resource declarations

4. **Vertex AI Integration Issues**
   - Created simpler test script using the correct Google Cloud libraries
   - Fixed permission issues with IAM role assignments
   - Added detailed error reporting

## Google Cloud Shell Commands

For some operations, it may be necessary to use Google Cloud Shell. The `fix_cloud_run_access.sh` script generates a file with Cloud Shell commands that can be run to fix permission issues:

```bash
# Run the fix script to generate Cloud Shell commands
./gcp_migration/fix_cloud_run_access.sh

# Copy the generated commands and run them in Cloud Shell
cat gcp_migration/cloud_shell_commands.sh
```

## Directory Structure

```
gcp_migration/
├── execute_migration_fixed.sh      # Main migration script (fixed version)
├── execute_non_interactive.sh      # Non-interactive migration script
├── deploy_minimal_service.py       # Minimal service deployment
├── test_vertex_ai.py               # Vertex AI connectivity test
├── fix_cloud_run_access.sh         # Cloud Run permission fixing utility
├── fix_vertex_ai_auth.py           # Vertex AI authentication utility
├── migration_logs/                 # Migration logs and reports
└── model_configs/                  # Model configuration files

terraform/migration/
├── main.tf                         # Main Terraform configuration
├── variables.tf                    # Variable definitions
├── outputs.tf                      # Output definitions
├── backend.tf                      # Backend configuration
└── monitoring.tf                   # Monitoring configuration
```

## Troubleshooting

### Authentication Issues

If you encounter authentication issues:

```bash
# Check current authentication
gcloud auth list

# Create a service account key for local testing
./gcp_migration/fix_vertex_ai_auth.py --key-path=/path/to/key.json
```

### Cloud Run Access Issues

If Cloud Run services return 403 Forbidden:

```bash
# Run the fix script
./gcp_migration/fix_cloud_run_access.sh

# Or manually update the service to allow unauthenticated access
gcloud run services update SERVICE_NAME --region=REGION --allow-unauthenticated
```

### Terraform State Issues

If Terraform state management fails:

```bash
# Use local backend
cd terraform/migration
terraform init -reconfigure
```

## Logs and Reports

Migration logs and reports are stored in:

```
gcp_migration/migration_logs/
```

Key files include:
- `migration_execution_YYYYMMDD_HHMMSS.log` - Detailed execution log
- `migration_final_report.md` - Final migration report
- `vertex_ai_test_report.json` - Vertex AI test results
- `fix_permissions_YYYYMMDD_HHMMSS.log` - Permission fix log
