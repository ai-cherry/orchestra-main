# Unified Secret Management System

A complete solution for managing secrets in Google Cloud Platform with enhanced security, automated rotation, and seamless integration with development workflows.

## Features

- **GCP Secret Manager Integration**: Centralized storage and management of secrets
- **Zero-Trust Access Controls**: IAM conditions for time-based and service-based access
- **GitHub Secrets Migration**: Automated tools to migrate from GitHub Secrets to GCP
- **Automated Secret Rotation**: Schedule-based secret rotation for enhanced security
- **Docker & DevContainer Integration**: Seamless integration with development workflows
- **Terraform Infrastructure as Code**: Fully automated deployment and configuration

## Architecture

```
┌────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                │     │                 │     │                 │
│ GitHub Secrets │────▶│  GCP Secret     │◀────│ CI/CD Pipelines │
│                │     │  Manager        │     │                 │
└────────────────┘     │                 │     └─────────────────┘
                       │  - IAM Controls │
                       │  - Versioning   │     ┌─────────────────┐
┌────────────────┐     │  - Encryption   │     │                 │
│                │     │                 │◀────│ Applications     │
│ Cloud Scheduler│────▶│                 │     │                 │
│                │     └─────────────────┘     └─────────────────┘
└────────────────┘            ▲
                             │
┌────────────────┐          │           ┌─────────────────┐
│                │          │           │                 │
│ Rotation       │──────────┘           │ Docker Builds   │
│ Function       │                      │ & DevContainers │
│                │                      │                 │
└────────────────┘                      └─────────────────┘
```

## Components

1. **Terraform Modules**
   - `secret-manager`: Creates and manages secrets with IAM conditions
   - `secret-rotation`: Sets up Cloud Scheduler and Functions for rotation

2. **Python Client Library**
   - Robust client for accessing secrets with caching and error handling
   - Built-in support for fallback values and environment variables

3. **Migration Tools**
   - Command-line tool for GitHub to GCP migration
   - GitHub Actions workflow for CI/CD integration

4. **Integration Helpers**
   - Docker build integration with secrets as build arguments
   - DevContainer configuration tools

## Getting Started

### Prerequisites

- Google Cloud Platform project with Secret Manager API enabled
- Terraform 1.0.0+
- Python 3.8+
- Docker (for container integration)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/secret-management.git
   cd secret-management
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Deploy the infrastructure:
   ```bash
   ./deploy_secret_manager.sh --project-id=your-project-id
   ```

### Configuration

Edit the Terraform configuration in `terraform/deployment/terraform.tfvars` to customize:

- Secret definitions with metadata
- IAM access controls
- Rotation schedules
- Replication settings

## Usage

### Accessing Secrets from Applications

```python
from gcp_secret_client import SecretClient

# Initialize the client
client = SecretClient(project_id="your-project-id")

# Get a secret
api_key = client.get_secret("API_KEY")

# With fallback value
debug_mode = client.get_secret("DEBUG_MODE", fallback="false")

# With transformation
is_enabled = client.get_secret(
    "FEATURE_FLAG", 
    transform=lambda x: x.lower() == "true"
)
```

### Docker Integration

```bash
# Generate Docker build args
python docker_secrets.py build-args --project-id=your-project \
  --secrets=DB_PASSWORD,API_KEY

# Run a Docker build with secrets
python docker_secrets.py docker-build --project-id=your-project \
  --secrets=DB_PASSWORD,API_KEY --tag=myapp:latest
```

### DevContainer Integration

```bash
# Update devcontainer.json with secret values
python docker_secrets.py update-devcontainer --project-id=your-project \
  --secrets=DB_PASSWORD,API_KEY
```

### Migrating GitHub Secrets

```bash
# Migrate secrets from a GitHub repository
python migrate_github_to_gcp.py --project-id=your-project \
  --repo=owner/repo --service-accounts=your-sa@project.iam.gserviceaccount.com
```

## Security Best Practices

1. **Use Time-Based Conditions**: Restrict secret access to specific time windows
   ```hcl
   condition {
     title       = "business_hours_only"
     expression  = "request.time.getHours('America/New_York') >= 9 && request.time.getHours('America/New_York') < 17"
   }
   ```

2. **Service-Based Restrictions**: Limit access to specific services
   ```hcl
   condition {
     title       = "from_cloud_run_only"
     expression  = "resource.type == 'cloudrun.googleapis.com/Service'"
   }
   ```

3. **Regular Rotation**: Set up automatic rotation for critical secrets
   ```hcl
   rotation_period = "720h"  # 30 days
   ```

4. **Secret Labels**: Use labels for organization and governance
   ```hcl
   labels = {
     "environment" = "prod"
     "sensitivity" = "high"
     "application" = "payment-service"
   }
   ```

## Advanced Usage

### Custom Rotation Strategies

You can define custom rotation strategies by modifying the rotation function code. Add labels to secrets to specify the rotation strategy:

```hcl
labels = {
  "rotation_strategy" = "api"
  "rotation_param_api_url" = "https://api.example.com/refresh"
}
```

### Multi-Environment Configuration

Define different environments (dev, staging, prod) with appropriate IAM permissions:

```bash
./deploy_secret_manager.sh --project-id=your-project --environment=prod
```

### CI/CD Integration

Use the provided GitHub Actions workflow to automate secret migration as part of your CI/CD pipelines. See `.github/workflows/migrate-github-secrets.yml`.

## Troubleshooting

Common issues and solutions:

- **Permissions Errors**: Ensure the service account has the `Secret Manager Admin` role
- **Rotation Failures**: Check Cloud Function logs for detailed error messages
- **Client Timeouts**: Consider adjusting retry settings in the client library

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
