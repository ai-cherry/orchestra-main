# Testing the FastAPI Backend Locally

Before deploying your FastAPI backend to Cloud Run, it's a good practice to test it locally to ensure everything works as expected. This guide provides steps for running and testing your API locally.

## Prerequisites

- Python 3.8+ installed
- Poetry or pip for dependency management
- Docker installed (optional, for container testing)

## Step 1: Install Dependencies

First, make sure all dependencies are installed:

```bash
# Navigate to the project root
cd /workspaces/orchestra-main

# Using pip
pip install -r requirements.txt

# Or using Poetry (if used in your project)
# poetry install
```

## Step 2: Set Up Environment Variables

Create or update your `.env` file with necessary configuration:

```bash
# Copy the example env file if needed
cp .env.example .env

# Edit the .env file with appropriate settings
# Typically you'll need to set:
# - API keys (OpenRouter, etc.)
# - Database connection strings
# - Other configuration specific to local development
```

## Step 3: Run the FastAPI Server

Start the FastAPI server locally:

```bash
# For development server
./run_api.sh

# Alternative options:
# uvicorn core.orchestrator.src.main:app --reload
# python -m core.orchestrator.src.main
```

The server should start and display a message indicating it's running, typically at http://localhost:8000.

## Step 4: Test API Endpoints

Now you can test the API endpoints using curl, httpie, or a tool like Postman or Insomnia:

### Test the Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected output: `{"status":"healthy"}` or similar health information.

### Test the Interaction Endpoint

```bash
curl -X POST http://localhost:8000/interact \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "session_id": "test-session-123",
    "params": {
      "temperature": 0.7
    }
  }'
```

### Interactive API Documentation

FastAPI automatically generates interactive documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Step 5: Test with Docker (Optional)

To ensure your API works correctly in a containerized environment similar to Cloud Run:

```bash
# Build the Docker image
docker build -t orchestrator-api-local .

# Run the container
docker run --env-file .env -p 8000:8000 orchestrator-api-local
```

Then test the API endpoints as described in Step 4, but ensure you're using the correct port mapping.

## Troubleshooting Common Issues

### Port Already in Use

If you see an error like `Address already in use`:

```bash
# Find the process using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Module Not Found Errors

If you encounter module import errors:

```bash
# Make sure your PYTHONPATH includes the project root
export PYTHONPATH=$PYTHONPATH:/workspaces/orchestra-main

# Then run the API again
```

### Authentication Errors

If you're seeing authentication errors with external services (like OpenRouter):

1. Check that your API keys are correctly set in the `.env` file
2. Verify that the environment variables are being loaded correctly
3. Ensure you have proper network connectivity to the external services

## Next Steps

Once you've verified that your API works correctly locally:

1. Follow the [Cloud Run Deployment Guide](cloud_run_deployment.md) to deploy your API to Cloud Run
2. Use the `deploy_to_cloud_run.sh` script to automate the deployment process

Remember that some environment-specific configurations might need to be adjusted when moving from local development to the cloud environment.
