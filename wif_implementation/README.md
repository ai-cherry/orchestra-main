# Workload Identity Federation (WIF) for GitHub & GCP

This package provides a comprehensive solution for implementing Workload Identity Federation between GitHub Actions and Google Cloud Platform (GCP). This approach eliminates the security risks associated with storing service account keys in GitHub Secrets.

## Overview

The WIF implementation provides:

1. **Type-safe configuration** using Pydantic models
2. **Template-based generation** of:
   - GitHub Actions workflows
   - Terraform configuration for WIF setup
3. **Command-line interface** for easy setup
4. **Error handling and logging** for reliable operation

## Components

- **`config_models.py`**: Pydantic models for configuration
- **`error_handler.py`**: Error handling utilities
- **`enhanced_template_manager.py`**: Template management with Jinja2
- **`cicd_manager.py`**: CI/CD integration
- **`setup_wif_cli.py`**: Command-line interface for setup

## Getting Started

### Prerequisites

- Python 3.11 or higher
- GCP project with billing enabled
- GitHub repository
- `gcloud` CLI tool installed and configured
- `gh` CLI tool installed and authenticated (for GitHub secrets setup)

### Installation

```bash
# Clone this repository (if not already included in your project)
git clone https://github.com/your-org/wif-implementation.git

# Navigate to the directory
cd wif-implementation

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

The quickest way to set up WIF is using the CLI:

```bash
python -m wif_implementation.setup_wif_cli \
  --project-id your-gcp-project-id \
  --region us-central1 \
  --github-repo your-org/your-repo
```

This will:
1. Generate Terraform configuration for WIF setup
2. Generate a GitHub Actions workflow template
3. Set up GitHub secrets (if GitHub CLI is available)

### Advanced Configuration

For more control, you can use the Python API:

```python
from wif_implementation.config_models import (
    GCPProjectConfig, GitHubConfig, RepositoryConfig, 
    WIFImplementationConfig, WorkloadIdentityConfig
)
from wif_implementation.enhanced_template_manager import create_template_manager

# Create configuration
config = WIFImplementationConfig(
    gcp=GCPProjectConfig(
        project_id="your-gcp-project-id",
        project_number="your-gcp-project-number",
        region="us-central1",
    ),
    workload_identity=WorkloadIdentityConfig(
        pool_id="github-pool",
        provider_id="github-provider",
        service_account_id="github-actions-sa",
    ),
    github=GitHubConfig(
        repositories=[
            RepositoryConfig(
                owner="your-org",
                name="your-repo",
            ),
        ],
    ),
)

# Create template manager
template_manager = create_template_manager(config)

# Generate Terraform configuration
template_manager.write_template_to_file(
    "terraform_wif.tf.j2",
    "terraform/wif.tf",
    context={"repo_condition": "your-org/your-repo"},
)

# Generate GitHub Actions workflow
template_manager.write_template_to_file(
    "github_workflow.yml.j2",
    ".github/workflows/deploy.yml",
    context={"workflow_name": "Deploy with WIF"},
)
```

## Implementation Details

### Workflow

1. **Create Workload Identity Pool and Provider** in GCP (via Terraform)
2. **Create Service Account** with appropriate permissions (via Terraform)
3. **Configure attribute mapping** to match GitHub's OIDC token claims
4. **Set up GitHub repository secrets** with the necessary configuration
5. **Update GitHub Actions workflows** to use WIF authentication

### GitHub Actions Configuration

The generated workflow includes:

```yaml
- name: Google Auth via Workload Identity Federation
  uses: google-github-actions/auth@v2
  with:
    token_format: 'access_token'
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
```

### Security Considerations

- **No service account keys** are stored in GitHub Secrets
- **Fine-grained access control** through repository-specific conditions
- **Temporary credentials** generated during workflow execution
- **Principle of least privilege** through targeted IAM roles

## Troubleshooting

If you encounter issues with WIF setup:

1. **Verify your GCP configuration** using the `gcloud` CLI
2. **Check GitHub repository secrets** are correctly set
3. **Validate the workflow YAML** for syntax errors
4. **Review IAM permissions** for the service account
5. **Check authentication logs** for permission issues

For more details, refer to the [Google Cloud documentation on Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation).

## Contributing

Feel free to contribute to this project by opening issues or pull requests. All contributions are welcome!