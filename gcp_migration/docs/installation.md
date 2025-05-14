P# GCP Migration Toolkit Installation Guide

This guide provides step-by-step instructions for installing and setting up the GCP Migration toolkit.

## Prerequisites

Before you begin, ensure you have:

1. Python 3.8 or later
2. Pip or Poetry for package management
3. GCP project with owner permissions
4. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed (optional but recommended)
5. GitHub account with repository access (if migrating GitHub resources)

## Installation Methods

### Method 1: Using Pip (Recommended for Most Users)

1. Install the package from PyPI:

```bash
pip install gcp-migration-toolkit
```

2. Verify installation:

```bash
python -c "from gcp_migration import __version__; print(__version__)"
```

### Method 2: From Source

1. Clone the repository:

```bash
git clone https://github.com/your-org/gcp-migration-toolkit.git
cd gcp-migration-toolkit
```

2. Install dependencies:

```bash
# Using pip
pip install -e .

# Or using Poetry
poetry install
```

### Method 3: Using Docker

```bash
# Pull the image
docker pull ghcr.io/your-org/gcp-migration-toolkit:latest

# Run the container
docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/.config/gcloud:/root/.config/gcloud \
  ghcr.io/your-org/gcp-migration-toolkit:latest
```

## Authentication Setup

### Option 1: Application Default Credentials (Recommended)

1. Authenticate with GCP:

```bash
gcloud auth application-default login
```

2. Set the project:

```bash
gcloud config set project YOUR_PROJECT_ID
```

### Option 2: Service Account Key

1. Create a service account key in GCP Console

2. Download the key file

3. Set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key-file.json
```

## First-time Setup

1. Enable required GCP APIs:

```bash
# Using gcloud
gcloud services enable secretmanager.googleapis.com storage.googleapis.com firestore.googleapis.com aiplatform.googleapis.com

# Or using the toolkit
python -m gcp_migration.cli.app setup-project --project-id YOUR_PROJECT_ID
```

2. Verify setup:

```bash
python -m gcp_migration.cli.app verify-setup --project-id YOUR_PROJECT_ID
```

## Configuration Options

### Environment Variables

- `GCP_PROJECT_ID`: Default GCP project ID
- `GCP_LOCATION`: Default GCP region (defaults to "us-central1")
- `GITHUB_TOKEN`: GitHub personal access token (for GitHub operations)
- `GEMINI_API_KEY`: Gemini API key (for Gemini Code Assist setup)

### Configuration File

You can create a configuration file at `~/.gcp-migration/config.yaml`:

```yaml
project_id: your-project-id
location: us-central1
github:
  token: your-github-token
  organization: your-github-org
gemini:
  api_key: your-gemini-api-key
  workspace_path: /path/to/your/workspace
```

## Troubleshooting

### Common Issues

#### Authentication Problems

If you encounter authentication errors:

```bash
# Check current credentials
gcloud auth list

# Revoke and reauthenticate if needed
gcloud auth revoke
gcloud auth login
```

#### API Enablement Failures

```bash
# Check API status
gcloud services list --available --filter="name:secretmanager.googleapis.com"

# Enable API manually
gcloud services enable secretmanager.googleapis.com
```

#### Permission Issues

Ensure your user or service account has the following roles:
- Secret Manager Admin (`roles/secretmanager.admin`)
- Storage Admin (`roles/storage.admin`)
- Firestore Admin (`roles/datastore.owner`)
- Vertex AI Admin (`roles/aiplatform.admin`)

## Next Steps

After installation, proceed to:
1. [Migrate GitHub Secrets](docs/migrate_github_secrets.md)
2. [Set Up Gemini Code Assist](docs/setup_gemini.md)
3. [Verify Migration](docs/verify_migration.md)

For the complete API reference, see [API Reference](api_reference.md).
