#  Secrets Management Guide

This document outlines the standard operating procedure for managing secrets within the Orchestra AI project. All secrets are managed centrally using **Pulumi ESC (Environments, Secrets, and Configuration)** to ensure security, consistency, and ease of use for Infrastructure as Code (IaC) operations.

## 🔑 Core Principles

1.  **Single Source of Truth**: Pulumi ESC is the *only* place where secrets are stored. No API keys, tokens, or other sensitive values should ever be stored in `.env` files, committed to Git, or passed directly via the command line.
2.  **Hierarchical Environments**: We use a three-tiered environment structure to separate concerns and provide a clear inheritance model:
    *   `scoobyjava/default/base`: Holds all common secrets and configuration shared across all environments. **All API keys go here.**
    *   `scoobyjava/default/dev`: Inherits from `base` and contains development-specific overrides.
    *   `scoobyjava/default/staging`: Inherits from `base` and contains staging-specific overrides.
    *   `scoobyjava/default/prod`: Inherits from `base` and contains production-specific overrides.
3.  **Secure by Default**: All sensitive values are stored as secrets, encrypted at rest and in transit.

## 🛠️ How to Manage Secrets

All commands should be run from the `infrastructure/pulumi` directory.

### Adding or Updating a Secret

To add a new secret or update an existing one, use the `pulumi env set` command with the `--secret` flag. All API keys should be added to the `base` environment.

**Syntax:**
```bash
pulumi env set <environment_name> secrets.<secret_name> <value> --secret
```

**Example: Updating the OpenAI API Key**
```bash
# This will prompt for the value securely
pulumi env set scoobyjava/default/base secrets.openai_api_key --secret
```
Or, you can pipe the value in from a file or environment variable:
```bash
cat ~/.my_keys/openai.key | pulumi env set scoobyjava/default/base secrets.openai_api_key --secret
```

### Viewing a Secret (Requires Permissions)

To view the value of a secret (which should be done rarely), use the `pulumi env get` command.

```bash
pulumi env get scoobyjava/default/base secrets.openai_api_key
```

## 🤖 Access for IaC & Cursor AI

The main Pulumi program (`__main__.py`) is already configured to automatically and securely access these secrets.

**How it Works:**

1.  **Automatic Environment Loading**: When you run `pulumi up`, Pulumi automatically detects the current stack (e.g., `dev`) and loads the corresponding ESC environment (`scoobyjava/default/dev`).
2.  **Configuration Object**: The code uses `config = Config("pulumi:environment")` to load the entire environment's values into a configuration object.
3.  **Secure Access**: Secrets are accessed via `config.require_object("secrets").require_secret("secret_name")`. This method ensures that the secret value is only ever decrypted in memory during the Pulumi run and is never exposed in plaintext in the logs or state files.

**For Cursor AI:**

When you instruct Cursor AI to perform IaC tasks, it will use the existing `__main__.py` program. Since the program is already configured to use Pulumi ESC, **Cursor AI will automatically have secure access to all the necessary API keys without any additional configuration.** You can simply instruct it to add a new resource that requires a key (e.g., "Create a new Vercel project"), and it will be able to retrieve the `vercel_api_key` from the secure store.

## ✅ List of Managed Secrets

The following secrets are managed in the `scoobyjava/default/base` environment under the `secrets` object:

*   `github_token`
*   `openai_api_key`
*   `anthropic_api_key`
*   `pulumi_access_token`
*   `notion_api_key`
*   `openrouter_api_key`
*   `pinecone_api_key`
*   `vercel_api_key`
*   `weaviate_api_key`
*   `lambda_api_key`

This unified structure ensures that our secret management is secure, consistent, and seamlessly available to our IaC workflows. 