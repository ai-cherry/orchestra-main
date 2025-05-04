# GCP Project Migration Summary

This document summarizes the changes made to migrate from the old GCP project ID (`agi-baby-cherry`) to the new GCP project ID (`cherry-ai-project`).

## Changes Completed

1. **Backend Configuration**
   - Updated `infra/backend.tf` to reference the new GCS bucket `tfstate-cherry-ai-project`

2. **Script Configurations**
   - Confirmed `terraform-optimizer.sh` is already correctly using the new project ID `cherry-ai-project`
   - Enhanced `migrate_github_to_gcp_secrets.sh` for better security by removing hardcoded GitHub token

3. **Created Migration Automation**
   - Developed `update-project-references.sh` to systematically update references across the codebase
   - The script handles various reference patterns:
     - Service account emails (`@agi-baby-cherry.iam.gserviceaccount.com`)
     - GCS bucket references (`gs://agi-baby-cherry-bucket/`)
     - Artifact Registry references
     - General project ID references

## Remaining Tasks

1. **Execute the Project Reference Update Script**
   ```bash
   ./update-project-references.sh
   ```
   
   This script will:
   - Find all occurrences of the old project ID
   - Create backups of modified files
   - Update references in a safe manner
   - Log files requiring manual review

2. **Verify in CI/CD Configuration**
   - The `.github/workflows/terraform-deploy.yml` file has been updated with optimized configurations
   - Ensure GitHub repository secrets are configured with new GCP project references

3. **Update Service Accounts**
   - Service accounts created in the old project need to be recreated in the new project:
     - `vertex-agent@cherry-ai-project.iam.gserviceaccount.com`
     - `secret-management@cherry-ai-project.iam.gserviceaccount.com`
     - `github-actions-deployer@cherry-ai-project.iam.gserviceaccount.com`

4. **Migrate GCS Buckets**
   - Transfer data from old buckets to new buckets in the new project
   - Update bucket references in code (handled by the script)

5. **Verify Terraform Plans**
   - Run `terraform plan` in each environment to verify configurations work with the new project ID

## Manual Review Requirements

The following file types may need special attention after running the update script:

1. **Terraform Configuration Files**
   - Backend configurations
   - Provider blocks
   - Resource references with project IDs

2. **CI/CD Pipeline Files**
   - GitHub Actions workflows
   - GitLab CI/CD configurations
   - Cloud Build configurations

3. **Infrastructure Scripts**
   - Deployment scripts
   - Migration scripts
   - Service account setup scripts

4. **Documentation**
   - README files
   - Deployment guides
   - Migration instructions

## Testing the Changes

After making all updates, follow these steps to validate:

1. **Terraform Operations**
   ```bash
   ./terraform-optimizer.sh validate all
   ./terraform-optimizer.sh plan all
   ```

2. **CI/CD Pipeline**
   - Create a test PR to verify GitHub Actions workflow runs successfully
   - Check if all environment references are correctly using the new project ID

3. **Local Development Scripts**
   - Test local development setup scripts to ensure they reference the new project

## Note on Project Resource Migration

This document primarily covers code references to the GCP project ID. For the actual migration of GCP resources from one project to another, refer to:

1. **GCP Documentation**: [Moving Resources Between Projects](https://cloud.google.com/resource-manager/docs/moving-projects-folders-organizations)
2. **Resource Migration Scripts**: Scripts in the repository for migrating specific resources (e.g., `gcp_archive_migrate.sh`)

For the actual resource migration process, use GCP-supported methods:
- Direct project moves (where supported)
- Data export/import for databases
- Storage transfer for GCS buckets
- Service account recreation and key management
