# Preventing Restricted Mode Rebuilds

This document explains why Orchestra might be rebuilding in restricted mode and the solutions implemented to prevent this.

## Root Causes Identified

After examining the codebase, several potential issues were identified that could cause Orchestra to rebuild in restricted mode:

1. **Environment Variable Inconsistency**: The `USE_RECOVERY_MODE` and `STANDARD_MODE` environment variables were not consistently set across all components.

2. **Docker Configuration Issues**:

   - The Dockerfile was removing Agno dependencies but docker-compose.yml still referenced them
   - Inconsistent virtual environment handling between development and Docker environments

3. **VSCode Restricted Mode Interaction**: VS Code's restricted mode might be interacting with the application's mode settings.

4. **Startup Script Limitations**: The existing mode toggling scripts might not be persisting properly across rebuilds.

## Solutions Implemented

The following solutions have been implemented to ensure Orchestra consistently runs in standard mode:

### 1. Docker Environment Updates

- **Dockerfile**: Modified to ensure standard mode is enforced:

  - Added explicit environment variables: `USE_RECOVERY_MODE=false` and `STANDARD_MODE=true`
  - Created a startup script to enforce mode settings at runtime
  - Configured Poetry to use in-project virtualenvs, consistent with development environment
  - Added error handling for dependency installation

- **docker-compose.yml**: Updated to enforce standard mode:
  - Added mode enforcement environment variables to all services
  - Made Agno dependency optional with fallback values
  - Updated service names for clarity

### 2. New Standard Mode Enforcement Tools

- **ensure_standard_mode.sh**: Created comprehensive script that:

  - Sets environment variables in `.bashrc`
  - Updates `.env` file with proper mode settings
  - Verifies Docker configuration
  - Creates/updates `force_standard_mode.py`
  - Creates a startup hook script for Docker containers
  - Makes all scripts executable

- **startup_hook.sh**: New entry point wrapper that enforces standard mode at container startup

- **force_standard_mode.py**: Updated to include better error handling and debugging

### 3. Poetry Configuration Fix

- Fixed inconsistency where development environment used in-project virtualenvs but Docker did not
- Added better error handling for Poetry operations

## How to Enforce Standard Mode

To ensure Orchestra always runs in standard mode:

1. **For Local Development**:

   ```bash
   # Run the enforcement script
   ./ensure_standard_mode.sh

   # Apply environment variables to current session
   source ~/.bashrc

   # Verify mode settings
   python force_standard_mode.py
   ```

2. **For Docker Environments**:

   ```bash
   # Rebuild and restart containers with updated settings
   docker-compose down
   docker-compose up --build -d
   ```

3. **On CI/CD and Production Deployments**:
   - Ensure your deployment process sets the environment variables properly
   - Consider adding `force_standard_mode.py` to your startup process
   - Use the startup hook script as your container entrypoint

## Verifying Standard Mode

You can verify the system is running in standard mode by:

1. Checking log output for: `Starting with RECOVERY_MODE=False, STANDARD_MODE=True`
2. Examining environment variables: `echo $STANDARD_MODE $USE_RECOVERY_MODE`
3. Looking for the "FORCE STANDARD MODE ACTIVE" message in logs

## Long-term Recommendations

To prevent future issues with restricted mode:

1. **Standardize Mode Handling**: Consider refactoring mode handling to use a single configuration source
2. **Remove Agno Dependency**: Fully remove Agno dependencies or properly handle their absence
3. **Consistent Docker Configuration**: Ensure Docker and local development environments use consistent configurations
4. **VS Code Settings**: Maintain the VS Code workspace trust settings in source control
5. **Pre-commit Hook**: Add a pre-commit hook to ensure mode settings aren't accidentally changed

By implementing these changes, Orchestra should now consistently run in standard mode across all environments and rebuilds.
