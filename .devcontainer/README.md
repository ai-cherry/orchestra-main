# Dev Container Configuration

This document describes the current development container configuration that ensures stable startup in GitHub Codespaces.

## Core Components

- **Base Image**: `python:3.11-slim-bullseye` - Chosen for stability over the more complex devcontainers image
- **Minimal Dependencies**: Only essential system packages are installed
- **Simple Setup Script**: Handles only environment variable setup, not complex installations
- **No Docker-in-Docker**: Avoids common causes of startup failures

## Modification Guidelines

When modifying the dev container configuration:

1. **Make incremental changes**: Test one change at a time
2. **Keep dependencies minimal**: Only add what you absolutely need
3. **Avoid Docker extensions/features**: These often cause issues in Codespaces
4. **Test locally first**: When possible, test with VS Code Remote Containers locally before pushing
5. **Be cautious with postCreateCommand**: Complex commands here often cause startup failures

## Troubleshooting

If startup issues return:
- Compare against this working version
- Check GitHub Codespaces logs for specific errors
- Consider rebuilding without cache using the VS Code command "Codespaces: Rebuild Container"

## Last Known Good Configuration

Date: April 20, 2025