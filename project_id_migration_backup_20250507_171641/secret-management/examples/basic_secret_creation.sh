#!/bin/bash
# basic_secret_creation.sh
# This example demonstrates the original simple secret creation approach
# as well as how to use our enhanced script for the same purpose

# 1. Original approach (simple but limited)
echo "Method 1: Using direct gcloud command (original approach)"
echo -n "my_secret_value" | gcloud secrets create MY_SECRET \
  --data-file=- \
  --replication-policy=automatic

echo ""
echo "Method 2: Using our enhanced create_secret.sh script"
# Assuming we're in the examples directory, we need to reference the script in ../scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../scripts"

# Create the same secret but with our enhanced script (with more options and error handling)
"$SCRIPT_DIR/create_secret.sh" "MY_SECRET" "my_secret_value" "agi-baby-cherry" "automatic" "production"

echo ""
echo "Both methods achieve the same result, but the enhanced script provides:"
echo "- Proper error handling"
echo "- Authentication verification"
echo "- Secret Manager API enablement checking"
echo "- Environment-based naming"
echo "- Support for both automatic and user-managed replication"
echo "- Versioning for existing secrets"
