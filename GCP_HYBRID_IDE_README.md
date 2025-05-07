# GCP Hybrid IDE Solution

This repository contains configuration and scripts for setting up a seamless hybrid development environment that integrates GitHub Codespaces with Google Cloud Platform's IDE solutions.

## Files in this Solution

| File | Description |
|------|-------------|
| `.devcontainer/devcontainer.json` | Configuration for GitHub Codespaces with GCP authentication |
| `setup-gcp-ides.sh` | Script to provision Cloud Workstation and Vertex AI Workbench instances |
| `cleanup_gcp_config.sh` | Script to remove conflicting GCP configurations |
| `GITHUB_CODESPACES_GCP_SETUP.md` | Documentation for setting up GitHub Codespaces with GCP |
| `HYBRID_GCP_IDE_SETUP.md` | Comprehensive guide for the entire hybrid IDE setup |

## Quick Start

1. **Clean up any conflicting configurations**:
   ```bash
   ./cleanup_gcp_config.sh
   ```
   This script ensures no existing GCP configurations will conflict with the new setup.

2. **Set up GitHub Codespaces**:
   - Add your GCP service account JSON key as a GitHub secret named `GCP_MASTER_SERVICE_JSON`
   - Launch GitHub Codespaces for this repository

3. **Provision GCP IDEs**:
   ```bash
   ./setup-gcp-ides.sh
   ```

4. **Access Your Environments**:
   - GitHub Codespaces: Via GitHub interface
   - Cloud Workstation: Via GCP Console
   - Vertex AI Workbench: Via GCP Console

## Features

- **Unified Authentication**: All environments use the same service account
- **Code Synchronization**: All environments clone the same repository
- **Persistent Credentials**: No URL-based authentication prompts
- **Private Repository Support**: Optional GitHub token for private repos
- **Customizable Resources**: Configurable machine types and locations
- **Conflict Prevention**: Disables conflicting scripts and configurations

## Documentation

For detailed instructions, refer to:
- [Hybrid GCP IDE Setup Guide](HYBRID_GCP_IDE_SETUP.md) - Complete end-to-end setup instructions
- [GitHub Codespaces GCP Setup](GITHUB_CODESPACES_GCP_SETUP.md) - Focused on Codespaces configuration

## Cleanup Resources

When you're done, you can clean up the GCP resources with:
```bash
./setup-gcp-ides.sh cleanup
