# AI Orchestra Admin Interface

This repository contains the code for the AI Orchestra Admin Interface, which provides a web-based interface for managing AI Orchestra agents, memory systems, and other components.

## Architecture

The Admin Interface consists of two main components:

1. **Backend API** (FastAPI): Handles data processing, GCP service interactions, and Gemini integration
2. **Frontend** (React): Provides the user interface for interacting with the admin features

## Backend API

The backend API is built with FastAPI and provides endpoints for:

- **Agent Management**: View, start, and stop agents
- **Memory Management**: View statistics, prune memories, and promote memories
- **System Information**: View system stats and GCP information
- **Gemini Integration**: Process natural language commands and analyze content

### API Routes

- `/api/v1/system/stats` - Get system statistics
- `/api/v1/system/gcp` - Get GCP project information
- `/api/v1/agents` - List all agents
- `/api/v1/agents/{agent_id}` - Get details for a specific agent
- `/api/v1/agents/{agent_id}/start` - Start an agent
- `/api/v1/agents/{agent_id}/stop` - Stop an agent
- `/api/v1/memory/stats/{agent_id}` - Get memory statistics for an agent
- `/api/v1/memory/prune/{agent_id}` - Prune memories for an agent
- `/api/v1/memory/promote/{memory_id}` - Promote a memory to a higher tier
- `/api/v1/command` - Execute a natural language command using Gemini
- `/api/v1/analyze` - Analyze content using Gemini

## GCP Integration

The admin interface integrates with the following GCP services:

- **Cloud Run**: For hosting the backend and frontend
- **Firestore**: For storing agent and memory data
- **Cloud Storage**: For storing large assets
- **Vertex AI**: For integrating with Gemini models

## Gemini Integration

The admin interface leverages Gemini 2.5 Pro via Vertex AI for two main capabilities:

1. **Natural Language Commands**: Process commands like "Start agent X" or "Prune memories older than 7 days for agent Y"
2. **Content Analysis**: Analyze logs, metrics, and other content to provide insights

### Gemini Function Calling

The implementation uses Gemini's function calling capability to map natural language commands to specific functions:

- `get_agent_status`
- `start_agent`
- `stop_agent`
- `list_agents`
- `prune_memory`
- `promote_memory`
- `get_memory_stats`

## Deployment

The admin interface is deployed to Google Cloud Run using Terraform and GitHub Actions.

### Terraform Configuration

The Terraform configuration in `admin-interface/terraform/main.tf` defines:

- Cloud Run services for frontend and backend
- Environment variables and service account configuration
- IAM permissions

### GitHub Actions

The GitHub Actions workflow in `.github/workflows/deploy-admin-interface.yml` automates the build and deployment process:

1. Builds Docker images for frontend and backend
2. Pushes images to Google Container Registry
3. Applies Terraform configuration
4. Deploys to Cloud Run

## Local Development

### Prerequisites

- Python 3.11+
- Poetry
- Node.js 20+
- Docker

### Setup

1. Install dependencies:

   ```bash
   cd services/admin-api
   poetry install
   ```

2. Set up environment variables in `.env`:

   ```
   PROJECT_ID=your-gcp-project-id
   REGION=us-central1
   API_URL=http://localhost:8080
   ```

3. Run the API server:
   ```bash
   poetry run python main.py
   ```

## Deployment

To deploy the admin interface:

1. Push changes to the main branch
2. The GitHub Actions workflow will automatically build and deploy the changes
3. Alternatively, deploy manually using:
   ```bash
   cd admin-interface/terraform
   terraform apply
   ```

## Security

This implementation focuses on stability and performance. For production use, consider implementing additional security measures:

- Enhanced authentication and authorization
- OWASP LLM security measures
- More restrictive CORS policies
- Secrets management via Secret Manager

## License

Proprietary - AI Orchestra Project
