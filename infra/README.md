# Pulumi Infrastructure (`infra/`)

This directory contains the Pulumi infrastructure code for AI Orchestra.

## Structure

```
infra/
├── main.py                    # Main infrastructure orchestration
├── components/
│   ├── database_component.py  # Database resources (DragonflyDB, MongoDB)
│   └── superagi_component.py  # SuperAGI and MCP deployments
├── requirements.txt           # Pulumi Python dependencies
├── Pulumi.yaml               # Project configuration
└── Pulumi.*.yaml             # Stack-specific configs
```

## Prerequisites

- Python 3.10 (exactly - not 3.11+)
- Pulumi CLI installed
- GCP authentication configured

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize stack
pulumi stack init dev
pulumi config set gcp_project_id <your-project-id>

# Deploy
pulumi up
```

## Stack Configuration

Required configuration values:

```bash
pulumi config set gcp_project_id <project-id>
pulumi config set region us-central1  # optional, defaults to us-central1
pulumi config set --secret mongodb_password <password>  # auto-generated if not set
pulumi config set --secret openrouter_api_key <api-key>  # for SuperAGI
```

## State Management

Pulumi state is stored in GCS bucket: `gs://cherry-ai-project-pulumi-state`

This is configured automatically when you run `pulumi login gs://cherry-ai-project-pulumi-state`.

## Component Architecture

### DatabaseComponent

Manages:
- DragonflyDB deployment (Redis-compatible)
- MongoDB StatefulSet
- Firestore configuration
- Persistent volumes and services

### SuperAGIComponent

Manages:
- SuperAGI deployment with HPA
- MCP servers (MongoDB and Weaviate)
- ConfigMaps and secrets
- LoadBalancer service

## Common Operations

```bash
# Preview changes
pulumi preview

# Update specific resource
pulumi up --target <resource-urn>

# Refresh state
pulumi refresh

# Export stack outputs
pulumi stack output --json

# Destroy infrastructure
pulumi destroy
```

## Troubleshooting

1. **Authentication errors**: Run `gcloud auth application-default login`
2. **State lock issues**: Check no other Pulumi operations are running
3. **Resource conflicts**: Use `pulumi refresh` to sync state

## References

- [Main Infrastructure Guide](../docs/INFRASTRUCTURE_GUIDE.md)
- [Pulumi GCP Provider](https://www.pulumi.com/registry/packages/gcp/)
- [Pulumi Kubernetes Provider](https://www.pulumi.com/registry/packages/kubernetes/)
