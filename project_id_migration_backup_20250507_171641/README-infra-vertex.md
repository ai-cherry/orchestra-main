# Orchestra Infrastructure with Vertex AI Integration

This project integrates Google Cloud infrastructure deployed with Terraform with Vertex AI Agent automation for enhanced DevOps capabilities.

## Overview

The infrastructure consists of multiple environments (dev, staging, production) deployed in Google Cloud Platform, with the following components:

- **Cloud Run** services for serving the Orchestra API
- **Firestore** for structured data and chat memory storage
- **Pub/Sub** event bus for communication between services
- **Vertex AI Vector Search** for embeddings and semantic search
- **Secret Manager** for secure credential management
- **Vertex AI Agent** for automation of operational tasks

## Architecture

![Architecture Diagram](https://example.com/architecture.png)

The system uses a multi-environment approach:
- Each environment (dev, stage, prod) has its own Cloud Run services with appropriate suffixes
- Terraform workspaces maintain separate state files for each environment
- Service accounts follow the least privilege principle with environment-specific separation

### Vertex AI Agent Manager Integration

The Vertex AI Agent Manager provides automation for:

1. **Infrastructure Operations**
   - Running initialization scripts
   - Applying Terraform configurations to specific environments
   - Monitoring resource usage and costs

2. **Agent Team Management**
   - Creating agent teams with the Planner/Doer/Reviewer pattern
   - Deploying agent teams to Cloud Run
   - Managing agent team configurations

3. **Vector Embedding Management**
   - Creating and managing embeddings in Vertex AI Vector Search
   - Performing semantic searches

4. **Game Session Management**
   - Managing interactive game sessions
   - Handling player actions and responses

## Getting Started

### Prerequisites

- Google Cloud SDK (gcloud)
- Terraform 1.5+
- Python 3.8+
- Access to the `agi-baby-cherry` GCP project

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ai-cherry/orchestra-main.git
   cd orchestra-main
   ```

2. **Authenticate with Google Cloud**
   ```bash
   echo "$GCP_API_KEY" | base64 -d > /tmp/gsa-key.json
   gcloud auth activate-service-account --key-file=/tmp/gsa-key.json
   gcloud config set project agi-baby-cherry
   gcloud config set run/region us-west2
   ```

3. **Install Vertex AI Agent Manager**
   ```bash
   cd packages/vertex_client
   pip install -e .
   cd ../..
   ```

4. **Initialize Infrastructure with Vertex Integration**
   ```bash
   cd infra
   ./run_with_vertex.sh init
   ```

5. **Deploy to an Environment**
   ```bash
   ./run_with_vertex.sh deploy dev
   ```

## Usage

### Infrastructure Operations

```bash
# Initialize infrastructure
./run_with_vertex.sh init

# Deploy to environments
./run_with_vertex.sh deploy dev
./run_with_vertex.sh deploy stage
./run_with_vertex.sh deploy prod

# Monitor resources
./run_with_vertex.sh monitor
```

### Agent Team Management

```bash
# Create an agent team
./run_with_vertex.sh create-team clinical-trial-followup
```

### Using the API Server

```bash
# Start the API server
cd packages/vertex_client
./run_api_server.py
```

Then use the API endpoints:
```bash
# Trigger a task via the API
curl -X POST http://localhost:8000/vertex/trigger-task \
  -H "Content-Type: application/json" \
  -d '{"task": "monitor resources"}'
```

### Using the CLI

```bash
# Run from anywhere in the project
vertex-cli monitor
vertex-cli terraform dev
vertex-cli team clinical-trial-followup
```

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make Changes**
   - Update Terraform modules in `infra/modules/`
   - Add/modify Vertex AI Agent Manager tasks in `packages/vertex_client/`

3. **Test Changes**
   - Use the CLI for manual testing: `vertex-cli [command]`
   - Deploy to dev environment: `./run_with_vertex.sh deploy dev`

4. **Submit Pull Request**
   - Follow the standard GitHub PR workflow
   - Ensure CI/CD pipeline passes

5. **Deploy to Production**
   - Merge to main branch
   - Deploy to production: `./run_with_vertex.sh deploy prod`

## Architecture Details

### Multi-Environment Strategy

The infrastructure uses Terraform workspaces to maintain separate state files for dev, stage, and prod environments, while keeping all resources in a single GCP project. This approach:

- Keeps blast radius low between environments
- Simplifies management through consistent naming patterns
- Provides a clean promotion path from dev → stage → prod

### Cloud Run Configuration

- **Autoscaling**: 0-20 instances
- **CPU Allocation**: Always allocated for handling long LLM calls
- **Environment Isolation**: Separate services with env-specific suffixes

### Firestore Usage

- **Native Mode**: For structured data storage
- **Collections**: Environment-specific collections with appropriate indexes
- **Data Separation**: Clear separation between environments

### Pub/Sub Event Bus

- **Topic Naming**: Environment-specific with appropriate suffixes
- **Dead-letter Handling**: Each environment has a dead-letter topic
- **Priority Handling**: Support for high-priority messages

### Vertex AI Integration

- **Vector Search**: Optimized for low latency (<10ms)
- **Agent Builder**: For automation of operational tasks
- **Resource Scaling**: Environment-appropriate resource allocation

## Scaling Considerations

- **Cloud Run**: Start with 0-20 instances, can scale to 1000+ instances
- **Pub/Sub**: Watch for 10 MB/s publish limit per topic
- **Firestore**: Monitor 10K writes/sec per collection limit
- **Cost Management**: Automatic monitoring and alerting via Vertex AI Agent

## Security

- **Service Accounts**: Follow least privilege principle with env-specific accounts
- **Secret Management**: All secrets stored in Secret Manager
- **Environment Isolation**: Proper isolation between environments

## Compliance & Data Residency

All data is stored in `us-west2` region. No specific compliance requirements are enforced currently, but the architecture supports adding CMEK (Customer Managed Encryption Keys) if needed in the future.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
