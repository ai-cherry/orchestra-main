# GCP Authentication and Configuration for AI Orchestra

This document outlines the GCP authentication and configuration setup for the AI Orchestra project.

## Overview

The AI Orchestra project uses Google Cloud Platform (GCP) for various services including Cloud Run, Firestore, and Vertex AI. This setup ensures:

1. **Persistent GCP Authentication**: Service account credentials survive Codespace rebuilds
2. **Standard Mode Enforcement**: Workspace trust is disabled for security
3. **Centralized Environment Configuration**: All environment variables in one place
4. **Tool-Specific Integrations**: Docker, Terraform, and Poetry configured with GCP credentials

## Setup Components

### 1. Centralized Environment Configuration

The `setup-env.sh` script centralizes all environment variables for the project:

```bash
source ~/setup-env.sh
```

This script sets:

- GCP credentials and project configuration
- Standard mode environment variables
- AI Orchestra specific configuration

### 2. GCP Authentication

Authentication is handled through:

- Service account key stored at `$HOME/.gcp/service-account.json`
- Environment variable `GOOGLE_APPLICATION_CREDENTIALS` pointing to this file
- Automatic authentication during Codespace creation via `postCreateCommand`

### 3. Tool-Specific Configurations

#### Docker

The Dockerfile includes GCP credentials configuration:

```dockerfile
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/.gcp/service-account.json
COPY .gcp/service-account.json /app/.gcp/service-account.json
```

#### Terraform

Use the `terraform-wrapper.sh` script to run Terraform commands with the proper environment:

```bash
./terraform-wrapper.sh apply
```

#### Poetry

Poetry inherits environment variables from the shell. Ensure you've sourced the environment:

```bash
source ~/setup-env.sh
poetry shell
```

### 4. Verification

Run the verification script to validate your setup:

```bash
./verify-setup.sh
```

This checks:

- GCP authentication status
- Environment variables
- Tool availability and configuration
- GCP API access

## Codespace Rebuild Process

The setup includes automatic handling of Codespace rebuilds:

1. **Initial Creation**: When a Codespace is first created, the `postCreateCommand` in `.devcontainer/devcontainer.json` runs to set up GCP authentication.

2. **Rebuilds**: When a Codespace is rebuilt, the `postStartCommand` runs the setup script with the `--rebuild` flag to verify and restore authentication.

3. **Logs**: Separate logs are maintained for initial setup (`codespace_setup.log`) and rebuilds (`codespace_rebuild.log`).

This ensures that GCP authentication persists across rebuilds without manual intervention.

### Testing Rebuilds

To test the rebuild process without actually rebuilding the Codespace, use the `test-rebuild.sh` script:

```bash
./test-rebuild.sh
```

This script:

- Simulates a Codespace rebuild by running the setup script with the `--rebuild` flag
- Verifies that GCP authentication is maintained
- Tests API access after the simulated rebuild
- Logs all actions to `$HOME/rebuild-test.log`

This is useful for testing changes to the rebuild process or troubleshooting authentication issues.

## Quick Authentication

For quick re-authentication without rebuilding the Codespace, use the `quick-auth.sh` script:

```bash
./quick-auth.sh
```

This script:

- Checks for the service account key file and attempts to recover if missing
- Authenticates with GCP using the service account
- Sets the project, region, and zone
- Sets required environment variables
- Tests GCP connectivity
- Logs all actions to `$HOME/quick-auth.log` for troubleshooting

### Troubleshooting with Logs

If you encounter issues with GCP authentication, check the appropriate log file:

```bash
# For quick authentication issues
cat ~/quick-auth.log

# For initial setup issues
cat /workspaces/orchestra-main/codespace_setup.log

# For rebuild issues
cat /workspaces/orchestra-main/codespace_rebuild.log
```

The log files contain detailed information about each step of the authentication process, including:

- Command outputs that aren't shown in the terminal
- Error messages from GCP commands
- Environment variable settings
- Timestamps for each action

## Rebuilding and Testing

After a Codespace rebuild:

1. Source the environment:

   ```bash
   source ~/.bashrc
   ```

2. Verify the setup:

   ```bash
   ./verify-setup.sh
   ```

3. Test GCP connectivity:
   ```bash
   gcloud projects list
   ```

## IDE Integration

The setup includes specific configurations for better IDE integration with GCP:

1. **VSCode Extensions**: The verification script checks for recommended GCP-related extensions:

   - Cloud Code: For GCP resource management and deployment
   - Google Cloud Spanner: For database operations

2. **Environment Variables**: The setup sets environment variables for IDE integration:

   ```bash
   export CLOUDCODE_ENABLE=true
   export CLOUDCODE_PROJECT="cherry-ai-project"
   export CLOUDCODE_REGION="us-central1"
   ```

3. **VSCode-GCP Sync**: Use the `sync-vscode-gcp.sh` script to sync VSCode with GCP:

   ```bash
   ./sync-vscode-gcp.sh
   ```

   This script:

   - Creates or updates VSCode settings for GCP integration
   - Configures Cloud Code settings for the project
   - Checks for recommended extensions
   - Sets up workspace trust settings
   - Creates project-specific settings in the `.vscode` directory

   ```

   ```

## Troubleshooting

### Common Issues

1. **Missing GCP credentials**:

   - Check if `$HOME/.gcp/service-account.json` exists
   - Ensure the `GCP_MASTER_SERVICE_JSON` secret is set in GitHub

2. **Authentication failures**:

   - Run `gcloud auth list` to check active accounts
   - Try `gcloud auth activate-service-account --key-file=$HOME/.gcp/service-account.json`

3. **Environment variables not set**:
   - Ensure `source ~/setup-env.sh` is in your `.bashrc`
   - Run `source ~/.bashrc` to reload

## Credential Maintenance

To update the service account credentials:

1. Generate a new service account key in GCP Console
2. Update the `GCP_MASTER_SERVICE_JSON` secret in GitHub
3. Rebuild the Codespace or manually update the file:
   ```bash
   echo "$GCP_MASTER_SERVICE_JSON" > $HOME/.gcp/service-account.json
   gcloud auth activate-service-account --key-file=$HOME/.gcp/service-account.json
   ```

## Security Considerations

- The service account key is stored securely in `$HOME/.gcp`
- The Docker configuration copies the key into the container
- Standard mode is enforced to prevent workspace trust issues

## References

- [GCP Service Accounts Documentation](https://cloud.google.com/iam/docs/service-accounts)
- [GitHub Codespaces Secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-encrypted-secrets-for-your-codespaces)
- [Docker Environment Variables](https://docs.docker.com/engine/reference/commandline/run/#env)
