#!/bin/bash
# load_env.sh - Simplified utility script to load environment variables from .env file
# This script is sourced by other scripts to ensure consistent configuration

# Function to load environment variables from .env file
load_env() {
  local env_file="${1:-.env}"
  
  # Check if .env file exists
  if [ ! -f "$env_file" ]; then
    echo "Info: $env_file not found. Using default values."
    
    # If .env.template exists, suggest copying it
    if [ -f ".env.template" ]; then
      echo "Tip: You can create $env_file by copying .env.template:"
      echo "cp .env.template $env_file"
    fi
    
    return 0  # Continue anyway
  fi
  
  echo "Loading environment variables from $env_file"
  
  # Load variables from .env file - simplified approach
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    
    # Extract variable name and value
    if [[ "$line" =~ ^([A-Za-z0-9_]+)=(.*)$ ]]; then
      name="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      
      # Remove quotes if present
      value="${value%\"}"
      value="${value#\"}"
      value="${value%\'}"
      value="${value#\'}"
      
      # Export the variable
      export "$name"="$value"
    fi
  done < "$env_file"
  
  return 0
}

# Function to get a configuration value with fallback
get_config() {
  local name="$1"
  local default="$2"
  
  # Use the environment variable if set, otherwise use the default
  echo "${!name:-$default}"
}

# Simplified function to print current configuration
print_config() {
  echo "Current Configuration:"
  echo "======================"
  echo "GCP_PROJECT_ID: $(get_config GCP_PROJECT_ID 'cherry-ai-project')"
  echo "GCP_REGION: $(get_config GCP_REGION 'us-central1')"
  echo "GCP_SERVICE_ACCOUNT: $(get_config GCP_SERVICE_ACCOUNT 'default')"
  echo "CLOUD_RUN_SERVICE_NAME: $(get_config CLOUD_RUN_SERVICE_NAME 'orchestra-api')"
  echo "CLOUD_RUN_ALLOW_UNAUTHENTICATED: $(get_config CLOUD_RUN_ALLOW_UNAUTHENTICATED 'true')"
  echo "DEPLOYMENT_ENVIRONMENT: $(get_config DEPLOYMENT_ENVIRONMENT 'development')"
  echo "======================"
}

# If this script is executed directly, load the environment and print configuration
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  # Default to .env, but allow specifying a different file
  env_file="${1:-.env}"
  
  load_env "$env_file"
  print_config
fi