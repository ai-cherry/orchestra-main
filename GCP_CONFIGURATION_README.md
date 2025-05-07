# GCP Configuration for AI Orchestra

This document explains how the GCP configuration is set up for the AI Orchestra project.

## Hardcoded GCP Configuration

The GCP configuration is hardcoded in the environment to ensure consistent access to the correct GCP project and account. This is implemented through several mechanisms:

1. **Environment Variables**: The following environment variables are set:
   - `CLOUDSDK_CORE_PROJECT="cherry-ai-project"`
   - `CLOUDSDK_CORE_ACCOUNT="scoobyjava@cherry-ai.me"`
   - `CLOUDSDK_CORE_REGION="us-central1"`
   - `CLOUDSDK_CORE_ZONE="us-central1-a"`

2. **Bash Configuration**: The environment variables are added to `~/.bashrc` to ensure they are set in every terminal session.

3. **Devcontainer Configuration**: The environment variables are also set in `.devcontainer/devcontainer.json` to ensure they are set when the Codespace starts.

4. **Git Configuration**: Git is configured to use gcloud credentials for authentication.

## Scripts

The following scripts are provided to manage the GCP configuration:

### `hardcode_gcp_config.sh`

This script sets up the GCP configuration by:
- Adding the environment variables to `~/.bashrc`
- Setting the environment variables for the current session
- Configuring git to use gcloud credentials

Run this script to set up the GCP configuration:

```bash
./hardcode_gcp_config.sh
```

### `check_gcloud.sh`

This script checks if gcloud is installed and configured correctly:
- If gcloud is installed, it verifies the configuration
- If gcloud is not installed, it provides instructions on how to install it
- It also sets the environment variables for the current session

Run this script to check the GCP configuration:

```bash
./check_gcloud.sh
```

### `ensure_gcp_env.sh`

This script ensures that the GCP environment variables are set correctly:
- It checks if the environment variables are set correctly
- If they are not set correctly, it sets them to the correct values
- It verifies that the environment variables are set correctly

Run this script to ensure the GCP environment variables are set correctly:

```bash
./ensure_gcp_env.sh
```

### `source_env_and_ensure_gcp.sh`

This script sources environment variables from the .env file and ensures that the GCP environment variables are set correctly:
- It checks if the .env file exists
- If it exists, it sources the environment variables from the .env file
- If it doesn't exist, it creates a new .env file with the correct environment variables
- It runs the ensure_gcp_env.sh script to ensure that the GCP environment variables are set correctly

Run this script to source environment variables from the .env file and ensure the GCP environment variables are set correctly:

```bash
./source_env_and_ensure_gcp.sh
```

### `add_to_bashrc.sh`

This script adds the source_env_and_ensure_gcp.sh script to the .bashrc file to ensure it runs automatically when a new terminal is opened:
- It checks if the script is already in .bashrc
- If it's not, it adds the script to .bashrc
- It removes any existing gcloud_config.sh call from .bashrc

Run this script to add the source_env_and_ensure_gcp.sh script to the .bashrc file:

```bash
./add_to_bashrc.sh
```

### `verify_gcp_config.sh`

This script verifies the GCP configuration and provides instructions on how to fix any issues:
- It checks if all the required scripts exist
- It checks if the scripts are executable
- It checks if the .env file exists
- It checks if the environment variables are set correctly
- It checks if source_env_and_ensure_gcp.sh is in .bashrc
- It checks if gcloud is installed and configured correctly

Run this script to verify the GCP configuration:

```bash
./verify_gcp_config.sh
```

### `test_gcp_deployment.sh`

This script tests the GCP deployment and verifies that resources have been successfully provisioned:
- It ensures GCP environment variables are set correctly
- It verifies gcloud configuration
- It tests GCP API access
- It tests Cloud Run service
- It tests Cloud Storage buckets
- It tests Firestore
- It tests Vertex AI
- It tests Secret Manager
- It tests IAM permissions

Run this script to test the GCP deployment:

```bash
./test_gcp_deployment.sh
```

### `setup_and_verify_gcp.sh`

This script runs all the configuration and verification scripts in the correct order:
1. `hardcode_gcp_config.sh`
2. `check_gcloud.sh`
3. `ensure_gcp_env.sh`
4. `source_env_and_ensure_gcp.sh`
5. `add_to_bashrc.sh`
6. `verify_gcp_config.sh`
7. `test_gcp_deployment.sh` (if gcloud is installed)

