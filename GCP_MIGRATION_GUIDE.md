# AI Orchestra GCP Migration Guide

This guide provides detailed instructions for completing the migration to Google Cloud Platform. It addresses all critical issues blocking the deployment process and provides step-by-step procedures for a successful migration.

## Critical Issues Fixed

This migration addresses the following critical issues that were blocking deployment:

1. **Poetry Configuration Format Mismatch**: Fixed the incompatibility between `pyproject.toml` format and Poetry expectations
2. **Service Account Permissions**: Added necessary IAM roles to the build service account
3. **Deployment Process Standardization**: Consolidated multiple approaches into a single, reliable deployment pipeline

## Prerequisites

Before beginning the migration, ensure you have:

- Google Cloud SDK (`gcloud`) installed and configured
- Docker installed and configured
- Access to the GCP project (`cherry-ai-project`)
- GitHub repository access with admin permissions
- Poetry 1.7.0 or higher installed

## Migration Steps

### 1. Fix Poetry Configuration

The `services/admin-api/pyproject.toml` file has been updated to use the correct Poetry format. This resolves the build failure where Poetry was unable to find the `[tool.poetry]` section.

**Verification:**
```bash
grep "\[tool.poetry\]" services/admin-api/pyproject.toml
```

If this returns the section header, the fix has been successfully applied.

### 2. Fix Service Account Permissions

The service account used for Cloud Build was missing necessary permissions, particularly `roles/logging.logWriter`. Run the provided script to add all required permissions:

```bash
# Make the script executable if needed
chmod +x fix_service_account_permissions.sh

# Run the script
./fix_service_account_permissions.sh
```

**Verification:**
After running the script, you should see confirmation that all roles were successfully granted to the service account.

### 3. Deploy Using the Standardized Process

A new standardized deployment script has been created that consolidates the various approaches and includes robust validation and error handling:

```bash
# Make the script executable if needed
chmod +x deploy_to_gcp.sh

# For a basic deployment with defaults
./deploy_to_gcp.sh

# For a customized deployment
./deploy_to_gcp.sh \
  --project-id=cherry-ai-project \
  --region=us-central1 \
  --service=admin-api \
  --source-dir=services/admin-api \
  --min-instances=1 \
  --max-instances=5 \
  --env-vars="DEBUG=false,LOG_LEVEL=info"
```

**Available Parameters:**
- `--project-id`: GCP project ID (default: cherry-ai-project)
- `--region`: GCP region (default: us-central1)
- `--service`: Service name (default: admin-api)
- `--dockerfile`: Path to Dockerfile (default: services/admin-api/Dockerfile)
- `--source-dir`: Source directory (default: services/admin-api)
- `--min-instances`: Minimum instances (default: 0)
- `--max-instances`: Maximum instances (default: 10)
- `--memory`: Memory allocation (default: 1Gi)
- `--cpu`: CPU allocation (default: 1)
- `--env-vars`: Environment variables (comma-separated key=value pairs)

### 4. Set Up GitHub Actions Workflow

A GitHub Actions workflow has been created that uses Workload Identity Federation for secure GCP authentication. This eliminates the need for storing service account keys in GitHub.

1. Ensure the repository has the following secrets configured:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_REGION`: Your preferred GCP region
   - `GCP_ARTIFACT_REGISTRY`: The name of your Artifact Registry
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`: The full resource name of your Workload Identity Provider
   - `GCP_SERVICE_ACCOUNT`: The email of your GCP service account

2. The workflow will automatically deploy the admin-api service when:
   - Code is pushed to main or develop branches
   - Pull requests are opened against main or develop
   - The workflow is manually triggered

## Continuous Integration/Deployment

The GitHub Actions workflow provides a robust CI/CD pipeline:

1. **Validation**: Checks that the Poetry configuration and Dockerfile are valid
2. **Build**: Builds and pushes the Docker image to Artifact Registry
3. **Deploy**: Deploys the image to Cloud Run
4. **Verify**: Confirms the deployment is successful and healthy
5. **Notify**: Posts status comments on pull requests

## Testing Your Migration

To verify the migration was successful:

1. Run the deployment script:
   ```bash
   ./deploy_to_gcp.sh
   ```

2. Visit the deployed service URL (provided at the end of deployment)

3. Check the logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=admin-api" --limit=10
   ```

## Troubleshooting

### Common Issues

1. **Docker Build Fails**:
   - Verify that `pyproject.toml` has the `[tool.poetry]` section
   - Check that `poetry.lock` is present and up-to-date
   - Ensure Dockerfile has the correct `COPY` commands for Python files

2. **Deployment Fails**:
   - Check service account permissions
   - Verify that all required APIs are enabled
   - Look for quota issues or resource constraints

3. **Service Unhealthy**:
   - Check the application logs for errors
   - Verify that all environment variables are set correctly
   - Confirm that the service has proper permissions to access other resources

### Getting Help

If you encounter issues not covered in this guide:

1. Check the detailed logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=admin-api" --limit=50
   ```

2. Review the build logs:
   ```bash
   gcloud builds list --filter="source.repo_source.repo_name=github_ai-cherry_orchestra-main"
   gcloud builds log [BUILD_ID]
   ```

## Next Steps

After completing the migration:

1. Remove any deprecated deployment scripts
2. Update documentation to reflect the new deployment process
3. Train team members on using the new deployment workflow
4. Consider setting up monitoring and alerting for the deployed services

## References

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
