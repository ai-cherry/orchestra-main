# Deployment System Changes

This document outlines the recent changes made to the Orchestra deployment system to improve consistency, reduce redundancy, and simplify the deployment process.

## Project Updates
- Updated Project ID from cherry-ai-project to cherry-ai.me
- Project Number: 525398941159
- Region: us-central1
- Service Account: vertex-agent@cherry-ai.me.iam.gserviceaccount.com

## Changes Made
1. Updated all Docker image references to new registry:
   - us-central1-docker.pkg.dev/cherry-ai.me/orchestra/*

2. Updated Cloud Storage bucket names:
   - tfstate-cherry-ai-me-orchestra
   - cherry-ai-me-cloudbuild-artifacts
   - cherry-ai-me-model-artifacts

3. Updated Cloud Run service configurations:
   - Service account updated to vertex-agent@cherry-ai.me.iam.gserviceaccount.com
   - Environment variables updated with new project ID
   - Endpoints reconfigured for new project

4. Updated Vertex AI configurations:
   - Model endpoints updated with new project references
   - Training pipelines reconfigured
   - Service account permissions updated

5. Updated GitHub Actions workflows:
   - Updated all GCP project references
   - Updated registry URLs
   - Updated service account references

6. Updated Infrastructure as Code:
   - Terraform state bucket renamed
   - Backend configurations updated
   - Resource naming updated
   - IAM policies reconfigured

7. Updated Container Registry:
   - Migrated images to new registry
   - Updated build triggers
   - Updated pull/push permissions

8. Updated Documentation:
   - Updated all project references
   - Updated command examples
   - Updated endpoint URLs

## Required Actions
1. Re-authenticate service accounts
2. Update CI/CD environment variables
3. Redeploy services with new configurations
4. Verify all endpoints and permissions
5. Update DNS records if needed

## Summary of Changes

1. **Unified Deployment Script**: Created a single `deploy.sh` script that handles all deployment scenarios, replacing separate scripts for Cloud Run and production deployments.

2. **Consolidated Terraform Management**: Updated `run_terraform.sh` to support all environments (dev, stage, prod) and commands, replacing the separate `run_terraform_dev.sh`.

3. **Fixed Circular References**: Eliminated circular references between deployment scripts to improve reliability.

4. **Added Missing Outputs**: Added required Terraform outputs to support the deployment scripts.

5. **Comprehensive Documentation**: Created `DEPLOYMENT.md` with detailed deployment instructions.

## New Deployment Structure

```
deploy.sh                # Main deployment entry point for all scenarios
├── deploy_to_cloud_run.sh   # Legacy wrapper (redirects to deploy.sh)
└── deploy_to_production.sh  # Legacy wrapper (redirects to deploy.sh)

run_terraform.sh         # Unified Terraform management
└── run_terraform_dev.sh     # Legacy wrapper (redirects to run_terraform.sh)
```

## Usage Examples

### Unified Deployment Script

```bash
# Deploy to development environment using Terraform (default)
./deploy.sh dev

# Deploy to production environment using Terraform
./deploy.sh prod

# Deploy directly to Cloud Run in the staging environment
./deploy.sh stage cloud-run
```

### Unified Terraform Script

```bash
# Initialize Terraform for development
./run_terraform.sh dev init

# Plan changes for production
./run_terraform.sh prod plan

# Apply changes in staging environment
./run_terraform.sh stage apply

# Show outputs for dev environment
./run_terraform.sh dev output
```

## Backward Compatibility

To ensure a smooth transition, legacy scripts are maintained as wrappers that redirect to the new unified scripts:

- `deploy_to_cloud_run.sh` → `deploy.sh [env] cloud-run`
- `deploy_to_production.sh` → `deploy.sh prod terraform`
- `run_terraform_dev.sh` → `run_terraform.sh dev plan`

These wrappers display a deprecation notice and will be removed in a future update.

## Benefits

1. **Consistency**: All deployment methods follow the same pattern and share common code
2. **Reduced Redundancy**: Eliminates duplicate code across multiple scripts
3. **Simplified Maintenance**: Changes to deployment logic only need to be made in one place
4. **Better Error Handling**: Improved validation and error reporting
5. **Clear Documentation**: Comprehensive guide for all deployment scenarios

## Next Steps

1. Update CI/CD pipelines to use the new unified scripts
2. Remove deprecated wrapper scripts in future releases
3. Extend environment support to include custom environments beyond dev/stage/prod