Run this script to set up and verify the GCP configuration:

```bash
./setup_and_verify_gcp.sh
```

## Automatic Setup

The GCP configuration is automatically set up when the Codespace starts through the `.devcontainer/devcontainer.json` file, which runs the `setup_and_verify_gcp.sh` script. This script runs all the configuration and verification scripts in the correct order:

1. `hardcode_gcp_config.sh`: Sets up the GCP configuration in the environment
2. `check_gcloud.sh`: Checks if gcloud is installed and configured correctly
3. `ensure_gcp_env.sh`: Ensures that the GCP environment variables are set correctly
4. `source_env_and_ensure_gcp.sh`: Sources environment variables from the .env file and ensures that the GCP environment variables are set correctly
5. `add_to_bashrc.sh`: Adds the source_env_and_ensure_gcp.sh script to the .bashrc file to ensure it runs automatically when a new terminal is opened
6. `verify_gcp_config.sh`: Verifies the GCP configuration and provides instructions on how to fix any issues
7. `test_gcp_deployment.sh`: Tests the GCP deployment (if gcloud is installed)

The `.devcontainer/devcontainer.json` file also sets the environment variables directly in the container environment:

The `.devcontainer/devcontainer.json` file also sets the environment variables directly in the container environment:

```json
"containerEnv": {
  "CLOUDSDK_CORE_PROJECT": "cherry-ai-project",
  "CLOUDSDK_CORE_ACCOUNT": "scoobyjava@cherry-ai.me",
  "CLOUDSDK_CORE_REGION": "us-central1",
  "CLOUDSDK_CORE_ZONE": "us-central1-a"
}
```

This ensures that the GCP configuration is set correctly even if the scripts fail to run.

## Manual Setup

If you need to set up the GCP configuration manually, you can either:

### Option 1: Run the all-in-one script

Run the `setup_and_verify_gcp.sh` script to set up and verify the GCP configuration:

```bash
./setup_and_verify_gcp.sh
```

This script will run all the configuration and verification scripts in the correct order.

### Option 2: Run the scripts individually

If you prefer to run the scripts individually, follow these steps:

1. Run the `hardcode_gcp_config.sh` script:
   ```bash
   ./hardcode_gcp_config.sh
   ```

2. Run the `check_gcloud.sh` script to verify the configuration:
   ```bash
   ./check_gcloud.sh
   ```

3. If gcloud is not installed, follow the instructions provided by the `check_gcloud.sh` script to install it.

4. Run the `verify_gcp_config.sh` script to verify the configuration and fix any issues:
   ```bash
   ./verify_gcp_config.sh
   ```

## Troubleshooting

If you encounter issues with the GCP configuration, try the following:

1. Run the `verify_gcp_config.sh` script to verify the configuration and fix any issues:
   ```bash
   ./verify_gcp_config.sh
   ```

2. Run the `check_gcloud.sh` script to verify the configuration:
   ```bash
   ./check_gcloud.sh
   ```

3. If the environment variables are not set correctly, run the `hardcode_gcp_config.sh` script:
   ```bash
   ./hardcode_gcp_config.sh
   ```

4. If gcloud is not installed, follow the instructions provided by the `check_gcloud.sh` script to install it.

## Deployment Verification

After setting up the GCP configuration, you should verify that the GCP resources have been successfully provisioned, configured, and tested in a production environment. See [GCP_DEPLOYMENT_VERIFICATION.md](GCP_DEPLOYMENT_VERIFICATION.md) for detailed instructions on how to verify the deployment.

The `test_gcp_deployment.sh` script automates the verification process:

```bash
./test_gcp_deployment.sh
```

4. If you still encounter issues, try setting the environment variables manually:
   ```bash
   export CLOUDSDK_CORE_PROJECT="cherry-ai-project"
   export CLOUDSDK_CORE_ACCOUNT="scoobyjava@cherry-ai.me"
   export CLOUDSDK_CORE_REGION="us-central1"
   export CLOUDSDK_CORE_ZONE="us-central1-a"
   ```

5. If you need to use a specific project or account for a single command, use the `--project` and `--account` flags:
   ```bash
   gcloud compute instances list --project cherry-ai-project --account scoobyjava@cherry-ai.me