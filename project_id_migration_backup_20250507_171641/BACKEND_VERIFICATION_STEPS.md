# Backend Verification Steps

This guide focuses specifically on verifying the memory management system and GCP infrastructure setup that's been implemented.

## Memory System Verification

### 1. Check Environment Variables

First, ensure your environment is properly configured:

```bash
# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
export GCP_PROJECT_ID=agi-baby-cherry

# Verify they're set correctly
echo $GOOGLE_APPLICATION_CREDENTIALS
echo $GCP_PROJECT_ID
```

### 2. Run Memory Validation Script

The validation script will test core memory management functionality:

```bash
# Run the validation script
python validate_memory_fixes.py
```

Expected output should show:
- Successful initialization of memory manager
- Successful health check
- Ability to add and retrieve memory items
- No errors during operation

### 3. Run Integration Tests

For a more comprehensive test of the backend:

```bash
# Enable integration testing
export RUN_INTEGRATION_TESTS=true

# Make script executable
chmod +x run_integration_tests.sh

# Run integration tests
./run_integration_tests.sh
```

## GCP Infrastructure Setup

If you need to provision the GCP infrastructure:

### 1. Terraform Initialization

```bash
# Navigate to infra directory
cd /workspaces/orchestra-main/infra

# Initialize Terraform
terraform init

# Select dev workspace
terraform workspace select dev
```

### 2. Plan and Apply

```bash
# See what will be created
terraform plan -var="env=dev"

# Create the infrastructure (answer 'yes' when prompted)
terraform apply -var="env=dev"
```

Important resources that will be created:
- Firestore database for memory storage
- Redis instance for caching
- Cloud Run service for API
- Secret Manager secrets for credentials
- Vector Search index for embeddings

### 3. Configure Redis Connection

After Terraform completes, you'll need to set these additional environment variables:

```bash
# Replace [values] with actual values from Terraform output
export REDIS_HOST=[from terraform output]
export REDIS_PORT=6379
export REDIS_PASSWORD_SECRET_NAME=redis-auth-dev
```

## End-to-End Testing

### 1. Start API Server

```bash
# Start the API server
./run_api.sh
```

### 2. Test Persona Switching

```bash
# Send a request with Cherry persona
curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, who am I talking to?"}'
```

You should get a response from Cherry with her distinct personality.

### 3. Test Memory Storage

```bash
# Store a message in memory
curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{"text":"Remember this message for testing", "user_id":"test_user"}'
```

### 4. Test Memory Retrieval

```bash
# Ask about the previous message
curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{"text":"What was my last message?", "user_id":"test_user"}'
```

The response should reference "Remember this message for testing".

## Troubleshooting

### Authentication Issues

If you see errors related to authentication:
- Verify your service account key is valid
- Check that GOOGLE_APPLICATION_CREDENTIALS points to the correct file
- Ensure the service account has the necessary permissions

### Firestore Connection Issues

If Firestore connections fail:
- Check GCP_PROJECT_ID is correct
- Verify Firestore is enabled in your GCP project
- Check network connectivity to GCP

### Memory Retrieval Issues

If memory items aren't being retrieved:
- Check that the user_id matches between storage and retrieval requests
- Verify the Firestore collection exists
- Check logs for any storage errors

### Redis Connection Issues

If Redis connection fails:
- Verify REDIS_HOST and REDIS_PORT are correct
- Check if Redis password is correctly stored in Secret Manager
- Ensure network connectivity to Redis instance
