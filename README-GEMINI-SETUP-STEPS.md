# Gemini Code Assist Enterprise Setup for GitHub Codespaces

This file provides a step-by-step guide to set up Gemini Code Assist Enterprise with Google Cloud Code in GitHub Codespaces.

## Complete Setup Process

### 1. Set Environment Variables

First, set the necessary environment variables:

```bash
# Set environment variables for your session
./set_environment_variables.sh

# Or to make them persistent
source set_environment_variables.sh --persistent
```

This script sets:
- `GCP_PROJECT_ID="cherry-ai-project"`
- `GCP_ORG_ID="873291114285"`
- `GCP_SA_JSON` with the service account credentials
- `FULL_SERVICE_ACCOUNT_JSON` for compatibility with the setup scripts

### 2. Extensions Setup

The `.devcontainer/devcontainer.json` has been updated to include the necessary extensions:

```json
"extensions": [
  "GoogleCloudTools.cloudcode",
  "GoogleCloudTools.gemini-code-assist-enterprise"
]
```

### 2. Authentication & API Enablement

Run the authentication script to set up your service account and enable required APIs:

```bash
# Authenticates with GCP and enables necessary APIs
./authenticate_with_service_account.sh
```

This script:
- Creates a service account key file at `/tmp/sa.json`
- Activates the service account with gcloud
- Enables the Cloud AI Companion API
- Sets the project to "cherry-ai-project"

### 3. Repository Connection

Connect your repository to Developer Connect and enable code customization:

```bash
# Connects repository and enables code customization
./connect_repo_and_enable_customization.sh
```

This script:
- Registers your GitHub repository with Developer Connect
- Enables code customization for the repository
- Verifies the setup with region compatibility check

### 4. Comprehensive Setup (Alternative)

Alternatively, you can use the all-in-one setup script:

```bash
# Set your service account JSON as an environment variable first
export FULL_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'

# Run the comprehensive setup script
./setup_gemini_enterprise.sh
```

### 5. Cleanup After Session

When you're done with your session, clean up credentials:

```bash
# Removes credentials securely
./cleanup_gemini_credentials.sh
```

## Using Gemini Code Assist Enterprise

1. Open any code file
2. Press `Ctrl+I` (Windows/Linux) or `Cmd+I` (Mac)
3. Use commands like:
   - `/generate Vertex AI pipeline with BigQuery input`
   - `/doc this Cloud Function with security warnings`
   - `/fix Redis connection timeout in line 42`

## Additional Documentation

For more detailed information, refer to:
- `GEMINI_CODE_ASSIST_ENTERPRISE_GUIDE.md` - Comprehensive documentation
- The individual script files contain detailed comments and instructions

## Security Note

The service account key in the authentication script is a template. Replace `[YOUR_ACTUAL_KEY]` with your actual private key if needed, but avoid committing actual credentials to your repository.
