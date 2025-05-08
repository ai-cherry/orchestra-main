#!/bin/bash
# terraform-wrapper.sh - Wrapper for Terraform to ensure environment is properly configured

# Source the centralized environment configuration
source ~/setup-env.sh

# Validate required environment variables
if [[ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
  echo "ERROR: GOOGLE_APPLICATION_CREDENTIALS not set"
  exit 1
fi

if [[ -z "$CLOUDSDK_CORE_PROJECT" ]]; then
  echo "ERROR: CLOUDSDK_CORE_PROJECT not set"
  exit 1
fi

# Print Terraform environment information
echo "Running Terraform with AI Orchestra environment configuration"
echo "Project: $CLOUDSDK_CORE_PROJECT"
echo "Region: $CLOUDSDK_CORE_REGION"
echo "Credentials: $GOOGLE_APPLICATION_CREDENTIALS"
echo "---------------------------------------------------"

# Execute Terraform with all arguments passed to this script
terraform "$@"
exit_code=$?

# Handle errors
if [[ $exit_code -ne 0 ]]; then
  echo "Terraform command failed with exit code $exit_code"
fi

exit $exit_code