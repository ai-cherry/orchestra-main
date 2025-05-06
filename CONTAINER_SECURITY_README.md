# Container Verification & Security Guide

This document provides instructions for verifying your development container setup and ensuring your Python dependencies are secure.

## Overview

After rebuilding your development container with the updated configuration in `.devcontainer/devcontainer.json`, you should verify:

1. **Environment Setup**: Ensure all required tools are installed and configured correctly
2. **Dependency Security**: Check for security vulnerabilities in your Python dependencies

Two scripts are provided to help with these tasks:

- `verify_container.sh`: Verifies the development environment setup
- `security_check.sh`: Checks for security vulnerabilities in dependencies

## Quick Start

After rebuilding your container, run:

```bash
# 1. Verify container setup
./verify_container.sh

# 2. Check for security vulnerabilities
./security_check.sh
```

## Verification Process

### 1. Environment Verification

Running `./verify_container.sh` will:

- Check that Python 3.11 is installed correctly
- Verify Poetry is available and working
- Confirm Docker is properly configured
- Ensure Terraform 1.5.x is installed
- Install project dependencies with `poetry install --with dev`

For detailed information, see [Container Verification Guide](container_verification_guide.md).

### 2. Security Verification

Running `./security_check.sh` will:

- Update pip to the latest version
- Create a `.safety-policy.yml` file (if it doesn't exist) that checks unpinned dependencies
- Scan your requirements files for security vulnerabilities using the recommended `safety scan` command
- Provide security recommendations

For detailed information, see [Security Check Guide](security_check_guide.md).

## Key Improvements

The scripts address several important issues:

1. **Environment Consistency**: Ensuring all developers use the same tooling versions
2. **Unpinned Dependencies**: The security script identifies vulnerabilities in unpinned dependencies (which are ignored by default)
3. **Deprecated Command**: Switches from the deprecated `safety check` command to the new `safety scan` command
4. **Security Policy**: Creates a custom security policy that addresses your project's specific needs

## Container Configuration

The `.devcontainer/devcontainer.json` file has been updated to:

- Use `mcr.microsoft.com/devcontainers/python:3.11` as the base image
- Include features for Poetry, Terraform 1.5.x, and Docker-outside-of-Docker
- Add necessary VS Code extensions
- Ensure dependencies are installed with `poetry install --with dev`

## Best Practices

For optimal security and consistency:

1. **Pin Dependencies**: Use exact versions (`==`) rather than ranges (`>=`) for production applications
2. **Regular Security Checks**: Run the security check script regularly, especially after adding new dependencies
3. **CI/CD Integration**: Add these checks to your CI/CD pipeline to prevent deploying vulnerable code
4. **Update Tools**: Keep tools like pip, safety, and Poetry updated to their latest versions

## Troubleshooting

If you encounter issues:

1. **Container Rebuild**: Make sure you've rebuilt your container after updating the configuration
2. **Path Issues**: Verify the tools are correctly added to your PATH
3. **Permission Errors**: Ensure both scripts are executable (`chmod +x script.sh`)
4. **Requirements Format**: For Poetry projects, you may need to export requirements with `poetry export -f requirements.txt --output requirements.txt`
