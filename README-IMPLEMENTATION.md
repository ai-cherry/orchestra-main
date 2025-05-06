# AI Orchestra Implementation Guide

This guide provides detailed instructions for setting up and deploying the AI Orchestra project on Google Cloud Platform (GCP). The implementation focuses on stability, scalability, and security while enabling advanced multi-agent capabilities with hyper-contextualized memory.

## Architecture Overview

AI Orchestra is a multi-agent orchestration system with the following key components:

1. **Agent Registry**: Manages agent selection based on capabilities and context
2. **Memory System**: Provides tiered memory storage across different persistence levels
3. **Infrastructure**: Cloud Run for deployment, with supporting GCP services
4. **CI/CD Pipeline**: GitHub Actions workflow for testing, building, and deployment

### Memory Architecture

The memory system uses a layered approach:

- **Short-term Memory**: Redis for fast, ephemeral context (seconds to hours)
- **Mid-term Memory**: Firestore for structured conversation history (hours to weeks)
- **Long-term Memory**: Vertex AI Vector Search for semantic retrieval (weeks to permanent)

## Setup Instructions

Follow these steps to set up the project from scratch:

### 1. Initial GCP Setup

```bash
# Clone the repository
git clone https://github.com/your-org/orchestra-main.git
cd orchestra-main

# Make the setup script executable
chmod +x scripts/setup_wif_auth.sh

# Run the setup script (requires GCP admin privileges)
bash scripts/setup_wif_auth.sh

# Create Terraform state bucket
gsutil mb -l us-west4 gs://cherry-ai-project-terraform-state
gsutil versioning set on gs://cherry-ai-project-terraform-state

# Enable required APIs
python scripts/enable_gcp_apis.py
```

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

- `WIF_PROVIDER_ID`: From the setup script output
- `WIF_SERVICE_ACCOUNT`: From the setup script output
- `PROJECT_ID`: `cherry-ai-project`

### 3. Local Development Setup

```bash
# Start the DevContainer in VS Code
# OR set up locally:
python -m venv .venv
source .venv/bin/activate
pip install poetry==1.7.1
poetry install --with dev
```

### 4. Deploy Infrastructure with Terraform

```bash
# Initialize Terraform
cd terraform
terraform init -backend-config="bucket=cherry-ai-project-terraform-state"

# Plan and apply
terraform plan -var="environment=staging"
terraform apply -var="environment=staging"
```

### 5. Create API Keys in Secret Manager

```bash
# Create secrets for LLM providers
gcloud secrets create openai-api-key --project=cherry-ai-project
gcloud secrets create anthropic-api-key --project=cherry-ai-project
gcloud secrets create gemini-api-key --project=cherry-ai-project

# Add versions with your API keys
echo "your-openai-key" | gcloud secrets versions add openai-api-key --data-file=-
echo "your-anthropic-key" | gcloud secrets versions add anthropic-api-key --data-file=-
echo "your-gemini-key" | gcloud secrets versions add gemini-api-key --data-file=-
```

## CI/CD Pipeline

The CI/CD pipeline is configured in `.github/workflows/orchestra-cicd.yml` and performs:

1. **Testing**: Runs pytest and flake8 linting
2. **Terraform Validation**: Ensures infrastructure code is valid
3. **Build & Deploy**: Builds Docker image and deploys to Cloud Run

## Memory System Usage

The memory system can be used in your agents as follows:

```python
# Create memory-aware registry
registry = MemoryAwareAgentRegistry()
await registry.initialize_async()

# Create context with conversation ID
context = registry.create_context(
    text="Hello, I'm looking for information about AI Orchestra.",
    conversation_id="user123",
)

# Store information in memory
await context.remember(
    content="Important information to remember",
    memory_type=MemoryType.MID_TERM,
)

# Retrieve information from memory
results = await context.recall("information")
```

## Security Best Practices

The implementation follows these security best practices:

1. **Workload Identity Federation**: No service account keys stored in GitHub
2. **Secret Manager**: API keys and credentials stored securely
3. **Least Privilege**: Service accounts with minimal required permissions
4. **Terraform**: Infrastructure defined as code with secure defaults

## Troubleshooting

### Common Issues

1. **Poetry Dependency Issues**:
   - Solution: Use `poetry update` to refresh dependencies

2. **Terraform Validation Errors**:
   - Solution: Check provider versions and API enablement

3. **Authentication Issues**:
   - Solution: Verify Workload Identity Federation setup

## Next Steps

1. **Agent Framework Integration**: Integrate LangChain, AutoGen, and other frameworks
2. **Vector Search Setup**: Complete Vertex AI Vector Search configuration
3. **Monitoring**: Add observability with Cloud Monitoring and Logging
4. **Performance Optimization**: Fine-tune memory TTLs and caching strategies