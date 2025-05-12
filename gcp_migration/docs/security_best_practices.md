# GCP Migration Security Best Practices

This document outlines security best practices for using the GCP Migration toolkit, particularly when migrating sensitive resources like secrets and credentials.

## Authentication and Authorization

### Service Account Security

1. **Use the principle of least privilege**
   - Create service accounts with only the specific roles needed for migration tasks
   - Avoid using owner roles except when absolutely necessary

2. **Secure service account keys**
   - Store service account keys securely with appropriate file permissions (`chmod 600`)
   - Consider using [workload identity federation](https://cloud.google.com/iam/docs/workload-identity-federation) instead of keys when possible
   - Never commit service account keys to version control
   - Rotate keys regularly

3. **Use temporary credentials**
   - For one-time migrations, create a service account with a temporary key
   - Delete the key after migration completion

### User Authentication

1. **Use application default credentials when possible**
   - Prefer `gcloud auth application-default login` over service account keys
   - Use `gcloud auth revoke` after migration is complete

2. **Use short-lived tokens**
   - For GitHub tokens, use tokens with the shortest possible expiration

## Secret Management

1. **Secret migration security**
   - Use HTTPS for all API calls
   - Don't log secret values, even in debug mode
   - Consider using secret rotation after migration

2. **GCP Secret Manager best practices**
   - Use appropriate access controls (IAM) for secrets
   - Add labels for better organization and tracking
   - Consider setting up secret rotation

3. **Clean up temporary secrets**
   - Remove any temporary secrets created during migration
   - Consider using [secret versioning](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create-secret-version) for tracking changes

## Data Security

1. **Storage security**
   - Use encrypted buckets for storing any migration data
   - Apply appropriate retention policies
   - Use signed URLs with short expiration for temporary access

2. **Firestore security**
   - Use security rules to restrict access to Firestore data
   - Consider using field-level encryption for sensitive data

3. **Network security**
   - Use VPC Service Controls when possible
   - Use Private Google Access for GCP services

## Infrastructure Security

1. **Infrastructure as Code security**
   - Ensure all Terraform state files are secured
   - Use remote state with appropriate access controls
   - Validate all infrastructure changes before applying

2. **Resource cleanup**
   - Remove unused resources after migration
   - Document remaining resources and their owners

3. **Logging and monitoring**
   - Enable Cloud Audit Logs for migration-related resources
   - Set up alerts for suspicious activities

## GitHub Security

1. **Repository security**
   - Use branch protection rules for repositories
   - Implement code owners for sensitive code
   - Consider making repositories private when they contain sensitive information

2. **GitHub token security**
   - Use the minimum required scope for GitHub tokens
   - Revoke GitHub tokens after migration
   - Use temporary tokens with short lifetimes

## Audit and Compliance

1. **Logging**
   - Enable comprehensive logging for all migration operations
   - Store logs for an appropriate period based on compliance requirements

2. **Audit**
   - Perform a post-migration audit to ensure all resources were migrated correctly
   - Check for any exposed credentials or secrets

3. **Documentation**
   - Document all migration steps for compliance purposes
   - Record decisions about security tradeoffs

## Example: Secure Secret Migration

Here's an example of migrating secrets securely:

```python
import os
import tempfile
from gcp_migration.infrastructure.secret_manager_service import SecretManagerService

# Use a temporary file for any intermediate storage
with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
    # Store sensitive data temporarily with restricted permissions
    os.chmod(temp_file.name, 0o600)
    
    # Initialize the service with minimal permissions
    secret_service = SecretManagerService()
    
    # Migrate secrets using token from environment (not hardcoded)
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    # Migrate with audit logging
    result = secret_service.migrate_github_secrets(
        github_org="your-org",
        github_repo="your-repo",
        project_id="your-project",
        github_token=github_token,
        audit_log="/path/to/audit.log"
    )
    
    # Revoke credentials immediately after use
    os.system("gcloud auth revoke")
```

## Security Checklist

Use this checklist before and after migration:

- [ ] Service accounts have minimal permissions
- [ ] Service account keys are secured and scheduled for deletion
- [ ] GitHub tokens are revoked after use
- [ ] Secrets are correctly migrated and verified
- [ ] Access to migrated resources is restricted
- [ ] Temporary resources are cleaned up
- [ ] Audit logs are exported and stored securely
- [ ] Post-migration security scan is completed
- [ ] Migration scripts don't contain hardcoded credentials
