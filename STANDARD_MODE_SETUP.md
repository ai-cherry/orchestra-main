# Standard Mode Configuration Guide

## Enhanced Setup Process

This repository now includes an enhanced setup process that automatically configures standard mode and GCP authentication when a Codespace is created or rebuilt. The improvements include:

1. **Robust Error Handling**:

   - Retry mechanisms for GCP authentication and file operations
   - Detailed logging to help diagnose issues

2. **Idempotent Operations**:

   - All configuration changes check for existing settings first
   - Prevents duplicate entries in configuration files

3. **Recovery Container Detection**:

   - Automatically detects if running in a recovery container
   - Implements appropriate fixes for this scenario

4. **Automated Setup**:
   - The `.devcontainer/setup_and_verify.sh` script handles all setup operations
   - Integrated into `devcontainer.json` via the `postCreateCommand`

## What Has Been Done

This repository has been configured to force standard mode operation and disable VS Code's restricted mode, which should resolve GCP authentication and workspace trust issues. The following actions have been completed:

1. **Environment Variables Set**:

   - `VSCODE_DISABLE_WORKSPACE_TRUST=true`
   - `STANDARD_MODE=true`
   - `DISABLE_WORKSPACE_TRUST=true`
   - `USE_RECOVERY_MODE=false`

2. **VS Code Settings Updated**:

   - `.vscode/settings.json` modified to disable workspace trust
   - `.devcontainer/devcontainer.json` updated with workspace trust settings

3. **CLI Command File Created**:

   - `.vscode/disable_trust.js` for further customization if needed

4. **GCP Authentication Fixed**:
   - Service account key file created
   - Authentication set up with the correct service account
   - Project set to cherry-ai-project
   - `GOOGLE_APPLICATION_CREDENTIALS` properly configured

## Recovery Container Issue

The creation log indicates this Codespace was created using a recovery container because the original container configuration failed to build. This was due to an error with the GCP feature installation:

```
ERR: Feature 'ghcr.io/googlecloudplatform/devcontainers-features/gcloud:latest' could not be processed.
```

Despite this, we've successfully configured GCP authentication and ensured that standard mode is enforced.

## Verification Scripts

Three scripts are now available to help maintain and verify your environment:

1. **.devcontainer/setup_and_verify.sh**:

   - Comprehensive setup script that runs automatically on container creation
   - Handles GCP authentication with retries and error handling
   - Configures VS Code settings and environment variables
   - Logs all operations to `/workspaces/orchestra-main/codespace_setup.log`

1. **verify_standard_mode.sh**:

   - Checks environment variables
   - Verifies VS Code settings
   - Ensures workspace trust is disabled

1. **enhanced_verify_gcp_setup.sh**:
   - Verifies GCP authentication
   - Checks service account key file
   - Tests GCP connectivity
   - Provides fix suggestions if issues are found

## For Future Sessions

To ensure standard mode is maintained:

### On Container Rebuild

The enhanced setup script will run automatically when the container is rebuilt, ensuring your environment is properly configured.

### Manual Verification

1. Run these scripts at the start of each session:

   ```bash
   ./verify_standard_mode.sh
   ./enhanced_verify_gcp_setup.sh
   ```

2. If restricted mode returns, execute:

   ```bash
   ./enforce_standard_mode.sh
   ./disable_restricted_mode.sh
   source ~/.bashrc
   ```

3. For persistent issues, you may need to rebuild the Codespace with:
   ```bash
   # From VS Code Command Palette
   # Codespaces: Rebuild Container
   ```

## Manual GCP Setup (If Needed)

If GCP integration issues persist, run these commands:

```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
mkdir -p $HOME/.gcp
echo $GCP_MASTER_SERVICE_JSON > $HOME/.gcp/service-account.json
gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=$HOME/.gcp/service-account.json
gcloud config set project cherry-ai-project
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
```

## Reporting Issues

If problems persist after these steps, consider:

1. Checking the VS Code Developer Console for errors
2. Examining the Codespace creation log for clues
3. Contacting GitHub support with details about the restricted mode and recovery container issues
