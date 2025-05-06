#!/bin/bash

# Set the credentials path
export GOOGLE_APPLICATION_CREDENTIALS="./gsa-key.json"

# Initialize Terraform with the GCS backend
terraform init -reconfigure

echo "Terraform has been initialized with GCS backend."
echo "State will be stored in bucket: cherry-ai-project-tfstate"
echo "Using prefix: orchestra/env/dev"
