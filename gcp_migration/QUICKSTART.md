# AI Orchestra GCP-GitHub Integration Quick Start Guide

This guide provides the quickest path to set up a secure, production-ready integration between GitHub and Google Cloud Platform (GCP) for the AI Orchestra project.

## Prerequisites

Before starting, ensure you have:

- A GCP project with billing enabled
- Admin access to a GitHub organization or repository
- Local machine with:
  - Python 3.8+ 
  - `gcloud` CLI
  - `gh` CLI (GitHub CLI)

## Step 1: Install Dependencies

```bash
# Clone the repository if you haven't already
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Install the required dependencies
pip install -r gcp_migration/requirements.txt

# Optional: Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r gcp_migration/requirements.txt
```

## Step 2: Set Up Authentication

Create service account keys in GCP and obtain a GitHub Personal Access Token:

```bash
# Create a GCP service account with admin privileges (one-time setup)
gcloud iam service-accounts create orchestra-admin \
  --display-name="Orchestra Admin SA" \
  --project=cherry-ai-project

# Grant necessary permissions
gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:orchestra-admin@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/owner"

# Create and download the key
gcloud iam service-accounts keys create orchestra-admin-key.json \
  --iam-account=orchestra-admin@cherry-ai-project.iam.gserviceaccount.com

# Set environment variables
export GCP_MASTER_SERVICE_JSON=$(cat orchestra-admin-key.json)
export GH_CLASSIC_PAT_TOKEN=your_github_token  # Replace with your GitHub token
```

> ⚠️ **Security Note**: In a production environment, never store service account keys in repositories or share them. Workload Identity Federation will be set up to eliminate the need for long-lived keys.

## Step 3: Initialize the Integration Structure

```bash
# Run the initialization script
./gcp_migration/init_integration_structure.sh
```

## Step 4: Run the Integration Setup

```bash
# Set up the complete integration (replace with your values)
python gcp_migration/setup_gcp_github_integration.py setup \
  --project-id=cherry-ai-project \
  --github-org=ai-cherry \
  --github-repo=ai-cherry/orchestra-main
```

This command will:
1. Set up authentication with GCP and GitHub
2. Create and configure Workload Identity Federation
3. Configure bidirectional secret synchronization
4. Set up GitHub Actions workflow templates

## Step 5: Verify the Integration

```bash
# Verify that everything is set up correctly
python gcp_migration/setup_gcp_github_integration.py verify \
  --project-id=cherry-ai-project \
  --github-org=ai-cherry
```

## Step 6: Deploy Your First Service

1. **Create a deployment workflow file** in your repository:

   ```bash
   # Copy the template to your repository
   mkdir -p .github/workflows
   cp gcp_migration/.github/workflows/deploy-cloud-run.yml .github/workflows/
   ```

2. **Commit and push the workflow file** to trigger the deployment:

   ```bash
   git add .github/workflows/deploy-cloud-run.yml
   git commit -m "Add Cloud Run deployment workflow"
   git push
   ```

3. **Monitor the deployment** in the GitHub Actions tab of your repository

## Common Tasks

### Synchronize Secrets

```bash
# Synchronize secrets between GitHub and GCP
python gcp_migration/setup_gcp_github_integration.py sync-secrets \
  --project-id=cherry-ai-project \
  --github-org=ai-cherry \
  --direction=bidirectional
```

### Add a New Service

1. Update your repository with the new service code
2. Create a service-specific workflow file (copy and modify the template)
3. Commit and push the changes
4. The GitHub Actions workflow will automatically build and deploy the service

## Security Best Practices

- **Repository Protection**: Enable branch protection rules for your main branch
- **Approval Workflows**: Require approvals for production deployments
- **Regular Updates**: Keep dependencies updated and monitor for security advisories
- **Audit Logs**: Regularly review GCP audit logs and GitHub Action runs

## Troubleshooting

**Authentication Issues**:
```bash
# Check GCP authentication
gcloud auth list

# Check GitHub authentication
gh auth status
```

**Workflow Failures**:
1. Check the GitHub Actions logs for detailed error messages
2. Verify that all required secrets are properly set
3. Ensure service accounts have the necessary permissions

**Secret Synchronization Issues**:
```bash
# Run the sync with verbose logging
python gcp_migration/setup_gcp_github_integration.py sync-secrets \
  --project-id=cherry-ai-project \
  --github-org=ai-cherry \
  --verbose
```

## Next Steps

- Read the full documentation in `gcp_migration/GCP_GITHUB_INTEGRATION.md`
- Set up monitoring and alerts for your GCP resources
- Configure additional GitHub workflow templates for CI/CD pipelines
- Implement environment-specific configurations for staging/production

For more detailed information, see the complete [GCP-GitHub Integration Documentation](./GCP_GITHUB_INTEGRATION.md).