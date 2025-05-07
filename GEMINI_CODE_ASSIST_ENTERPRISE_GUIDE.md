# Gemini Code Assist Enterprise with GitHub Codespaces

This guide provides comprehensive instructions for setting up and using Gemini Code Assist Enterprise within GitHub Codespaces, with specific guidance for effective development workflows.

## Setup Process

The integration is handled through three key components:

1. VS Code Extensions configuration in `.devcontainer/devcontainer.json`
2. Authentication configuration with service account credentials
3. Repository registration with Developer Connect

### Quick Start

To set up Gemini Code Assist Enterprise in your Codespace:

1. Ensure you have the necessary service account credentials stored in a secure environment variable:
   ```bash
   export FULL_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'
   ```

2. Run the setup script:
   ```bash
   ./setup_gemini_enterprise.sh
   ```

3. When finished with your session, clean up credentials:
   ```bash
   ./cleanup_gemini_credentials.sh
   ```

## Key Components

### 1. VS Code Extensions

The `.devcontainer/devcontainer.json` file configures the necessary extensions:

```json
"extensions": [
  "GoogleCloudTools.cloudcode",
  "GoogleCloudTools.gemini-code-assist-enterprise"
]
```

These extensions provide the integration between VS Code and Gemini Code Assist Enterprise.

### 2. Authentication Configuration

Authentication is handled through GCP service account credentials and properly configured environment variables:

```bash
echo 'GOOGLE_APPLICATION_CREDENTIALS="service-account.json"' >> .env
echo "$FULL_SERVICE_ACCOUNT_JSON" > service-account.json
gcloud auth activate-service-account --key-file=service-account.json
```

### 3. Developer Connect Integration

The setup connects your GitHub repository to Google Cloud via Developer Connect:

```bash
gcloud alpha developer-connect repos register github_cherry-ai-project \
  --gitlab-host-uri="https://github.com" \
  --project=cherry-ai-project \
  --region=us-west4

gcloud alpha genai code customize enable \
  --project=cherry-ai-project \
  --repos=github_cherry-ai-project
```

## Usage Guide

### Shortcut-Driven Development

Gemini Code Assist Enterprise provides powerful code generation capabilities through keyboard shortcuts:

1. Open any code file
2. Press `Ctrl+I` (Windows/Linux) or `Cmd+I` (Mac)
3. Enter prompts using these special commands:

| Command | Description | Example |
|---------|-------------|---------|
| `/generate` | Generate new code | `/generate Vertex AI pipeline with BigQuery input` |
| `/doc` | Add or improve documentation | `/doc this Cloud Function with security warnings` |
| `/fix` | Fix issues in code | `/fix Redis connection timeout in line 42` |
| `/refactor` | Refactor code | `/refactor this function to use async/await` |
| `/test` | Generate tests | `/test create unit tests for this class` |

### Customized Code Generation

Gemini Code Assist Enterprise has access to your repository's code through Developer Connect, enabling it to:

1. Understand your codebase and coding patterns
2. Generate code that matches your project's style and conventions
3. Reference existing implementations when creating new code
4. Suggest improvements based on your project's architecture

### Region Compatibility

Verify that your repositories are properly connected and in a supported region:

```bash
gcloud alpha genai code customize list --project=cherry-ai-project
```

Supported regions include:
- us-west4
- europe-west1
- asia-southeast1

### Security Best Practices

1. Store service account credentials securely:
   - Use GitHub Codespaces secrets for the `FULL_SERVICE_ACCOUNT_JSON` variable
   - Never commit credentials to your repository

2. Clean up after each session:
   ```bash
   ./cleanup_gemini_credentials.sh
   ```

3. Use a service account with minimal required permissions:
   - Developer Connect Repository Admin
   - Vertex AI User

## Troubleshooting

### Common Issues

1. **Extension not working**: Ensure both extensions are properly installed and that VS Code has reloaded.

2. **Authentication failures**: Verify your service account has the necessary permissions and that `GOOGLE_APPLICATION_CREDENTIALS` points to a valid file.

3. **Repository not found**: Check that Developer Connect registration completed successfully with correct repository details.

4. **Region issues**: Ensure your project and repository are registered in a supported region.

### Logs and Diagnostics

Access VS Code logs for extension troubleshooting:
1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type and select "Developer: Open Extension Logs"
3. Filter for "cloudcode" or "gemini-code-assist"

## Why This Works in Codespaces

This configuration is particularly effective in GitHub Codespaces due to:

1. **Full IDE Integration** - Cloud Code and Gemini extensions inherit complete VS Code capabilities
2. **Ephemeral Security** - Credentials exist only during active session
3. **Customization Sync** - Developer Connect maintains repository links across sessions
4. **GCP Native Tooling** - Direct access to your project's services and APIs

## Migration Automation Prompts

Below are specific prompts you can use with Gemini Code Assist Enterprise to automate common GCP migration tasks:

### For Terraform Configuration

```
/generate Terraform module for GCP Cloud Workstations with:
- Project: cherry-ai-project
- Machine: n2d-standard-32
- 2x NVIDIA T4 GPUs
- 1TB SSD
- Preinstalled JupyterLab
- IAM for vertex-agent@
```

### For Migration Scripts

```
/create Python script to:
1. Move project to org 873291114285
2. Auto-retry on IAM propagation errors
3. Validate with gcloud projects describe
4. Cleanup temp credentials
Use existing service account key from env
```

### For Error Handling

```
/fix [PASTE ERROR MESSAGE HERE] 
Provide solution with gcloud commands
```

## Additional Resources

- [Gemini Code Assist Enterprise Documentation](https://cloud.google.com/code/docs/gemini-code-assist-enterprise)
- [Cloud Code for VS Code](https://cloud.google.com/code/docs/vscode)
- [Developer Connect Documentation](https://cloud.google.com/developer-connect/docs)
