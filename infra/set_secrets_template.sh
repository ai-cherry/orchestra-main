#!/bin/bash
# Template for setting MongoDB and Weaviate secrets in Pulumi config
# Copy this to set_secrets.sh and fill in your actual values
# Usage: ./set_secrets.sh [stack-name]

STACK_ARG=""
if [ -n "$1" ]; then
  STACK_ARG="--stack $1"
fi

# MongoDB Atlas connection string
pulumi config set --secret mongodb_connection_string "mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority&appName=YOUR_APP" $STACK_ARG

# MongoDB service account credentials
pulumi config set --secret mongodb_service_client_id "YOUR_SERVICE_CLIENT_ID" $STACK_ARG
pulumi config set --secret mongodb_service_client_secret "YOUR_SERVICE_CLIENT_SECRET" $STACK_ARG

# Weaviate cloud credentials
pulumi config set --secret weaviate_rest_endpoint "YOUR_WEAVIATE_ENDPOINT.weaviate.cloud" $STACK_ARG
pulumi config set --secret weaviate_api_key "YOUR_WEAVIATE_API_KEY" $STACK_ARG

# Recraft API key
pulumi config set --secret recraft_api_key "rB7rkw7u0xwg75ENuOoROdJFBG4qco7Dbjy8PkGuQSRwNeoqqYN9u9PErXhqPJHh" $STACK_ARG

echo "Secrets set in Pulumi config. Now run 'pulumi up' in infra/ to provision/update secrets in Vultr."
