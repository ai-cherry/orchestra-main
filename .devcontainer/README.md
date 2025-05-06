# Terraform Development Environment

This dev container is set up for Terraform development with the following tools pre-installed:

- **Terraform CLI**: Version 1.5.0
- **TFLint**: Version v0.48.0 for linting Terraform code
- **Terragrunt**: Version v0.51.0 for managing Terraform configurations at scale (optional)
- **Google Cloud CLI**: For working with GCP resources

## Getting Started

1. Open this workspace in VS Code with the Remote - Containers extension installed
2. VS Code will prompt you to reopen the workspace in a container - select "Reopen in Container"
3. The container will build and start, providing a full Terraform development environment

## Extensions Included

- HashiCorp Terraform - Syntax highlighting, IntelliSense, and validation for Terraform
- Docker - For managing Docker containers
- GitLens - Enhanced Git integration
- YAML - Support for YAML files (commonly used with Terraform)
- 4ops.terraform - Additional Terraform features and snippets

## Usage

- Create your Terraform files in the workspace
- Use the integrated terminal to run Terraform commands
- TFLint is available for checking your Terraform code for possible errors and best practices

## Example Commands

```bash
# Initialize Terraform in the current directory
terraform init

# Validate your Terraform configuration
terraform validate

# Check for lint errors
tflint

# If using Terragrunt, initialize with
terragrunt init
```

You can create Terraform files anywhere in the workspace and manage them using this environment.