#!/bin/bash

# Script to guide the user through the process of creating "badass" Vertex service keys and updating GitHub organization secrets

set -e

# Prompt the user to retrieve the GCP_PROJECT_ADMIN_KEY secret from the GitHub organization
echo "Please retrieve the GCP_PROJECT_ADMIN_KEY secret from the GitHub organization (https://github.com/ai-cherry)."
read -p "Enter the value of GCP_PROJECT_ADMIN_KEY: " gcp_project_admin_key

# Prompt the user to retrieve the GCP_SECRET_MANAGEMENT_KEY secret from the GitHub organization
echo "Please retrieve the GCP_SECRET_MANAGEMENT_KEY secret from the GitHub organization (https://github.com/ai-cherry)."
read -p "Enter the value of GCP_SECRET_MANAGEMENT_KEY: " gcp_secret_management_key

# Create the "badass" Vertex service keys using the create_badass_service_keys.sh script
echo "Creating the badass Vertex service keys..."
./create_badass_service_keys.sh "$gcp_project_admin_key" "$gcp_secret_management_key"

# Guide the user through the process of updating the GitHub organization secrets with the updated names and keys
echo "Please update the GitHub organization secrets with the updated names and keys."
echo "Refer to the documentation for instructions on how to update the secrets."

echo "Key creation and GitHub secret update process completed."