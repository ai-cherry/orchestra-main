# GitHub Actions Secrets for Workload Identity Federation

This document outlines the specific GitHub Actions Secrets required to configure the `google-github-actions/auth@v1` action for Workload Identity Federation.

## Required Secrets

To properly configure Workload Identity Federation for GitHub Actions with the cherry-ai-project, you need to set up the following secrets in your GitHub repository:

| Secret Name | Value Format | Description |
|-------------|--------------|-------------|
| `WORKLOAD_IDENTITY_PROVIDER` | `projects/{PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/providers/github-provider` | The full resource name of the Workload Identity Provider |
| `SERVICE_ACCOUNT` | `github-actions-deployer@cherry-ai-project.iam.gserviceaccount.com` | The email address of the service account to impersonate |
| `PROJECT_ID` | `cherry-ai-project` | The Google Cloud project ID |

## Workflow Configuration

Here's an example of how to use these secrets in a GitHub Actions workflow:

```yaml
name: Deploy to GCP

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    # These permissions are required for workload identity federation
    permissions:
      contents: 'read'
      id-token: 'write'
    
    steps:
    - uses: 'actions/checkout@v3'
    
    - id: 'auth'
      name: 'Authenticate to Google Cloud'
      uses: 'google-github-actions/auth@v1'
      with:
        workload_identity_provider: '${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}'
        service_account: '${{ secrets.SERVICE_ACCOUNT }}'
        project_id: '${{ secrets.PROJECT_ID }}'
    
    # After authentication, you can use other GCP actions
    - name: 'Set up Cloud SDK'
      uses: 'google-github-actions/setup-gcloud@v1'
    
    # Example of deploying to Cloud Run
    - name: 'Deploy to Cloud Run'
      run: |-
        gcloud run deploy my-service \
          --region us-central1 \
          --image gcr.io/${{ secrets.PROJECT_ID }}/my-image \
          --platform managed
```

## Important Notes

1. The `id-token: 'write'` permission is crucial as it allows the action to request an OIDC token from GitHub's token service.

2. The Workload Identity Provider value should include your actual GCP project number. You can obtain this from the outputs of your Terraform deployment or from the GCP console.

3. Make sure the service account (`github-actions-deployer`) has been granted the appropriate IAM roles as defined in your Terraform configuration.

4. The service account must have been properly configured for workload identity federation with the correct principal set format:
   ```
   principalSet://iam.googleapis.com/projects/{PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/ai-cherry/orchestra-main
   ```

## Terraform Outputs

You can extract these values from your Terraform outputs:

```bash
# Get the Workload Identity Provider
terraform output -raw workload_identity_pool_provider_name

# Get the Service Account email
terraform output -raw github_actions_deployer_email
```

## Security Considerations

- Never commit these secrets directly to your repository
- Regularly rotate the service account credentials if you're not using Workload Identity Federation
- Limit the permissions of the service account to only what is necessary for your workflows
