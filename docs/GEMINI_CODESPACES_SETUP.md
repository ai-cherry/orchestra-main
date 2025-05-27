# Gemini Code Assist & Cloud Code Setup for Codespaces

This document explains how Cloud Code and Gemini Code Assist extensions are configured in your GitHub Codespaces environment.

## Automatic Setup

The `.devcontainer/devcontainer.json` file has been configured to automatically:

1. Install required VS Code extensions:

   - Cloud Code (`GoogleCloudTools.cloudcode`)
   - Gemini Code Assist (`GoogleCloudTools.cloudcode-gemini`)

2. Configure Gemini Code Assist:

   - Set project ID to `cherry-ai-project`
   - Enable context-aware code completion
   - Enable Gemini-powered code review

3. Set up    - Authenticate using the service account key
   - Set the active project to `cherry-ai-project`

When you open the project in Codespaces, these configurations are automatically applied.

## Manual Setup

If you need to manually set up or refresh the configuration, you can run the provided backup script:

```bash
./scripts/setup_codespaces_gemini.sh
```

This script will:

- Install the required VS Code extensions
- Check for - Set the active project to `cherry-ai-project`
- Configure VS Code settings for Gemini Code Assist
- Enable required
## Using Gemini Code Assist

Once configured, you can use Gemini Code Assist in your development workflow:

1. **Context-Aware Code Completion**:

   - As you type, you'll see AI-powered code suggestions that understand your codebase context
   - Accept suggestions by pressing Tab or Enter

2. **Gemini-Powered Code Review**:

   - Right-click on code and select "Review with Gemini"
   - Get AI-powered code reviews with suggestions and improvements

3. **Generate Code**:
   - Place your cursor where you want code to be generated
   - Press Ctrl+I (or Cmd+I on Mac) to trigger Gemini
   - Type a prompt describing what you want to generate

## Troubleshooting

If you encounter issues with the extensions:

1. **Authentication Problems**:

   - Verify authentication with: `gcloud auth list`
   - Check the project is set correctly: `gcloud config get-value project`

2. **Extension Not Working**:

   - Check if extensions are installed in VS Code Extensions panel
   - Reload VS Code window with Ctrl+Shift+P, then "Developer: Reload Window"

3. **API Access Issues**:
   - Ensure APIs are enabled: `gcloud services list --enabled --filter=aiplatform`
   - Enable if needed: `gcloud services enable aiplatform.googleapis.com --project=cherry-ai-project`
