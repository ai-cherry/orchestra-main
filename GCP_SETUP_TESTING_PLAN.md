# GCP Environment Setup Testing Plan

This document outlines the testing procedures for verifying the GCP environment setup for the AI Orchestra project.

## Prerequisites

Before running the tests, ensure you have:

1. Set up the `GCP_SERVICE_ACCOUNT_KEY` Codespaces secret with your service account key
2. Rebuilt your Codespace container (or created a new one) to apply the devcontainer.json changes
3. Run the `setup-gcp.sh` script to enable APIs and verify authentication
4. Provisioned the necessary GCP resources using the appropriate scripts

## 1. Authentication Testing

Verify that your Codespace is properly authenticated with GCP:

```bash
# Check active account
gcloud auth list

# Verify project configuration
gcloud config get-value project

# Verify service account credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS | jq .client_email
```

Expected results:
- The active account should be your service account (`orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com`)
- The project should be set to `cherry-ai-project`
- The `GOOGLE_APPLICATION_CREDENTIALS` environment variable should point to your service account key file

## 2. API Availability Testing

Verify that the required APIs are enabled:

```bash
# List enabled APIs
gcloud services list --enabled --project=cherry-ai-project | grep -E 'aiplatform|compute|storage|workstations|notebooks|run'
```

Expected results:
- The following APIs should be listed:
  - `aiplatform.googleapis.com` (Vertex AI)
  - `compute.googleapis.com` (Compute Engine)
  - `storage.googleapis.com` (Cloud Storage)
  - `workstations.googleapis.com` (Cloud Workstations)
  - `notebooks.googleapis.com` (Vertex AI Workbench)
  - `run.googleapis.com` (Cloud Run)

## 3. Vertex AI Workbench Testing

If you've provisioned a Vertex AI Workbench instance:

```bash
# List Vertex AI Workbench instances
gcloud notebooks instances list --project=cherry-ai-project

# Get the URL for your notebook
gcloud notebooks instances describe cherry-notebook --location=us-central1-a --format="value(proxyUri)"
```

Manual testing:
1. Open the Workbench URL in your browser
2. Verify you can access JupyterLab
3. Create a new notebook and run a simple Python cell:
   ```python
   import google.cloud.aiplatform as aiplatform
   aiplatform.init(project='cherry-ai-project')
   print("Successfully connected to Vertex AI!")
   ```
4. Verify that the repository has been cloned to the instance

## 4. Cloud Workstation Testing

If you've provisioned a Cloud Workstation:

```bash
# List Cloud Workstation configurations
gcloud beta workstations configs list --project=cherry-ai-project --location=us-central1

# List Cloud Workstation instances
gcloud beta workstations list --project=cherry-ai-project --location=us-central1
```

Manual testing:
1. Open the Google Cloud Console
2. Navigate to Cloud Workstations
3. Launch your workstation
4. Verify that VS Code opens in the browser
5. Verify that the repository has been cloned to the workstation
6. Run a simple command to test GCP authentication:
   ```bash
   gcloud config list
   ```

## 5. Compute Engine VM Testing

If you've provisioned a Compute Engine VM:

```bash
# List Compute Engine instances
gcloud compute instances list --project=cherry-ai-project

# SSH into the VM
gcloud compute ssh my-workstation --zone=us-central1-a --project=cherry-ai-project
```

Once connected to the VM:
```bash
# Verify GCP authentication
gcloud auth list
gcloud config list

# Verify repository clone
cd ~/orchestra-main
ls -la

# Verify Python environment
python3 -m venv venv
source venv/bin/activate
python -c "import google.cloud.aiplatform as aiplatform; print('Vertex AI available')"
```

## 6. Cloud Run Deployment Testing

If you've deployed to Cloud Run:

```bash
# List Cloud Run services
gcloud run services list --project=cherry-ai-project

# Get the URL of your service
gcloud run services describe orchestra-api --project=cherry-ai-project --region=us-central1 --format="value(status.url)"
```

Manual testing:
1. Open the service URL in your browser
2. Verify that the API is responding (e.g., check the `/health` endpoint)
3. Test API functionality using appropriate requests

## 7. Cloud Code Extension Testing

If you're using the Cloud Code VS Code extension:

1. Install the Cloud Code extension in VS Code
2. Configure it with your GCP credentials:
   ```bash
   gcloud auth application-default login
   ```
3. Use the Cloud Code extension to:
   - Browse GCP resources
   - Deploy a sample application to Cloud Run
   - Debug a Cloud Run service locally

## 8. Rebuild Resistance Testing

To verify that your setup is rebuild-resistant:

1. Close your Codespace
2. Rebuild the Codespace:
   - Go to GitHub repository
   - Click on "Codespaces"
   - Click on the three dots next to your Codespace
   - Select "Rebuild container"
3. After the rebuild completes, verify:
   ```bash
   # Check GCP authentication
   gcloud auth list
   
   # Verify environment variables
   echo $GOOGLE_APPLICATION_CREDENTIALS
   
   # Test a GCP command
   gcloud projects describe cherry-ai-project
   ```

The authentication should be automatically set up during the container rebuild process because:
- The service account key is stored as a Codespaces secret (`GCP_SERVICE_ACCOUNT_KEY`)
- The `onCreateCommand` in devcontainer.json copies the key to the appropriate location
- The `postCreateCommand` installs gcloud and activates the service account

## Troubleshooting

If any tests fail, check the following:

1. Verify that the `GCP_SERVICE_ACCOUNT_KEY` Codespaces secret is correctly set
2. Check the logs of the setup scripts for any errors
3. Ensure the service account has the necessary permissions
4. Verify that the required APIs are enabled
5. Check for any quota limitations in your GCP project

### Common Issues and Solutions

1. **Authentication Failure**:
   - Check that the service account key is valid and has the necessary permissions
   - Verify that the key was correctly copied to `$HOME/.gcp/service-account.json`
   - Try manually running: `gcloud auth activate-service-account --key-file=$HOME/.gcp/service-account.json`

2. **Missing gcloud Command**:
   - If gcloud is not found, check if it was installed correctly
   - Verify that it's in your PATH: `echo $PATH | grep google-cloud-sdk`
   - Try manually installing: `curl -sSL https://sdk.cloud.google.com | bash`

3. **API Not Enabled**:
   - Run `gcloud services list --enabled` to check which APIs are enabled
   - Enable missing APIs manually: `gcloud services enable API_NAME`

For specific error messages, refer to the GCP documentation or contact your GCP administrator.