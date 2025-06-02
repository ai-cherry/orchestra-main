# AI Orchestra Credential Integration Guide

This guide explains how to integrate the secure credential management system into your AI Orchestra application code. It provides examples for different components and use cases.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Python Integration](#python-integration)
  - [FastAPI Routes](#fastapi-routes)
  - [Agent Components](#agent-components)
  - [Memory System](#memory-system)
  - [LLM Integration](#llm-integration)
- [Bash Script Integration](#bash-script-integration)
- [GitHub Actions Integration](#github-actions-integration)
- [Pulumi Integration](#pulumi-integration)
- [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

## Overview

The AI Orchestra secure credential management system provides a unified way to access credentials across different environments and components. It uses
- Environment-specific credentials (dev, staging, prod)
- Credential caching for performance
- Automatic credential rotation
- Workload Identity Federation for GitHub Actions

## Prerequisites

Before integrating the credential management system, ensure you have:

1. Deployed the Pulumi infrastructure using `implementation_plan.sh`
2. Migrated existing credentials to 3. Set up Workload Identity Federation for GitHub Actions
4. Added the required dependencies:
   ```bash
   poetry add google-cloud-secret-manager
   ```

## Python Integration

### FastAPI Routes

For FastAPI routes, use the dependency injection system to access credentials:

```python
from fastapi import Depends, FastAPI
from core.orchestrator.src.api.dependencies.credentials import (
    get_vertex_ai_credentials,
    get_gemini_credentials,
    get_redis_credentials,
)

app = FastAPI()

@app.post("/vertex/predict")
async def predict(
    request: PredictRequest,
    credentials: dict = Depends(get_vertex_ai_credentials)
):
    """
    Make a prediction using
    Uses the     """
    # Initialize     from google.cloud import aiplatform

    aiplatform.init(
        project=credentials["project_id"],
        location="us-central1",
        credentials=credentials
    )

    # Use     endpoint = aiplatform.Endpoint(request.endpoint_id)
    prediction = endpoint.predict(instances=request.instances)

    return {"prediction": prediction}

@app.post("/gemini/generate")
async def generate(
    request: GenerateRequest,
    credentials: dict = Depends(get_gemini_credentials)
):
    """
    Generate text using Gemini.

    Uses the Gemini credentials injected by the dependency.
    """
    # Use Gemini credentials
    from google.cloud import aiplatform

    aiplatform.init(
        project=credentials["project_id"],
        location="us-central1",
        credentials=credentials
    )

    # Use Gemini
    model = aiplatform.TextGenerationModel.from_pretrained("gemini-pro")
    response = model.predict(request.prompt)

    return {"text": response.text}

@app.get("/memory/retrieve")
async def retrieve_memory(
    key: str,
    redis_config: dict = Depends(get_redis_credentials)
):
    """
    Retrieve a memory item from Redis.

    Uses the Redis credentials injected by the dependency.
    """
    import redis

    # Connect to Redis
    r = redis.Redis(
        host=redis_config["host"],
        port=int(redis_config["port"]),
        password=redis_config["password"],
        ssl=True
    )

    # Retrieve value
    value = r.get(key)

    return {"key": key, "value": value}
```

### Agent Components

For agent components, use the credential manager directly:

```python
from core.security.credential_manager import get_credential_manager

class VertexAgent:
    """Agent that uses
    def __init__(self, project_id=None, environment=None):
        """
        Initialize the Vertex Agent.

        Args:
            project_id:             environment: Environment name (dev, staging, prod).
        """
        self.credential_manager = get_credential_manager(project_id, environment)
        self.credentials = self.credential_manager.get_service_account_key("vertex-ai-agent")

        # Initialize         from google.cloud import aiplatform

        aiplatform.init(
            project=self.credentials["project_id"],
            location="us-central1",
            credentials=self.credentials
        )

    async def predict(self, endpoint_id, instances):
        """
        Make a prediction using
        Args:
            endpoint_id: The             instances: The instances to predict.

        Returns:
            The prediction results.
        """
        from google.cloud import aiplatform

        endpoint = aiplatform.Endpoint(endpoint_id)
        prediction = endpoint.predict(instances=instances)

        return prediction
```

### Memory System

For the memory system, use the credential manager to access different storage backends:

```python
from core.security.credential_manager import get_credential_manager
from typing import Any, Dict, Optional

class MemoryManager:
    """
    Memory manager for AI Orchestra.

    Manages access to different memory storage backends.
    """

    def __init__(self, project_id=None, environment=None):
        """
        Initialize the Memory Manager.

        Args:
            project_id:             environment: Environment name (dev, staging, prod).
        """
        self.credential_manager = get_credential_manager(project_id, environment)
        self.redis_config = {
            "host": self.credential_manager.get_secret("redis-host"),
            "port": self.credential_manager.get_secret("redis-port"),
            "password": self.credential_manager.get_secret("redis-password"),
        }
        self.MongoDB

    def get_redis_client(self):
        """
        Get a Redis client.

        Returns:
            A Redis client.
        """
        import redis

        return redis.Redis(
            host=self.redis_config["host"],
            port=int(self.redis_config["port"]),
            password=self.redis_config["password"],
            ssl=True
        )

    def get_MongoDB
        """
        Get a MongoDB

        Returns:
            A MongoDB
        """
        from google.cloud import MongoDB

        return MongoDB
            project=self.MongoDB
            credentials=self.MongoDB
        )

    async def store_short_term(self, key: str, value: Any, ttl: int = 3600):
        """
        Store a value in short-term memory (Redis).

        Args:
            key: The key to store.
            value: The value to store.
            ttl: Time to live in seconds.
        """
        client = self.get_redis_client()
        client.set(key, value, ex=ttl)

    async def retrieve_short_term(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from short-term memory (Redis).

        Args:
            key: The key to retrieve.

        Returns:
            The value, or None if not found.
        """
        client = self.get_redis_client()
        return client.get(key)

    async def store_long_term(self, collection: str, document_id: str, data: Dict[str, Any]):
        """
        Store a value in long-term memory (MongoDB

        Args:
            collection: The collection to store in.
            document_id: The document ID.
            data: The data to store.
        """
        client = self.get_MongoDB
        client.collection(collection).document(document_id).set(data)

    async def retrieve_long_term(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value from long-term memory (MongoDB

        Args:
            collection: The collection to retrieve from.
            document_id: The document ID.

        Returns:
            The data, or None if not found.
        """
        client = self.get_MongoDB
        doc = client.collection(collection).document(document_id).get()
        return doc.to_dict() if doc.exists else None
```

### LLM Integration

For LLM integration, use the credential manager to access API keys:

```python
from core.security.credential_manager import get_credential_manager
from typing import List, Dict, Any, Optional

class LLMManager:
    """
    LLM Manager for AI Orchestra.

    Manages access to different LLM providers.
    """

    def __init__(self, project_id=None, environment=None):
        """
        Initialize the LLM Manager.

        Args:
            project_id:             environment: Environment name (dev, staging, prod).
        """
        self.credential_manager = get_credential_manager(project_id, environment)

        # Get credentials for different LLM providers
        self.vertex_credentials = self.credential_manager.get_service_account_key("vertex-ai-agent")
        self.gemini_credentials = self.credential_manager.get_service_account_key("gemini-agent")
        self.openai_api_key = self.credential_manager.get_secret("openai-api-key")
        self.anthropic_api_key = self.credential_manager.get_secret("anthropic-api-key")

    async def generate_vertex(self, prompt: str, model: str = "text-bison") -> str:
        """
        Generate text using
        Args:
            prompt: The prompt to generate from.
            model: The model to use.

        Returns:
            The generated text.
        """
        from google.cloud import aiplatform

        aiplatform.init(
            project=self.vertex_credentials["project_id"],
            location="us-central1",
            credentials=self.vertex_credentials
        )

        model = aiplatform.TextGenerationModel.from_pretrained(model)
        response = model.predict(prompt)

        return response.text

    async def generate_gemini(self, prompt: str) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: The prompt to generate from.

        Returns:
            The generated text.
        """
        from google.cloud import aiplatform

        aiplatform.init(
            project=self.gemini_credentials["project_id"],
            location="us-central1",
            credentials=self.gemini_credentials
        )

        model = aiplatform.TextGenerationModel.from_pretrained("gemini-pro")
        response = model.predict(prompt)

        return response.text

    async def generate_openai(self, prompt: str, model: str = "gpt-4") -> str:
        """
        Generate text using OpenAI.

        Args:
            prompt: The prompt to generate from.
            model: The model to use.

        Returns:
            The generated text.
        """
        import openai

        openai.api_key = self.openai_api_key

        response = openai.Completion.create(
            model=model,
            prompt=prompt,
            max_tokens=1000
        )

        return response.choices[0].text

    async def generate_anthropic(self, prompt: str, model: str = "claude-2") -> str:
        """
        Generate text using Anthropic.

        Args:
            prompt: The prompt to generate from.
            model: The model to use.

        Returns:
            The generated text.
        """
        import anthropic

        client = anthropic.Anthropic(api_key=self.anthropic_api_key)

        response = client.completions.create(
            model=model,
            prompt=prompt,
            max_tokens_to_sample=1000
        )

        return response.completion
```

## Bash Script Integration

For bash scripts, use the `secure_credential_manager.sh` script to access credentials:

```bash
#!/bin/bash
# deploy_model.sh

# Get credentials from export GOOGLE_APPLICATION_CREDENTIALS=$(mktemp)
./secure_credential_manager.sh get-secret vertex-ai-key > "$GOOGLE_APPLICATION_CREDENTIALS"
chmod 600 "$GOOGLE_APPLICATION_CREDENTIALS"

# Deploy model
gcloud ai models upload \
  --region=us-central1 \
  --display-name=my-model \
  --container-image-uri=gcr.io/cherry-ai-project/my-model:latest

# Clean up
rm -f "$GOOGLE_APPLICATION_CREDENTIALS"
```

## GitHub Actions Integration

For GitHub Actions, use Workload Identity Federation:

```yaml
name: Deploy to
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write # Required for Workload Identity Federation

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      # Authenticate using Workload Identity Federation
      - id: "auth"
        name: "Authenticate to         uses: "google-github-actions/auth@v1"
        with:
          workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.SERVICE_ACCOUNT_EMAIL }}

      # Setup gcloud CLI
      - name: "Set up Cloud SDK"
        uses: "google-github-actions/setup-gcloud@v1"

      # Deploy to       - name: Deploy to         uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: ai-orchestra
          region: us-central1
          image: gcr.io/${{ secrets.```

## Pulumi Integration

For Pulumi, use the `secure-credentials` module:

```hcl
secure_credentials = ComponentResource( {
  source      = "./modules/secure-credentials"
  project_id  = var.project_id
  region      = var.region
  env         = var.env
  github_org  = "ai-cherry"
  github_repo = "orchestra-main"
}

# Use the outputs
pulumi.export("service_account_emails", {
  value = module.secure_credentials.service_account_emails
}

pulumi.export("workload_identity_provider", {
  value = module.secure_credentials.workload_identity_provider
}
```

## Monitoring and Troubleshooting

### Monitoring Credential Usage

To monitor credential usage, set up Cloud Monitoring:

```python
from core.security.credential_manager import get_credential_manager
from google.cloud import monitoring_v3

# Create a monitoring client
monitoring_client = monitoring_v3.MetricServiceClient()

# Create a custom metric descriptor
project_name = f"projects/{project_id}"
descriptor = monitoring_v3.MetricDescriptor(
    name=f"{project_name}/metricDescriptors/custom.googleapis.com/credential_access",
    type="custom.googleapis.com/credential_access",
    metric_kind=monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
    value_type=monitoring_v3.MetricDescriptor.ValueType.INT64,
    description="Number of credential access operations",
    labels=[
        monitoring_v3.LabelDescriptor(
            key="credential_name",
            value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
            description="Name of the credential being accessed",
        ),
        monitoring_v3.LabelDescriptor(
            key="environment",
            value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
            description="Environment (dev, staging, prod)",
        ),
    ],
)

monitoring_client.create_metric_descriptor(
    name=project_name,
    metric_descriptor=descriptor,
)

# Instrument the credential manager
class MonitoredCredentialManager:
    def __init__(self, project_id=None, environment=None):
        self.credential_manager = get_credential_manager(project_id, environment)
        self.project_id = project_id or "cherry-ai-project"
        self.environment = environment or "dev"
        self.monitoring_client = monitoring_v3.MetricServiceClient()

    def get_secret(self, secret_name, version="latest"):
        # Get the secret
        secret = self.credential_manager.get_secret(secret_name, version)

        # Record the access
        self._record_access(secret_name)

        return secret

    def _record_access(self, credential_name):
        # Create a time series
        series = monitoring_v3.TimeSeries()
        series.metric.type = "custom.googleapis.com/credential_access"
        series.metric.labels["credential_name"] = credential_name
        series.metric.labels["environment"] = self.environment

        # Create a data point
        point = series.points.add()
        point.value.int64_value = 1
        now = time.time()
        point.interval.end_time.seconds = int(now)

        # Write the time series
        self.monitoring_client.create_time_series(
            name=f"projects/{self.project_id}",
            time_series=[series],
        )
```

### Troubleshooting

If you encounter issues with the credential management system:

1. **Authentication Failures**:

   - Check if the service account has the necessary permissions
   - Verify that the credentials are correctly stored in    - Ensure the environment variables are set correctly

2. **Secret Not Found**:

   - Check if the secret exists in    - Verify that you're using the correct name and environment suffix
   - Ensure you have permission to access the secret

3. **Workload Identity Federation Issues**:
   - Check if the Workload Identity Pool is configured correctly
   - Verify that the GitHub repository has the correct permissions
   - Ensure the id-token permission is set in the workflow

For more detailed troubleshooting, refer to the [SECURE_CREDENTIAL_MANAGEMENT.md](SECURE_CREDENTIAL_MANAGEMENT.md) documentation.
