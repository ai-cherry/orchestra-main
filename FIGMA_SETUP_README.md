# Figma Pages Setup Guide

This guide explains how to use the `setup_figma_pages.py` script to automatically create the standard page structure in your Figma file.

## Prerequisites

1. Python 3 installed with the `requests` library
2. Figma Personal Access Token (PAT)
3. Your Figma file ID

## File Configuration

The script is already configured with:
- Figma File ID: `368236963`
- Standard page structure defined in the script

## Running the Script

### Option 1: Using Figma PAT from GitHub Secrets

If your Figma PAT is stored in GitHub Secrets (organization level as FIGMA_PAT), you can access it through your CI/CD workflows. For local development, you'll need to:

1. Get the PAT value from your GitHub organization's secrets
2. Set it temporarily as an environment variable:

```bash
export FIGMA_PAT='your-figma-pat-here'
python3 setup_figma_pages.py
```

### Option 2: Providing PAT Directly to the Script

Alternatively, you can provide the PAT directly as a command-line argument:

```bash
python3 setup_figma_pages.py YOUR_FIGMA_PAT
```

### Option 3: Using the GitHub CLI to Access Organization Secrets

If you have the GitHub CLI (`gh`) installed and configured, you can use it to access organization secrets:

```bash
# This is a hypothetical example - actual command depends on GitHub CLI capabilities
# and your organization's security policies
export FIGMA_PAT=$(gh secret get FIGMA_PAT -o your-org-name)
python3 setup_figma_pages.py
```

## Troubleshooting

### Authentication Issues

If you see an error like:
```
❌ Failed: 403 Forbidden. Details: {"status":403,"err":"Access denied, check token"}
```

This means your Figma PAT is invalid or doesn't have the necessary permissions. Ensure you:

1. Have a valid Figma PAT with "files:write" permission
2. Are using the correct PAT value (check for extra spaces or line breaks)
3. Have access to the specified Figma file

### Rate Limiting

Figma API has rate limits. If you encounter rate limiting errors, the script already includes a small delay between requests, but you might need to wait before trying again.

### File Access Issues

If you see an error about the file not being found, verify:
1. The File ID is correct (currently set to `368236963`)
2. Your Figma account has access to this file

## Script Details

The script creates the following pages in your Figma file:

- _Foundations & Variables
- _Core Components [Adapted]
- Web - Dashboard
- Web - Agents
- Web - Personas
- Web - Memory
- Web - Projects
- Web - Settings
- Web - TrainingGround
- Android - Core Screens
- Prototypes
- Archive

Each page is created sequentially, with status updates printed to the console.
