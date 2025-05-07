# Codespace Environment Fix Guide

This guide provides a comprehensive solution for fixing issues with GitHub Codespaces environments, particularly related to gcloud crashes, restricted mode issues, and GitHub Copilot delays. The tools and scripts in this guide address these problems systemically to ensure a stable and functional development environment.

## Overview of Issues & Solutions

### 1. gcloud Crash
- **Issue**: gcloud crashing during updates, with errors related to clearing staging directories (shutil.rmtree)
- **Solution**: Complete reinstallation of gcloud SDK with proper configuration

### 2. Restricted Mode in GitHub Codespaces
- **Issue**: Restricted mode blocking file writes and environment variable persistence
- **Solution**: Enforced standard mode through VS Code settings and environment variables

### 3. GCP Authentication Issues
- **Issue**: Authentication failures and configuration not persisting across sessions
- **Solution**: Robust service account authentication with proper environment variable setup

### 4. GitHub Copilot Delays
- **Issue**: "Copilot took too long to get ready" errors due to resource constraints
- **Solution**: Optimized Git performance and reduced system load

## Fix Scripts

### 1. `fix-gcloud.sh`
Reinstalls gcloud SDK completely:
```bash
chmod +x fix-gcloud.sh
./fix-gcloud.sh
```

### 2. `fix_codespace_environment.sh`
Comprehensive fix that addresses all issues:
```bash
chmod +x fix_codespace_environment.sh
./fix_codespace_environment.sh
```

This script:
- Reinstalls gcloud SDK
- Enforces standard mode in VS Code
- Configures GCP authentication
- Optimizes Git performance
- Verifies all settings

## Testing Scripts

### 1. `test_gcp_integration.sh`
Validates GCP integration is working correctly:
```bash
chmod +x test_gcp_integration.sh
./test_gcp_integration.sh
```

### 2. `test_cloud_run_deployment.sh`
Tests a complete GCP deployment to Cloud Run:
```bash
chmod +x test_cloud_run_deployment.sh
./test_cloud_run_deployment.sh
```

## Configuration Files

### 1. VS Code Settings
`.vscode/settings.json` disables workspace trust to prevent restricted mode:
```json
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
```

### 2. DevContainer Configuration
`.devcontainer/devcontainer.json` includes updated configuration to enforce standard mode and properly set up the GCP environment.

## Usage Instructions

### Full Recovery Process

To perform a complete recovery of your Codespace environment:

1. Run the comprehensive fix script:
   ```bash
   chmod +x fix_codespace_environment.sh
   ./fix_codespace_environment.sh
   ```

2. Source your bashrc to apply environment variables:
   ```bash
   source ~/.bashrc
   ```

3. Reload your VS Code window:
   - Press F1 and select 'Developer: Reload Window'

4. Verify the fix worked:
   ```bash
   ./test_gcp_integration.sh
   ```

5. If needed, test a full deployment:
   ```bash
   ./test_cloud_run_deployment.sh
   ```

### If Issues Persist

If problems remain after running the fix scripts:

1. Check the log file: `/workspaces/orchestra-main/codespace_fix.log`
2. Verify standard mode is enabled:
   ```bash
   ./verify_standard_mode.sh
   ```
3. Verify GCP setup:
   ```bash
   ./enhanced_verify_gcp_setup.sh
   ```
4. Try rebuilding the Codespace as a last resort

## Preventing Future Issues

To maintain a stable environment:

1. Regularly update gcloud components:
   ```bash
   gcloud components update --quiet
   ```

2. Monitor for signs of restricted mode activation:
   - File permission errors
   - Environment variables not persisting
   - 'Restricted Mode' indicator in VS Code status bar

3. Run the verification scripts after rebuilds:
   ```bash
   ./verify_standard_mode.sh
   ./enhanced_verify_gcp_setup.sh
   ```

4. Keep Git repositories clean to improve Copilot performance:
   ```bash
   git add .
   git commit -m "Maintain clean working tree"
   git gc
   ```

## Files Created/Modified

- `fix-gcloud.sh`: Reinstalls gcloud SDK
- `fix_codespace_environment.sh`: Comprehensive environment fix
- `test_gcp_integration.sh`: Tests GCP integration
- `test_cloud_run_deployment.sh`: Tests Cloud Run deployment
- `.vscode/settings.json`: Enforces standard mode
- `.devcontainer/devcontainer.json`: Updated with better environment variables
