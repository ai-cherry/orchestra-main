# Orchestra Credential Setup Guide

This guide provides comprehensive instructions for setting up all required credentials needed to run Orchestra locally or in a Codespaces environment. It covers GCP authentication, LLM provider keys, Portkey integration, and tool-specific credentials.

## Quick Start

For a guided setup experience, run:

```bash
./setup_credentials.sh
```

This interactive script will:
1. Create or update your `.env` file with necessary environment variables
2. Optionally create Portkey virtual keys for you
3. Verify that your credentials are working properly

## Required Credentials Overview

Orchestra requires several sets of credentials to function properly:

### 1. GCP Authentication

These credentials allow Orchestra to connect to Google Cloud Platform services like Firestore and Redis:

- `GCP_PROJECT_ID`: The Google Cloud project ID (e.g., "agi-baby-cherry")
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your GCP service account key JSON file
- `GCP_SA_KEY_PATH`: Alternative reference to the same key file

### 2. LLM Provider Authentication

Orchestra uses various LLM providers through Portkey:

#### Portkey Integration
- `PORTKEY_API_KEY`: Your primary Portkey API key
- `MASTER_PORTKEY_ADMIN_KEY`: Admin key for managing Portkey virtual keys
- `PREFERRED_LLM_PROVIDER`: Set to "portkey" for Portkey integration

#### Portkey Virtual Keys
These virtual keys map to actual provider API keys stored in Portkey:
- `PORTKEY_VIRTUAL_KEY_OPENAI`: Virtual key for OpenAI
- `PORTKEY_VIRTUAL_KEY_ANTHROPIC`: Virtual key for Anthropic
- `PORTKEY_VIRTUAL_KEY_OPENROUTER`: Virtual key for OpenRouter

#### Native LLM Keys
Even when using Portkey virtual keys, the actual provider keys are needed for authentication headers:
- `OPENAI_API_KEY`: Direct OpenAI API key
- `ANTHROPIC_API_KEY`: Direct Anthropic API key
- `OPENROUTER_API_KEY`: Direct OpenRouter API key

### 3. Tool-Specific Credentials

For specialized tools like the Salesforce integration:
- `SALESFORCE_USERNAME`: Salesforce account username
- `SALESFORCE_PASSWORD`: Salesforce account password
- `SALESFORCE_SECURITY_TOKEN`: Salesforce security token

### 4. Memory Configuration

Settings for the Orchestra memory system:
- `MEMORY_ENVIRONMENT`: Environment name (e.g., "dev", "prod")
- `MEMORY_ENABLE_DEV_NOTES`: Whether to store development notes
- `MEMORY_DEFAULT_PRIVACY_LEVEL`: Default privacy level for memory storage
- `MEMORY_ENFORCE_PRIVACY`: Whether to enforce privacy classification

## Obtaining the Credentials

### GCP Service Account Key

1. Log in to the GCP Console: https://console.cloud.google.com/
2. Navigate to IAM & Admin > Service Accounts
3. Create a new service account or select an existing one
4. Create a new key (JSON type) and download it
5. Store it securely and reference its path in your `.env` file

### Portkey API Keys

1. Sign up for a Portkey account at https://app.portkey.ai/
2. On the Settings page, create an API key
3. For the admin key, create a key with admin privileges

### Creating Portkey Virtual Keys

Virtual keys can be created using our management script:

```bash
# Set your Portkey Admin API key
export MASTER_PORTKEY_ADMIN_KEY="your-admin-key"

# Create virtual keys for each provider
python scripts/manage_portkey_keys.py create-key \
  --name "OpenAI-Dev" \
  --provider openai \
  --key "sk-..."
```

Or you can create them through the Portkey dashboard.

### LLM Provider API Keys

Obtain direct API keys from each provider:
- OpenAI: https://platform.openai.com/account/api-keys
- Anthropic: https://console.anthropic.com/account/keys
- OpenRouter: https://openrouter.ai/keys

### Salesforce Credentials

To use the Salesforce integration tools:
1. Log in to your Salesforce account
2. Go to Settings > My Personal Information > Reset Security Token
3. Salesforce will email you a new security token

## Environment Variables Reference

