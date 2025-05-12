# GitHub Codespaces to Google Cloud Workstations Migration

This guide provides a comprehensive approach to migrating from GitHub Codespaces to Google Cloud Workstations, with special focus on maintaining AI coding assistance and optimizing for performance.

## Table of Contents

- [Migration Overview](#migration-overview)
- [Prerequisites](#prerequisites)
- [Step-by-Step Migration Process](#step-by-step-migration-process)
- [AI Coding Assistance Post-Migration](#ai-coding-assistance-post-migration)
- [Pros and Cons After Migration](#pros-and-cons-after-migration)
- [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
- [GitHub's Role Post-Migration](#githubs-role-post-migration)

## Migration Overview

The migration involves four main phases:

1. **Infrastructure Setup**: Create GCP resources using Terraform
2. **Secret Migration**: Transfer GitHub and GCP secrets to Google Secret Manager
3. **Development Environment Configuration**: Set up Cloud Workstations with VSCode and AI assistants
4. **CI/CD Pipeline Migration**: Convert GitHub Actions to Cloud Build pipelines

## Prerequisites

- Google Cloud Platform account with billing enabled
- Google Cloud SDK (gcloud CLI) installed
- Terraform installed (v1.0.0+)
- GitHub repository access
- Current GitHub secrets and environment variables

## Step-by-Step Migration Process

### 1. Run the Automated Migration Script

We've created a migration script that will set up the necessary infrastructure and configuration files:

```bash
# Make the script executable
chmod +x gcp_workstation_migrate.sh

# Run the script
./gcp_workstation_migrate.sh
```

The script will create:
- Terraform configuration for Cloud Workstations
- Secret migration scripts
- AI coding assistance configuration files

### 2. Set Up Infrastructure with Terraform

```bash
# Navigate to the Terraform directory
cd terraform/gcp_workstation

# Create your terraform.tfvars file from the example
cp terraform.tfvars.example terraform.tfvars

# Edit the terraform.tfvars file with your GCP project details
nano terraform.tfvars

# Initialize Terraform
terraform init

# Apply the Terraform configuration
terraform apply
```

This will create:
- Cloud Workstation cluster and configurations
- Network infrastructure
- Service accounts with necessary permissions
- Secret Manager secrets

### 3. Migrate Secrets

```bash
# Run the secret migration script
./migrate_secrets.sh
```

This will transfer all GitHub and GCP secrets to Google Secret Manager.

### 4. Set Up Cloud Workstation

1. Open the Google Cloud Console
2. Navigate to Cloud Workstations
3. Launch your Cloud Workstation
4. Clone your GitHub repository:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```
5. Run the AI assistance setup script:
   ```bash
   ./setup_ai_assistance.sh
   ```

## AI Coding Assistance Post-Migration

The following AI coding assistants are configured post-migration:

### Gemini Code Assist

- Configured with enhanced GCP integration
- Directly connected to Vertex AI services
- Enhanced with GCP-specific commands and capabilities
- Path adjusted for Cloud Workstations environment

### Roo and Cline Integration

- Both assistants remain fully functional
- Enhanced with MCP memory integration
- Connected to Firestore for persistent memory storage
- Configured for Cloud Workstations environment

### MCP Memory System

- Memory storage migrated to Firestore
- Enhanced context awareness for GCP environment
- Performance-first configuration
- Shared memory across all AI assistants

### Advantages Over GitHub Codespaces

- Lower latency to GCP resources
- Direct API access without network hops
- Higher quotas and priority access to AI services
- Support for larger context windows
- Better integration with Vertex AI for experiments

## Pros and Cons After Migration

### Pros

1. **Scalability**: No more repository size or GPU limits
2. **Performance**: Direct access to GCP resources without latency
3. **Integration**: Native access to Vertex AI, BigQuery, etc.
4. **Security**: Secrets managed properly in Secret Manager
5. **Resources**: More compute power, memory, and storage
6. **Cost control**: Better visibility into resource usage
7. **Development speed**: Faster builds, deployments, and testing

### Cons

1. **Cost**: $200-600/month vs. GitHub's included hours
2. **Learning curve**: New Cloud Build syntax to master
3. **Lock-in**: Deeper integration with GCP ecosystem
4. **Setup time**: Initial migration requires effort
5. **GitHub sync**: Need to maintain GitHub repo in sync with GCP

## Common Issues and Troubleshooting

### Authentication Issues

If you encounter authentication problems:

```bash
# Re-authenticate with GCP
gcloud auth login

# Configure application default credentials
gcloud auth application-default login
```

### Network Connectivity

If your Cloud Workstation can't connect to the internet:

1. Check if the Cloud NAT gateway is properly configured
2. Ensure firewall rules allow egress traffic
3. Verify VPC configuration

### Missing Extensions

If VS Code extensions aren't working:

```bash
# Install extensions manually
code --install-extension googlecloudtools.cloudcode
code --install-extension ms-python.python
code --install-extension anthropic.claude
```

### AI Assistance Not Working

If AI coding assistance isn't working:

1. Check Secret Manager for required API keys
2. Verify service account permissions
3. Rebuild the AI memory system:
   ```bash
   python3 $HOME/.ai-memory/initialize.py
   ```

## GitHub's Role Post-Migration

GitHub remains involved in the following ways:
- Primary code repository (source of truth)
- Pull request reviews and collaboration
- Issue tracking

However, all execution now happens in GCP:
- Cloud Build handles CI/CD (not GitHub Actions)
- Deployment happens directly to Cloud Run
- Development occurs in Cloud Workstations
- Secrets are managed in Secret Manager

For more detailed information, refer to the full documentation in `GCP_WORKSTATION_MIGRATION_PLAN.md`.
