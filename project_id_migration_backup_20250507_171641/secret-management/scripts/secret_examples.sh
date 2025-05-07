#!/bin/bash
# secret_examples.sh
# Examples demonstrating how to use create_secret.sh for common secret management tasks

# Make sure create_secret.sh is executable
if [ ! -x ./create_secret.sh ]; then
    chmod +x ./create_secret.sh
fi

# Example 1: Create a basic API key secret with automatic replication
echo "Example 1: Creating a basic API key secret"
./create_secret.sh API_KEY "my-sample-api-key-12345"

# Example 2: Create a secret with user-managed replication in multiple regions
echo -e "\nExample 2: Creating a secret with user-managed replication"
./create_secret.sh DATABASE_PASSWORD "secure-db-password-789" "agi-baby-cherry" "user-managed" "production" "us-central1,us-west1"

# Example 3: Create a secret for a development environment
echo -e "\nExample 3: Creating a secret for development environment"
./create_secret.sh TEST_SECRET "test-value-for-development" "agi-baby-cherry" "automatic" "dev"

# Example 4: Create a JSON-structured secret
echo -e "\nExample 4: Creating a JSON-structured secret"
JSON_CONFIG='{
  "user": "service-account",
  "key": "abc123xyz",
  "scopes": [
    "read",
    "write"
  ],
  "expiry": "2025-12-31"
}'
./create_secret.sh SERVICE_CONFIG "$JSON_CONFIG"

# Example 5: Create a secret with a value from a file
echo -e "\nExample 5: Creating a secret from a file"
echo "This is a secret read from a file" > temp_secret_file.txt
SECRET_FROM_FILE=$(cat temp_secret_file.txt)
./create_secret.sh FILE_SECRET "$SECRET_FROM_FILE"
rm temp_secret_file.txt

echo -e "\nAll examples completed!"
