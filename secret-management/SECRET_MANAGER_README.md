# GCP Secret Manager Automation

This directory contains scripts for programmatic interaction with Google Cloud Secret Manager. These tools allow you to create, update, and manage secrets with proper error handling, authentication verification, and best practices.

## Prerequisites

- Google Cloud SDK (gcloud) installed and configured
- Project ID with Secret Manager API enabled
- Appropriate IAM permissions to create/access secrets

## Scripts Overview

### 1. `create_secret.sh`

A comprehensive script for creating or updating secrets in Google Cloud Secret Manager.

Features:
- Automatic authentication checking
- Secret Manager API enablement (if needed)
- Support for automatic or user-managed replication
- Environment-based naming convention (e.g., `SECRET_NAME-production`)
- Versioning support for existing secrets
- Detailed output and error handling

#### Usage

```bash
./create_secret.sh SECRET_NAME SECRET_VALUE [PROJECT_ID] [REPLICATION_POLICY] [ENVIRONMENT] [LOCATION]
```

#### Parameters

- `SECRET_NAME` (required): Name of the secret
- `SECRET_VALUE` (required): Value to store in the secret
- `PROJECT_ID` (optional): GCP project ID (defaults to "agi-baby-cherry" or value in .env file)
- `REPLICATION_POLICY` (optional): "automatic" or "user-managed" (default: "automatic")
- `ENVIRONMENT` (optional): Environment suffix (default: "production")
- `LOCATION` (optional): Region(s) for user-managed replication (default: "us-central1")

#### Examples

Basic usage:
```bash
./create_secret.sh API_KEY "my-secret-api-key"
```

Custom project and environment:
```bash
./create_secret.sh DATABASE_PASSWORD "secure-password" "my-project-id" "automatic" "staging"
```

Multi-region replication:
```bash
./create_secret.sh SERVICE_ACCOUNT_KEY "$(cat key.json)" "my-project" "user-managed" "prod" "us-central1,us-west1"
```

### 2. `secret_examples.sh`

Sample script demonstrating various use cases for the `create_secret.sh` script:
- Basic API key creation
- Multi-region secret replication
- Environment-specific secrets
- JSON structured secrets
- Reading secrets from files

## Integration with Existing Secret Management

This solution integrates with the existing unified secret management system:

1. Uses the same environment-based naming convention (`SECRET_NAME-environment`)
2. Supports the same replication policies
3. Maintains versioning for secret updates
4. Compatible with existing Terraform modules and CI/CD pipelines

## Best Practices

1. **Naming Convention**: Use consistent naming with environment suffixes
2. **Secret Values**: Avoid special characters in command-line values (use files for complex values)
3. **Replication**: Use "automatic" for most cases, "user-managed" for specific compliance needs
4. **IAM Permissions**: Apply least privilege principle for secret access
5. **Rotation**: Implement periodic rotation of sensitive secrets (e.g., via Cloud Scheduler)

## Troubleshooting

### Authentication Issues
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Permission Denied
Ensure you have the following IAM roles:
- Secret Manager Admin (`roles/secretmanager.admin`)
- Service Usage Admin (`roles/serviceusage.admin`) - for enabling APIs

### API Not Enabled
```bash
gcloud services enable secretmanager.googleapis.com
```

## Using Secrets in Applications

### Command Line
```bash
# Access the latest version
SECRET_VALUE=$(gcloud secrets versions access latest --secret="MY_SECRET-production")

# Access a specific version
SECRET_VALUE=$(gcloud secrets versions access 2 --secret="MY_SECRET-production")
```

### Python Client
```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/PROJECT_ID/secrets/MY_SECRET-production/versions/latest"
response = client.access_secret_version(request={"name": name})
secret_value = response.payload.data.decode("UTF-8")
```

### Terraform Integration
```hcl
data "google_secret_manager_secret_version" "my_secret" {
  project = "my-project"
  secret  = "MY_SECRET-production"
  version = "latest"
}

# Use the secret value
resource "some_resource" "example" {
  secret_data = data.google_secret_manager_secret_version.my_secret.secret_data
}
```

## Security Recommendations

1. **Never commit secrets** to version control
2. **Always use IAM conditions** for sensitive secrets (time-based, service-based)
3. **Enable audit logging** for Secret Manager
4. **Implement secret rotation** for sensitive credentials
5. **Use VPC Service Controls** for additional security

## Related Resources

- [GCP Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Secret Manager Terraform Module](https://registry.terraform.io/modules/GoogleCloudPlatform/secret-manager/google/latest)
- [Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
