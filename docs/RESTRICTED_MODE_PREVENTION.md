# Preventing VS Code Restricted Mode in GitHub Codespaces

This document explains how the AI Orchestra project prevents VS Code's restricted mode in GitHub Codespaces environments and what to do if you encounter this issue.

## Background

GitHub Codespaces may sometimes start in "restricted mode," which limits functionality and prevents certain operations due to workspace trust settings. This can interfere with development workflows and cause unexpected behavior in the AI Orchestra project.

## Implemented Solutions

The following measures have been implemented to prevent restricted mode:

### 1. Devcontainer Configuration

The `.devcontainer/devcontainer.json` file includes:

- Workspace trust settings that disable restricted mode:
  ```json
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
  ```

- Environment variables that enforce standard mode:
  ```json
  "STANDARD_MODE": "true"
  ```

### 2. Startup Scripts

- `.devcontainer/setup.sh`: Runs during container creation and includes code to:
  - Set critical environment variables
  - Make all scripts executable
  - Update VS Code settings to disable workspace trust

- `.devcontainer/verify-environment.sh`: Runs when the container starts and:
  - Verifies that standard mode is active
  - Checks that restricted mode is disabled
  - Applies fixes if needed

### 3. Manual Recovery Scripts

If you still encounter restricted mode, the following scripts can be used:

- `fix_restricted_mode.sh`: The new comprehensive fix script that addresses all potential causes of restricted mode
- `prevent_restricted_mode.sh`: The original script that disables restricted mode
- `disable_restricted_mode.sh`: A more extensive script with multiple approaches
- `exit_restricted_mode.sh`: Focuses on fixing filesystem issues and cleaning up
- `force_standard_mode.py`: A Python script that patches the core module directly

The `fix_restricted_mode.sh` script is now the recommended solution as it implements a more robust approach that addresses all potential causes of restricted mode.

## If You Encounter Restricted Mode

If your Codespace starts in restricted mode despite these preventions:

1. Run the following command in the terminal:
   ```bash
   ./fix_restricted_mode.sh
   ```

2. Verify the fix worked by running:
   ```bash
   ./verify_standard_mode.sh
   ```

3. If the issue persists, try:
   ```bash
   ./prevent_restricted_mode.sh
   ```

4. If still having issues:
   ```bash
   ./disable_restricted_mode.sh
   ```

5. As a last resort, rebuild the container:
   - Open VS Code Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
   - Type and select "Codespaces: Rebuild Container"
   - Wait for the rebuild to complete

## Long-Term Prevention

To ensure restricted mode doesn't occur in future Codespaces:

1. Always use the provided devcontainer configuration
2. Don't modify the workspace trust settings in VS Code
3. Ensure the environment variables are properly set:
   - `STANDARD_MODE=true`
   - `USE_RECOVERY_MODE=false`

## Technical Details

Restricted mode is controlled by:

1. VS Code workspace trust settings
2. Environment variables that control application behavior
3. Filesystem permissions and ownership

Our solution addresses all three aspects to ensure a consistent development experience.

## Technical Implementation Details

The comprehensive fix implemented in `fix_restricted_mode.sh` addresses the following:

1. **Environment Variables**: Sets and persists critical environment variables in multiple locations:
   - Current shell session
   - Shell configuration files (`.bashrc`, `.profile`, etc.)
   - VS Code settings
   - Docker containers via Dockerfile and docker-compose
   - CI/CD pipelines via GitHub Actions

2. **VS Code Settings**: Updates both workspace and global VS Code settings to disable workspace trust:
   - `.vscode/settings.json` for workspace settings
   - Global VS Code settings in Codespaces

3. **Filesystem Permissions**: Ensures proper permissions on scripts and creates marker files:
   - Makes all scripts executable
   - Creates `.standard_mode` marker files

4. **Startup Hooks**: Adds hooks to ensure settings are applied on each session:
   - Creates a startup script that runs on each terminal session
   - Integrates with container startup via `postCreateCommand` and `postStartCommand`

5. **Verification**: Provides a verification script to check if the fix worked:
   - Checks environment variables
   - Verifies VS Code settings
   - Validates marker files
   - Reports overall status

This multi-layered approach ensures that restricted mode is prevented across all potential entry points and scenarios.