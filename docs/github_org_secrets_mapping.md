# GitHub Organization Secrets Mapping

This document describes how to use the provided scripts to map GitHub organization-level secrets to your local `.env` file.

## Overview

The Orchestra project uses GitHub organization-level secrets for storing sensitive credentials that are shared across multiple repositories. This approach provides:

- **Centralized management** of credentials
- **Consistent access** across repositories
- **Reduced credential duplication**
- **Easier credential rotation**

However, when developing locally, you need these secrets available in your `.env` file. The scripts provided in this repository automate the process of mapping organization secrets to your local environment.

## Available Scripts

Two scripts are provided for different use cases:

1. **`scripts/update_github_org_secrets.sh`**: Interactive script for developers
2. **`scripts/update_github_org_secrets_ci.sh`**: Non-interactive script for CI/CD environments

## Prerequisites

Both scripts require:

- [GitHub CLI (gh)](https://cli.github.com/manual/installation) installed
- Authentication with GitHub (`gh auth login`)
- Appropriate permissions to access organization secrets

## Supported Secret Mappings

The following GitHub organization secrets are mapped to local environment variables:

| GitHub Organization Secret         | Local `.env` Variable          |
| ---------------------------------- | ------------------------------ |
| `ORG_| `ORG_| `ORG_| `ORG_VERTEX_KEY`                   | `VERTEX_KEY`                   |
| `ORG_| `ORG_| `ORG_GKE_CLUSTER_PROD`             | `GKE_CLUSTER_PROD`             |
| `ORG_GKE_CLUSTER_STAGING`          | `GKE_CLUSTER_STAGING`          |
| `ORG_PORTKEY_API_KEY`              | `PORTKEY_API_KEY`              |
| `ORG_TERRAFORM_API_KEY`            | `TERRAFORM_API_KEY`            |
| `ORG_TERRAFORM_ORGANIZATION_TOKEN` | `TERRAFORM_ORGANIZATION_TOKEN` |
| `ORG_REDIS_HOST`                   | `REDIS_HOST`                   |
| `ORG_REDIS_PORT`                   | `REDIS_PORT`                   |
| `ORG_REDIS_USER`                   | `REDIS_USER`                   |
| `ORG_REDIS_PASSWORD`               | `REDIS_PASSWORD`               |
| `ORG_REDIS_DATABASE_NAME`          | `REDIS_DATABASE_NAME`          |
| `ORG_REDIS_DATABASE_ENDPOINT`      | `REDIS_DATABASE_ENDPOINT`      |

## Using the Interactive Script

For local development, use the interactive script that guides you through the process:

```bash
./scripts/update_github_org_secrets.sh
```

This script will:

1. Automatically determine your GitHub organization from the repository
2. Fetch the list of available organization secrets
3. Create a backup of your existing `.env` file
4. Map organization secrets to your `.env` file with placeholder values
5. Provide instructions for next steps

**Note**: GitHub encrypts organization secrets in a way that prevents direct retrieval of values. The script adds placeholders to your `.env` file that you'll need to replace with actual values from a secure source.

## Using the Non-Interactive Script (for CI/CD)

For automated environments, use the non-interactive script:

```bash
./scripts/update_github_org_secrets_ci.sh --org your-github-org --yes
```

Arguments:

- `--org <name>`: (Required) GitHub organization name
- `--yes`: (Optional) Skip all confirmations (for CI/CD environments)
- `--env-file <path>`: (Optional) Custom path to `.env` file

Example for CI/CD pipeline:

```bash
./scripts/update_github_org_secrets_ci.sh --org orchestra-project --yes
```

## Security Note

These scripts do not retrieve the actual secret values from GitHub (as GitHub makes this impossible by design). Instead, they create a structure in your `.env` file that shows what values you need to set.

For production environments, consider using:

- Google - AWS Secrets Manager for AWS deployments

## Troubleshooting

### Common Issues

1. **"Not authenticated with GitHub CLI"**

   ```bash
   gh auth login
   ```

2. **"Cannot access organization"**

   - Verify organization name
   - Ensure you're a member of the organization
   - Check you have sufficient permissions

3. **"No secrets found or insufficient permissions"**
   - Organization admin permissions are required to list secrets
   - Contact your organization administrator

### Getting Help

If you encounter issues with these scripts, please:

1. Check the error messages for specific guidance
2. Review the script code for error handling
3. Contact your organization's DevOps or Infrastructure team

## Extending the Scripts

If you need to map additional organization secrets:

1. Update the `SECRET_MAPPING` associative array in each script
2. Update this documentation to reflect the new mappings
3. Consider adding validation for the new environment variables

Example for adding a new secret mapping:

```bash
# In both scripts, add to the SECRET_MAPPING array:
declare -A SECRET_MAPPING=(
  # Existing mappings...
  ["ORG_NEW_SECRET_NAME"]="LOCAL_ENV_VAR_NAME"
)
```

## Integration with CI/CD

For GitHub Actions, you can add the following step to your workflow:

```yaml
- name: Update environment from organization secrets
  run: |
    # Install GitHub CLI
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh

    # Authenticate (using the GITHUB_TOKEN provided by Actions)
    echo "${{ secrets.GITHUB_TOKEN }}" | gh auth login --with-token

    # Run the script
    ./scripts/update_github_org_secrets_ci.sh --org ${{ github.repository_owner }} --yes
```

## Best Practices

1. **Regular Updates**: Run the script whenever organization secrets are updated
2. **Credential Rotation**: Regularly rotate secrets according to your security policy
3. **Verification**: Always verify credentials work after updates
4. **Secure Storage**: Never commit real secret values to the repository
5. **Least Privilege**: Ensure service accounts have minimal required permissions

## Conclusion

By using these scripts and following GitHub organization secrets best practices, you can maintain secure and consistent credential management across your development environments and CI/CD pipelines.
