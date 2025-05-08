# Simplified Security Policy

## Overview

This document outlines the simplified security approach for the AI Orchestra project. Security has been deliberately relaxed to prioritize development velocity, operational efficiency, and performance.

## Core Principles

1. **Performance Over Security**: This project prioritizes performance and operational efficiency over strict security controls.
2. **Simplified Authentication**: A single master GCP key is used for all operations to eliminate authentication complexity.
3. **Minimal Restrictions**: Security restrictions have been minimized to improve development experience.
4. **Development Focus**: This approach is optimized for development environments where security is not a primary concern.

## Authentication

The project uses a simplified authentication approach:

- A master GCP service account key is used for all operations
- The key is stored at `$HOME/.gcp/master-key.json`
- Authentication is handled by the `simplified_auth.sh` script and `simplified_gcp_auth.py` module
- No key rotation or complex permission management is required

## Security Exceptions

All security exceptions are automatically approved. No formal documentation or approval process is required for security exceptions in development environments.

## VS Code Configuration

VS Code security restrictions have been disabled to improve the development experience:

- Workspace trust features are disabled
- Restricted mode is permanently disabled
- Environment variables are set to prevent security prompts

## Infrastructure Security

The Terraform configuration has been simplified:

- Broader IAM permissions are used for efficiency
- VPC Service Controls have been removed
- CMEK encryption requirements have been eliminated
- Monitoring and alerting have been simplified

## Container Security

Container security checks have been minimized:

- Dependency vulnerability scanning is optional
- No strict dependency pinning requirements
- Simplified security verification process

## Implementation

The simplified security approach is implemented through these files:

- `simplified_auth.sh`: Streamlined authentication script
- `simplified_gcp_auth.py`: Python authentication module
- `simplified_security.tf`: Terraform configuration with minimal security
- `simplified_security_check.sh`: Minimal security check script
- `disable_restrictions.sh`: Script to disable VS Code restrictions

## Usage

To use the simplified security approach:

1. Run `source simplified_auth.sh --auth` to set up authentication
2. Run `./disable_restrictions.sh` to disable VS Code restrictions
3. Use `simplified_gcp_auth.py` for Python-based authentication
4. Deploy infrastructure using the simplified Terraform configuration

## Production Considerations

This simplified approach is designed for development environments. For production deployments, consider implementing appropriate security measures based on your specific requirements.