Here's a complete reference of all environment variables used by Orchestra:

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| **GCP Authentication** |
| `GCP_PROJECT_ID` | Yes | GCP project identifier | "agi-baby-cherry" |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to service account key | "/tmp/vertex-agent-key.json" |
| `GCP_SA_KEY_PATH` | Yes | Path to service account key | "/tmp/vertex-agent-key.json" |
| **Redis Configuration** |
| `REDIS_HOST` | Yes | Redis host address | "localhost" or GCP Redis host |
| `REDIS_PORT` | Yes | Redis port | "6379" |
| `REDIS_PASSWORD_SECRET_NAME` | Yes | Name of Redis password secret | "redis-auth-dev" |
| **LLM Provider Configuration** |
| `PORTKEY_API_KEY` | Yes | Portkey API key | "pk-..." |
| `PREFERRED_LLM_PROVIDER` | Yes | Default LLM provider | "portkey" |
| `MASTER_PORTKEY_ADMIN_KEY` | Only for key management | Admin key for Portkey | "pk-admin-..." |
| **Native LLM API Keys** |
| `OPENAI_API_KEY` | Yes | OpenAI API key | "sk-..." |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key | "sk-ant-..." |
| `OPENROUTER_API_KEY` | Optional | OpenRouter API key | "sk-or-..." |
| **Portkey Virtual Keys** |
| `PORTKEY_VIRTUAL_KEY_OPENAI` | Yes | Virtual key for OpenAI | "vk_openai_..." |
| `PORTKEY_VIRTUAL_KEY_ANTHROPIC` | Optional | Virtual key for Anthropic | "vk_anthropic_..." |
| `PORTKEY_VIRTUAL_KEY_OPENROUTER` | Optional | Virtual key for OpenRouter | "vk_openrouter_..." |
| **Portkey Gateway Configuration** |
| `PORTKEY_CONFIG_ID` | Optional | Gateway configuration ID | "gw_config_..." |
| `PORTKEY_STRATEGY` | Optional | Routing strategy | "fallback" |
| `PORTKEY_CACHE_ENABLED` | Optional | Enable semantic caching | "true" |
| **Salesforce Credentials** |
| `SALESFORCE_USERNAME` | Optional | Salesforce username | "user@example.com" |
| `SALESFORCE_PASSWORD` | Optional | Salesforce password | "password" |
| `SALESFORCE_SECURITY_TOKEN` | Optional | Salesforce security token | "abcd1234..." |
| **Memory Configuration** |
| `MEMORY_ENVIRONMENT` | Optional | Environment name | "dev" |
| `MEMORY_ENABLE_DEV_NOTES` | Optional | Enable dev notes | "true" |
| `MEMORY_DEFAULT_PRIVACY_LEVEL` | Optional | Default privacy level | "standard" |
| `MEMORY_ENFORCE_PRIVACY` | Optional | Enforce privacy classification | "false" |
| **Testing Configuration** |
| `RUN_INTEGRATION_TESTS` | Optional | Enable integration tests | "true" |

## Verification Tests

After setting up your credentials, verify they're working properly:

### 1. Verify GCP Authentication and Memory System
```bash
python validate_memory_fixes.py
```

Expected output: Successful initialization of memory manager and core operations.

### 2. Test LLM Integration with Portkey
```bash
python -m packages.llm.src.test_phidata_integration
```

Expected output: Successful connection to LLM providers through Portkey.

### 3. Test Tool Integration
```bash
python -m packages.tools.src.test_phidata_integration
```

Expected output: Successful tool operations.

### 4. Run Full Integration Tests
```bash
export RUN_INTEGRATION_TESTS=true
./run_integration_tests.sh
```

## Security Best Practices

- **Never commit your `.env` file to version control**
- Rotate your API keys periodically
- Use Portkey virtual keys to simplify key management
- Set budget limits on your API keys to prevent unexpected costs
- Follow the principle of least privilege for service accounts

## Troubleshooting

### GCP Authentication Issues
- Verify your service account key is valid and not expired
- Check that your service account has the necessary permissions
- Ensure the project ID matches your actual GCP project

### Portkey Integration Issues
- Check that both your Portkey API key and provider keys are valid
- Verify that you've created virtual keys correctly
- Ensure the Portkey service is available

### Memory System Issues
- Check that Firestore is enabled in your GCP project
- Verify Redis connection parameters

### LLM Response Issues
- Check rate limits on your API keys
- Verify that the requested models are available
- Check for syntax errors in your prompts

## Need Help?

For additional assistance:
- Check the [docs](./docs/) directory for more detailed guides
- Review integration test outputs for specific error messages
- Consult the official documentation for each service
