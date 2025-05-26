# Orchestra AI Secret Management

## Overview

Orchestra AI uses Pulumi for centralized secret management. All secrets are stored encrypted in Pulumi's state backend and never committed to git.

## Architecture

```
┌─────────────────────┐
│ config/             │
│ managed-services.env│ ──── Local file with actual secrets (NEVER commit!)
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Pulumi Config       │ ──── Encrypted storage in Pulumi state
│ (infra/Pulumi.*.yaml)│
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ .env file           │ ──── Generated from Pulumi for local development
│ (auto-generated)    │
└─────────────────────┘
```

## Setup Process

### 1. Initial Setup

```bash
# Set Pulumi passphrase
export PULUMI_CONFIG_PASSPHRASE="orchestra-dev-123"

# Load secrets from managed services config
source config/managed-services.env

# Run setup script to store in Pulumi
./scripts/setup_all_secrets.sh
```

### 2. Generate Local .env

```bash
# Generate .env from Pulumi secrets
python scripts/generate_env_from_pulumi.py

# Source the environment
source .env
```

## Secret Categories

### Database Services
- `MONGODB_URI` - MongoDB Atlas connection string
- `DRAGONFLY_URI` - DragonflyDB cloud connection

### Vector Search
- `WEAVIATE_URL` - Weaviate cloud endpoint
- `WEAVIATE_API_KEY` - Weaviate API key

### LLM Services
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `OPENROUTER_API_KEY` - OpenRouter API key
- `PORTKEY_API_KEY` - Portkey gateway API key

### Deployment
- `DIGITALOCEAN_TOKEN` - DigitalOcean API token
- `PULUMI_ACCESS_TOKEN` - Pulumi cloud access token

## Security Best Practices

1. **Never commit secrets to git**
   - `.env` is in `.gitignore`
   - `config/managed-services.env` should never be committed
   - Use `.env.example` for documentation

2. **Use Pulumi for all environments**
   - Dev: `pulumi stack select dev`
   - Staging: `pulumi stack select staging`
   - Prod: `pulumi stack select prod`

3. **Rotate secrets regularly**
   - Update in Pulumi: `pulumi config set --secret <key> <new-value>`
   - Regenerate .env: `python scripts/generate_env_from_pulumi.py`

4. **Access control**
   - Pulumi passphrase protects local access
   - Pulumi cloud RBAC for team access
   - Service-specific API key permissions

## Troubleshooting

### Wrong passphrase error
```bash
export PULUMI_CONFIG_PASSPHRASE="orchestra-dev-123"
```

### Missing secrets
```bash
# Check what's configured
cd infra && pulumi config --show-secrets

# Add missing secret
pulumi config set --secret <key> <value>
```

### Environment not loading
```bash
# Regenerate .env
python scripts/generate_env_from_pulumi.py

# Source it
source .env

# Verify
env | grep -E "(MONGODB|WEAVIATE|OPENAI)"
```

## CI/CD Integration

For GitHub Actions or other CI/CD:

1. Set `PULUMI_ACCESS_TOKEN` as a repository secret
2. Set `PULUMI_CONFIG_PASSPHRASE` as a repository secret
3. Use Pulumi CLI to access secrets during deployment

```yaml
- name: Configure Pulumi
  env:
    PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
    PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}
  run: |
    cd infra
    pulumi stack select ${{ env.ENVIRONMENT }}
    pulumi config --show-secrets
```

## Migration from Other Systems

### From GitHub Secrets
Use the migration script (if needed):
```bash
python scripts/migrate_github_to_pulumi.py
```

### From .env files
```bash
# Source old .env
source .env.old

# Run setup script
./scripts/setup_all_secrets.sh
```
